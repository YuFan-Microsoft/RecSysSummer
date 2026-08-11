import importlib.util
import math
from pathlib import Path
import sys
import types
import unittest


MODULE_PATH = Path(__file__).with_name("sid_reasoning_format.py")
SPEC = importlib.util.spec_from_file_location("sid_reasoning_format", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
calculate_process_rewards = MODULE.calculate_process_rewards

VALID_REASONING = """<think>
<history_summary>
- <a_4><b_5><c_6> => The history contains one recorded item.
</history_summary>
<future_interests>
- [exploit] <a_4><b_5><c_6> => The user may continue this observed interest.
- [explore] <a_4><b_5><c_6> => One shared attribute supports an adjacent interest.
</future_interests>
</think>
<a_1><b_2><c_3>"""
HISTORY_SIDS = ["<a_4><b_5><c_6>"]


def load_reward_module(domain: str):
    verl_module = sys.modules.setdefault("verl", types.ModuleType("verl"))
    utils_module = sys.modules.setdefault("verl.utils", types.ModuleType("verl.utils"))
    reward_score_module = sys.modules.setdefault(
        "verl.utils.reward_score", types.ModuleType("verl.utils.reward_score")
    )
    verl_module.utils = utils_module
    utils_module.reward_score = reward_score_module
    sys.modules["verl.utils.reward_score.sid_reasoning_format"] = MODULE

    path = Path(__file__).with_name(f"direct_recommendation_StepRule_{domain}.py")
    spec = importlib.util.spec_from_file_location(f"reward_{domain.lower()}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BeamProcessRewardTest(unittest.TestCase):
    def test_valid_v4_trace_receives_full_process_reward(self):
        self.assertEqual(
            calculate_process_rewards(VALID_REASONING, HISTORY_SIDS),
            {
                "history_summary_grounding_reward": 1.0,
                "future_interests_grounding_reward": 1.0,
                "format_reward": 1.0,
                "history_reference_coverage": 1.0,
                "process_reward": 1.0,
            },
        )

    def test_missing_mode_keeps_grounding_but_reduces_process_reward(self):
        response = VALID_REASONING.replace("[explore]", "[exploit]", 1)
        scores = calculate_process_rewards(response, HISTORY_SIDS)
        self.assertEqual(scores["format_reward"], 0.0)
        self.assertEqual(scores["history_summary_grounding_reward"], 1.0)
        self.assertEqual(scores["future_interests_grounding_reward"], 1.0)
        self.assertAlmostEqual(scores["process_reward"], 2.0 / 3.0)

    def test_ungrounded_future_line_reduces_only_future_grounding(self):
        response = VALID_REASONING.replace(
            "[explore] <a_4><b_5><c_6>",
            "[explore] <a_9><b_9><c_9>",
            1,
        )
        scores = calculate_process_rewards(response, HISTORY_SIDS)
        self.assertEqual(scores["format_reward"], 1.0)
        self.assertEqual(scores["history_summary_grounding_reward"], 1.0)
        self.assertEqual(scores["future_interests_grounding_reward"], 0.5)
        self.assertAlmostEqual(scores["process_reward"], 5.0 / 6.0)

    def test_process_reward_is_separate_from_beam_ndcg(self):
        expected_ndcg = 1.0 / math.log2(3.0)
        for domain in ("Games", "Office", "Industrial"):
            with self.subTest(domain=domain):
                reward = load_reward_module(domain).MyRewardComputer().compute(
                    data_source="rec/test",
                    solution_str=VALID_REASONING,
                    ground_truth="<a_1><b_2><c_3>",
                    extra_info={
                        "history_sids": HISTORY_SIDS,
                        "sid_beam_predictions": [
                            "<a_9><b_9><c_9>",
                            "<a_1><b_2><c_3>",
                        ],
                    },
                )

                self.assertAlmostEqual(reward["score"], expected_ndcg)
                self.assertAlmostEqual(reward["sid_match_reward"], expected_ndcg)
                self.assertEqual(reward["process_reward"], 1.0)

    def test_legacy_question_fallback(self):
        reward = load_reward_module("Games").MyRewardComputer().compute(
            data_source="rec/test",
            solution_str=VALID_REASONING,
            ground_truth="<a_1><b_2><c_3>",
            extra_info={
                "question": [{"role": "user", "content": "History: <a_4><b_5><c_6>."}],
                "sid_beam_predictions": ["<a_1><b_2><c_3>"],
            },
        )
        self.assertEqual(reward["score"], 1.0)
        self.assertEqual(reward["process_reward"], 1.0)


if __name__ == "__main__":
    unittest.main()