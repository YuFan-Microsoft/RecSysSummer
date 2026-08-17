import importlib.util
from pathlib import Path
import sys
import types
import unittest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

verl_module = sys.modules.setdefault("verl", types.ModuleType("verl"))
utils_module = sys.modules.setdefault("verl.utils", types.ModuleType("verl.utils"))
reward_score_module = sys.modules.setdefault(
    "verl.utils.reward_score", types.ModuleType("verl.utils.reward_score")
)
verl_module.utils = utils_module
utils_module.reward_score = reward_score_module

format_path = Path(__file__).resolve().parents[2] / "utils" / "reward_score" / "sid_reasoning_format.py"
format_spec = importlib.util.spec_from_file_location(
    "verl.utils.reward_score.sid_reasoning_format",
    format_path,
)
FORMAT_MODULE = importlib.util.module_from_spec(format_spec)
sys.modules[format_spec.name] = FORMAT_MODULE
format_spec.loader.exec_module(FORMAT_MODULE)

module_path = Path(__file__).with_name("interest_reward.py")
module_spec = importlib.util.spec_from_file_location("interest_reward_test_module", module_path)
MODULE = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(MODULE)
evaluate_interest_rewards = MODULE.evaluate_interest_rewards
build_interest_validation_metrics = MODULE.build_interest_validation_metrics
extract_target_sid = MODULE._extract_target_sid


def reasoning(*interest_texts):
    lines = [
        f"- [{'exploit' if index == 0 else 'explore'}] <a_1><b_2><c_3> => {text}"
        for index, text in enumerate(interest_texts)
    ]
    return (
        "<think>\n<history_summary>\n"
        "- <a_1><b_2><c_3> => A history item.\n"
        "</history_summary>\n<future_interests>\n"
        + "\n".join(lines)
        + "\n</future_interests>\n</think>\n<a_9><b_9><c_9>"
    )


class FakeClient:
    calls = []
    rank_by_interest = {
        "target at seven": 7,
        "target at thirty": 30,
        "miss": -1,
    }

    def __init__(self, endpoint, timeout, max_attempts):
        self.endpoint = endpoint

    def rank_batch(self, payloads):
        self.__class__.calls.append(payloads)
        return [self.rank_by_interest[payload["interest"]] for payload in payloads]


class FailingSecondBatchClient(FakeClient):
    def rank_batch(self, payloads):
        if len(self.__class__.calls) == 1:
            raise RuntimeError("HTTP 404")
        return super().rank_batch(payloads)


class WrongLengthClient(FakeClient):
    def rank_batch(self, payloads):
        return []


