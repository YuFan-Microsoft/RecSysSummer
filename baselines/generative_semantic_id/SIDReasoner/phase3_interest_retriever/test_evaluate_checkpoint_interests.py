import unittest

from phase3_interest_retriever.evaluate_checkpoint_interests import (
    extract_interest_lines,
    summarize,
    target_rank_for_label,
)


REASONING = """<think>
<history_summary>
- <a_1><b_2><c_3> => A game.
</history_summary>
<future_interests>
- [exploit] <a_1><b_2><c_3> => More action games.
- [explore] <a_4><b_5><c_6> => Console accessories.
</future_interests>"""


class EvaluateCheckpointInterestsTest(unittest.TestCase):
    def test_extract_preserves_full_interest_lines(self):
        interests = extract_interest_lines(REASONING)
        self.assertEqual([interest["label"] for interest in interests], ["exploit", "explore"])
        self.assertEqual(
            interests[0]["query"],
            "- [exploit] <a_1><b_2><c_3> => More action games.",
        )
        self.assertEqual(interests[0]["text"], "More action games.")

    def test_invalid_interest_line_is_rejected(self):
        with self.assertRaises(ValueError):
            extract_interest_lines(REASONING.replace("[explore]", "[invalid]"))

    def test_target_rank_can_be_scoped_by_label(self):
        interests = extract_interest_lines(REASONING)
        response = {
            "results": [
                {"target_hit": False, "target_rank": None},
                {"target_hit": True, "target_rank": 7},
            ]
        }
        self.assertEqual(target_rank_for_label(response, interests), 7)
        self.assertIsNone(target_rank_for_label(response, interests, "exploit"))
        self.assertEqual(target_rank_for_label(response, interests, "explore"), 7)

    def test_summary_computes_any_interest_recall(self):
        records = [
            {
                "status": "ok",
                "interest_count": 2,
                "all_target_rank": 3,
                "exploit_target_rank": 3,
                "explore_target_rank": None,
                "prediction_beam_hit_at_10": True,
            },
            {
                "status": "ok",
                "interest_count": 3,
                "all_target_rank": None,
                "exploit_target_rank": None,
                "explore_target_rank": None,
                "prediction_beam_hit_at_10": False,
            },
            {"status": "parse_error", "prediction_beam_hit_at_10": False},
        ]
        summary = summarize(records, (1, 5))
        self.assertEqual(summary["evaluated_records"], 2)
        self.assertEqual(summary["parse_failures"], 1)
        self.assertEqual(summary["mean_interests_per_record"], 2.5)
        self.assertEqual(summary["all_recall"]["recall_at_1"], 0.0)
        self.assertAlmostEqual(summary["all_recall"]["recall_at_5"], 1.0 / 3.0)
        self.assertEqual(summary["all_conditional_recall"]["recall_at_5"], 0.5)
        self.assertAlmostEqual(summary["prediction_beam_recall_at_10"], 1.0 / 3.0)


if __name__ == "__main__":
    unittest.main()