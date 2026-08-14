import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).with_name("sid_diversity.py")
SPEC = importlib.util.spec_from_file_location("sid_diversity", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load SID diversity module from {MODULE_PATH}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
select_sid_candidate = MODULE.select_sid_candidate
count_unique_first_sid_tokens = MODULE.count_unique_first_sid_tokens


class SidDiversitySelectionTest(unittest.TestCase):
    def test_validation_diversity_counts_unique_first_tokens_in_top_ten(self):
        predictions = [
            "<a_1><b_1><c_1>",
            "<a_1><b_2><c_2>",
            "<a_2><b_3><c_3>",
            "<a_3><b_4><c_4>",
        ]

        self.assertEqual(count_unique_first_sid_tokens(predictions), 3)

    def test_diversity_uses_unique_first_sid_tokens(self):
        selection = select_sid_candidate(
            candidates=[[1, 10, 100], [1, 11, 101], [2, 20, 200], [3, 30, 300]],
            cumulative_logprobs=[-1.0, -2.0, -3.0, -4.0],
            target_sid=[9, 90, 900],
        )

        self.assertEqual(selection.first_token_unique_count, 3)

    def test_exact_match_is_selected(self):
        selection = select_sid_candidate(
            candidates=[[1, 10, 100], [2, 20, 200], [3, 30, 300]],
            cumulative_logprobs=[-0.1, -3.0, -1.0],
            target_sid=[2, 20, 200],
        )

        self.assertEqual(selection.selected_index, 1)
        self.assertEqual(selection.exact_match_count, 1)

    def test_best_logprob_wins_when_exact_match_is_sampled_multiple_times(self):
        selection = select_sid_candidate(
            candidates=[[2, 20, 200], [1, 10, 100], [2, 20, 200]],
            cumulative_logprobs=[-2.0, -0.1, -0.5],
            target_sid=[2, 20, 200],
        )

        self.assertEqual(selection.selected_index, 2)
        self.assertEqual(selection.exact_match_count, 2)

    def test_first_sample_is_retained_without_exact_match(self):
        selection = select_sid_candidate(
            candidates=[[1, 10, 100], [2, 20, 200]],
            cumulative_logprobs=[-4.0, -0.1],
            target_sid=[3, 30, 300],
        )

        self.assertEqual(selection.selected_index, 0)
        self.assertEqual(selection.exact_match_count, 0)


if __name__ == "__main__":
    unittest.main()