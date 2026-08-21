"""Generate interest-aligned GPT-5.4 summaries for supported catalog domains.

The source dataset is intentionally fixed to:
https://huggingface.co/datasets/yufan/recsys-genrec-dataset-final/viewer/Video_Games_catalog

Every output row preserves all source catalog fields except that it sets or
replaces ``retrieval_summary`` with the newly generated value. Results are
appended immediately and can be resumed by rerunning the same command.

Example:

    python data_curation/gpt5_generate_catalog_retrieval_summaries.py

    python data_curation/gpt5_generate_catalog_retrieval_summaries.py \
        --limit 3 \
        --output ~/Downloads/Video_Games_catalog_retrieval_summary_smoke.jsonl
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import multiprocessing as mp
import os
import queue
import random
import re
import time
from pathlib import Path
from typing import Any


HF_REPO = "yufan/recsys-genrec-dataset-final"
HF_SPLIT = "train"
HF_REVISION = "main"
MODEL = "gpt-5.4"
DEFAULT_DOMAINS = ("Video_Games",)
SUPPORTED_DOMAINS = (
    "Video_Games",
    "Office_Products",
    "Industrial_and_Scientific",
)
DOMAIN_DISPLAY_NAMES = {
    "Video_Games": "Video Games",
    "Office_Products": "Office Products",
    "Industrial_and_Scientific": "Industrial and Scientific",
}
DOMAIN_RETRIEVAL_GUIDANCE = {
    "Office_Products": """OFFICE PRODUCTS RETRIEVAL DIMENSIONS
1. Open with the exact title and precise product type, such as printer supply, writing instrument, paper product, filing system, desk organizer, presentation supply, office furniture, mailing supply, calculator, label, binder, or machine accessory.
2. State the primary office workflow or task: printing, scanning, writing, correcting, labeling, filing, archiving, shipping, presenting, scheduling, organizing, cleaning, securing, or ergonomic workstation use.
3. Preserve hard compatibility constraints such as printer or device family, paper size, sheet or label format, mounting interface, refill system, electrical standard, and supported media.
4. Include concrete differentiators supported by the source: dimensions, capacity, quantity, yield, color, tip or point size, material, finish, closure or binding style, adjustability, portability, and included components.
5. Explain two to four functional features in connected prose and close with the strongest distinction from similar office products.""",
    "Industrial_and_Scientific": """INDUSTRIAL AND SCIENTIFIC RETRIEVAL DIMENSIONS
1. Open with the exact title and precise product class, such as tool, fastener, fitting, sensor, test instrument, lab supply, safety product, electrical component, pneumatic or hydraulic part, material-handling component, maintenance supply, or process consumable.
2. State the primary industrial, laboratory, maintenance, manufacturing, construction, measurement, repair, or safety application.
3. Preserve hard technical constraints and compatibility: dimensions, thread or connector type, voltage, pressure, temperature or measurement range, capacity, tolerance, material, standards, equipment family, and installation method when supported.
4. Include operating mechanism, form factor, durability or environmental properties, package quantity, included components, and the concrete workflow benefit without inventing performance claims.
5. Close with the strongest source-supported discriminator from nearby components or supplies, especially specification, material grade, fit, range, or intended process.""",
}
DEFAULT_OUTPUT_DIR = "~/Downloads"
DEFAULT_PER_ENDPOINT = 4
DEFAULT_REASONING_EFFORT = "low"
DEFAULT_FAILURE_RETRY_ROUNDS = 3
INTEREST_ANALYSIS_SOURCE = "yufan_reasoning_with_user_interest.jsonl"
INTEREST_ANALYSIS_SAMPLE_SIZE = 200
INTEREST_ANALYSIS_SAMPLE_SEED = 20260818
INTEREST_ANALYSIS_LABEL_COUNTS = {"exploit": 100, "explore": 100}
MAX_COMPLETION_TOKENS = 2600
MAX_API_ATTEMPTS = 4
MAX_RAW_DESCRIPTION_CHARS = 5000
MAX_DETAILED_DESCRIPTION_CHARS = 3000
LOG_EVERY_SECONDS = 10
CONTENT_FILTER_SANITIZER_VERSION = "video_games_mature_content_v1"
SUMMARY_LENGTH_PROFILES = {
    "sparse": (45, 85),
    "normal": (110, 160),
    "rich": (140, 190),
}
FORBIDDEN_SUMMARY_PHRASES = (
    "source metadata",
    "source text",
    "this prompt",
    "semantic retrieval",
    "embedding",
)
SOURCE_QUALITY_OVERRIDES = {
    3460: {
        "title": "Silent Hill: Book of Memories - PlayStation Vita",
        "excluded_fields": ["description", "detailed_description"],
        "reason": (
            "Both description fields describe Silent Hill HD Collection, "
            "Silent Hill 2, and Silent Hill 3 rather than the titled product."
        ),
    }
}

SYSTEM_PROMPT = """You write one factual product summary for dense semantic retrieval against natural-language future user interests in the {domain_name} domain.

