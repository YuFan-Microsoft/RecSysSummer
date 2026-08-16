import unittest

from phase3_interest_retriever.build_index import (
    DEFAULT_BUILD_BATCH_SIZE,
    INDEX_TEXT_FIELDS,
    item_index_text,
    parse_gpu_ids,
    partition_ranges,
)
from phase3_interest_retriever.embedder import DEFAULT_MODEL


class BuildIndexTest(unittest.TestCase):
    def test_default_build_batch_size_is_128_per_gpu(self):
        self.assertEqual(DEFAULT_BUILD_BATCH_SIZE, 128)

    def test_default_model_uses_local_checkpoint(self):
        self.assertEqual(
            DEFAULT_MODEL,
            "/yufan/open_source_models/Embedding_Model/Qwen3-Embedding-0.6B",
        )

    def test_document_uses_catalog_metadata_but_not_generated_narrative(self):
        item = {
            "sid": "<a_1><b_2><c_3>",
            "title": "Wireless Controller",
            "brand": "Example Brand",
            "description": "Rechargeable game controller.",
            "detailed_description": "Designed for local multiplayer gaming.",
            "sid_interleaved_narrative": "Do not index this generated text.",
        }
        text = item_index_text(item)
        self.assertIn("Title: Wireless Controller", text)
        self.assertIn("Brand: Example Brand", text)
        self.assertIn("Description: Rechargeable game controller.", text)
        self.assertIn("Details: Designed for local multiplayer gaming.", text)
        self.assertNotIn("generated text", text)
        self.assertNotIn("sid_interleaved_narrative", INDEX_TEXT_FIELDS)

    def test_document_requires_at_least_one_nonempty_field(self):
        with self.assertRaises(ValueError):
            item_index_text({"sid": "<a_1><b_2><c_3>"})

    def test_default_eight_gpu_ids_are_accepted(self):
        self.assertEqual(
            parse_gpu_ids("0,1,2,3,4,5,6,7"),
            ["0", "1", "2", "3", "4", "5", "6", "7"],
        )

    def test_gpu_ids_must_be_exactly_eight_and_distinct(self):
        for value in ("0,1,2,3,4,5,6", "0,1,2,3,4,5,6,6", "0,1,2,3,4,5,6,7,8"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_gpu_ids(value)

    def test_partition_ranges_preserve_order_and_cover_all_items(self):
        ranges = partition_ranges(100)
        self.assertEqual(len(ranges), 8)
        self.assertEqual(ranges[0], (0, 12))
        self.assertEqual(ranges[-1], (87, 100))
        self.assertEqual([start for start, _ in ranges[1:]], [end for _, end in ranges[:-1]])

    def test_partition_requires_one_item_per_gpu(self):
        with self.assertRaises(ValueError):
            partition_ranges(7)


if __name__ == "__main__":
    unittest.main()