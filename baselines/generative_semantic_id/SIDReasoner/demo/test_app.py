from __future__ import annotations

import random
import re
import unittest
from types import SimpleNamespace

from app import (
    CatalogItem,
    GameCatalog,
    ModelEndpoint,
    build_sid_token_trie,
    build_messages,
    normalize_openai_base_url,
    parse_generation,
    prepare_reasoning_prefix,
    sample_test_history,
    validate_history_selections,
)


def make_item(item_id: int, sid: str, title: str) -> CatalogItem:
    return CatalogItem(
        item_id=item_id,
        sid=sid,
        title=title,
        description=f"Description for {title}",
        brand="Test Brand",
        detailed_description="",
        retrieval_summary=f"Summary for {title}",
    )


class CatalogTest(unittest.TestCase):
    def setUp(self) -> None:
        self.first = make_item(1, "<a_1><b_2><c_3>", "The First Game")
        self.second = make_item(2, "<a_4><b_5><c_6>", "Another Great Game")
        self.catalog = GameCatalog([self.first, self.second])

    def test_resolves_sid_and_title_history(self) -> None:
        sid_items, _ = self.catalog.resolve_history(
            "<a_1><b_2><c_3>, <a_4><b_5><c_6>"
        )
        title_items, notes = self.catalog.resolve_history(
            "The First Game\nAnother Great Game"
        )
        self.assertEqual(sid_items, [self.first, self.second])
        self.assertEqual(title_items, [self.first, self.second])
        self.assertEqual(notes, ["exact title", "exact title"])

    def test_rejects_unknown_sid(self) -> None:
        with self.assertRaisesRegex(ValueError, "not in Video_Games_catalog"):
            self.catalog.resolve_history("<a_9><b_9><c_9>")

    def test_preserves_sid_collisions(self) -> None:
        duplicate = make_item(3, self.first.sid, "A Different Catalog Item")
        catalog = GameCatalog([self.first, duplicate])
        items, notes = catalog.resolve_history(self.first.sid)
        self.assertEqual(catalog.by_sid[self.first.sid], [self.first, duplicate])
        self.assertEqual(items, [self.first])
        self.assertEqual(notes, ["exact SID (2 catalog matches)"])

    def test_selector_choices_show_title_and_sid(self) -> None:
        choices = self.catalog.selector_choices()
        self.assertIn(
            ("The First Game — <a_1><b_2><c_3>", self.first.sid),
            choices,
        )

    def test_selector_choices_keep_popularity_top_five_per_first_sid(self) -> None:
        items = [
            make_item(index, f"<a_1><b_{index}><c_{index}>", f"Game {index:02d}")
            for index in range(8)
        ]
        popularity = {item.sid: item.item_id for item in items}
        catalog = GameCatalog(items, sid_popularity=popularity)
        choices = catalog.selector_choices(max_per_first_sid=5)
        self.assertEqual(len(choices), 5)
        self.assertEqual(
            {sid for _, sid in choices},
            {item.sid for item in items[-5:]},
        )

    def test_history_selection_requires_two_to_five_items(self) -> None:
        with self.assertRaisesRegex(ValueError, "first 2"):
            validate_history_selections([self.first.sid])
        selected = validate_history_selections(
            [self.first.sid, self.second.sid, None]
        )
        self.assertEqual(selected, [self.first.sid, self.second.sid])

    def test_history_selection_rejects_empty_middle_position(self) -> None:
        with self.assertRaisesRegex(ValueError, "without empty positions"):
            validate_history_selections(
                [self.first.sid, self.second.sid, self.first.sid, None, self.second.sid]
            )

    def test_random_history_is_an_unchanged_test_sequence(self) -> None:
        histories = [
            ["<a_1><b_1><c_1>", "<a_1><b_2><c_2>"],
            ["<a_2><b_1><c_1>", "<a_3><b_2><c_2>", "<a_2><b_3><c_3>"],
        ]
        history = sample_test_history(histories, rng=random.Random(42))
        self.assertIn(history, histories)
        self.assertIsNot(history, histories[0])
        self.assertIsNot(history, histories[1])


class GenerationParserTest(unittest.TestCase):
    def test_parses_v4_reasoning_and_prediction(self) -> None:
        raw = """<think>
<history_summary>
- <a_1><b_2><c_3> => The history contains an action game.
</history_summary>
<future_interests>
- [exploit] <a_1><b_2><c_3> => More action games with direct combat.
- [explore] <a_1><b_2><c_3> => Tactical games bridged by strategic combat.
</future_interests>
</think>

<a_4><b_5><c_6>"""
        parsed = parse_generation(raw)
        self.assertEqual(parsed.prediction_sid, "<a_4><b_5><c_6>")
        self.assertEqual(parsed.summaries[0]["evidence"], "<a_1><b_2><c_3>")
        self.assertEqual(
            [interest["mode"] for interest in parsed.interests],
            ["exploit", "explore"],
        )
        self.assertEqual(parsed.format_status, "Valid structured output")

    def test_keeps_prediction_when_reasoning_is_unstructured(self) -> None:
        parsed = parse_generation("Free-form reasoning\n<a_4><b_5><c_6>")
        self.assertEqual(parsed.prediction_sid, "<a_4><b_5><c_6>")
        self.assertIn("missing history_summary", parsed.format_status)


