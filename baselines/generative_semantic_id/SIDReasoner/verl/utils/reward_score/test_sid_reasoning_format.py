import importlib.util
from pathlib import Path
import sys
import types
import unittest


MODULE_PATH = Path(__file__).with_name("sid_reasoning_format.py")
SPEC = importlib.util.spec_from_file_location("sid_reasoning_format", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
calculate_format_reward = MODULE.calculate_format_reward


def load_reward_module(domain):
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


VALID_REASONING = """<think>
<behavior>
- <a_240><b_208><c_129> => engaged with a PlayStation game
</behavior>
<interest>
- <a_240><b_208><c_129> => may prefer franchise-based action games
</interest>
<intent>
- [continue] likely to continue with action-oriented games
- [adjacent] could consider other mainstream PlayStation titles
- [explore] may explore the broader PlayStation catalog
</intent>
</think>
<a_1><b_2><c_3>"""


class FormatRewardTest(unittest.TestCase):
    def test_accepts_three_ordered_non_empty_blocks(self):
        self.assertEqual(calculate_format_reward(VALID_REASONING), 1.0)

    def test_accepts_response_without_opening_think_token(self):
        self.assertEqual(calculate_format_reward(VALID_REASONING.replace("<think>\n", "", 1)), 1.0)

    def test_rejects_wrong_block_order(self):
        interest_start = VALID_REASONING.index("<interest>")
        intent_start = VALID_REASONING.index("<intent>")
        intent_end = VALID_REASONING.index("</intent>") + len("</intent>")
        reordered = (
            VALID_REASONING[:interest_start]
            + VALID_REASONING[intent_start:intent_end]
            + "\n"
            + VALID_REASONING[interest_start:intent_start]
            + VALID_REASONING[intent_end:]
        )
        self.assertEqual(calculate_format_reward(reordered), 0.0)

    def test_rejects_missing_duplicate_empty_or_extra_content(self):
        invalid_responses = (
            VALID_REASONING.replace("<interest>", "", 1),
            VALID_REASONING.replace("<behavior>", "<behavior><behavior>", 1),
            VALID_REASONING.replace(
                "- <a_240><b_208><c_129> => may prefer franchise-based action games", ""
            ),
            VALID_REASONING.replace("<behavior>", "unsupported preamble\n<behavior>", 1),
        )
        for response in invalid_responses:
            with self.subTest(response=response):
                self.assertEqual(calculate_format_reward(response), 0.0)

    def test_rejects_missing_or_duplicate_think_closer(self):
        self.assertEqual(calculate_format_reward(VALID_REASONING.replace("</think>", "", 1)), 0.0)
        self.assertEqual(calculate_format_reward(VALID_REASONING + "</think>"), 0.0)

    def test_all_domains_add_only_the_binary_format_bonus(self):
        for domain in ("Games", "Office", "Industrial"):
            with self.subTest(domain=domain):
                reward_computer = load_reward_module(domain).MyRewardComputer()
                kwargs = {
                    "data_source": "rec/test",
                    "ground_truth": "<a_1><b_2><c_3>",
                    "extra_info": {"sid_beam_predictions": ["<a_1><b_2><c_3>"]},
                }
                valid_score = reward_computer.compute(solution_str=VALID_REASONING, **kwargs)
                invalid_score = reward_computer.compute(
                    solution_str=VALID_REASONING.replace("<interest>", "", 1), **kwargs
                )

                self.assertAlmostEqual(valid_score["score"], 1.05)
                self.assertEqual(valid_score["format_reward"], 1.0)
                self.assertAlmostEqual(invalid_score["score"], 1.0)
                self.assertEqual(invalid_score["format_reward"], 0.0)
                self.assertEqual([key for key in valid_score if "format" in key], ["format_reward"])


if __name__ == "__main__":
    unittest.main()