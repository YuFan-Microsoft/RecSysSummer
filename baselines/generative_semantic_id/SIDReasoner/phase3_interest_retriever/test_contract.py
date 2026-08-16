import unittest

from phase3_interest_retriever.schemas import (
    InterestResult,
    RetrieveBatchRequest,
    RetrieveRequest,
    RetrieveResponse,
    RetrievedItem,
)


class RetrieverContractTest(unittest.TestCase):
    def test_request_accepts_multiple_interests(self):
        request = RetrieveRequest(
            request_id="rollout-7",
            target_sid="<a_1><b_2><c_3>",
            interests=["survival crafting games", "console accessories"],
            top_k=20,
        )
        self.assertEqual(len(request.interests), 2)

    def test_request_rejects_invalid_sid(self):
        with self.assertRaises(ValueError):
            RetrieveRequest(target_sid="item-1", interests=["games"])

    def test_batch_rejects_duplicate_request_ids(self):
        request = RetrieveRequest(
            request_id="duplicate",
            target_sid="<a_1><b_2><c_3>",
            interests=["games"],
        )
        with self.assertRaises(ValueError):
            RetrieveBatchRequest(requests=[request, request])

    def test_response_uses_any_interest_hit(self):
        miss = InterestResult(
            interest="console accessories",
            target_hit=False,
            items=[],
        )
        hit = InterestResult(
            interest="survival crafting games",
            target_hit=True,
            target_rank=1,
            items=[
                RetrievedItem(
                    sid="<a_1><b_2><c_3>",
                    title="Target game",
                    score=0.9,
                    rank=1,
                )
            ],
        )
        response = RetrieveResponse(
            request_id="rollout-7",
            target_sid="<a_1><b_2><c_3>",
            any_hit=True,
            reward=1.0,
            results=[miss, hit],
            latency_ms=3,
        )
        self.assertEqual(response.reward, 1.0)

    def test_response_rejects_inconsistent_reward(self):
        with self.assertRaises(ValueError):
            RetrieveResponse(
                request_id="rollout-7",
                target_sid="<a_1><b_2><c_3>",
                any_hit=False,
                reward=1.0,
                results=[],
                latency_ms=3,
            )


if __name__ == "__main__":
    unittest.main()