import unittest

from phase3_interest_retriever.build_index import (
    DEFAULT_BUILD_BATCH_SIZE,
    DEFAULT_MAX_BATCH_TOKENS,
    INDEX_TEXT_FIELDS,
    item_index_text,
    parse_gpu_ids,
    partition_ranges,
)
from phase3_interest_retriever.embedder import DEFAULT_DOCUMENT_MAX_LENGTH, DEFAULT_MODEL


class BuildIndexTest(unittest.TestCase):
    def test_default_build_batch_size_is_32_per_gpu(self):
        self.assertEqual(DEFAULT_BUILD_BATCH_SIZE, 32)

    def test_validated_document_defaults(self):
        self.assertEqual(DEFAULT_DOCUMENT_MAX_LENGTH, 1024)
        self.assertEqual(DEFAULT_MAX_BATCH_TOKENS, 32768)

    def test_default_model_uses_local_checkpoint(self):
        self.assertEqual(
            DEFAULT_MODEL,
            "/yufan/open_source_models/Embedding_Model/Qwen3-Embedding-0.6B",
        )

    def test_document_uses_title_brand_and_retrieval_summary(self):
        item = {
            "sid": "<a_1><b_2><c_3>",
            "title": "Wireless Controller",
            "brand": "Example Brand",
            "description": "Rechargeable game controller.",
            "detailed_description": "Do not index the legacy generated description.",
            "retrieval_summary": "A wireless controller for local multiplayer gaming.",
            "sid_interleaved_narrative": "Do not index this generated text.",
        }
        text = item_index_text(item)
        self.assertEqual(
            text,
            "Title: Wireless Controller\n"
            "Brand: Example Brand\n"
            "Summary: A wireless controller for local multiplayer gaming.",
        )
        self.assertNotIn("Description:", text)
        self.assertNotIn("Rechargeable game controller.", text)
        self.assertNotIn("legacy generated description", text)
        self.assertNotIn("generated text", text)
        self.assertNotIn("description", INDEX_TEXT_FIELDS)
        self.assertNotIn("detailed_description", INDEX_TEXT_FIELDS)
        self.assertNotIn("sid_interleaved_narrative", INDEX_TEXT_FIELDS)

    def test_document_omits_empty_fields_without_blank_placeholders(self):
        self.assertEqual(
            item_index_text(
                {
                    "sid": "<a_1><b_2><c_3>",
                    "title": "Example Game",
                    "brand": "",
                    "retrieval_summary": "An example game summary.",
                }
            ),
            "Title: Example Game\nSummary: An example game summary.",
        )

    def test_document_requires_title_and_summary(self):
        with self.assertRaisesRegex(ValueError, "no title"):
            item_index_text(
                {
                    "sid": "<a_1><b_2><c_3>",
                    "retrieval_summary": "Summary without a title.",
                }
            )
        with self.assertRaisesRegex(ValueError, "no retrieval_summary"):
            item_index_text(
                {
                    "sid": "<a_1><b_2><c_3>",
                    "title": "Title without a summary",
                }
            )

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