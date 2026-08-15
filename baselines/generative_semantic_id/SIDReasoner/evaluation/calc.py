import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
# from transformers import GenerationConfig, LlamaForCausalLM, LlamaTokenizer
# import transformers
# import torch
import fire
import json
import math
import numpy as np
from pathlib import Path

from evaluation.evaluate_phase2_checkpoint import calculate_metrics, write_results_jsonl
    
from tqdm import tqdm
def gao(path, item_path):
    if type(path) != list:
        path = [path]
    if item_path.endswith(".txt"):
        item_path = item_path[:-4]
    CC=0
        
    
    import hf_data
    items = hf_data.load_info_lines(f"{item_path}.txt")
    # item_names = [ _[:-len(_.split('\t')[-1])].strip() for _ in items]
    item_names= [_.split('\t')[0].strip() for _ in items]
    item_ids = [_ for _ in range(len(item_names))]
    item_dict = dict()
    for i in range(len(item_names)):
        if item_names[i] not in item_dict:
            item_dict[item_names[i]] = [item_ids[i]]
        else:   
            item_dict[item_names[i]].append(item_ids[i])
    
    

    result_dict = dict()
    topk_list = [1, 3, 5, 10, 20, 50]
    n_beam = -1
    for p in path:
        result_dict[p] = {
            "NDCG": [],
            "HR": [],
        }
        f = open(p, 'r')
        import json
        test_data = json.load(f)
        f.close()
        
        text = [ [_.strip("\"\n").strip() for _ in sample["predict"]] for sample in test_data]
        
        for index, sample in tqdm(enumerate(text)):
            if n_beam == -1:
                n_beam = len(sample)
                valid_topk = [k for k in topk_list if k <= n_beam]
                ALLNDCG = np.zeros(len(valid_topk))
                ALLHR = np.zeros(len(valid_topk))
            if type(test_data[index]['output']) == list:
                target_item = test_data[index]['output'][0].strip("\"").strip(" ")
            else:
                target_item = test_data[index]['output'].strip(" \n\"")
            minID = 1000000
            for i in range(len(sample)):
                
                if sample[i] not in item_dict:
                    CC += 1
                    print(sample[i])
                    print(target_item)
                if sample[i] == target_item:
                    minID = i
                    break
            
            for index, topk in enumerate(topk_list):
                if topk > n_beam:
                    continue
                if minID < topk:
                    ALLNDCG[index] = ALLNDCG[index] + (1 / math.log(minID + 2))
                    ALLHR[index] = ALLHR[index] + 1
        print(n_beam)
        valid_topk = [k for k in topk_list if k <= n_beam]
        print(valid_topk)
        print(f"NDCG:\t{ALLNDCG / len(text) / (1.0 / math.log(2))}")
        print(f"HR\t{ALLHR / len(text)}")
        print(CC)

        item_info_path = f"{item_path}.txt"
        grouped_metrics = calculate_metrics(p, item_info_path)
        for group, group_metrics in grouped_metrics["groups"].items():
            if not group_metrics["rows"]:
                print(f"{group}: rows=0")
                continue
            print(
                f"{group}: rows={group_metrics['rows']} | "
                f"HR@5={group_metrics['hr']['5']:.6f} "
                f"HR@10={group_metrics['hr']['10']:.6f} | "
                f"NDCG@5={group_metrics['ndcg']['5']:.6f} "
                f"NDCG@10={group_metrics['ndcg']['10']:.6f}"
            )

        results_jsonl_path = Path(p).with_suffix(".jsonl")
        result_count = write_results_jsonl(results_jsonl_path, test_data)
        metrics_path = Path(p).with_name(f"{Path(p).stem}_metrics.json")
        metrics_payload = {
            **grouped_metrics,
            "predictions": str(Path(p).resolve()),
            "results_jsonl": str(results_jsonl_path.resolve()),
        }
        with metrics_path.open("w", encoding="utf-8") as handle:
            json.dump(metrics_payload, handle, indent=2)
        print(f"Wrote {result_count} evaluation rows to {results_jsonl_path}")
        print(f"Wrote grouped metrics to {metrics_path}")

if __name__=='__main__':
    fire.Fire(gao)

    # # debugging
    # data_path = "./results/global_step_50__actor_merged/final_result_Video_Games.json"
    # item_path = "./data/Amazon_Games/info/Video_Games_5_2016-10-2018-11.txt"
    # gao(data_path, item_path)
