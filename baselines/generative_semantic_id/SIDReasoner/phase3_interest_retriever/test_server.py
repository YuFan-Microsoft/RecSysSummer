import asyncio
import argparse
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from phase3_interest_retriever.index import InterestIndex
from phase3_interest_retriever.schemas import RankRequest
from phase3_interest_retriever.server import InterestRetrieverService, validate_query_runtime
from phase3_interest_retriever.embedder import query_instruction_for_domain


class FakeEmbedder:
    def __init__(self):
        self.calls = []

    def encode_queries(self, queries, instruction, batch_size):
        self.calls.append(list(queries))
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
        self.embedder = FakeEmbedder()
        self.service = InterestRetrieverService(InterestIndex(index_dir), self.embedder)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_rank_returns_one_based_position_or_minus_one(self):
        hit = asyncio.run(
            self.service.rank(
                RankRequest(
                    interest="survival games",
                    target_sid="<a_1><b_1><c_1>",
                )
            )
        )
        miss = asyncio.run(
            self.service.rank(
                RankRequest(
                    interest="office supplies",
                    target_sid="<a_1><b_1><c_1>",
                )
            )
        )
        self.assertEqual(hit, 1)
        self.assertEqual(miss, 2)

    def test_rank_batch_deduplicates_interests_in_one_embedding_call(self):
        ranks = asyncio.run(
            self.service.rank_many(
                [
                    RankRequest(
                        interest="survival games",
                        target_sid="<a_1><b_1><c_1>",
                    ),
                    RankRequest(
                        interest="survival games",
                        target_sid="<a_2><b_2><c_2>",
                    ),
                    RankRequest(
                        interest="office supplies",
                        target_sid="<a_2><b_2><c_2>",
                    ),
                ]
            )
        )
        self.assertEqual(ranks, [1, 2, 1])
        self.assertEqual(self.embedder.calls[-1], ["survival games", "office supplies"])

    def test_rank_rejects_target_absent_from_catalog(self):
        with self.assertRaises(ValueError):
            asyncio.run(
                self.service.rank(
                    RankRequest(
                        interest="survival games",
                        target_sid="<a_9><b_9><c_9>",
                    )
                )
            )

    def test_rank_returns_minus_one_for_catalog_target_outside_top_100(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            index_dir = Path(temporary_directory)
            metadata = [
                {
                    "sid": f"<a_{index}><b_{index}><c_{index}>",
                    "title": f"Item {index}",
                }
                for index in range(101)
            ]
            embeddings = np.asarray(
                [[1.0, 0.0]] * 100 + [[0.0, 1.0]],
                dtype=np.float32,
            )
            np.save(index_dir / "embeddings.npy", embeddings)
            (index_dir / "metadata.json").write_text(
                json.dumps(metadata),
                encoding="utf-8",
            )
            (index_dir / "manifest.json").write_text(
                json.dumps(
                    {
                        "category": "Video_Games",
                        "model_name_or_path": "test-model",
                        "query_instruction": "retrieve products",
                        "item_count": 101,
                        "embedding_dim": 2,
                    }
                ),
                encoding="utf-8",
            )
            service = InterestRetrieverService(InterestIndex(index_dir), FakeEmbedder())
            rank = asyncio.run(
                service.rank(
                    RankRequest(
                        interest="survival games",
                        target_sid="<a_100><b_100><c_100>",
                    )
                )
            )
            self.assertEqual(rank, -1)

    def test_runtime_rejects_stale_instruction_and_accepts_validated_config(self):
        args = argparse.Namespace(
            domain=None,
            dtype="float16",
            max_length=512,
            use_flash_attention=False,
        )
        self.service.index.manifest.update(
            {
                "dtype": "float16",
                "query_max_length": 512,
                "attention_backend": "transformers_default",
            }
        )
        with self.assertRaises(ValueError):
            validate_query_runtime(self.service.index, args)
        self.service.index.manifest["query_instruction"] = query_instruction_for_domain(
            "Video_Games"
        )
        validate_query_runtime(self.service.index, args)

    def test_runtime_validates_each_supported_domain(self):
        args = argparse.Namespace(
            domain=None,
            dtype="float16",
            max_length=512,
            use_flash_attention=False,
        )
        self.service.index.manifest.update(
            {
                "dtype": "float16",
                "query_max_length": 512,
                "attention_backend": "transformers_default",
            }
        )
        for domain in (
            "Video_Games",
            "Office_Products",
            "Industrial_and_Scientific",
        ):
            with self.subTest(domain=domain):
                self.service.index.manifest["category"] = domain
                self.service.index.manifest["query_instruction"] = (
                    query_instruction_for_domain(domain)
                )
                validate_query_runtime(self.service.index, args)

    def test_runtime_rejects_requested_domain_mismatch(self):
        args = argparse.Namespace(
            domain="Office_Products",
            dtype="float16",
            max_length=512,
            use_flash_attention=False,
        )
        self.service.index.manifest.update(
            {
                "query_instruction": query_instruction_for_domain("Video_Games"),
                "dtype": "float16",
                "query_max_length": 512,
                "attention_backend": "transformers_default",
            }
        )
        with self.assertRaisesRegex(ValueError, "does not match requested domain"):
            validate_query_runtime(self.service.index, args)


if __name__ == "__main__":
    unittest.main()