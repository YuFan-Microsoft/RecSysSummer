import os
# os.environ["CUDA_VISIBLE_DEVICES"] = "0"

from typing import Dict, List, Optional
import numpy as np
import fire
import torch
import transformers
from peft import TrainableTokensConfig, get_peft_model
from transformers import EarlyStoppingCallback, AutoConfig
import math
from functools import partial
from torch.optim.lr_scheduler import LambdaLR
import json
from contextlib import contextmanager
from transformers import AutoModelForCausalLM, AutoTokenizer
from data_Qwen3 import SidSFTDataset, SidItemFeatDataset, ReasoningActivationDataset
import random
from datasets import Dataset as HFDataset


class MultiEvalTrainer(transformers.Trainer):
    """
    Runs the default evaluation and then iterates through any extra eval sets so every epoch
    produces loss numbers for the auxiliary datasets as well.
    """

    def __init__(self, *args, extra_eval_sets: Optional[Dict[str, HFDataset]] = None, **kwargs):
        self.extra_eval_sets = extra_eval_sets or {}
        super().__init__(*args, **kwargs)

    @contextmanager
    def _disable_callback(self, callback_cls):
        callbacks = self.callback_handler.callbacks
        removed = [cb for cb in callbacks if isinstance(cb, callback_cls)]
        if not removed:
            yield
            return
        self.callback_handler.callbacks = [cb for cb in callbacks if not isinstance(cb, callback_cls)]
        try:
            yield
        finally:
            self.callback_handler.callbacks = callbacks

    def evaluate(
        self,
        eval_dataset: Optional[HFDataset] = None,
        ignore_keys: Optional[List[str]] = None,
        metric_key_prefix: str = "eval",
    ):
        metrics = super().evaluate(
            eval_dataset=eval_dataset,
            ignore_keys=ignore_keys,
            metric_key_prefix=metric_key_prefix,
        )

        if not self.extra_eval_sets:
            return metrics

        for name, dataset in self.extra_eval_sets.items():
            if dataset is None:
                continue
            with self._disable_callback(EarlyStoppingCallback):
                extra_metrics = super().evaluate(
                    eval_dataset=dataset,
                    ignore_keys=ignore_keys,
                    metric_key_prefix=f"{metric_key_prefix}_{name}",
                )
            self.log(extra_metrics)
            metrics.update(extra_metrics)
        return metrics


class TokenExtender:
    def __init__(self, data_path, dataset, index_file=".index.json"):
        self.data_path = data_path
        self.dataset = dataset
        self.index_file = index_file
        self.indices = None
        self.new_tokens = None
        
    def _load_data(self):
        import hf_data
        self.indices = hf_data.load_indices(os.path.join(self.data_path, self.dataset + self.index_file))
    
    def get_new_tokens(self):
        if self.new_tokens is not None:
            return self.new_tokens
            
        if self.indices is None:
            self._load_data()
        
        self.new_tokens = set()
        for index in self.indices.values():
            for token in index:
                self.new_tokens.add(token)
        self.new_tokens = sorted(list(self.new_tokens))
        
        return self.new_tokens


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)  # if you are using multi-GPU.
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def _decode_tokens(tokens, tokenizer_ref):
    if not isinstance(tokens, (list, tuple)):
        return ""
    valid_ids = [tid for tid in tokens if isinstance(tid, int) and tid >= 0]
    if not valid_ids:
        return ""
    return tokenizer_ref.decode(valid_ids, skip_special_tokens=False)

def _preview_dataset(dataset, name, tokenizer_ref, max_samples=3):
    print(f"[Preview] {name}: displaying up to {max_samples} samples")
    preview_count = min(max_samples, len(dataset))
    for idx in range(preview_count):
        sample = dataset[idx]
        input_text = ""
        # label_text = ""
        if isinstance(sample, dict):
            if "input_ids" in sample:
                input_text = _decode_tokens(sample["input_ids"], tokenizer_ref)
            if "labels" in sample:
                # Filter label padding tokens (e.g., -100) before decoding for readability
                label_ids = [tid for tid in sample["labels"] if isinstance(tid, int) and tid >= 0]
                label_text = _decode_tokens(label_ids, tokenizer_ref)
        print(f"Sample {idx + 1}:")
        if input_text:
            print(f"  Input : {input_text}")
        if label_text:
            print(f"  Label : {label_text}")
            print(f"  Length: {len(label_ids)} tokens")
        print()



def _get_cosine_schedule_with_warmup_lr_lambda(
    current_step, *, num_warmup_steps, num_training_steps, num_cycles
):
    if current_step < num_warmup_steps:
        return max(0.1, float(current_step) / float(max(1, num_warmup_steps)))
    progress = float(current_step - num_warmup_steps) / float(max(1, num_training_steps - num_warmup_steps))
    return max(0.1, 0.5 * (1.0 + math.cos(math.pi * float(num_cycles) * 2.0 * progress)))

