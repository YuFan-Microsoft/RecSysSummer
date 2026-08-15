import importlib.util
import math
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).with_name("sid_eval_slices.py")
SPEC = importlib.util.spec_from_file_location("sid_eval_slices", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load SID evaluation slices from {MODULE_PATH}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
SLICE_METRIC_KEYS = MODULE.SLICE_METRIC_KEYS
compute_novel_repeat_ranking_metrics = MODULE.compute_novel_repeat_ranking_metrics
mean_present_values = MODULE.mean_present_values


class SidEvaluationSlicesTest(unittest.TestCase):
    def test_metrics_remain_batch_aligned_and_average_each_slice(self):
        metrics = compute_novel_repeat_ranking_metrics(
            beam_predictions=[
                [
                    "<a_1><b_1><c_1>",
                    "<a_2><b_2><c_2>",
                    "<a_3><b_3><c_3>",
                    "<a_4><b_4><c_4>",
                    "<a_5><b_5><c_5>",
                    "<a_9><b_9><c_9>",
                ],
                ["<a_1><b_1><c_1>", "<a_2><b_2><c_2>", "<a_7><b_7><c_7>"],
            ],
            ground_truths=["<a_9><b_9><c_9>", "<a_7><b_7><c_7>"],
            history_sids=[["<a_1><b_1><c_1>"], ["<a_7><b_7><c_7>"]],
        )

        self.assertTrue(all(len(values) == 2 for values in metrics.values()))
        self.assertEqual(metrics["sid_eval_novel_hr_at_5"], [0.0, None])
        self.assertEqual(metrics["sid_eval_novel_hr_at_10"], [1.0, None])
        self.assertEqual(metrics["sid_eval_repeat_hr_at_5"], [None, 1.0])
        self.assertEqual(metrics["sid_eval_repeat_ndcg_at_5"], [None, 0.5])
        self.assertAlmostEqual(
            mean_present_values(metrics["sid_eval_novel_ndcg_at_10"]),
            1.0 / math.log2(7),
        )
        self.assertEqual(mean_present_values(metrics["sid_eval_repeat_hr_at_10"]), 1.0)

    def test_empty_slice_has_no_mean(self):
        self.assertIsNone(mean_present_values([None, None]))

    def test_all_expected_metrics_are_emitted(self):
        metrics = compute_novel_repeat_ranking_metrics(
            beam_predictions=[["<a_1><b_1><c_1>"]],
            ground_truths=["<a_1><b_1><c_1>"],
            history_sids=[[]],
        )

        self.assertEqual(set(metrics), set(SLICE_METRIC_KEYS))


if __name__ == "__main__":
    unittest.main()