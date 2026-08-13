import importlib.util
from pathlib import Path
import unittest

import numpy as np


MODULE_PATH = Path(__file__).with_name("generation_metadata.py")
SPEC = importlib.util.spec_from_file_location("generation_metadata", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load generation metadata helper from {MODULE_PATH}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
copy_reward_models_for_generation = MODULE.copy_reward_models_for_generation


class GenerationMetadataTest(unittest.TestCase):
    def test_reward_models_are_copied_without_removing_source_metadata(self):
        reward_models = np.array(
            [{"ground_truth": "<a_1><b_1><c_1>"}, {"ground_truth": "<a_2><b_2><c_2>"}],
            dtype=object,
        )
        non_tensor_batch = {"reward_model": reward_models}

        copied = copy_reward_models_for_generation(non_tensor_batch, expected_size=2)

        self.assertIsNot(copied, reward_models)
        self.assertIs(non_tensor_batch["reward_model"], reward_models)
        self.assertEqual(copied.tolist(), reward_models.tolist())

    def test_missing_reward_models_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "requires reward_model metadata"):
            copy_reward_models_for_generation({}, expected_size=1)

    def test_misaligned_reward_models_are_rejected(self):
        reward_models = np.array([{"ground_truth": "<a_1><b_1><c_1>"}], dtype=object)

        with self.assertRaisesRegex(ValueError, "aligned with the generation batch"):
            copy_reward_models_for_generation({"reward_model": reward_models}, expected_size=2)


if __name__ == "__main__":
    unittest.main()