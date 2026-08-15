import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from build_index import append_new_papers, build_domain
from common import ArxivPaper


def make_paper(arxiv_id: str, title: str) -> ArxivPaper:
    return ArxivPaper(
        arxiv_id=arxiv_id,
        title=title,
        abstract="",
        authors="Test Author",
        year=2026,
        publication_date="2026-08-15",
        citation_count=0,
        influential_citation_count=0,
        domain="Test",
    )


class IncrementalBuildTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.out_dir = Path(self.temp_dir.name) / "Test"
        self.out_dir.mkdir()
        self.emb_path = self.out_dir / "embeddings.npy"
        self.meta_path = self.out_dir / "metadata.json"
        self.old_papers = [make_paper("2608.00001", "Old A"), make_paper("2608.00002", "Old B")]
        self.old_embeddings = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float32)
        np.save(self.emb_path, self.old_embeddings)
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump([paper.to_dict() for paper in self.old_papers], f)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    @patch("build_index.embed_texts_multi_gpu")
    def test_appends_only_unseen_ids_and_then_becomes_noop(self, embed_mock) -> None:
        new_paper = make_paper("2608.00003", "New")
        embed_mock.return_value = np.array([[7, 8, 9]], dtype=np.float32)
        papers = self.old_papers + [new_paper, new_paper]

        added = append_new_papers(
            cfg={"embedding_model_path": "unused"},
            domain="Test",
            papers=papers,
            emb_path=self.emb_path,
            meta_path=self.meta_path,
            gpus=[0],
        )

        self.assertEqual(added, 1)
        embeddings = np.load(self.emb_path)
        np.testing.assert_array_equal(embeddings[:2], self.old_embeddings)
        np.testing.assert_array_equal(embeddings[2], np.array([7, 8, 9], dtype=np.float32))
        with open(self.meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        self.assertEqual([item["arxiv_id"] for item in metadata], ["2608.00001", "2608.00002", "2608.00003"])

        embed_mock.reset_mock()
        self.assertEqual(
            append_new_papers(
                cfg={"embedding_model_path": "unused"},
                domain="Test",
                papers=papers,
                emb_path=self.emb_path,
                meta_path=self.meta_path,
                gpus=[0],
            ),
            0,
        )
        embed_mock.assert_not_called()

    def test_rejects_row_count_mismatch(self) -> None:
        np.save(self.emb_path, self.old_embeddings[:1])
        with self.assertRaisesRegex(RuntimeError, "do not match"):
            append_new_papers(
                cfg={"embedding_model_path": "unused"},
                domain="Test",
                papers=self.old_papers,
                emb_path=self.emb_path,
                meta_path=self.meta_path,
                gpus=[0],
            )

    @patch("build_index.iter_domain_papers")
    def test_rejects_half_existing_shard(self, iter_mock) -> None:
        iter_mock.return_value = iter(self.old_papers)
        self.meta_path.unlink()
        with self.assertRaisesRegex(RuntimeError, "requires both"):
            build_domain(
                cfg={"data_dir": "unused"},
                domain="Test",
                years=[2026],
                out_dir=self.out_dir,
                gpus=[0],
                incremental=True,
            )


if __name__ == "__main__":
    unittest.main()