import unittest

from phase3_interest_retriever.gradio_app import flatten_results, parse_interest_input


class GradioAppTest(unittest.TestCase):
    def test_interest_input_preserves_complete_nonempty_lines(self):
        value = (
            "- [exploit] <a_1><b_2><c_3> => More games.\n\n"
            "- [explore] <a_4><b_5><c_6> => Console accessories."
        )
        self.assertEqual(
            parse_interest_input(value),
            [
                "- [exploit] <a_1><b_2><c_3> => More games.",
                "- [explore] <a_4><b_5><c_6> => Console accessories.",
            ],
        )

    def test_interest_input_rejects_empty_or_too_many_lines(self):
        with self.assertRaises(ValueError):
            parse_interest_input("\n")
        with self.assertRaises(ValueError):
            parse_interest_input("\n".join(f"interest {index}" for index in range(9)))

    def test_flatten_results_defines_table_output(self):
        rows = flatten_results(
            {
                "results": [
                    {
                        "interest": "games",
                        "target_hit": True,
                        "target_rank": 1,
                        "items": [
                            {
                                "rank": 1,
                                "item_id": 7,
                                "sid": "<a_1><b_2><c_3>",
                                "title": "Target game",
                                "score": 0.91234567,
                            }
                        ],
                    }
                ]
            }
        )
        self.assertEqual(
            rows,
            [[1, "games", True, 1, 1, 7, "<a_1><b_2><c_3>", "Target game", 0.912346]],
        )


if __name__ == "__main__":
    unittest.main()