The summary design below comes from an analysis of 200 distinct future-interest queries (100 exploit and 100 explore). Those queries most often describe products through exact platform or device compatibility, product type, fine-grained genre, play mode, core mechanics, setting or franchise, progression structure, control modality, and concrete accessory use case. Write the summary so that supported concepts from those dimensions co-occur naturally, while retaining details that distinguish this item from near-neighbor products.

FIRST IDENTIFY THE PRODUCT PATH
- GAME OR GAME CONTENT: a base game, remaster, compilation, DLC, expansion, season pass, digital code, or special edition.
- HARDWARE, ACCESSORY, SERVICE, OR COLLECTIBLE: a console, handheld, controller, camera, mount, charger, cable, adapter, storage device, headset, keyboard, mouse, protective case, guide, figure, membership, gift card, bundle, or other non-game item.

FOR A GAME OR GAME CONTENT
1. Open with the exact title, precise product format, and explicitly supported platform. Say whether it is a base game, DLC, expansion, compilation, remaster, digital release, bundle, or special edition when known.
2. Name the most specific supported genre or subgenre, not merely "action" or "adventure." Natural retrieval vocabulary includes action RPG, JRPG, open-world action-adventure, first- or third-person shooter, survival horror, fighting game, platformer, racing simulation, strategy game, rhythm game, party game, and life or management simulation.
3. State known play modes and player topology: single-player campaign, local multiplayer, split-screen, online competitive multiplayer, co-op, team-based play, party play, or voice-chat-oriented play.
4. Describe two to four defining mechanics or core-loop elements in connected prose. Examples include exploration, mission progression, real-time or turn-based combat, stealth, hacking, traversal, environmental puzzles, dungeon progression, crafting, building, survival, resource management, creature collection and training, vehicle handling, combo execution, motion control, VR, or stylus and touch interaction.
5. Include supported progression or campaign shape, such as character growth, upgrades, skill or class systems, branching choices, faction consequences, gear progression, settlement development, narrative relationships, or stage-based progression.
6. Include salient setting, tone, licensed universe, or franchise when supported: science fiction, fantasy, dark fantasy, horror, post-apocalyptic, military, historical, anime, superhero, family-friendly, retro, or a named series.
7. Close with the strongest item-specific discriminator, such as perspective, unusual mechanic, edition contents, bundled DLC, remastered titles, playable roster, distinctive protagonist, exact era, or platform-specific feature.

FOR HARDWARE, ACCESSORIES, SERVICES, OR COLLECTIBLES
1. Open with the exact title, precise product type, and every explicitly supported console, controller, operating system, or device family. Compatibility is a hard constraint.
2. State the concrete primary function and play context, not the generic phrase "gaming accessory." Examples include controller charging, console power, save storage, wireless controller connectivity, voice chat, gameplay capture, motion tracking, precision aiming, programmable input, macro control, display mounting, carrying and scratch protection, media navigation, or online multiplayer access.
3. Describe the supported controls, capabilities, connection type, form factor, included components, and concrete benefit in natural prose.
4. Preserve ecosystem relationships: membership entitlements, prepaid duration or balance, DLC role, toys-to-life or amiibo linkage, included figures or games, bundle contents, and exact edition.
5. Close with the strongest discriminator from similar products, such as capacity, cable length, wireless versus wired operation, button layout, colorway, material, mounting method, model generation, or exact compatibility exclusions.

