import importlib.util
import math
from pathlib import Path
import unittest


def load_reward_module(domain: str):
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
                    "solution_str": "<think>reasoning</think>\n<a_1><b_2><c_3>",
                    "ground_truth": "<a_1><b_2><c_3>",
                }
                hit = reward_computer.compute(
                    **common,
                    extra_info={"sid_beam_predictions": ["<a_1><b_2><c_3>"]},
                )
                miss = reward_computer.compute(
                    **common,
                    extra_info={"sid_beam_predictions": ["<a_9><b_9><c_9>"]},
                )

                self.assertEqual(hit["score"], 1.0)
                self.assertEqual(hit["sid_match_reward"], 1.0)
                self.assertEqual(miss["score"], 0.0)
                self.assertEqual(miss["sid_match_reward"], 0.0)
                self.assertFalse(
                    {"process_reward", "format_reward", "grounding_reward"} & hit.keys()
                )

    def test_validation_beam_uses_ndcg_without_process_reward(self):
        reward_computer = load_reward_module("Games").MyRewardComputer()
        reward = reward_computer.compute(
            data_source="rec/test",
            solution_str="<think>reasoning</think>\n<a_9><b_9><c_9>",
            ground_truth="<a_1><b_2><c_3>",
            extra_info={
                "sid_beam_predictions": [
                    "<a_9><b_9><c_9>",
                    "<a_1><b_2><c_3>",
                ]
            },
        )

        self.assertAlmostEqual(reward["score"], 1.0 / math.log2(3.0))
        self.assertEqual(reward["beam_rank"], 2.0)
        self.assertNotIn("process_reward", reward)


if __name__ == "__main__":
    unittest.main()