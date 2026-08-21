import unittest

from phase3_interest_retriever.embedder import (
    DEFAULT_DOCUMENT_MAX_LENGTH,
    DEFAULT_QUERY_INSTRUCTION,
    DEFAULT_QUERY_MAX_LENGTH,
    SUPPORTED_DOMAINS,
    Qwen3Embedder,
    query_instruction_for_domain,
)


class FakeTokenizer:
    def __call__(self, texts, **kwargs):
        max_length = kwargs.get("max_length", 10**9)
        return {"length": [min(int(text), max_length) for text in texts]}


class EmbedderBatchingTest(unittest.TestCase):
    def setUp(self):
        self.embedder = Qwen3Embedder.__new__(Qwen3Embedder)
        self.embedder.max_length = DEFAULT_DOCUMENT_MAX_LENGTH
        self.embedder.tokenizer = FakeTokenizer()

    def test_validated_document_and_query_lengths(self):
        self.assertEqual(DEFAULT_DOCUMENT_MAX_LENGTH, 1024)
        self.assertEqual(DEFAULT_QUERY_MAX_LENGTH, 512)

    def test_query_prompt_has_exact_instruction_and_space_after_query_colon(self):
        query = "cooperative survival crafting games"
        expected = (
            "Instruct: Retrieve relevant Video Games products.\n"
            "Query: cooperative survival crafting games"
        )
        self.assertEqual(
            Qwen3Embedder.__dict__["encode_queries"].__defaults__[0],
            DEFAULT_QUERY_INSTRUCTION,
        )
        self.assertEqual(f"Instruct: {DEFAULT_QUERY_INSTRUCTION}\nQuery: {query}", expected)

    def test_each_supported_domain_has_a_canonical_query_instruction(self):
        self.assertEqual(
            SUPPORTED_DOMAINS,
            ("Video_Games", "Office_Products", "Industrial_and_Scientific"),
        )
        self.assertEqual(
            query_instruction_for_domain("Office_Products"),
            "Retrieve relevant Office products.",
        )
        self.assertEqual(
            query_instruction_for_domain("Industrial_and_Scientific"),
            "Retrieve relevant Industrial and Scientific products.",
        )

    def test_unsupported_domain_has_no_fallback_instruction(self):
        with self.assertRaisesRegex(ValueError, "unsupported retrieval domain"):
            query_instruction_for_domain("Books")

    def test_token_budget_groups_similar_lengths_and_preserves_indices(self):
        batches = self.embedder._batch_indices(
            ["100", "1000", "8000", "200"],
            batch_size=32,
            max_batch_tokens=2_000,
        )
        self.assertEqual(batches, [[0, 3], [1], [2]])
        self.assertEqual(sorted(index for batch in batches for index in batch), [0, 1, 2, 3])

    def test_document_count_cap_applies_below_token_budget(self):
        batches = self.embedder._batch_indices(
            ["10", "10", "10", "10", "10"],
            batch_size=2,
            max_batch_tokens=1000,
        )
        self.assertEqual([len(batch) for batch in batches], [2, 2, 1])

    def test_static_batching_remains_available(self):
        batches = self.embedder._batch_indices(
            ["100", "200", "300"],
            batch_size=2,
            max_batch_tokens=None,
        )
        self.assertEqual(batches, [[0, 1], [2]])


if __name__ == "__main__":
    unittest.main()