WRITING AND GROUNDING RULES
- Write exactly one coherent paragraph within the item-specific TARGET LENGTH supplied in the user message. The target is shorter for sparse evidence and longer only when the source supports complementary semantic facets.
- Use available length to cover complementary evidence: exact identity and constraints, core gameplay or function, modes, mechanics, progression, setting or franchise, and item-specific distinctions.
- Stop as soon as all supported retrieval-relevant facts have been covered. Every sentence must add a new semantic facet or a concrete discriminator. Never repeat, paraphrase, or summarize an earlier claim merely to reach the target length.
- Use precise canonical domain terms and close paraphrases that a user might put in an interest query, but integrate them into grammatical sentences with meaningful co-occurrence. This is dense embedding retrieval, not literal keyword matching.
- Repeat a platform, product type, or defining genre once when needed for clarity, but do not pad the paragraph with synonyms.
- Preserve hard constraints before soft facets. Platform, compatibility, product type, and content format must never be blurred by broader semantic similarity.
- Use only facts directly stated or unambiguously supported by SOURCE METADATA. You may normalize a described feature into a standard domain term only when the mapping is clear; otherwise omit it. Never import outside product knowledge.
- Treat the original description list as the primary factual source. Use the detailed description as supplemental context for explicit genre, mechanics, modes, functions, and distinguishing attributes. If they conflict, follow the title and original descriptions.
- Do not copy the detailed description's headings, numbered structure, audience targeting, keyword lists, SEO language, or marketing conclusions into the summary.
- Prefer gameplay loops, progression, modes, functions, and exact compatibility over plot synopsis, generic audience claims, cosmetic packaging, or marketing language.
- Distinguish games, consoles, controllers, cameras, mounts, chargers, guides, cases, cables, storage, subscriptions, DLC, and figures precisely.
- Do not write headings, sections, bullets, field labels, tag lists, comma-separated keyword strings, or SEO copy.
- Do not recommend the item, address the reader, or discuss purchasing.
- Do not add target-audience, collector, import-shopping, shipping, delivery, or generic use-case language merely to make the paragraph longer. Mention import status, physical condition, or shipping only when it is among the few concrete facts that distinguish a sparse listing, and state it once.
- Do not use empty praise such as "immersive," "exciting," "innovative," "high quality," "ideal for gamers," "perfect choice," "enhances gameplay," or "hours of fun" unless the word is part of a factual quoted title.
- Do not mention semantic IDs, item IDs, retrieval, embeddings, metadata, source text, query analysis, or this prompt.
- Output only the summary paragraph."""

NON_GAME_SYSTEM_PROMPT = """You write one factual product summary for dense semantic retrieval against natural-language future user interests in the {domain_name} domain.

The summary must make supported product identity, use case, compatibility, technical constraints, functional features, and differentiators co-occur naturally. It is optimized for matching concise future-interest descriptions while keeping hard constraints more important than broad semantic similarity.

{domain_guidance}

WRITING AND GROUNDING RULES
- Write exactly one coherent paragraph within the item-specific TARGET LENGTH supplied in the user message. Use the available length only for complementary, source-supported semantic facets.
- Stop as soon as the supported retrieval-relevant facts have been covered. Every sentence must add a new semantic facet or concrete discriminator; never repeat facts to reach the target length.
- Use precise canonical domain terms and close paraphrases a user might put in an interest query, but write grammatical prose rather than a keyword list.
- Preserve hard constraints before soft facets. Product type, compatibility, dimensions, specifications, material, quantity, and operating range must never be blurred by broader similarity.
- Use only facts directly stated or unambiguously supported by SOURCE METADATA. Normalize a feature into a standard domain term only when the mapping is clear; otherwise omit it. Never import outside product knowledge.
- Treat the original description list as the primary factual source. Use the detailed description as supplemental context. If they conflict, follow the title and original descriptions.
- Do not copy headings, numbered structure, audience targeting, keyword lists, SEO language, or marketing conclusions from the detailed description.
- Do not write headings, sections, bullets, field labels, tag lists, comma-separated keyword strings, or SEO copy.
- Do not recommend the item, address the reader, discuss purchasing, or add unsupported target-audience language.
- Do not use empty praise such as "innovative," "high quality," "ideal," "perfect choice," or "enhances productivity" unless it is part of a factual quoted title.
- Do not mention semantic IDs, item IDs, retrieval, embeddings, metadata, source text, query analysis, or this prompt.
- Output only the summary paragraph."""

USER_TEMPLATE = """SOURCE METADATA

Title: {title}
Brand: {brand}
Original descriptions: {description}
Detailed description: {detailed_description}

TARGET LENGTH: {min_words}-{max_words} words ({length_profile} source evidence). Do not exceed this range, and do not repeat facts to fill it.

