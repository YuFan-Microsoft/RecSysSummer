import unittest

from phase3_interest_retriever.client import (
    AsyncInterestRetrieverClient,
    InterestRetrieverClient,
)
from phase3_interest_retriever.schemas import (
    RankBatchResponse,
    RankRequest,
    RankResponse,
)


class RetrieverContractTest(unittest.TestCase):
    def test_rank_contract_uses_one_interest_and_one_target(self):
        request = RankRequest(
            interest="survival crafting games",
            target_sid="<a_1><b_2><c_3>",
        )
        self.assertEqual(request.interest, "survival crafting games")
        self.assertEqual(RankResponse(rank=-1).rank, -1)
        self.assertEqual(RankResponse(rank=100).rank, 100)

    def test_rank_contract_rejects_out_of_range_values(self):
        for rank in (-2, 0, 101):
            with self.subTest(rank=rank), self.assertRaises(ValueError):
                RankResponse(rank=rank)
        with self.assertRaises(ValueError):
            RankBatchResponse(ranks=[1, 0])

    def test_rank_request_rejects_invalid_sid(self):
        with self.assertRaises(ValueError):
            RankRequest(target_sid="item-1", interest="games")

    def test_clients_accept_full_rank_endpoints(self):
        batch_endpoint = "https://example.test/v1/rank/batch/"
        rank_endpoint = "https://example.test/v1/rank"
        self.assertEqual(InterestRetrieverClient(batch_endpoint).base_url, "https://example.test")
        self.assertEqual(AsyncInterestRetrieverClient(rank_endpoint).base_url, "https://example.test")


if __name__ == "__main__":
    unittest.main()