from __future__ import annotations

import argparse
import ast
import difflib
import os
import random
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import gradio as gr
from openai import OpenAI


DEFAULT_CHECKPOINT_REPO = "yufan/recsys-genrec-checkpoints-final"
DEFAULT_CHECKPOINT_SUBDIR = "Video_Games/stage3_interest_grounding_candidate1"
DEFAULT_CHECKPOINT_REVISION = "e50227d879aebe80a6054750536a3d505a8bea0d"
DEFAULT_DATASET = "yufan/recsys-genrec-dataset-final"
DEFAULT_CONFIG = "Video_Games_catalog"
MIN_HISTORY_ITEMS = 2
MAX_HISTORY_ITEMS = 5
SELECTOR_ITEMS_PER_FIRST_SID = 5
SID_BEAM_WIDTH = 10
EVAL_MAX_NEW_TOKENS = 1024
SID_DEPTH = 3
SYSTEM_PROMPT = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.
Can you recommend the next item for the user based on their interaction history?
"""
SID_PATTERN = re.compile(r"<a_\d+><b_\d+><c_\d+>")
SUMMARY_BLOCK_PATTERN = re.compile(
    r"<history_summary>\s*(.*?)\s*</history_summary>", re.DOTALL
)
INTEREST_BLOCK_PATTERN = re.compile(
    r"<future_interests>\s*(.*?)\s*</future_interests>", re.DOTALL
)
SUMMARY_LINE_PATTERN = re.compile(
    rf"^-\s+(?P<evidence>{SID_PATTERN.pattern}(?:\s*,\s*{SID_PATTERN.pattern})*)"
    r"\s*=>\s*(?P<text>\S.*)$"
)
INTEREST_LINE_PATTERN = re.compile(
    rf"^-\s+\[(?P<mode>exploit|explore)\]\s+"
    rf"(?P<evidence>{SID_PATTERN.pattern}(?:\s*,\s*{SID_PATTERN.pattern})*)"
    r"\s*=>\s*(?P<text>\S.*)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class CatalogItem:
    item_id: int
    sid: str
    title: str
    description: str
    brand: str
    detailed_description: str
    retrieval_summary: str


@dataclass(frozen=True)
class ParsedGeneration:
    raw_response: str
    reasoning: str
    summaries: list[dict[str, str]]
    interests: list[dict[str, str]]
    prediction_sid: str
    format_status: str


def _clean_text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _normalize_title(value: str) -> str:
    return " ".join(value.casefold().split())


def _strip_list_prefix(value: str) -> str:
    return re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", value).strip()


class GameCatalog:
    def __init__(
        self,
        items: list[CatalogItem],
        sid_popularity: dict[str, int] | None = None,
        test_histories: list[list[str]] | None = None,
    ) -> None:
        if not items:
            raise ValueError("Video Games catalog is empty")
        self.items = items
        self.sid_popularity = sid_popularity or {}
        self.test_histories = test_histories or []
        self.by_sid: dict[str, list[CatalogItem]] = {}
        self.by_title: dict[str, list[CatalogItem]] = {}
        for item in items:
            self.by_sid.setdefault(item.sid, []).append(item)
            self.by_title.setdefault(_normalize_title(item.title), []).append(item)
        self._normalized_titles = list(self.by_title)

    def selector_choices(
        self,
        max_per_first_sid: int = SELECTOR_ITEMS_PER_FIRST_SID,
    ) -> list[tuple[str, str]]:
        if max_per_first_sid < 1:
            raise ValueError("max_per_first_sid must be positive")

        grouped_sids: dict[str, list[str]] = {}
        for sid in self.by_sid:
            first_sid = sid[: sid.index(">") + 1]
            grouped_sids.setdefault(first_sid, []).append(sid)

        selected_sids = []
        for first_sid, group_sids in sorted(grouped_sids.items()):
            top_sids = sorted(
                group_sids,
                key=lambda sid: (
                    -self.sid_popularity.get(sid, 0),
                    self.by_sid[sid][0].title.casefold(),
                    sid,
                ),
            )[:max_per_first_sid]
            selected_sids.extend(top_sids)

        choices = []
        for sid in selected_sids:
            choices.append(self.selector_choice(sid))
        return sorted(choices, key=lambda choice: choice[0].casefold())

    def selector_choice(self, sid: str) -> tuple[str, str]:
        items = self.by_sid.get(sid, [])
        if not items:
            raise ValueError(f"SID is not in Video_Games_catalog: {sid}")
        titles = " | ".join(dict.fromkeys(item.title for item in items))
        collision = f" ({len(items)} catalog matches)" if len(items) > 1 else ""
        return f"{titles} — {sid}{collision}", sid

    @classmethod
    def from_hugging_face(
        cls,
        dataset: str = DEFAULT_DATASET,
        revision: str | None = None,
    ) -> "GameCatalog":
        from datasets import load_dataset

        catalog_split = load_dataset(
            dataset, DEFAULT_CONFIG, split="train", revision=revision
        )
        train_split = load_dataset(
            dataset, "Video_Games_seqrec", split="train", revision=revision
        )
        test_split = load_dataset(
            dataset, "Video_Games_seqrec", split="test", revision=revision
        )
        popularity = Counter()
        for row in train_split:
            history_value = row.get("history_item_sid")
            if isinstance(history_value, str):
                try:
                    history_value = ast.literal_eval(history_value)
                except (SyntaxError, ValueError):
                    pass
            popularity.update(SID_PATTERN.findall(str(history_value)))
            popularity.update(SID_PATTERN.findall(_clean_text(row.get("item_sid"))))

        items = [
            CatalogItem(
                item_id=int(row["item_id"]),
                sid=_clean_text(row["sid"]),
                title=_clean_text(row["title"]),
                description=_clean_text(row.get("description")),
                brand=_clean_text(row.get("brand")),
                detailed_description=_clean_text(row.get("detailed_description")),
                retrieval_summary=_clean_text(row.get("retrieval_summary")),
            )
            for row in catalog_split
        ]
        catalog_sids = {item.sid for item in items}
        test_histories = []
        for row in test_split:
            history = SID_PATTERN.findall(_clean_text(row.get("history_item_sid")))
            if len(history) >= MIN_HISTORY_ITEMS and all(
                sid in catalog_sids for sid in history
            ):
                test_histories.append(history[-MAX_HISTORY_ITEMS:])
        if not test_histories:
            raise ValueError("Video Games test split has no eligible real histories.")
        return cls(
            items,
            sid_popularity=dict(popularity),
            test_histories=test_histories,
        )

    def resolve_history(self, value: str) -> tuple[list[CatalogItem], list[str]]:
        raw_value = value.strip()
        if not raw_value:
            raise ValueError("Enter at least one history item.")

        sid_matches = SID_PATTERN.findall(raw_value)
        residue = SID_PATTERN.sub("", raw_value)
        if sid_matches and not residue.replace(",", "").strip():
            entries = sid_matches
        else:
            entries = [
                _strip_list_prefix(line)
                for line in raw_value.splitlines()
                if _strip_list_prefix(line)
            ]
        if not entries:
            raise ValueError("No history items could be parsed.")
        if len(entries) > 50:
            raise ValueError("Use at most 50 history items.")

        resolved = []
        notes = []
        for position, entry in enumerate(entries, start=1):
            sid_match = SID_PATTERN.fullmatch(entry)
            if sid_match:
                matching_items = self.by_sid.get(sid_match.group(0), [])
                if not matching_items:
                    raise ValueError(
                        f"History item {position} is not in Video_Games_catalog: {entry}"
                    )
                resolved.append(matching_items[0])
                note = "exact SID"
                if len(matching_items) > 1:
                    note += f" ({len(matching_items)} catalog matches)"
                notes.append(note)
                continue

            normalized = _normalize_title(entry.strip('"\''))
            exact_items = self.by_title.get(normalized, [])
            if len(exact_items) == 1:
                resolved.append(exact_items[0])
                notes.append("exact title")
                continue
            if len(exact_items) > 1:
                raise ValueError(
                    f"History title {position} is ambiguous; enter its SID: {entry}"
                )

            matches = difflib.get_close_matches(
                normalized, self._normalized_titles, n=1, cutoff=0.72
            )
            if not matches:
                raise ValueError(
                    f"History title {position} was not found in the catalog: {entry}"
                )
            best_items = self.by_title[matches[0]]
            if len(best_items) != 1:
                raise ValueError(
                    f"History title {position} has an ambiguous fuzzy match; enter a SID."
                )
            score = difflib.SequenceMatcher(None, normalized, matches[0]).ratio()
            resolved.append(best_items[0])
            notes.append(f"fuzzy title ({score:.0%})")
        return resolved, notes


def normalize_openai_base_url(endpoint: str) -> str:
    base_url = endpoint.strip().rstrip("/")
    if not base_url:
        raise ValueError("The model endpoint is empty.")
    for suffix in ("/chat/completions", "/completions"):
        if base_url.endswith(suffix):
            base_url = base_url[: -len(suffix)]
    if not base_url.endswith("/v1"):
        base_url += "/v1"
    return base_url


def build_messages(history_sids: list[str]) -> list[dict[str, str]]:
    history = ", ".join(history_sids)
    user_prompt = (
        f"The user has sequentially interacted with items {history}. "
        "Can you recommend the next item for him? Let's think step by step before "
        "making recommendation. Directly output the item SID after thinking."
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


class ModelEndpoint:
    def __init__(
        self, endpoint: str, model: str, api_key: str, timeout: float
    ) -> None:
        self.base_url = normalize_openai_base_url(endpoint)
        self.model = model.strip()
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=api_key or "EMPTY",
            timeout=timeout,
        )

    def resolve_model(self) -> str:
        if self.model:
            return self.model
        models = self.client.models.list().data
        if not models:
            raise RuntimeError("The endpoint returned no served models.")
        return models[0].id

    def generate(
        self,
        messages: list[dict[str, str]],
        max_tokens: int,
    ) -> list[int]:
        response = self.client.chat.completions.create(
            model=self.resolve_model(),
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.0,
            top_p=1.0,
            seed=42,
            n=1,
            extra_body={
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
        if not response.choices:
            raise RuntimeError("The endpoint returned no completion choices.")
        token_ids = getattr(response.choices[0], "token_ids", None)
        if not token_ids:
            raise RuntimeError(
                "Endpoint returned no token_ids; vLLM 0.10.2+ with "
                "return_token_ids support is required."
            )
        return list(token_ids)

    def constrained_sid_beam(
        self,
        messages: list[dict[str, str]],
        response_ids: list[int],
        tokenizer: Any,
        sid_token_trie: dict[tuple[int, ...], list[int]],
        beam_width: int = SID_BEAM_WIDTH,
    ) -> list[str]:
        prompt_ids = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
        )
        end_think_marker = tokenizer.encode("</think>", add_special_tokens=False)
        reasoning_separator = tokenizer.encode("</think>\n\n", add_special_tokens=False)
        reasoning_ids = prepare_reasoning_prefix(
            response_ids,
            end_think_marker=end_think_marker,
            reasoning_separator=reasoning_separator,
            eos_token_id=tokenizer.eos_token_id,
            max_length=EVAL_MAX_NEW_TOKENS - SID_DEPTH - 1,
        )
        base_prompt_ids = list(prompt_ids) + reasoning_ids

        beams: list[tuple[list[int], float]] = [([], 0.0)]
        for _ in range(SID_DEPTH):
            candidates: list[tuple[list[int], float]] = []
            for prefix, cumulative_logprob in beams:
                allowed = sid_token_trie.get(tuple(prefix), [])
                if not allowed:
                    raise RuntimeError(f"No valid SID continuation for prefix {prefix}.")
                response = self.client.completions.create(
                    model=self.resolve_model(),
                    prompt=base_prompt_ids + prefix,
                    max_tokens=1,
                    temperature=0.0,
                    top_p=1.0,
                    seed=42,
                    logprobs=min(beam_width, len(allowed)),
                    extra_body={
                        "allowed_token_ids": allowed,
                        "top_k": -1,
                        "min_p": 0.0,
                        "repetition_penalty": 1.0,
                        "add_special_tokens": False,
                        "return_tokens_as_token_ids": True,
                    },
                )
                if not response.choices or response.choices[0].logprobs is None:
                    raise RuntimeError("Endpoint did not return SID token logprobs.")
                top_logprobs = response.choices[0].logprobs.top_logprobs
                if not top_logprobs or top_logprobs[0] is None:
                    raise RuntimeError("Endpoint returned no constrained top logprobs.")

                allowed_by_text = {
                    tokenizer.decode([token_id], skip_special_tokens=False): token_id
                    for token_id in allowed
                }
                for token_text, token_logprob in top_logprobs[0].items():
                    token_id = None
                    if token_text.startswith("token_id:"):
                        try:
                            candidate_token_id = int(token_text.removeprefix("token_id:"))
                        except ValueError:
                            candidate_token_id = -1
                        if candidate_token_id in allowed:
                            token_id = candidate_token_id
                    if token_id is None:
                        token_id = allowed_by_text.get(token_text)
                    if token_id is None:
                        encoded = tokenizer.encode(token_text, add_special_tokens=False)
                        if len(encoded) == 1 and encoded[0] in allowed:
                            token_id = encoded[0]
                    if token_id is not None:
                        candidates.append(
                            (prefix + [token_id], cumulative_logprob + token_logprob)
                        )
            if not candidates:
                raise RuntimeError("Constrained SID beam search produced no candidates.")
            beams = sorted(candidates, key=lambda beam: beam[1], reverse=True)[:beam_width]

        return [
            tokenizer.decode(token_ids, skip_special_tokens=False)
            for token_ids, _ in beams
        ]


def _nonempty_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def prepare_reasoning_prefix(
    tokens: list[int],
    end_think_marker: list[int],
    reasoning_separator: list[int],
    eos_token_id: int,
    max_length: int,
) -> list[int]:
    marker_length = len(end_think_marker)
    for start in range(len(tokens) - marker_length + 1):
        if tokens[start : start + marker_length] == end_think_marker:
            reasoning = tokens[: start + marker_length]
            break
    else:
        reasoning = list(tokens)
        while reasoning and reasoning[-1] == eos_token_id:
            reasoning.pop()
        reasoning = reasoning[: max_length - len(reasoning_separator)]
        if not reasoning:
            raise RuntimeError("Reasoning rollout ended before producing any token.")
        return reasoning + reasoning_separator

    separator_suffix = reasoning_separator[marker_length:]
    normalized = reasoning + separator_suffix
    if len(normalized) > max_length:
        raise ValueError("Sampled reasoning leaves no room for constrained SID decoding.")
    return normalized


def load_default_tokenizer() -> Any:
    from huggingface_hub import snapshot_download
    from transformers import AutoTokenizer

    tokenizer_files = (
        "added_tokens.json",
        "chat_template.jinja",
        "merges.txt",
        "special_tokens_map.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "vocab.json",
    )
    snapshot_path = snapshot_download(
        repo_id=DEFAULT_CHECKPOINT_REPO,
        repo_type="dataset",
        revision=DEFAULT_CHECKPOINT_REVISION,
        allow_patterns=[f"{DEFAULT_CHECKPOINT_SUBDIR}/{name}" for name in tokenizer_files],
    )
    return AutoTokenizer.from_pretrained(
        Path(snapshot_path) / DEFAULT_CHECKPOINT_SUBDIR
    )


def build_sid_token_trie(
    tokenizer: Any,
    catalog_sids: Any,
) -> dict[tuple[int, ...], list[int]]:
    trie: dict[tuple[int, ...], set[int]] = {}
    for sid in catalog_sids:
        sid_tokens = re.findall(r"<[abc]_\d+>", sid)
        if len(sid_tokens) != 3:
            raise ValueError(f"Catalog SID does not have three tokens: {sid}")
        token_ids = tokenizer.encode(sid, add_special_tokens=False)
        if len(token_ids) != 3:
            raise ValueError(f"Catalog SID is not atomic in the tokenizer: {sid}")
        for position, token_id in enumerate(token_ids):
            trie.setdefault(tuple(token_ids[:position]), set()).add(token_id)
    return {prefix: sorted(token_ids) for prefix, token_ids in trie.items()}


def parse_generation(raw_response: str) -> ParsedGeneration:
    raw = raw_response.strip()
    think_match = re.search(r"<think>\s*(.*?)\s*</think>", raw, re.DOTALL)
    if think_match:
        reasoning = think_match.group(1).strip()
        answer = raw[think_match.end() :].strip()
    elif "</think>" in raw:
        reasoning, answer = raw.split("</think>", maxsplit=1)
        reasoning = reasoning.removeprefix("<think>").strip()
        answer = answer.strip()
    else:
        reasoning = raw
        answer = raw

    summary_match = SUMMARY_BLOCK_PATTERN.search(reasoning)
    interest_match = INTEREST_BLOCK_PATTERN.search(reasoning)
    summaries = []
    interests = []
    malformed_lines = 0
    if summary_match:
        for line in _nonempty_lines(summary_match.group(1)):
            parsed_line = SUMMARY_LINE_PATTERN.fullmatch(line)
            if parsed_line is None:
                malformed_lines += 1
                summaries.append({"evidence": "", "summary": line})
            else:
                summaries.append(
                    {
                        "evidence": parsed_line.group("evidence"),
                        "summary": parsed_line.group("text"),
                    }
                )
    if interest_match:
        for line in _nonempty_lines(interest_match.group(1)):
            parsed_line = INTEREST_LINE_PATTERN.fullmatch(line)
            if parsed_line is None:
                malformed_lines += 1
                interests.append({"mode": "", "evidence": "", "interest": line})
            else:
                interests.append(
                    {
                        "mode": parsed_line.group("mode").casefold(),
                        "evidence": parsed_line.group("evidence"),
                        "interest": parsed_line.group("text"),
                    }
                )

    answer_sids = SID_PATTERN.findall(answer)
    all_sids = SID_PATTERN.findall(raw)
    prediction_sid = answer_sids[0] if answer_sids else (all_sids[-1] if all_sids else "")
    issues = []
    if summary_match is None:
        issues.append("missing history_summary")
    if interest_match is None:
        issues.append("missing future_interests")
    if malformed_lines:
        issues.append(f"{malformed_lines} malformed reasoning line(s)")
    if not prediction_sid:
        issues.append("missing prediction SID")
    labels = {row["mode"] for row in interests}
    if interests and labels != {"exploit", "explore"}:
        issues.append("interest modes must include exploit and explore")

    return ParsedGeneration(
        raw_response=raw,
        reasoning=reasoning,
        summaries=summaries,
        interests=interests,
        prediction_sid=prediction_sid,
        format_status="Valid structured output" if not issues else "; ".join(issues),
    )


def _history_table(
    catalog: GameCatalog,
    items: list[CatalogItem],
) -> list[list[str | int]]:
    rows = []
    for position, item in enumerate(items, start=1):
        matches = catalog.by_sid[item.sid]
        rows.append(
            [
                position,
                item.sid,
                " | ".join(match.title for match in matches),
                " | ".join(dict.fromkeys(match.brand for match in matches if match.brand)),
            ]
        )
    return rows


def validate_history_selections(values: list[str | None]) -> list[str]:
    if len(values) > MAX_HISTORY_ITEMS:
        raise ValueError(f"Select at most {MAX_HISTORY_ITEMS} history items.")
    normalized = [str(value).strip() if value else "" for value in values]
    normalized.extend([""] * (MAX_HISTORY_ITEMS - len(normalized)))
    if any(not value for value in normalized[:MIN_HISTORY_ITEMS]):
        raise ValueError(f"The first {MIN_HISTORY_ITEMS} history items are required.")
    first_empty = next(
        (index for index, value in enumerate(normalized) if not value),
        len(normalized),
    )
    if any(normalized[first_empty + 1 :]):
        raise ValueError("History items must be selected without empty positions.")
    selected_sids = normalized[:first_empty]
    if not MIN_HISTORY_ITEMS <= len(selected_sids) <= MAX_HISTORY_ITEMS:
        raise ValueError(
            f"Select between {MIN_HISTORY_ITEMS} and {MAX_HISTORY_ITEMS} history items."
        )
    return selected_sids


def sample_test_history(
    test_histories: list[list[str]],
    rng: random.Random | random.SystemRandom | None = None,
) -> list[str]:
    if not test_histories:
        raise ValueError("No eligible test histories are available.")
    randomizer = rng or random.SystemRandom()
    history = list(randomizer.choice(test_histories))
    if not MIN_HISTORY_ITEMS <= len(history) <= MAX_HISTORY_ITEMS:
        raise ValueError("Stored test history must contain 2-5 items.")
    return history


def build_demo(
    catalog: GameCatalog,
    endpoint: ModelEndpoint,
    tokenizer: Any | None = None,
) -> gr.Blocks:
    selector_choices = catalog.selector_choices(
        max_per_first_sid=SELECTOR_ITEMS_PER_FIRST_SID
    )
    sid_token_trie = (
        build_sid_token_trie(tokenizer, catalog.by_sid)
        if tokenizer is not None
        else None
    )

    def recommend(
        *inputs: Any,
    ) -> tuple[Any, ...]:
        selection_values = list(inputs[:MAX_HISTORY_ITEMS])
        try:
            if tokenizer is None or sid_token_trie is None:
                raise RuntimeError("Checkpoint tokenizer is not loaded for SID beam search.")
            selected_sids = validate_history_selections(selection_values)
            history_items, _ = catalog.resolve_history("\n".join(selected_sids))
            messages = build_messages(selected_sids)
            reasoning_separator = tokenizer.encode(
                "</think>\n\n", add_special_tokens=False
            )
            max_reasoning_tokens = (
                EVAL_MAX_NEW_TOKENS
                - len(reasoning_separator)
                - SID_DEPTH
                - 1
            )
            response_ids = endpoint.generate(
                messages,
                max_tokens=max_reasoning_tokens,
            )
            raw_response = tokenizer.decode(
                response_ids,
                skip_special_tokens=False,
            )
            parsed = parse_generation(raw_response)
            prediction_sids = endpoint.constrained_sid_beam(
                messages,
                response_ids,
                tokenizer,
                sid_token_trie,
                beam_width=SID_BEAM_WIDTH,
            )
        except Exception as error:
            raise gr.Error(str(error)) from error

        prediction_rows = []
        for sid in prediction_sids:
            matching_items = catalog.by_sid.get(sid, [])
            if not matching_items:
                raise RuntimeError(f"Beam returned an out-of-catalog SID: {sid}")
            titles = " | ".join(dict.fromkeys(item.title for item in matching_items))
            prediction_rows.append([sid, titles])
        return (
            _history_table(catalog, history_items),
            [[row["evidence"], row["summary"]] for row in parsed.summaries],
            [
                [row["mode"], row["evidence"], row["interest"]]
                for row in parsed.interests
            ],
            parsed.reasoning,
            prediction_rows,
        )

    def randomize_history() -> tuple[Any, ...]:
        history = sample_test_history(catalog.test_histories)
        return tuple(
            gr.update(
                choices=(
                    [catalog.selector_choice(history[index])]
                    + [choice for choice in selector_choices if choice[1] != history[index]]
                    if index < len(history)
                    else selector_choices
                ),
                value=history[index] if index < len(history) else None,
                visible=index < len(history),
            )
            for index in range(MAX_HISTORY_ITEMS)
        ) + (len(history),)
    css = """
    :root, body, .gradio-container,
    .gradio-container input, .gradio-container textarea,
    .gradio-container button, .gradio-container select,
    [role="listbox"], [role="option"] {
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif !important;
        letter-spacing: 0 !important;
    }
    .gradio-container { max-width: 1440px !important; }
    .endpoint-note { color: var(--body-text-color-subdued); font-size: 0.9rem; }
    .reasoning-table td, .reasoning-table th,
    .reasoning-table .handsontable td, .reasoning-table .handsontable th {
        white-space: normal !important;
        overflow-wrap: anywhere !important;
        word-break: normal !important;
        line-height: 1.5 !important;
        vertical-align: top !important;
    }
    .summary-reasoning-table { min-height: 320px; }
    .interest-reasoning-table { min-height: 420px; }
    """
    with gr.Blocks(
        title="SIDReasoner Video Games Demo",
        theme=gr.themes.Soft(primary_hue="orange", neutral_hue="gray"),
        css=css,
    ) as demo:
        gr.Markdown("# SIDReasoner · Video Games")
        gr.Markdown(
            "Build a chronological history by searching the fixed Video Games catalog. "
            "The dice draws a real test-set click history (2–5 most recent items, "
            "oldest first). Manual choices use each first-level SID group's "
            f"{SELECTOR_ITEMS_PER_FIRST_SID} most popular training items."
        )
        gr.Markdown(
            f"Endpoint: `{endpoint.base_url}` · Default checkpoint: "
            f"`{DEFAULT_CHECKPOINT_REPO}/{DEFAULT_CHECKPOINT_SUBDIR}` · Catalog: "
            f"`{DEFAULT_DATASET}` / `{DEFAULT_CONFIG}` ({len(catalog.items):,} items)",
            elem_classes=["endpoint-note"],
        )

        visible_count = gr.State(MIN_HISTORY_ITEMS)
        with gr.Row():
            with gr.Column():
                history_selectors = []
                for index in range(MAX_HISTORY_ITEMS):
                    history_selectors.append(
                        gr.Dropdown(
                            choices=selector_choices,
                            value=None,
                            label=f"{index + 1}. History item",
                            info=(
                                "Required"
                                if index < MIN_HISTORY_ITEMS
                                else "Optional"
                            ),
                            filterable=True,
                            interactive=True,
                            visible=index < MIN_HISTORY_ITEMS,
                        )
                    )
                with gr.Row():
                    randomize_button = gr.Button("🎲 Random history", variant="primary")
                    submit = gr.Button("Run recommendation", variant="primary")

        selector_outputs = [*history_selectors, visible_count]
        demo.load(fn=randomize_history, outputs=selector_outputs)
        randomize_button.click(
            fn=randomize_history,
            outputs=selector_outputs,
        )

        gr.Markdown("## Resolved history")
        history_table = gr.Dataframe(
            headers=["#", "SID", "Title", "Brand"],
            datatype=["number", "str", "str", "str"],
            interactive=False,
        )

        gr.Markdown("## Structured reasoning")
        summary_table = gr.Dataframe(
            headers=["Evidence SID(s)", "History summary"],
            datatype=["str", "str"],
            label="History summary",
            wrap=True,
            line_breaks=True,
            column_widths=["28%", "72%"],
            elem_classes=["reasoning-table", "summary-reasoning-table"],
            interactive=False,
        )
        interest_table = gr.Dataframe(
            headers=["Mode", "Evidence SID(s)", "Interest prediction"],
            datatype=["str", "str", "str"],
            label="Future interests",
            wrap=True,
            line_breaks=True,
            column_widths=["12%", "25%", "63%"],
            elem_classes=["reasoning-table", "interest-reasoning-table"],
            interactive=False,
        )
        with gr.Accordion("Raw reasoning", open=False):
            reasoning_text = gr.Textbox(label="Reasoning", lines=14, interactive=False)

        gr.Markdown("## Final prediction")
        prediction_table = gr.Dataframe(
            headers=["SID", "Title"],
            datatype=["str", "str"],
            label="Beam Top-10",
            wrap=True,
            line_breaks=True,
            column_widths=["32%", "68%"],
            interactive=False,
        )

        submit.click(
            fn=recommend,
            inputs=history_selectors,
            outputs=[
                history_table,
                summary_table,
                interest_table,
                reasoning_text,
                prediction_table,
            ],
            api_name="recommend",
        )
    return demo


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Serve the SIDReasoner Video Games endpoint demo with Gradio."
    )
    parser.add_argument(
        "--endpoint",
        default=os.environ.get("SIDR_DEMO_ENDPOINT", "http://127.0.0.1:8000/v1"),
        help="OpenAI-compatible vLLM/SGLang base URL.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("SIDR_DEMO_MODEL", "sidreasoner"),
        help="Served model name.",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("SIDR_DEMO_API_KEY", ""),
        help="Endpoint API key. Prefer the environment variable.",
    )
    parser.add_argument("--timeout", type=float, default=600.0)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--dataset-revision", default=None)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument(
        "--share", action=argparse.BooleanOptionalAction, default=True
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    catalog = GameCatalog.from_hugging_face(
        dataset=args.dataset, revision=args.dataset_revision
    )
    endpoint = ModelEndpoint(
        endpoint=args.endpoint,
        model=args.model,
        api_key=args.api_key,
        timeout=args.timeout,
    )
    tokenizer = load_default_tokenizer()
    build_demo(catalog, endpoint, tokenizer).queue(default_concurrency_limit=4).launch(
        server_name=args.host,
        server_port=args.port,
        share=args.share,
        show_error=True,
    )


if __name__ == "__main__":
    main()