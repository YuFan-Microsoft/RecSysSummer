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
<history_summary>
- <a_240><b_208><c_129> => The recorded item is a Rockstar Games title.
- <a_240><b_208><c_129> => The game is part of the Grand Theft Auto series.
</history_summary>
<future_interests>
- [exploit] <a_240><b_208><c_129> => The user may continue with urban action games from the same series.
- [explore] <a_240><b_208><c_129> => The open-world setting bridges to other exploration-driven games and <a_9><b_9><c_9>.
</future_interests>
</think>
<a_9><b_9><c_9>"""
HISTORY_SIDS = ["<a_240><b_208><c_129>"]

MULTI_SID_REASONING = """<history_summary>
- <a_140><b_237><c_88>, <a_74><b_218><c_196> => Two game listings belong to the same franchise.
- <a_249><b_80><c_0>, <a_249><b_138><c_211>, <a_249><b_138><c_211> => The history contains related hardware and accessory listings.
- <a_10><b_193><c_15>, <a_131><b_233><c_112> => Two console game listings are role-playing titles.
</history_summary>
<future_interests>
- [exploit] <a_249><b_80><c_0>, <a_249><b_138><c_211>, <a_249><b_138><c_211> => The user may continue with accessories for the same hardware family.
- [explore] <a_140><b_237><c_88>, <a_74><b_218><c_196> => The shared franchise bridges to story-driven games in a neighboring genre.
- [explore] <a_10><b_193><c_15>, <a_131><b_233><c_112> => Role-playing progression bridges to strategy games with long-term character planning.
</future_interests>
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
    def test_v4_multi_sid_trace_receives_full_reward(self):
        self.assertEqual(
            calculate_process_rewards(MULTI_SID_REASONING, MULTI_SID_HISTORY),
            {
                "history_summary_grounding_reward": 1.0,
                "future_interests_grounding_reward": 1.0,
                "format_reward": 1.0,
                "history_reference_coverage": 1.0,
                "latest_history_summary_reference_reward": 1.0,
                "process_reward": 1.0,
            },
        )

    def test_history_reference_coverage_is_independent_of_grounding(self):
        response = MULTI_SID_REASONING.replace(
            "<a_249><b_138><c_211>",
            "<a_249><b_80><c_0>",
        )
        scores = calculate_process_rewards(response, MULTI_SID_HISTORY)
        self.assertEqual(scores["format_reward"], 1.0)
        self.assertEqual(scores["history_summary_grounding_reward"], 1.0)
        self.assertEqual(scores["future_interests_grounding_reward"], 1.0)
        self.assertEqual(scores["latest_history_summary_reference_reward"], 1.0)
        self.assertEqual(scores["process_reward"], 1.0)
        self.assertAlmostEqual(scores["history_reference_coverage"], 5.0 / 6.0)

    def test_latest_history_sid_must_be_cited_in_summary(self):
        response = MULTI_SID_REASONING.replace(
            "- <a_10><b_193><c_15>, <a_131><b_233><c_112> => Two console game listings are role-playing titles.",
            "- <a_10><b_193><c_15> => One console game listing is a role-playing title.",
            1,
        )
        scores = calculate_process_rewards(response, MULTI_SID_HISTORY)
        self.assertEqual(scores["format_reward"], 1.0)
        self.assertEqual(scores["history_summary_grounding_reward"], 1.0)
        self.assertEqual(scores["future_interests_grounding_reward"], 1.0)
        self.assertEqual(scores["history_reference_coverage"], 1.0)
        self.assertEqual(scores["latest_history_summary_reference_reward"], 0.0)
        self.assertEqual(scores["process_reward"], 0.0)

    def test_invalid_citation_syntax_fails_process_hard_gate(self):
        response = VALID_REASONING.replace(
            "<a_240><b_208><c_129> => The recorded item",
            "<a_240><b_208><c_129> <a_240><b_208><c_129> => The recorded item",
            1,
        )
        scores = calculate_process_rewards(response, HISTORY_SIDS)
        self.assertEqual(scores["format_reward"], 0.0)
        self.assertEqual(scores["history_summary_grounding_reward"], 0.5)
        self.assertEqual(scores["process_reward"], 0.0)

    def test_non_history_citation_fails_process_hard_gate(self):
        response = VALID_REASONING.replace(
            "[explore] <a_240><b_208><c_129>",
            "[explore] <a_240><b_208><c_129>, <a_999><b_999><c_999>",
            1,
        )
        scores = calculate_process_rewards(response, HISTORY_SIDS)
        self.assertEqual(scores["format_reward"], 1.0)
        self.assertEqual(scores["history_summary_grounding_reward"], 1.0)
        self.assertEqual(scores["future_interests_grounding_reward"], 0.5)
        self.assertEqual(scores["process_reward"], 0.0)

    def test_valid_repeated_citations_and_target_in_text_receive_full_reward(self):
        self.assertTrue(
            all(
                reward == 1.0
                for reward in calculate_process_rewards(VALID_REASONING, HISTORY_SIDS).values()
            )
        )

    def test_opening_think_is_optional(self):
        response = VALID_REASONING.replace("<think>\n", "", 1)
        self.assertEqual(calculate_process_rewards(response, HISTORY_SIDS)["process_reward"], 1.0)

    def test_missing_mode_fails_process_hard_gate(self):
        response = VALID_REASONING.replace("[explore]", "[exploit]", 1)
        scores = calculate_process_rewards(response, HISTORY_SIDS)
        self.assertEqual(scores["format_reward"], 0.0)
        self.assertEqual(scores["history_summary_grounding_reward"], 1.0)
        self.assertEqual(scores["future_interests_grounding_reward"], 1.0)
        self.assertEqual(scores["process_reward"], 0.0)

    def test_invalid_future_interest_count_fails_process_hard_gate(self):
        response = VALID_REASONING.replace(
            "- [explore] <a_240><b_208><c_129> => The open-world setting bridges to other exploration-driven games and <a_9><b_9><c_9>.\n",
            "",
        )
        scores = calculate_process_rewards(response, HISTORY_SIDS)
        self.assertEqual(scores["format_reward"], 0.0)
        self.assertEqual(scores["history_summary_grounding_reward"], 1.0)
        self.assertEqual(scores["future_interests_grounding_reward"], 1.0)
        self.assertEqual(scores["process_reward"], 0.0)

    def test_wrong_block_order_or_extra_text_returns_zero(self):
        history_start = VALID_REASONING.index("<history_summary>")
        history_end = VALID_REASONING.index("</history_summary>") + len("</history_summary>")
        interest_start = VALID_REASONING.index("<future_interests>")
        interest_end = VALID_REASONING.index("</future_interests>") + len("</future_interests>")
        wrong_order = (
            VALID_REASONING[:history_start]
            + VALID_REASONING[interest_start:interest_end]
            + "\n"
            + VALID_REASONING[history_start:history_end]
            + VALID_REASONING[interest_end:]
        )
        extra_text = VALID_REASONING.replace("<history_summary>", "preamble\n<history_summary>", 1)
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