class InterestRewardTest(unittest.TestCase):
    def setUp(self):
        FakeClient.calls = []

    def test_any_interest_rank_controls_configurable_block_reward(self):
        result = evaluate_interest_rewards(
            solutions=[reasoning("miss", "target at thirty")],
            target_sids=["<a_9><b_9><c_9>"],
            endpoint="http://retriever",
            reward_top_k=50,
            client_factory=FakeClient,
        )
        self.assertEqual(result["interest_block_rank"], [30.0])
        self.assertEqual(result["interest_reward"], [1.0])
        self.assertEqual(result["interest_hit_at_20"], [0.0])
        self.assertEqual(result["interest_hit_at_50"], [1.0])

    def test_miss_is_minus_one_and_zero_reward(self):
        result = evaluate_interest_rewards(
            solutions=[reasoning("miss", "miss")],
            target_sids=["<a_9><b_9><c_9>"],
            endpoint="http://retriever",
            reward_top_k=100,
            client_factory=FakeClient,
        )
        self.assertEqual(result["interest_block_rank"], [-1.0])
        self.assertEqual(result["interest_reward"], [0.0])

    def test_invalid_format_skips_endpoint_and_receives_zero(self):
        result = evaluate_interest_rewards(
            solutions=["malformed"],
            target_sids=["<a_9><b_9><c_9>"],
            endpoint="http://retriever",
            reward_top_k=50,
            client_factory=FakeClient,
        )
        self.assertEqual(FakeClient.calls, [])
        self.assertEqual(result["interest_format_valid"], [0.0])
        self.assertEqual(result["interest_block_rank"], [-1.0])
        self.assertEqual(result["interest_query_count"], [0.0])
        self.assertEqual(result["interest_reward"], [0.0])

    def test_requests_are_chunked_without_reordering_results(self):
        result = evaluate_interest_rewards(
            solutions=[
                reasoning("target at seven", "miss"),
                reasoning("target at thirty", "miss"),
            ],
            target_sids=["<a_9><b_9><c_9>", "<a_8><b_8><c_8>"],
            endpoint="http://retriever",
            reward_top_k=20,
            request_batch_size=2,
            client_factory=FakeClient,
        )
        self.assertEqual(len(FakeClient.calls), 2)
        self.assertEqual(result["interest_block_rank"], [7.0, 30.0])
        self.assertEqual(result["interest_reward"], [1.0, 0.0])

    def test_failed_request_chunk_disables_interest_reward_for_whole_batch(self):
        with self.assertWarnsRegex(RuntimeWarning, "HTTP 404"):
            result = evaluate_interest_rewards(
                solutions=[
                    reasoning("target at seven", "miss"),
                    reasoning("target at thirty", "miss"),
                ],
                target_sids=["<a_9><b_9><c_9>", "<a_8><b_8><c_8>"],
                endpoint="http://retriever",
                reward_top_k=50,
                request_batch_size=2,
                client_factory=FailingSecondBatchClient,
            )
        self.assertEqual(result["interest_block_rank"], [-1.0, -1.0])
        self.assertEqual(result["interest_reward"], [0.0, 0.0])
        self.assertEqual(result["interest_request_failed"], [1.0, 1.0])

    def test_wrong_length_response_disables_interest_reward(self):
        with self.assertWarnsRegex(RuntimeWarning, "wrong number of results"):
            result = evaluate_interest_rewards(
                solutions=[reasoning("target at seven", "miss")],
                target_sids=["<a_9><b_9><c_9>"],
                endpoint="http://retriever",
                reward_top_k=50,
                client_factory=WrongLengthClient,
            )
        self.assertEqual(result["interest_reward"], [0.0])
        self.assertEqual(result["interest_request_failed"], [1.0])

    def test_failed_request_chunk_can_remain_strict(self):
        with self.assertRaisesRegex(RuntimeError, "HTTP 404"):
            evaluate_interest_rewards(
                solutions=[reasoning("target at seven", "miss")],
                target_sids=["<a_9><b_9><c_9>"],
                endpoint="http://retriever",
                reward_top_k=50,
                request_batch_size=1,
                fail_open=False,
                client_factory=FailingSecondBatchClient,
            )

    def test_target_sid_must_be_one_exact_sid(self):
        self.assertEqual(extract_target_sid(" <a_1><b_2><c_3> "), "<a_1><b_2><c_3>")
        for value in (
            "target=<a_1><b_2><c_3>",
            "<a_1><b_2><c_3> <a_4><b_5><c_6>",
            "missing",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                extract_target_sid(value)

    def test_validation_metrics_use_one_vote_per_history(self):
        interest_results = {
            "interest_hit_at_20": [1.0, 0.0, 1.0],
            "interest_hit_at_50": [1.0, 1.0, 1.0],
            "interest_hit_at_100": [1.0, 1.0, 1.0],
        }
        metrics = build_interest_validation_metrics(interest_results, [0.0, 1.0, 1.0])
        self.assertEqual(metrics["interest_only_hit_at_20"], [1.0, 0.0, 0.0])
        self.assertEqual(set(metrics), {
            "interest_only_hit_at_20",
            "interest_only_hit_at_50",
            "interest_only_hit_at_100",
        })


if __name__ == "__main__":
    unittest.main()