def get_cosine_schedule_with_warmup(
    optimizer, num_warmup_steps, num_training_steps, num_cycles: float = 0.5, last_epoch: int = -1
):

    lr_lambda = partial(
        _get_cosine_schedule_with_warmup_lr_lambda,
        num_warmup_steps=num_warmup_steps,
        num_training_steps=num_training_steps,
        num_cycles=num_cycles,
    )
    return LambdaLR(optimizer, lr_lambda, last_epoch)


def train(
    # model/data params
    base_model: str = "./output_dir/Office_Products_stage1_sft_Qwen3-1.7B/final_checkpoint",
    train_file: str = "./data/Amazon/train/Office_Products_5_2016-10-2018-11.csv",
    eval_file: str = "./data/Amazon/valid/Office_Products_5_2016-10-2018-11.csv",
    output_dir: str = "./output_dir/Office_Products_stage2_reasoning_activation_Qwen3-1.7B",
    sample: int = -1,
    seed: int = 42,
    category: str = "Office_Products",
    
    # training hyperparams
    batch_size: int = 1024,
    micro_batch_size: int = 8,
    num_epochs: int = 5,
    learning_rate: float = 1e-5,
    cutoff_len: int = 1024,
    # llm hyperparams
    group_by_length: bool = False,  # faster, but produces an odd training loss curve
    # wandb params
    wandb_project: str = "MiniOneRec",
    wandb_run_name: str = "Office_Products_stage2_reasoning_activation_Qwen3-1.7B",
    resume_from_checkpoint: str = None,  # either training checkpoint or final adapter
    train_from_scratch: bool = False,
    sid_index_path: str = "./data/Amazon/index/Office_Products.index.json",
    item_meta_path: str = "./data/Amazon/index/Office_Products.item.json",
    reasoning_train_file: str = "./data/Amazon/index/Office_Products.integrated_narrative.csv",
    train_new_token_embeddings_only: bool = False,
):
    set_seed(seed)
    os.environ['WANDB_PROJECT'] = wandb_project
    category_dict = {"Industrial_and_Scientific": "industrial and scientific items", "Office_Products": "office products", "Toys_and_Games": "toys and games", "Sports": "sports and outdoors", "Books": "books", "Video_Games": "video games"}
    if category not in category_dict:
        category = "items"
    else:   
        category = category_dict[category]
        
    assert (
        base_model
    ), "Please specify a --base_model, e.g. --base_model='decapoda-research/llama-7b-hf'"
    gradient_accumulation_steps = batch_size // micro_batch_size
    
    world_size = int(os.environ.get("WORLD_SIZE", 1))
    ddp = world_size != 1
    if ddp:
        gradient_accumulation_steps = gradient_accumulation_steps // world_size

    if not train_from_scratch:
        model = AutoModelForCausalLM.from_pretrained(
            base_model,
            torch_dtype=torch.bfloat16,
        )
    else:
        config = AutoConfig.from_pretrained(base_model)
        model = AutoModelForCausalLM.from_config(config)
        print("Training from scratch!")
        
    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.pad_token_id = tokenizer.eos_token_id
    tokenizer.padding_side = "left"

    print(f"Tokenizer length: {len(tokenizer)}")
    
    if sid_index_path:
        print(f"Loading index from {sid_index_path}")
        token_extender = TokenExtender(
            data_path=os.path.dirname(sid_index_path),
            dataset=os.path.basename(sid_index_path).split('.')[0]
        )
        new_tokens = token_extender.get_new_tokens()
        if new_tokens:
            existing_vocab = set(tokenizer.get_vocab().keys())
            tokens_to_add = [tok for tok in new_tokens if tok not in existing_vocab]
            if tokens_to_add:
                print(f"Adding {len(tokens_to_add)} new tokens to tokenizer")
                tokenizer.add_tokens(tokens_to_add)
                model.resize_token_embeddings(len(tokenizer))
                num_new_tokens = len(tokens_to_add)
            else:
                print("All candidate tokens already exist in the tokenizer; skipping addition.")
                num_new_tokens = 0
        else:
            num_new_tokens = 0
    else:
        new_tokens = []
        num_new_tokens = 0

    if train_new_token_embeddings_only:
        if num_new_tokens > 0:
            vocab_size = len(tokenizer)
            new_token_indices = list(range(vocab_size - num_new_tokens, vocab_size))
            print(f"Restricting training to new token ids.")
            peft_config = TrainableTokensConfig(
                token_indices=new_token_indices,
                target_modules=["embed_tokens"],
                init_weights=True,
            )
            model = get_peft_model(model, peft_config)
            model.print_trainable_parameters()
    else:
        print("Full fine-tuning enabled: attention blocks, FFNs, and embeddings remain trainable.")

    if num_new_tokens == 0 and train_new_token_embeddings_only:
        print("No new tokens added; the entire model will remain trainable.")

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    percent = (trainable_params / total_params) * 100 if total_params > 0 else 0.0
    print(f"Trainable parameters: {trainable_params} / {total_params} ({percent:.4f}%)")
        

    train_data = ReasoningActivationDataset(reasoning_train_file=reasoning_train_file, item_file=item_meta_path, index_file=sid_index_path, tokenizer=tokenizer, max_len=cutoff_len,  sample=sample, seed=seed, category=category)
    main_rank = int(os.environ.get("RANK", 0)) == 0 and int(os.environ.get("LOCAL_RANK", 0)) == 0
    if main_rank:
        train_dataset_names = [
            "ReasoningActivationDataset",
        ]
        for ds, name in zip([train_data], train_dataset_names):
            _preview_dataset(ds, name, tokenizer)

    val_data_sid_prediction = SidSFTDataset(train_file=eval_file, tokenizer=tokenizer, max_len=cutoff_len,  sample=sample, seed=seed, category=category, test=False, mask_assistant=True)
    val_data_title2sid_translation = SidItemFeatDataset(item_file=item_meta_path, index_file=sid_index_path, tokenizer=tokenizer, max_len=cutoff_len,  sample=sample, seed=seed, category=category, task_type='title2sid', test=False, mask_assistant=True)
    val_data_sid2title_translation = SidItemFeatDataset(item_file=item_meta_path, index_file=sid_index_path, tokenizer=tokenizer, max_len=cutoff_len,  sample=sample, seed=seed, category=category, task_type='sid2title', test=False, mask_assistant=True)
    print("LOAD DATA FINISHED")    
    
    if not ddp and torch.cuda.device_count() > 1:
        model.is_parallelizable = True
        model.model_parallel = True
    
    sample_frac = 1
    hf_train_dataset = HFDataset.from_dict({k: [v[k] for v in train_data] for k in train_data[0].keys()})
    hf_train_dataset = hf_train_dataset.shuffle(seed=42).select(range(int(sample_frac * len(hf_train_dataset))))
    hf_val_dataset = HFDataset.from_dict({k: [v[k] for v in val_data_sid_prediction] for k in val_data_sid_prediction[0].keys()}).shuffle(seed=seed)
    hf_val_dataset = hf_val_dataset.shuffle(seed=42)
    # additional eval set for translation performance
    hf_eval_dataset_title2sid_translation = HFDataset.from_dict({k: [v[k] for v in val_data_title2sid_translation] for k in val_data_title2sid_translation[0].keys()}).shuffle(seed=seed)
    hf_eval_dataset_title2sid_translation = hf_eval_dataset_title2sid_translation.shuffle(seed=42)
    hf_eval_dataset_sid2title_translation = HFDataset.from_dict({k: [v[k] for v in val_data_sid2title_translation] for k in val_data_sid2title_translation[0].keys()}).shuffle(seed=seed)
    hf_eval_dataset_sid2title_translation = hf_eval_dataset_sid2title_translation.shuffle(seed=42)

    extra_eval_sets = {
        "title2sid": hf_eval_dataset_title2sid_translation,
        "sid2title": hf_eval_dataset_sid2title_translation,
    }

    print(hf_train_dataset)
    print(hf_val_dataset)
    print(hf_eval_dataset_title2sid_translation)
    print(hf_eval_dataset_sid2title_translation)

    # eval_step = 0.05
    trainer = MultiEvalTrainer(
        # deepspeed=deepspeed,
        model=model,
        # train_dataset=hf_train_dataset.select(range(128)),
        train_dataset=hf_train_dataset,
        eval_dataset=hf_val_dataset,
        extra_eval_sets=extra_eval_sets,
        args=transformers.TrainingArguments(
            # deepspeed=deepspeed,
            run_name=wandb_run_name,
            per_device_train_batch_size=micro_batch_size,
            per_device_eval_batch_size=micro_batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            warmup_steps=10,
            num_train_epochs=num_epochs,
            learning_rate=learning_rate,
            bf16=True,
            logging_steps=1,
            optim="adamw_torch",
            # eval_strategy="steps",
            # eval_steps=100,
            # save_strategy="steps",
            # save_steps=100,
            eval_strategy="epoch",
            save_strategy="epoch",
            metric_for_best_model="eval_loss",
            greater_is_better=False,

            output_dir=output_dir,
            save_total_limit=10,
            load_best_model_at_end=True,
            ddp_find_unused_parameters=False if ddp else None,
            group_by_length=group_by_length,
            report_to="wandb",
        ),
        data_collator=transformers.DataCollatorForSeq2Seq(
            tokenizer, pad_to_multiple_of=8, return_tensors="pt", padding=True
        ),
        callbacks = [
            EarlyStoppingCallback(early_stopping_patience=5),
        ],
        # optimizers=(optimizer, lr_scheduler) 
    )
    model.config.use_cache = False

    # evaluate first before training
    # trainer.evaluate()

    trainer.train(resume_from_checkpoint=resume_from_checkpoint)
    # trainer.save_model(output_dir)
    
    model.state_dict()
    output_dir = os.path.join(output_dir, "final_checkpoint")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)



if __name__ == "__main__":
    fire.Fire(train)
