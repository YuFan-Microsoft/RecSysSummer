import unittest

from phase3_interest_retriever.gradio_app import parse_interest_input


class GradioAppTest(unittest.TestCase):
    def test_interest_input_preserves_one_pure_text_interest(self):
        self.assertEqual(
            parse_interest_input("  cooperative survival crafting games  "),
            "cooperative survival crafting games",
        )

    def test_interest_input_rejects_empty_or_multiple_lines(self):
        with self.assertRaises(ValueError):
            parse_interest_input("\n")
        with self.assertRaises(ValueError):
            parse_interest_input("interest one\ninterest two")


if __name__ == "__main__":
    unittest.main()