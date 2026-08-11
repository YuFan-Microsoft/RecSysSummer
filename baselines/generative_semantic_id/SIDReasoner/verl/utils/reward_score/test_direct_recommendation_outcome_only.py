import importlib.util
import math
from pathlib import Path
import sys
import types
import unittest


METRICS_PATH = Path(__file__).with_name("sid_reasoning_format.py")
METRICS_SPEC = importlib.util.spec_from_file_location("sid_reasoning_format", METRICS_PATH)
METRICS_MODULE = importlib.util.module_from_spec(METRICS_SPEC)
METRICS_SPEC.loader.exec_module(METRICS_MODULE)


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


def load_reward_module(domain: str):
    verl_module = sys.modules.setdefault("verl", types.ModuleType("verl"))
    utils_module = sys.modules.setdefault("verl.utils", types.ModuleType("verl.utils"))
    reward_score_module = sys.modules.setdefault(
        "verl.utils.reward_score", types.ModuleType("verl.utils.reward_score")
    )
    verl_module.utils = utils_module
    utils_module.reward_score = reward_score_module
    sys.modules["verl.utils.reward_score.sid_reasoning_format"] = METRICS_MODULE

    path = Path(__file__).with_name(f"direct_recommendation_StepRule_{domain}.py")
    spec = importlib.util.spec_from_file_location(f"reward_{domain.lower()}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OutcomeOnlyRewardTest(unittest.TestCase):
    def test_training_reward_is_sampled_sid_exact_match_only(self):
        for domain in ("Games", "Office", "Industrial"):
            with self.subTest(domain=domain):
                reward_computer = load_reward_module(domain).MyRewardComputer()
                common = {
                    "data_source": "rec/test",
                    "solution_str": VALID_REASONING,
                    "ground_truth": "<a_1><b_2><c_3>",
                }
                hit = reward_computer.compute(
                    **common,
                    extra_info={
                        "history_sids": ["<a_4><b_5><c_6>"],
                        "sid_beam_predictions": ["<a_1><b_2><c_3>"],
                    },
                )
                miss = reward_computer.compute(
                    **common,
                    extra_info={
                        "history_sids": ["<a_4><b_5><c_6>"],
                        "sid_beam_predictions": ["<a_9><b_9><c_9>"],
                    },
                )

                self.assertEqual(hit["score"], 1.0)
                self.assertEqual(hit["sid_match_reward"], 1.0)
                self.assertEqual(miss["score"], 0.0)
                self.assertEqual(miss["sid_match_reward"], 0.0)
                self.assertEqual(hit["process_reward"], 1.0)
                self.assertEqual(miss["process_reward"], 1.0)
                self.assertEqual(miss["format_reward"], 1.0)

    def test_invalid_process_metrics_do_not_reduce_sid_reward(self):
        reward_computer = load_reward_module("Games").MyRewardComputer()
        reward = reward_computer.compute(
            data_source="rec/test",
            solution_str="<think>free-form reasoning</think>\n<a_1><b_2><c_3>",
            ground_truth="<a_1><b_2><c_3>",
            extra_info={
                "history_sids": ["<a_4><b_5><c_6>"],
                "sid_beam_predictions": ["<a_1><b_2><c_3>"],
            },
        )

        self.assertEqual(reward["score"], 1.0)
        self.assertEqual(reward["sid_match_reward"], 1.0)
        self.assertEqual(reward["format_reward"], 0.0)
        self.assertEqual(reward["process_reward"], 0.0)

    def test_validation_beam_uses_ndcg_with_process_metrics_only(self):
        reward_computer = load_reward_module("Games").MyRewardComputer()
        reward = reward_computer.compute(
            data_source="rec/test",
            solution_str=VALID_REASONING,
            ground_truth="<a_1><b_2><c_3>",
            extra_info={
                "history_sids": ["<a_4><b_5><c_6>"],
                "sid_beam_predictions": [
                    "<a_9><b_9><c_9>",
                    "<a_1><b_2><c_3>",
                ]
            },
        )

        self.assertAlmostEqual(reward["score"], 1.0 / math.log2(3.0))
        self.assertEqual(reward["beam_rank"], 2.0)
        self.assertEqual(reward["process_reward"], 1.0)


if __name__ == "__main__":
    unittest.main()