Write only the compact retrieval summary."""


def config_for_domain(domain: str) -> str:
    if domain not in SUPPORTED_DOMAINS:
        raise ValueError(f"unsupported catalog domain: {domain}")
    return f"{domain}_catalog"


def system_prompt_for_domain(domain: str) -> str:
    try:
        domain_name = DOMAIN_DISPLAY_NAMES[domain]
    except KeyError as error:
        raise ValueError(f"unsupported catalog domain: {domain}") from error
    if domain == "Video_Games":
        return SYSTEM_PROMPT.format(domain_name=domain_name)
    return NON_GAME_SYSTEM_PROMPT.format(
        domain_name=domain_name,
        domain_guidance=DOMAIN_RETRIEVAL_GUIDANCE[domain],
    )


def default_output_for_domain(domain: str, output_dir: str = DEFAULT_OUTPUT_DIR) -> str:
    config = config_for_domain(domain)
    return str(Path(os.path.expanduser(output_dir)) / f"{config}_with_retrieval_summary.jsonl")


def _clip(value: Any, limit: int) -> str:
    text = str(value or "").strip()
    return text if len(text) <= limit else text[:limit] + "..."


def normalize_description(value: Any) -> str:
    if value is None:
        return ""
    parsed = value
    if isinstance(value, str):
        text = value.strip()
        if text.startswith(("[", "(")):
            try:
                parsed = ast.literal_eval(text)
            except (SyntaxError, ValueError):
                parsed = value
    if isinstance(parsed, (list, tuple)):
        values = []
        seen = set()
        for item in parsed:
            text = " ".join(str(item).split())
            if text and text not in seen:
                seen.add(text)
                values.append(text)
        return "\n\n".join(values)
    return " ".join(str(parsed).split())


def summary_length_profile(original_description: str) -> tuple[str, int, int]:
    character_count = len(original_description)
    if character_count >= 700:
        profile = "rich"
    elif character_count >= 250:
        profile = "normal"
    else:
        profile = "sparse"
    min_words, max_words = SUMMARY_LENGTH_PROFILES[profile]
    return profile, min_words, max_words


def summary_length_profile_for_row(
    row: dict[str, Any],
    source_quality_overrides: dict[int, dict[str, Any]] = SOURCE_QUALITY_OVERRIDES,
) -> tuple[str, int, int]:
    description = normalize_description(row.get("description"))
    if int(row.get("item_id")) in source_quality_overrides:
        description = ""
    return summary_length_profile(description)


def build_user_prompt(
    row: dict[str, Any],
    source_quality_overrides: dict[int, dict[str, Any]] = SOURCE_QUALITY_OVERRIDES,
) -> tuple[str, int, int]:
    title = " ".join(str(row.get("title") or "").split())
    if not title:
        raise ValueError("catalog item has an empty title")
    brand = " ".join(str(row.get("brand") or "").split()) or "(not provided)"
    description = normalize_description(row.get("description"))
    detailed_description = normalize_description(row.get("detailed_description"))
    if int(row.get("item_id")) in source_quality_overrides:
        description = ""
        detailed_description = ""
    length_profile, min_words, max_words = summary_length_profile_for_row(
        row,
        source_quality_overrides,
    )
    prompt = USER_TEMPLATE.format(
        title=title,
        brand=brand,
        description=_clip(description, MAX_RAW_DESCRIPTION_CHARS) or "(not provided)",
        detailed_description=(
            _clip(detailed_description, MAX_DETAILED_DESCRIPTION_CHARS)
            or "(not provided)"
        ),
        length_profile=length_profile,
        min_words=min_words,
        max_words=max_words,
    )
    return prompt, min_words, max_words


def normalize_summary(raw: str) -> str:
    summary = " ".join(str(raw).strip().split())
    if summary.startswith("```"):
        summary = re.sub(r"^```(?:text)?\s*|\s*```$", "", summary, flags=re.IGNORECASE)
        summary = " ".join(summary.split())
    if len(summary) >= 2 and summary[0] == summary[-1] == '"':
        summary = summary[1:-1].strip()
    return summary


def content_filter_safe_prompt(user_prompt: str) -> str:
    """Preserve retrieval semantics while removing graphic catalog phrasing."""
    title_match = re.search(r"^Title:\s*(.+)$", user_prompt, re.MULTILINE)
    brand_match = re.search(r"^Brand:\s*(.+)$", user_prompt, re.MULTILINE)
    detailed_match = re.search(
        r"^Detailed description:\s*(.*?)\n\nTARGET LENGTH:",
        user_prompt,
        re.MULTILINE | re.DOTALL,
    )
    target_match = re.search(r"^TARGET LENGTH:.+$", user_prompt, re.MULTILINE)
    if not all((title_match, brand_match, detailed_match, target_match)):
        raise ValueError("could not construct content-filter-safe catalog prompt")
    safe_prompt = (
        "SOURCE METADATA\n\n"
        f"Title: {title_match.group(1)}\n"
        f"Brand: {brand_match.group(1)}\n"
        "Safety-normalized factual description: "
        f"{detailed_match.group(1)}\n\n"
        f"{target_match.group(0)}\n\n"
        "Write only the compact retrieval summary."
    )
    replacements = (
        (r"\b(?:blood\w*|gor\w*)\b", "mature visual effects"),
        (r"\b(?:dismemberment|dismembered|decapitation)\b", "combat effects"),
        (r"\b(?:execution|executions|slaughter|slaughters)\b", "combat"),
        (r"\b(?:kill|kills|killing|killed)\b", "defeat"),
        (r"\b(?:deadly|lethal|brutal|ruthless|violent|violence)\b", "intense"),
        (r"\b(?:flesh|intestines|limbs)\b", "enemies"),
        (r"\b(?:psychotic|psychopath\w*|demented)\b", "mature"),
        (r"\b(?:tortur\w*|murder\w*)\b", "conflict"),
        (r"\b(?:sexy|sexiest|buxom|bikini)\b", "stylized"),
        (r"\b(?:zombie|zombies|undead)\b", "infected enemies"),
    )
    for pattern, replacement in replacements:
        safe_prompt = re.sub(pattern, replacement, safe_prompt, flags=re.IGNORECASE)
    return safe_prompt


def validate_summary(raw: str, min_words: int = 45, max_words: int = 190) -> str:
    raw_text = str(raw).strip()
    if "```" in raw_text or re.search(r"^\s*[-*]\s+", raw_text, re.MULTILINE):
        raise ValueError("summary contains formatting instead of one paragraph")
    summary = normalize_summary(raw)
    if not summary:
        raise ValueError("GPT returned an empty summary")
    if re.search(r"<a_[^>]+><b_[^>]+><c_[^>]+>", summary):
        raise ValueError("summary contains a semantic ID")
    if re.match(r"^(summary|retrieval summary|title)\s*:", summary, re.IGNORECASE):
        raise ValueError("summary starts with a forbidden heading")
    forbidden_phrase = next(
        (phrase for phrase in FORBIDDEN_SUMMARY_PHRASES if phrase in summary.casefold()),
        None,
    )
    if forbidden_phrase is not None:
        raise ValueError(f"summary contains forbidden meta language: {forbidden_phrase}")
    word_count = len(re.findall(r"\b[\w][\w'’-]*\b", summary))
    if word_count < min_words:
        raise ValueError(
            f"summary is too short: {word_count} words; minimum is {min_words}"
        )
    if word_count > max_words:
        raise ValueError(
            f"summary is too long: {word_count} words; maximum is {max_words}"
        )
    return summary


def generate_summary(
    client: Any,
    system_prompt: str,
    user_prompt: str,
    model: str,
    reasoning_effort: str,
    min_words: int,
    max_words: int,
) -> str:
    last_error: Exception | None = None
    feedback = ""
    active_prompt = user_prompt
    for attempt in range(1, MAX_API_ATTEMPTS + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": active_prompt + feedback},
                ],
                max_completion_tokens=MAX_COMPLETION_TOKENS,
                reasoning_effort=reasoning_effort,
            )
            return validate_summary(
                response.choices[0].message.content or "",
                min_words=min_words,
                max_words=max_words,
            )
        except Exception as error:
            last_error = error
            if "content_filter" in str(error) or "ResponsibleAIPolicyViolation" in str(error):
                active_prompt = content_filter_safe_prompt(user_prompt)
            feedback = (
                "\n\nThe previous response failed validation: "
                f"{type(error).__name__}: {str(error)[:240]}. "
                "Return one corrected factual paragraph only."
            )
            if attempt < MAX_API_ATTEMPTS:
                time.sleep(min(2 ** (attempt - 1), 8))
    raise RuntimeError(
        f"GPT summary failed after {MAX_API_ATTEMPTS} attempts: {last_error}"
    ) from last_error


def prompt_signature(domain: str, model: str, reasoning_effort: str) -> str:
    is_video_games = domain == "Video_Games"
    payload = {
        "dataset": HF_REPO,
        "config": config_for_domain(domain),
        "split": HF_SPLIT,
        "revision": HF_REVISION,
        "model": model,
        "reasoning_effort": reasoning_effort,
        "system_prompt": system_prompt_for_domain(domain),
        "user_template": USER_TEMPLATE,
        "input_fields": ["title", "brand", "description", "detailed_description"],
        "summary_length_profiles": SUMMARY_LENGTH_PROFILES,
        "source_quality_overrides": SOURCE_QUALITY_OVERRIDES if is_video_games else {},
        "interest_analysis_source": INTEREST_ANALYSIS_SOURCE if is_video_games else None,
        "interest_analysis_sample_size": (
            INTEREST_ANALYSIS_SAMPLE_SIZE if is_video_games else None
        ),
        "interest_analysis_sample_seed": (
            INTEREST_ANALYSIS_SAMPLE_SEED if is_video_games else None
        ),
        "interest_analysis_label_counts": (
            INTEREST_ANALYSIS_LABEL_COUNTS if is_video_games else None
        ),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()[:20]


def row_key(row: dict[str, Any]) -> str:
    return f"{row.get('item_id')}::{row.get('sid')}"


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def append_jsonl(path: str, value: dict[str, Any]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def load_completed(path: str) -> dict[str, dict[str, Any]]:
    if not os.path.exists(path):
        return {}
    completed = {}
    for record in load_jsonl(path):
        if not isinstance(record.get("retrieval_summary"), str):
            continue
        completed[row_key(record)] = record
    return completed


def write_canonical_output(path: str, records: dict[str, dict[str, Any]]) -> None:
    ordered = sorted(
        records.values(),
        key=lambda record: (int(record["item_id"]), str(record["sid"])),
    )
    temporary_path = path + ".tmp"
    with Path(temporary_path).open("w", encoding="utf-8") as handle:
        for record in ordered:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary_path, path)


def write_metadata(
    path: str,
    domain: str,
    signature: str,
    model: str,
    reasoning_effort: str,
    item_count: int,
) -> None:
    is_video_games = domain == "Video_Games"
    metadata = {
        "source_dataset": HF_REPO,
        "source_domain": domain,
        "source_config": config_for_domain(domain),
        "source_split": HF_SPLIT,
        "source_revision": HF_REVISION,
        "source_viewer": (
            "https://huggingface.co/datasets/yufan/recsys-genrec-dataset-final/"
            f"viewer/{config_for_domain(domain)}"
        ),
        "item_count": item_count,
        "output_field": "retrieval_summary",
        "output_field_behavior": "replace if present, otherwise add",
        "summary_input_fields": [
            "title",
            "brand",
            "description",
            "detailed_description",
        ],
        "summary_length_profiles": SUMMARY_LENGTH_PROFILES,
        "summary_length_profile_basis": (
            "normalized original description character count after source-quality overrides"
        ),
        "content_filter_sanitizer_version": (
            CONTENT_FILTER_SANITIZER_VERSION if is_video_games else None
        ),
        "source_quality_overrides": SOURCE_QUALITY_OVERRIDES if is_video_games else {},
        "model": model,
        "reasoning_effort": reasoning_effort,
        "prompt_signature": signature,
        "interest_analysis": (
            {
                "source": INTEREST_ANALYSIS_SOURCE,
                "sample_size": INTEREST_ANALYSIS_SAMPLE_SIZE,
                "sample_seed": INTEREST_ANALYSIS_SAMPLE_SEED,
                "label_counts": INTEREST_ANALYSIS_LABEL_COUNTS,
            }
            if is_video_games
            else None
        ),
    }
    metadata_path = path.replace(".jsonl", ".meta.json")
    if os.path.exists(metadata_path):
        existing = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
        if existing.get("prompt_signature") != signature:
            raise RuntimeError(
                f"{metadata_path} uses a different prompt/model; choose a new output path"
            )
    Path(metadata_path).parent.mkdir(parents=True, exist_ok=True)
    with Path(metadata_path).open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def worker(
    task_queue: Any,
    result_queue: Any,
    endpoint: str,
    model: str,
    reasoning_effort: str,
    system_prompt: str,
) -> None:
    try:
        from gpt5_endpoint_test import get_GPT5_client

        client = get_GPT5_client(endpoint)
    except Exception as error:
        result_queue.put(("worker_error", endpoint, type(error).__name__, str(error)[:1000]))
        return
    while True:
        task = task_queue.get()
        if task is None:
            return
        key, source_index, row, user_prompt, min_words, max_words = task
        try:
            summary = generate_summary(
                client,
                system_prompt,
                user_prompt,
                model,
                reasoning_effort,
                min_words,
                max_words,
            )
            result_queue.put(
                ("ok", key, source_index, row, summary, endpoint)
            )
        except Exception as error:
            result_queue.put(
                (
                    "fail",
                    key,
                    source_index,
                    endpoint,
                    type(error).__name__,
                    str(error)[:1000],
                )
            )


def run_pool(
    tasks: list[tuple[str, int, dict[str, Any], str, int, int]],
    output_path: str,
    completed: dict[str, dict[str, Any]],
    endpoints: list[str],
    per_endpoint: int,
    model: str,
    reasoning_effort: str,
    system_prompt: str,
) -> tuple[int, int]:
    if not tasks:
        print("Nothing to do")
        return 0, 0
    context = mp.get_context("spawn")
    task_queue = context.Queue()
    result_queue = context.Queue()
    worker_endpoints = [endpoint for endpoint in endpoints for _ in range(per_endpoint)]
    processes = [
        context.Process(
            target=worker,
            args=(
                task_queue,
                result_queue,
                endpoint,
                model,
                reasoning_effort,
                system_prompt,
            ),
            daemon=True,
        )
        for endpoint in worker_endpoints
    ]
    for process in processes:
        process.start()
    for task in tasks:
        task_queue.put(task)
    for _ in processes:
        task_queue.put(None)

    failure_path = output_path.replace(".jsonl", ".failures.jsonl")
    started_at = time.time()
    last_log = 0.0
    succeeded = 0
    failed = 0
    total = len(tasks)
    print(
        f"{total} tasks / {len(endpoints)} endpoints x {per_endpoint} "
        f"= {len(processes)} processes",
        flush=True,
    )
    try:
        while succeeded + failed < total:
            try:
                message = result_queue.get(timeout=1)
            except queue.Empty:
                if not any(process.is_alive() for process in processes):
                    raise RuntimeError(
                        f"all workers exited with {total - succeeded - failed} tasks unfinished"
                    )
                continue
            kind = message[0]
            if kind == "ok":
                _, key, _, row, summary, _ = message
                record = dict(row)
                record["retrieval_summary"] = summary
                completed[key] = record
                append_jsonl(output_path, record)
                succeeded += 1
            elif kind == "fail":
                _, key, source_index, endpoint, error_type, error = message
                append_jsonl(
                    failure_path,
                    {
                        "row_key": key,
                        "source_index": source_index,
                        "endpoint": endpoint,
                        "error_type": error_type,
                        "error": error,
                    },
                )
                failed += 1
            else:
                _, endpoint, error_type, error = message
                print(f"WORKER ERROR {endpoint}: {error_type}: {error}", flush=True)

            now = time.time()
            finished = succeeded + failed
            if now - last_log >= LOG_EVERY_SECONDS or finished == total:
                last_log = now
                elapsed = now - started_at
                rate = finished / elapsed if elapsed else 0.0
                eta = (total - finished) / rate if rate else math.inf
                print(
                    f"{finished}/{total} ({finished / total * 100:.1f}%) | "
                    f"{rate:.2f} rows/s | ETA {eta / 60:.1f} min | failed={failed}",
                    flush=True,
                )
    finally:
        for process in processes:
            process.join(timeout=5)
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join()
    return succeeded, failed


def validate_complete_catalog(
    records: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    domain: str,
) -> None:
    if len(records) != len(source_rows):
        raise ValueError(
            f"refusing partial catalog upload: {len(records)} records for "
            f"{len(source_rows)} source rows"
        )
    record_keys = [row_key(record) for record in records]
    source_keys = [row_key(row) for row in source_rows]
    if len(set(record_keys)) != len(record_keys):
        raise ValueError("generated catalog contains duplicate row keys")
    if set(record_keys) != set(source_keys):
        raise ValueError("generated catalog row keys do not match the source catalog")
    source_quality_overrides = (
        SOURCE_QUALITY_OVERRIDES if domain == "Video_Games" else {}
    )
    for record in records:
        _, min_words, max_words = build_user_prompt(
            record,
            source_quality_overrides,
        )
        validate_summary(
            record.get("retrieval_summary", ""),
            min_words=min_words,
            max_words=max_words,
        )


def push_catalog_to_hub(
    output_path: str,
    domain: str,
    source_rows: list[dict[str, Any]],
) -> None:
    from datasets import Dataset

    records = load_jsonl(output_path)
    validate_complete_catalog(records, source_rows, domain)
    token = os.environ.get("HF_TOKEN")
    dataset = Dataset.from_list(records)
    commit_info = dataset.push_to_hub(
        HF_REPO,
        config_name=config_for_domain(domain),
        split=HF_SPLIT,
        token=token,
        commit_message=f"Add {domain} retrieval summaries",
    )
    print(
        f"Uploaded {len(records)} rows to {HF_REPO}/"
        f"{config_for_domain(domain)}@{commit_info.oid}",
        flush=True,
    )


def process_domain(args: argparse.Namespace, domain: str, endpoints: list[str]) -> int:
    from datasets import load_dataset

    config = config_for_domain(domain)
    dataset = load_dataset(
        HF_REPO,
        config,
        split=HF_SPLIT,
        revision=HF_REVISION,
    )
    source_rows = [dict(row) for row in dataset]
    rows = source_rows
    if args.limit is not None:
        rows = rows[: args.limit]
    elif args.sample_size is not None:
        if args.sample_size > len(rows):
            raise ValueError(
                f"--sample-size exceeds the {domain} catalog size {len(rows)}"
            )
        rows = random.Random(args.seed).sample(rows, args.sample_size)

    output_path = (
        os.path.expanduser(args.output)
        if args.output is not None
        else default_output_for_domain(domain, args.output_dir)
    )
    system_prompt = system_prompt_for_domain(domain)
    source_quality_overrides = (
        SOURCE_QUALITY_OVERRIDES if domain == "Video_Games" else {}
    )
    signature = prompt_signature(domain, args.model, args.reasoning_effort)
    write_metadata(
        output_path,
        domain,
        signature,
        args.model,
        args.reasoning_effort,
        len(rows),
    )

    tasks = []
    seen = set()
    for source_index, row in enumerate(rows):
        key = row_key(row)
        if key in seen:
            raise ValueError(f"duplicate {domain} catalog row key: {key}")
        seen.add(key)
        user_prompt, min_words, max_words = build_user_prompt(
            row,
            source_quality_overrides,
        )
        tasks.append((key, source_index, row, user_prompt, min_words, max_words))

    print(
        f"[{domain}] config={config} rows={len(rows)} output={output_path}",
        flush=True,
    )
    if args.dry_run:
        print(system_prompt)
        print(tasks[0][3])
        print(f"PROMPT_SIGNATURE={signature}")
        return 0

    completed = load_completed(output_path)
    pending = [task for task in tasks if task[0] not in completed]
    total_succeeded = 0
    for retry_round in range(args.failure_retry_rounds + 1):
        if not pending:
            break
        if retry_round:
            print(
                f"[{domain}] retry round {retry_round}/"
                f"{args.failure_retry_rounds}: {len(pending)} unresolved rows",
                flush=True,
            )
        succeeded, _ = run_pool(
            pending,
            output_path,
            completed,
            endpoints,
            args.per_endpoint,
            args.model,
            args.reasoning_effort,
            system_prompt,
        )
        total_succeeded += succeeded
        pending = [task for task in pending if task[0] not in completed]
    failed = len(pending)
    write_canonical_output(output_path, completed)
    failure_path = output_path.replace(".jsonl", ".failures.jsonl")
    if len(completed) == len(rows) and os.path.exists(failure_path):
        os.remove(failure_path)
    print(
        f"[{domain}] wrote {len(completed)}/{len(rows)} rows to {output_path} "
        f"({total_succeeded} new, {failed} unresolved)",
        flush=True,
    )
    if args.push_to_hub:
        if args.limit is not None or args.sample_size is not None:
            raise ValueError("--push-to-hub cannot be combined with a partial catalog")
        if failed or len(completed) != len(source_rows):
            raise ValueError(f"refusing to upload incomplete {domain} generation")
        push_catalog_to_hub(output_path, domain, source_rows)
    return failed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate GPT-5.4 retrieval summaries for supported catalog domains."
    )
    parser.add_argument(
        "--domains",
        nargs="+",
        choices=SUPPORTED_DOMAINS,
        default=list(DEFAULT_DOMAINS),
    )
    parser.add_argument("--output", default=None, help="Single-domain output override.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--model", default=MODEL)
    parser.add_argument(
        "--reasoning-effort",
        choices=("minimal", "low", "medium", "high"),
        default=DEFAULT_REASONING_EFFORT,
    )
    parser.add_argument("--per-endpoint", type=int, default=DEFAULT_PER_ENDPOINT)
    parser.add_argument(
        "--failure-retry-rounds",
        type=int,
        default=DEFAULT_FAILURE_RETRY_ROUNDS,
        help="Fresh worker rounds for rows still failing after four internal attempts.",
    )
    parser.add_argument("--endpoints", nargs="*", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sample-size", type=int, default=None)
    parser.add_argument("--seed", type=int, default=20260818)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--push-to-hub",
        action="store_true",
        help="Replace each completed domain's catalog config in the source HF repo.",
    )
    args = parser.parse_args()
    if args.per_endpoint < 1:
        parser.error("--per-endpoint must be positive")
    if args.failure_retry_rounds < 0:
        parser.error("--failure-retry-rounds must be nonnegative")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    if args.sample_size is not None and args.sample_size < 1:
        parser.error("--sample-size must be positive")
    if args.limit is not None and args.sample_size is not None:
        parser.error("--limit and --sample-size are mutually exclusive")
    if args.output is not None and len(args.domains) != 1:
        parser.error("--output can only be used with one domain")
    if args.push_to_hub and (args.limit is not None or args.sample_size is not None):
        parser.error("--push-to-hub requires complete catalogs")
    if args.push_to_hub and args.dry_run:
        parser.error("--push-to-hub cannot be combined with --dry-run")

    from gpt5_endpoint_test import ENDPOINTS

    endpoints = args.endpoints or list(ENDPOINTS)
    unknown = sorted(set(endpoints) - set(ENDPOINTS))
    if unknown:
        parser.error(f"unknown endpoint(s): {unknown}")
    total_failed = sum(process_domain(args, domain, endpoints) for domain in args.domains)
    if total_failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()