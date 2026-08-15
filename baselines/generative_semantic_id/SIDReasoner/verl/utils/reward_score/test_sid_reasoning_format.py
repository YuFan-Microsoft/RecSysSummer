import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).with_name("sid_reasoning_format.py")
SPEC = importlib.util.spec_from_file_location("sid_reasoning_format", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load process reward from {MODULE_PATH}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
calculate_process_rewards = MODULE.calculate_process_rewards


HISTORY_SIDS = ["<a_1><b_1><c_1>", "<a_2><b_2><c_2>"]
VALID_RESPONSE = """<think>
<history_summary>
- <a_2><b_2><c_2> => The latest interaction is a cooperative action game.
</history_summary>
<future_interests>
- [exploit] <a_2><b_2><c_2> => The user may continue with cooperative action play.
- [explore] <a_1><b_1><c_1> => The shared strategic play may bridge to tactical games.
</future_interests>
</think>
<a_9><b_9><c_9>"""


class SidReasoningFormatTest(unittest.TestCase):
    def test_fully_valid_trace_passes_hard_gate(self):
        scores = calculate_process_rewards(VALID_RESPONSE, HISTORY_SIDS)

        self.assertEqual(scores["format_reward"], 1.0)
        self.assertEqual(scores["history_summary_grounding_reward"], 1.0)
        self.assertEqual(scores["future_interests_grounding_reward"], 1.0)
        self.assertEqual(scores["latest_history_summary_reference_reward"], 1.0)
        self.assertEqual(scores["process_reward"], 1.0)

    def test_latest_history_sid_is_required_in_summary(self):
        response = VALID_RESPONSE.replace(
            "- <a_2><b_2><c_2> => The latest interaction is a cooperative action game.",
            "- <a_1><b_1><c_1> => An earlier interaction is a cooperative action game.",
        )

        scores = calculate_process_rewards(response, HISTORY_SIDS)

        self.assertEqual(scores["format_reward"], 1.0)
        self.assertEqual(scores["history_summary_grounding_reward"], 1.0)
        self.assertEqual(scores["future_interests_grounding_reward"], 1.0)
        self.assertEqual(scores["latest_history_summary_reference_reward"], 0.0)
        self.assertEqual(scores["process_reward"], 0.0)

    def test_partial_grounding_fails_instead_of_receiving_soft_reward(self):
        response = VALID_RESPONSE.replace(
            "[explore] <a_1><b_1><c_1>",
            "[explore] <a_9><b_9><c_9>",
        )

        scores = calculate_process_rewards(response, HISTORY_SIDS)

        self.assertEqual(scores["format_reward"], 1.0)
        self.assertEqual(scores["future_interests_grounding_reward"], 0.5)
        self.assertEqual(scores["process_reward"], 0.0)


if __name__ == "__main__":
    unittest.main()