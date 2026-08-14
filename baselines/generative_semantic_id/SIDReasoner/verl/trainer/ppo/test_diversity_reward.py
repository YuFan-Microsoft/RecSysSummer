import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).with_name("diversity_reward.py")
SPEC = importlib.util.spec_from_file_location("diversity_reward", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load diversity reward module from {MODULE_PATH}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
binary_diversity_rewards = MODULE.binary_diversity_rewards


class DiversityRewardTest(unittest.TestCase):
    def test_runtime_float_baseline_thresholds_integer_counts(self):
        self.assertEqual(
            binary_diversity_rewards([2, 3, 4, 5], baseline_threshold=3.105),
            [0.0, 0.0, 1.0, 1.0],
        )

    def test_threshold_is_not_hardcoded(self):
        self.assertEqual(
            binary_diversity_rewards([3, 4, 5], baseline_threshold=4.2),
            [0.0, 0.0, 1.0],
        )


if __name__ == "__main__":
    unittest.main()