import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).with_name("beam_diversity.py")
SPEC = importlib.util.spec_from_file_location("beam_diversity", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load beam diversity module from {MODULE_PATH}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
calculate_beam_diversity = MODULE.calculate_beam_diversity


class BeamDiversityTest(unittest.TestCase):
    def test_counts_unique_first_tokens_and_normalizes_by_beam_size(self):
        sid_beam = [
            [1, 10, 100],
            [1, 11, 101],
            [2, 20, 200],
            [2, 21, 201],
            [3, 30, 300],
            [3, 31, 301],
            [4, 40, 400],
            [4, 41, 401],
            [1, 12, 102],
            [2, 22, 202],
        ]

        diversity = calculate_beam_diversity(sid_beam, expected_size=10)

        self.assertEqual(diversity.first_token_unique_count, 4)
        self.assertEqual(diversity.normalized_reward, 0.4)

    def test_collapsed_beam_has_minimum_normalized_reward(self):
        sid_beam = [[1, index, index] for index in range(10)]

        diversity = calculate_beam_diversity(sid_beam, expected_size=10)

        self.assertEqual(diversity.first_token_unique_count, 1)
        self.assertEqual(diversity.normalized_reward, 0.1)

    def test_ragged_beam_keeps_the_configured_top_ten_scale(self):
        diversity = calculate_beam_diversity(
            [[1, 10, 100], [2, 20, 200], [3, 30, 300]],
            expected_size=10,
        )

        self.assertEqual(diversity.first_token_unique_count, 3)
        self.assertEqual(diversity.normalized_reward, 0.3)


if __name__ == "__main__":
    unittest.main()