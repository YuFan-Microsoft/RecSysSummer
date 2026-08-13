import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).with_name("sid_eval_metrics.py")
SPEC = importlib.util.spec_from_file_location("sid_eval_metrics", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load SID evaluation metrics from {MODULE_PATH}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
count_unique_first_sid_tokens = MODULE.count_unique_first_sid_tokens


class SidEvaluationMetricsTest(unittest.TestCase):
    def test_diversity_counts_unique_first_tokens(self):
        predictions = [
            "<a_1><b_1><c_1>",
            "<a_1><b_2><c_2>",
            "<a_2><b_3><c_3>",
            "<a_3><b_4><c_4>",
        ]

        self.assertEqual(count_unique_first_sid_tokens(predictions), 3)

    def test_diversity_uses_only_top_ten(self):
        predictions = [f"<a_{index}><b_1><c_1>" for index in range(11)]

        self.assertEqual(count_unique_first_sid_tokens(predictions), 10)


if __name__ == "__main__":
    unittest.main()