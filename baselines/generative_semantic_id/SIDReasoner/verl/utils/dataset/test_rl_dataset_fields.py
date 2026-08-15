import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).with_name("rl_dataset_fields.py")
SPEC = importlib.util.spec_from_file_location("rl_dataset_fields", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load dataset field helpers from {MODULE_PATH}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
ensure_history_sids_in_extra_info = MODULE.ensure_history_sids_in_extra_info


class EnsureHistorySidsInExtraInfoTest(unittest.TestCase):
    def test_preserves_nested_history_sids(self):
        row = {
            "history_sids": ["top-level"],
            "extra_info": {"history_sids": ["nested"]},
        }

        normalized = ensure_history_sids_in_extra_info(row)

        self.assertEqual(normalized["extra_info"]["history_sids"], ["nested"])

    def test_copies_top_level_history_sids_when_nested_value_is_missing(self):
        row = {"history_sids": ["<a_1><b_1><c_1>"], "extra_info": {"index": 7}}

        normalized = ensure_history_sids_in_extra_info(row)

        self.assertEqual(normalized["extra_info"]["history_sids"], row["history_sids"])
        self.assertEqual(normalized["extra_info"]["index"], 7)

    def test_initializes_empty_extra_info_without_history_sids(self):
        normalized = ensure_history_sids_in_extra_info({"extra_info": None})

        self.assertEqual(normalized["extra_info"], {})


if __name__ == "__main__":
    unittest.main()