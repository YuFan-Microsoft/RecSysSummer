import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from phase3_interest_retriever.index import InterestIndex


class InterestIndexTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        index_dir = Path(self.temporary_directory.name)
        metadata = [
            {"sid": "<a_1><b_1><c_1>", "title": "Survival game"},
            {"sid": "<a_2><b_2><c_2>", "title": "Office chair"},
            {"sid": "<a_3><b_3><c_3>", "title": "Game controller"},
        ]
        embeddings = np.asarray(
            [[1.0, 0.0], [0.0, 1.0], [0.8, 0.6]],
            dtype=np.float32,
        )
        np.save(index_dir / "embeddings.npy", embeddings)
        (index_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
        (index_dir / "manifest.json").write_text(
            json.dumps(
                {
                    "category": "Video_Games",
                    "model_name_or_path": "Qwen/Qwen3-Embedding-4B",
                    "query_instruction": "retrieve products",
                    "item_count": 3,
                    "embedding_dim": 2,
                }
            ),
            encoding="utf-8",
        )
        self.index = InterestIndex(index_dir)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_search_returns_descending_cosine_scores(self):
        results = self.index.search(np.asarray([[1.0, 0.0]], dtype=np.float32), top_k=2)
        self.assertEqual(
            [item["sid"] for item in results[0]],
            ["<a_1><b_1><c_1>", "<a_3><b_3><c_3>"],
        )
        self.assertEqual([item["rank"] for item in results[0]], [1, 2])

    def test_top_k_is_capped_at_catalog_size(self):
        results = self.index.search(np.asarray([[0.0, 1.0]], dtype=np.float32), top_k=20)
        self.assertEqual(len(results[0]), 3)

    def test_index_exposes_all_rows_for_a_colliding_sid(self):
        self.index.metadata[1]["sid"] = "<a_1><b_1><c_1>"
        index_dir = Path(self.temporary_directory.name)
        (index_dir / "metadata.json").write_text(
            json.dumps(self.index.metadata),
            encoding="utf-8",
        )
        reloaded = InterestIndex(index_dir)
        self.assertEqual(reloaded.sid_to_rows["<a_1><b_1><c_1>"], [0, 1])

    def test_wrong_query_dimension_is_rejected(self):
        with self.assertRaises(ValueError):
            self.index.search(np.ones((1, 3), dtype=np.float32), top_k=2)


if __name__ == "__main__":
    unittest.main()