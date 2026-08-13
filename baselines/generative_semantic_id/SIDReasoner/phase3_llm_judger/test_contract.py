import json
import unittest

from phase3_llm_judger.prompts import build_messages
from phase3_llm_judger.schemas import JudgeRequest, ModelJudgeOutput


def sample_request() -> JudgeRequest:
    return JudgeRequest.model_validate(
        {
            "request_id": "group-42",
            "history": [
                {
                    "sid": "<a_1><b_2><c_3>",
                    "title": "Fallout 4 - PlayStation 4",
                }
            ],
            "target": {
                "sid": "<a_4><b_5><c_6>",
                "title": "The Forest - PlayStation 4",
            },
            "candidates": [
                {
                    "candidate_id": "0",
                    "reasoning": "A history-grounded survival-crafting bridge.",
                    "predicted_item": {
                        "sid": "<a_7><b_8><c_9>",
                        "title": "ARK: Survival Evolved - PlayStation 4",
                    },
                },
                {
                    "candidate_id": "1",
                    "reasoning": "Only a broad platform shortcut.",
                    "predicted_item": {
                        "sid": "<a_10><b_11><c_12>",
                        "title": "DualShock 4 Wireless Controller",
                    },
                    "hard_valid": False,
                },
            ],
        }
    )


class JudgeContractTest(unittest.TestCase):
    def test_prompt_shuffle_is_deterministic_and_preserves_ids(self):
        request = sample_request()
        first = build_messages(request)
        second = build_messages(request)
        self.assertEqual(first, second)
        payload = json.loads(first[1]["content"].split("INPUT_DATA:\n", maxsplit=1)[1])
        self.assertEqual(
            {candidate["candidate_id"] for candidate in payload["rollout_candidates"]},
            {"0", "1"},
        )

    def test_model_output_accepts_relative_tiers(self):
        output = ModelJudgeOutput.model_validate(
            {
                "high": ["0"],
                "medium": [],
                "low": ["1"],
            }
        )
        self.assertEqual(output.high, ["0"])

    def test_all_low_output_is_allowed(self):
        output = ModelJudgeOutput.model_validate(
            {"high": [], "medium": [], "low": ["0", "1"]}
        )
        self.assertEqual(output.low, ["0", "1"])

    def test_candidate_cannot_appear_in_multiple_tiers(self):
        with self.assertRaises(ValueError):
            ModelJudgeOutput.model_validate(
                {"high": ["0"], "medium": ["0"], "low": ["1"]}
            )

    def test_duplicate_candidate_ids_are_rejected(self):
        payload = sample_request().model_dump()
        payload["candidates"][1]["candidate_id"] = "0"
        with self.assertRaises(ValueError):
            JudgeRequest.model_validate(payload)

    def test_oversized_request_is_rejected(self):
        payload = sample_request().model_dump()
        template = payload["candidates"][0]
        payload["candidates"] = []
        for index in range(12):
            candidate = json.loads(json.dumps(template))
            candidate["candidate_id"] = str(index)
            candidate["reasoning"] = "x" * 9000
            payload["candidates"].append(candidate)
        with self.assertRaises(ValueError):
            JudgeRequest.model_validate(payload)

    def test_guided_json_schema_is_strict(self):
        schema = ModelJudgeOutput.model_json_schema()
        self.assertEqual(schema["type"], "object")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["properties"]), {"high", "medium", "low"})


if __name__ == "__main__":
    unittest.main()