import asyncio
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from phase3_interest_retriever.index import InterestIndex
from phase3_interest_retriever.schemas import RetrieveRequest
from phase3_interest_retriever.server import InterestRetrieverService


class FakeEmbedder:
    def encode_queries(self, queries, instruction, batch_size):
        vectors = {
            "survival games": [1.0, 0.0],
            "office supplies": [0.0, 1.0],
        }
        return np.asarray([vectors[query] for query in queries], dtype=np.float32)


class InterestRetrieverServiceTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        index_dir = Path(self.temporary_directory.name)
        metadata = [
            {"sid": "<a_1><b_1><c_1>", "title": "Survival game"},
            {"sid": "<a_2><b_2><c_2>", "title": "Office chair"},
        ]
        np.save(
            index_dir / "embeddings.npy",
            np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32),
        )
        (index_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
        (index_dir / "manifest.json").write_text(
            json.dumps(
                {
                    "category": "Video_Games",
                    "model_name_or_path": "Qwen/Qwen3-Embedding-0.6B",
                    "query_instruction": "retrieve products",
                    "item_count": 2,
                    "embedding_dim": 2,
                }
            ),
            encoding="utf-8",
        )
        self.service = InterestRetrieverService(
            InterestIndex(index_dir),
            FakeEmbedder(),
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_any_interest_hit_does_not_penalize_other_interests(self):
        response = asyncio.run(
            self.service.retrieve(
                RetrieveRequest(
                    request_id="group-1",
                    target_sid="<a_1><b_1><c_1>",
                    interests=["office supplies", "survival games"],
                    top_k=1,
                )
            )
        )
        self.assertEqual(response.reward, 1.0)
        self.assertEqual([result.target_hit for result in response.results], [False, True])

    def test_all_misses_receive_zero(self):
        response = asyncio.run(
            self.service.retrieve(
                RetrieveRequest(
                    request_id="group-2",
                    target_sid="<a_1><b_1><c_1>",
                    interests=["office supplies"],
                    top_k=1,
                )
            )
        )
        self.assertEqual(response.reward, 0.0)


if __name__ == "__main__":
    unittest.main()