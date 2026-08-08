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
extract_history_sids_from_question = MODULE.extract_history_sids_from_question


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
<history_evidence>
- <a_240><b_208><c_129> => The recorded item is a Rockstar Games title.
- <a_240><b_208><c_129> => The game is part of the Grand Theft Auto series.
</history_evidence>
<next_interest>
- [exploit] <a_240><b_208><c_129> => Another game from the same series is a likely continuation.
- [explore] <a_240><b_208><c_129> => The user may explore other urban action games and <a_9><b_9><c_9>.
</next_interest>
</think>
<a_9><b_9><c_9>"""
HISTORY_SIDS = ["<a_240><b_208><c_129>"]

MULTI_SID_REASONING = """<history_evidence>
- <a_140><b_237><c_88>, <a_74><b_218><c_196> => Two Sony game listings are for the same PlayStation 2 franchise.
- <a_249><b_80><c_0>, <a_249><b_138><c_211>, <a_249><b_138><c_211> => The history contains PlayStation 2 hardware/accessory listings.
- <a_10><b_193><c_15>, <a_131><b_233><c_112> => Two Bethesda console game listings are role-playing titles on Xbox 360.
</history_evidence>
<next_interest>
- [exploit] <a_249><b_80><c_0>, <a_249><b_138><c_211>, <a_249><b_138><c_211> => Another PlayStation 2 accessory is the strongest continuation.
- [explore] <a_140><b_237><c_88>, <a_74><b_218><c_196> => Another game from the same franchise is plausible.
- [explore] <a_10><b_193><c_15>, <a_131><b_233><c_112> => Another Xbox 360 role-playing game is plausible.
</next_interest>
</think>
<a_1><b_2><c_3>"""
MULTI_SID_HISTORY = [
    "<a_140><b_237><c_88>",
    "<a_74><b_218><c_196>",
    "<a_249><b_80><c_0>",
    "<a_249><b_138><c_211>",
    "<a_10><b_193><c_15>",
    "<a_131><b_233><c_112>",
]


class ProcessRewardTest(unittest.TestCase):
    def test_real_v3_multi_sid_trace_receives_full_reward(self):
        self.assertEqual(
            calculate_process_rewards(MULTI_SID_REASONING, MULTI_SID_HISTORY),
            {
                "format_reward": 1.0,
                "grounding_reward": 1.0,
                "process_reward": 1.0,
            },
        )

    def test_space_separated_v3_citations_receive_full_reward(self):
        response = MULTI_SID_REASONING.replace(", ", " ")
        self.assertEqual(
            calculate_process_rewards(response, MULTI_SID_HISTORY),
            {
                "format_reward": 1.0,
                "grounding_reward": 1.0,
                "process_reward": 1.0,
            },
        )

    def test_multi_sid_line_is_ungrounded_when_any_citation_is_not_in_history(self):
        response = MULTI_SID_REASONING.replace(
            "<a_140><b_237><c_88>, <a_74><b_218><c_196>",
            "<a_140><b_237><c_88>, <a_999><b_999><c_999>",
            1,
        )
        scores = calculate_process_rewards(response, MULTI_SID_HISTORY)
        self.assertEqual(scores["format_reward"], 1.0)
        self.assertAlmostEqual(scores["grounding_reward"], 5.0 / 6.0)
        self.assertAlmostEqual(scores["process_reward"], 11.0 / 12.0)

    def test_valid_repeated_citations_and_target_in_text_receive_full_reward(self):
        self.assertEqual(
            calculate_process_rewards(VALID_REASONING, HISTORY_SIDS),
            {
                "format_reward": 1.0,
                "grounding_reward": 1.0,
                "process_reward": 1.0,
            },
        )

    def test_opening_think_is_optional(self):
        response = VALID_REASONING.replace("<think>\n", "", 1)
        self.assertEqual(calculate_process_rewards(response, HISTORY_SIDS)["process_reward"], 1.0)

    def test_missing_label_fails_format_but_keeps_grounding(self):
        response = VALID_REASONING.replace("[explore] ", "", 1)
        scores = calculate_process_rewards(response, HISTORY_SIDS)
        self.assertEqual(scores["format_reward"], 0.0)
        self.assertEqual(scores["grounding_reward"], 0.75)
        self.assertEqual(scores["process_reward"], 0.375)

    def test_ungrounded_leading_citation_reduces_grounding(self):
        response = VALID_REASONING.replace(
            "[explore] <a_240><b_208><c_129>", "[explore] <a_7><b_8><c_9>", 1
        )
        scores = calculate_process_rewards(response, HISTORY_SIDS)
        self.assertEqual(scores["format_reward"], 1.0)
        self.assertEqual(scores["grounding_reward"], 0.75)
        self.assertEqual(scores["process_reward"], 0.875)

    def test_wrong_block_order_or_extra_text_returns_zero(self):
        history_start = VALID_REASONING.index("<history_evidence>")
        history_end = VALID_REASONING.index("</history_evidence>") + len("</history_evidence>")
        interest_start = VALID_REASONING.index("<next_interest>")
        interest_end = VALID_REASONING.index("</next_interest>") + len("</next_interest>")
        wrong_order = (
            VALID_REASONING[:history_start]
            + VALID_REASONING[interest_start:interest_end]
            + "\n"
            + VALID_REASONING[history_start:history_end]
            + VALID_REASONING[interest_end:]
        )
        extra_text = VALID_REASONING.replace("<history_evidence>", "preamble\n<history_evidence>", 1)
        self.assertEqual(calculate_process_rewards(wrong_order, HISTORY_SIDS)["process_reward"], 0.0)
        self.assertEqual(calculate_process_rewards(extra_text, HISTORY_SIDS)["process_reward"], 0.0)

    def test_legacy_question_history_extraction(self):
        question = [
            {"role": "system", "content": "Recommend an item."},
            {
                "role": "user",
                "content": "History: <a_1><b_2><c_3>, <a_4><b_5><c_6>.",
            },
        ]
        self.assertEqual(
            extract_history_sids_from_question(question),
            ["<a_1><b_2><c_3>", "<a_4><b_5><c_6>"],
        )

    def test_all_domains_keep_sid_score_separate_from_process_reward(self):
        for domain in ("Games", "Office", "Industrial"):
            with self.subTest(domain=domain):
                reward_computer = load_reward_module(domain).MyRewardComputer()
                common = {
                    "data_source": "rec/test",
                    "solution_str": VALID_REASONING,
                    "ground_truth": "<a_9><b_9><c_9>",
                    "extra_info": {
                        "history_sids": HISTORY_SIDS,
                        "sid_beam_predictions": ["<a_9><b_9><c_9>"],
                    },
                }
                hit = reward_computer.compute(**common)
                miss = reward_computer.compute(
                    **{
                        **common,
                        "extra_info": {
                            **common["extra_info"],
                            "sid_beam_predictions": ["<a_7><b_8><c_9>"],
                        },
                    }
                )

                self.assertEqual(hit["score"], 1.0)
                self.assertEqual(hit["sid_match_reward"], 1.0)
                self.assertEqual(hit["process_reward"], 1.0)
                self.assertEqual(miss["score"], 0.0)
                self.assertEqual(miss["sid_match_reward"], 0.0)
                self.assertEqual(miss["process_reward"], 1.0)

    def test_legacy_question_fallback_and_validation_beam_score(self):
        reward_computer = load_reward_module("Games").MyRewardComputer()
        expected_ndcg = 1.0 / math.log2(3.0)
        reward = reward_computer.compute(
            data_source="rec/test",
            solution_str=VALID_REASONING,
            ground_truth="<a_9><b_9><c_9>",
            extra_info={
                "question": [
                    {
                        "role": "user",
                        "content": "History: <a_240><b_208><c_129>.",
                    }
                ],
                "sid_beam_predictions": [
                    "<a_7><b_8><c_9>",
                    "<a_9><b_9><c_9>",
                ],
            },
        )

        self.assertAlmostEqual(reward["score"], expected_ndcg)
        self.assertAlmostEqual(reward["sid_match_reward"], expected_ndcg)
        self.assertEqual(reward["process_reward"], 1.0)


if __name__ == "__main__":
    unittest.main()