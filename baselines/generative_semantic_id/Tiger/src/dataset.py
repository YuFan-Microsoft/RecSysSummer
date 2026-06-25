"""Sequence dataset for TIGER training / evaluation.

Each interaction row from the HF dataset is (history, target, user_id) where
`history` is a list of parent_asin (oldest first) and `target` is the next
parent_asin. We map asins to item indices, then to semantic-ID tuples:

    input  = flattened semantic ids of the history items   (len = hist_len * H)
    target = semantic ids of the next item                 (len = H)

The leave-one-out split (train / valid / test) is already done in the dataset,
so we simply turn each row into one example.

The model masks padded positions, so the padding value itself is irrelevant.
"""

import torch
from torch.utils.data import Dataset

from common import user_hash


class SequenceDataset(Dataset):
    def __init__(self, rows, asin2idx, item_codes, num_hierarchies, max_items=20):
        """
        rows:        list of (history_asins, target_asin, user_id)
        asin2idx:    dict parent_asin -> item index
        item_codes:  LongTensor (num_items, H)   semantic ids per item
        """
        self.codes = item_codes
        self.H = num_hierarchies
        self.max_items = max_items
        self.examples = []  # (history_idx, target_idx, user_bin)

        for history, target, user_id in rows:
            if target not in asin2idx:
                continue
            hist_idx = [asin2idx[a] for a in history if a in asin2idx]
            if not hist_idx:
                continue
            self.examples.append((hist_idx, asin2idx[target], user_hash(user_id)))

    def __len__(self):
        return len(self.examples)

    def _item_tokens(self, item_id):
        return self.codes[item_id]  # (H,)

    def __getitem__(self, idx):
        history, target, user_bin = self.examples[idx]
        history = history[-self.max_items :]
        input_tokens = torch.cat([self._item_tokens(i) for i in history])  # (hist_len*H,)
        target_tokens = self._item_tokens(target)  # (H,)
        return input_tokens, target_tokens, user_bin


class Collate:
    """Right-pad variable-length input token sequences within a batch.

    A picklable class (not a closure) so it works with DataLoader workers on
    spawn-based platforms (macOS / Windows).
    """

    def __init__(self, pad_id):
        self.pad_id = pad_id

    def __call__(self, batch):
        inputs, targets, user_ids = zip(*batch)
        max_len = max(x.shape[0] for x in inputs)
        padded = torch.full((len(inputs), max_len), self.pad_id, dtype=torch.long)
        mask = torch.zeros((len(inputs), max_len), dtype=torch.long)
        for i, seq in enumerate(inputs):
            padded[i, : seq.shape[0]] = seq
            mask[i, : seq.shape[0]] = 1
        return padded, mask, torch.stack(targets), torch.tensor(user_ids, dtype=torch.long)