class EndpointAndPromptTest(unittest.TestCase):
    def test_normalizes_endpoint(self) -> None:
        self.assertEqual(
            normalize_openai_base_url("http://localhost:8000/v1/chat/completions"),
            "http://localhost:8000/v1",
        )

    def test_reasoning_request_matches_evaluation_sampling(self) -> None:
        class FakeChatCompletions:
            def __init__(self):
                self.kwargs = None

            def create(self, **kwargs):
                self.kwargs = kwargs
                return SimpleNamespace(
                    choices=[SimpleNamespace(token_ids=[1, 2, 3])]
                )

        chat = FakeChatCompletions()
        endpoint = ModelEndpoint.__new__(ModelEndpoint)
        endpoint.model = "sidreasoner"
        endpoint.client = SimpleNamespace(
            chat=SimpleNamespace(completions=chat)
        )
        token_ids = endpoint.generate(
            build_messages(["<a_1><b_2><c_3>", "<a_4><b_5><c_6>"]),
            max_tokens=1016,
        )
        self.assertEqual(token_ids, [1, 2, 3])
        self.assertEqual(chat.kwargs["temperature"], 0.0)
        self.assertEqual(chat.kwargs["top_p"], 1.0)
        self.assertEqual(chat.kwargs["seed"], 42)
        self.assertEqual(chat.kwargs["n"], 1)
        self.assertEqual(
            chat.kwargs["extra_body"],
            {
                "best_of": 1,
                "min_tokens": 1,
                "top_k": -1,
                "min_p": 0.0,
                "repetition_penalty": 1.0,
                "add_generation_prompt": True,
                "add_special_tokens": False,
                "return_token_ids": True,
                "skip_special_tokens": False,
                "spaces_between_special_tokens": False,
            },
        )
        self.assertEqual(
            normalize_openai_base_url("http://localhost:8000"),
            "http://localhost:8000/v1",
        )

    def test_prompt_matches_training_shape(self) -> None:
        messages = build_messages(["<a_1><b_2><c_3>"])
        self.assertEqual(
            messages,
            [
                {
                    "role": "system",
                    "content": (
                        "Below is an instruction that describes a task, paired with an "
                        "input that provides further context. Write a response that "
                        "appropriately completes the request.\nCan you recommend the next "
                        "item for the user based on their interaction history?\n"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "The user has sequentially interacted with items "
                        "<a_1><b_2><c_3>. Can you recommend the next item for him? "
                        "Let's think step by step before making recommendation. Directly "
                        "output the item SID after thinking."
                    ),
                },
            ],
        )

    def test_reasoning_prefix_matches_evaluation_normalization(self) -> None:
        self.assertEqual(
            prepare_reasoning_prefix(
                [1, 2, 90, 50, 51],
                end_think_marker=[90],
                reasoning_separator=[90, 91],
                eos_token_id=0,
                max_length=10,
            ),
            [1, 2, 90, 91],
        )
        self.assertEqual(
            prepare_reasoning_prefix(
                [1, 2, 0],
                end_think_marker=[90],
                reasoning_separator=[90, 91],
                eos_token_id=0,
                max_length=10,
            ),
            [1, 2, 90, 91],
        )

    def test_constrained_beam_returns_ten_valid_sids(self) -> None:
        token_to_id = {
            **{f"<a_{index}>": index for index in range(1, 3)},
            **{f"<b_{index}>": 10 + index for index in range(1, 4)},
            **{f"<c_{index}>": 20 + index for index in range(1, 3)},
        }
        id_to_token = {token_id: token for token, token_id in token_to_id.items()}

        class FakeTokenizer:
            eos_token_id = 0

            def encode(self, text, add_special_tokens=False):
                del add_special_tokens
                if text == "</think>":
                    return [90]
                if text == "</think>\n\n":
                    return [90, 91]
                if "</think>" in text:
                    return [97, 90, 1]
                sid_tokens = re.findall(r"<[abc]_\d+>", text)
                if sid_tokens and "".join(sid_tokens) == text:
                    return [token_to_id[token] for token in sid_tokens]
                return [99]

            def decode(self, token_ids, skip_special_tokens=False):
                del skip_special_tokens
                return "".join(id_to_token[token_id] for token_id in token_ids)

            def apply_chat_template(self, messages, add_generation_prompt, tokenize):
                del messages, add_generation_prompt, tokenize
                return [98]

        class FakeCompletions:
            def create(self, **kwargs):
                allowed = kwargs["extra_body"]["allowed_token_ids"]
                top_logprobs = {
                    id_to_token[token_id]: -float(token_id) / 100
                    for token_id in allowed
                }
                logprobs = SimpleNamespace(top_logprobs=[top_logprobs])
                return SimpleNamespace(
                    choices=[SimpleNamespace(logprobs=logprobs)]
                )

        tokenizer = FakeTokenizer()
        catalog_sids = [
            f"<a_{a}><b_{b}><c_{c}>"
            for a in range(1, 3)
            for b in range(1, 4)
            for c in range(1, 3)
        ]
        trie = build_sid_token_trie(tokenizer, catalog_sids)
        endpoint = ModelEndpoint.__new__(ModelEndpoint)
        endpoint.model = "sidreasoner"
        endpoint.client = SimpleNamespace(completions=FakeCompletions())
        beams = endpoint.constrained_sid_beam(
            build_messages([catalog_sids[0], catalog_sids[1]]),
            [97, 90, 1],
            tokenizer,
            trie,
            beam_width=10,
        )
        self.assertEqual(len(beams), 10)
        self.assertEqual(len(set(beams)), 10)
        self.assertTrue(set(beams) <= set(catalog_sids))


if __name__ == "__main__":
    unittest.main()