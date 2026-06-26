import os
import re
import json
import arxiv
import yaml
import logging
import argparse
import datetime
from pathlib import Path  # Use pathlib for modern, object-oriented path handling
from typing import Optional

# --- Basic Configuration ---
logging.basicConfig(
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%m/%d/%Y %H:%M:%S',
    level=logging.INFO
)
ARXIV_URL_PREFIX = "http://arxiv.org/abs/"

# A single shared arXiv client so its rate limiting (delay_seconds) is enforced
# across ALL queries, including separate per-month backfill windows. Creating a
# fresh client per window resets the timer and bursts requests, which arXiv
# throttles with HTTP 429.
_ARXIV_CLIENT = None

def get_arxiv_client() -> arxiv.Client:
    global _ARXIV_CLIENT
    if _ARXIV_CLIENT is None:
        _ARXIV_CLIENT = arxiv.Client(page_size=100, delay_seconds=15, num_retries=8)
    return _ARXIV_CLIENT

# --- Helper Functions ---

def get_authors(authors: list[arxiv.Result.Author], first_author: bool = False) -> str:
    """Returns a formatted string of author names."""
    if first_author:
        return str(authors[0])
    return ", ".join(str(author) for author in authors)

def sort_papers_by_id(papers: dict) -> dict:
    """Sorts a dictionary of papers by their keys (paper_id) in reverse chronological order."""
    return dict(sorted(papers.items(), reverse=True))

def normalize_text(s: str) -> str:
    """Lowercase and fold hyphens/underscores/slashes to spaces for robust
    substring matching, then collapse runs of whitespace.

    This lets variants like "collaborative-filtering", "Cold_Start" and
    "next/item" all match their space-separated filter terms.
    """
    s = re.sub(r'[\-_/]+', ' ', s.lower())
    return re.sub(r'\s+', ' ', s).strip()

def extract_venue(comment: Optional[str], journal_ref: Optional[str]) -> str:
    """Best-effort extraction of an accepted/published venue from arXiv metadata.

    arXiv has no dedicated venue field, so acceptance info usually lives in the
    free-text `comment` (e.g. "Accepted by KDD 2026") or in `journal_ref`.
    """
    if journal_ref:
        return journal_ref.strip()
    if comment and re.search(r'accept|to appear|camera[\s-]?ready|proceedings', comment, re.IGNORECASE):
        return comment.strip()
    return "null"

# Known name variants for each conference. A `venues` entry in the config expands
# to all of its aliases so that, e.g., "NeurIPS" also matches "NIPS" and the full
# "Neural Information Processing Systems" spelling found in comments/journal_ref.
VENUE_ALIASES = {
    "ICLR": ["ICLR", "International Conference on Learning Representations"],
    "NeurIPS": ["NeurIPS", "NIPS", "Neural Information Processing Systems"],
    "ICML": ["ICML", "International Conference on Machine Learning"],
    "ACL": ["ACL", "Association for Computational Linguistics"],
}

def build_venue_pattern(aliases: list[str]) -> 're.Pattern':
    """Compile a case-insensitive regex matching any of the given venue aliases.

    Uses letter-only boundaries so a year/apostrophe suffix still matches
    (e.g. "ICML2024", "NeurIPS'23") while avoiding false hits inside other
    acronyms (e.g. "ACL" must not match NAACL / EACL / TACL).
    """
    # Longer aliases first so the full name is preferred over its acronym.
    parts = sorted({re.escape(a) for a in aliases}, key=len, reverse=True)
    return re.compile(r'(?<![A-Za-z])(' + '|'.join(parts) + r')(?![A-Za-z])', re.IGNORECASE)

# Map every known alias (lowercased) to a canonical short venue name. Used to
# label each paper with a compact "<Venue><Year>" tag, e.g. "ICML2026".
VENUE_CANON = {
    "iclr": "ICLR",
    "international conference on learning representations": "ICLR",
    "neurips": "NeurIPS",
    "nips": "NeurIPS",
    "neural information processing systems": "NeurIPS",
    "icml": "ICML",
    "international conference on machine learning": "ICML",
    "acl": "ACL",
    "association for computational linguistics": "ACL",
}
_VENUE_FIND_RE = build_venue_pattern(list(VENUE_CANON.keys()))

def _normalize_year(yy: str) -> str:
    """Turn a 2-digit year into 4 digits (all target venues are 20xx)."""
    return str(2000 + int(yy)) if len(yy) == 2 else yy

def canonical_venue(comment: Optional[str], journal_ref: Optional[str]) -> str:
    """Return a compact "<Venue><Year>" tag (e.g. "ICML2026", "ACL2025").

    Scans the free-text comment/journal_ref for any known venue alias and the
    year next to it. Prefers a match that has an adjacent year; falls back to the
    bare venue name, or "null" when no known venue is mentioned.
    """
    text = " ".join(x for x in (comment, journal_ref) if x)
    if not text:
        return "null"
    fallback = None
    for m in _VENUE_FIND_RE.finditer(text):
        canon = VENUE_CANON[m.group(0).lower()]
        tail = text[m.end():m.end() + 8]
        apos = re.match(r"\s*'(\d{2})\b", tail)            # ICML'26
        full = re.match(r"[\s:\-/]*((?:19|20)\d{2})\b", tail)  # ICML 2026 / ICML2026
        if apos:
            return f"{canon}{_normalize_year(apos.group(1))}"
        if full:
            return f"{canon}{full.group(1)}"
        if fallback is None:
            fallback = canon
    return fallback or "null"

def iter_month_windows(since: datetime.date, until: datetime.date):
    """Yield (start_date, end_date_inclusive) for each calendar month in [since, until].

    Used to split a wide date range into per-month arXiv queries. arXiv's API
    refuses to page beyond ~10,000 results for a single query, so a broad query
    (tens of thousands of hits) must be chunked into windows that each stay
    under that ceiling.
    """
    current = since.replace(day=1)
    while current <= until:
        if current.month == 12:
            next_month = current.replace(year=current.year + 1, month=1)
        else:
            next_month = current.replace(month=current.month + 1)
        window_start = max(current, since)
        window_end = min(next_month - datetime.timedelta(days=1), until)
        yield window_start, window_end
        current = next_month

# --- Core Logic ---

def load_config(config_file: Path) -> dict:
    """Loads, parses, and returns the YAML configuration."""
    if not config_file.exists():
        logging.error(f"Configuration file not found at: {config_file}")
        exit() # Or raise an exception

    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f) # Use safe_load for security

    # REFACTORED: Simplified query building
    # The original "pretty_filters" was complex. A simple join is often sufficient.
    # The arxiv library can handle advanced queries directly if needed.
    keyword_queries = {}
    title_filters = {}
    output_paths = {}
    venue_filters = {}
    abstract_filters = {}
    abstract_categories = {}
    for key, value in config.get('keywords', {}).items():
        # Keyword terms (optional). Join with " OR ", quoting multi-word phrases.
        filters = value.get('filters', [])
        query_parts = [f'"{f}"' if ' ' in f else f for f in filters]
        kw_query = " OR ".join(query_parts)
        # arXiv subject categories (optional), e.g. cs.CL -> "cat:cs.CL".
        cat_query = " OR ".join(f"cat:{c}" for c in value.get('categories', []))
        # Accepted venues (optional). arXiv has no venue field, so we (a) narrow
        # server-side by searching every venue name variant across all fields and
        # (b) post-filter on comment/journal_ref via a regex (see get_daily_papers).
        aliases = []
        for v in value.get('venues', []):
            aliases.extend(VENUE_ALIASES.get(v, [v]))
        venue_query = " OR ".join(f'all:"{a}"' if ' ' in a else f'all:{a}' for a in aliases)
        venue_filters[key] = build_venue_pattern(aliases) if aliases else None
        # Combine all present query components with AND.
        components = [f"({c})" for c in (kw_query, cat_query, venue_query) if c]
        keyword_queries[key] = " AND ".join(components)
        # Title filters: explicit list wins; else fall back to keyword filters;
        # else None (no title filtering, e.g. category-only topics).
        if 'title_filters' in value:
            title_filters[key] = [t.lower() for t in value['title_filters']]
        elif filters:
            title_filters[key] = [t.lower() for t in filters]
        else:
            title_filters[key] = None
        # Abstract-level recall booster (opt-in). When `abstract_filters` is set, a
        # paper that fails the title filter is still kept if its ABSTRACT matches
        # one of these terms and (when `abstract_categories` is given) its primary
        # category is in that allowlist — catching papers that only name the topic
        # in the abstract while keeping cross-domain noise out.
        abstract_filters[key] = [t.lower() for t in value['abstract_filters']] if value.get('abstract_filters') else None
        abstract_categories[key] = list(value['abstract_categories']) if value.get('abstract_categories') else None
        # Optional per-topic output file; falls back to the global path in main().
        if value.get('output'):
            output_paths[key] = value['output']

    config['keyword_queries'] = keyword_queries
    config['title_filters'] = title_filters
    config['output_paths'] = output_paths
    config['venue_filters'] = venue_filters
    config['abstract_filters'] = abstract_filters
    config['abstract_categories'] = abstract_categories
    logging.info(f"Configuration loaded: {config}")
    return config

def get_daily_papers(topic: str, query: str, max_results: int, title_filters: Optional[list[str]] = None, days: Optional[int] = None, since: Optional[datetime.date] = None, date_range: Optional[tuple] = None, venue_filters: Optional['re.Pattern'] = None, abstract_filters: Optional[list[str]] = None, abstract_categories: Optional[list[str]] = None) -> dict:
    """
    Searches arXiv for papers based on a query and returns a dictionary of found papers.

    REFACTORED:
    - Fixed the critical bug where no papers were being saved.
    - Simplified the title filtering logic.
    - Now stores paper data in a structured dictionary instead of a pipe-delimited string.
    - Optionally restricts results to papers submitted within the last `days` days.
    - `date_range` (start, end) bounds the query with a submittedDate clause so a
      wide backfill can be chunked into <10k-result windows (arXiv's paging cap).
    """
    papers = {}
    # Normalize filter terms (lowercase + hyphen folding) so matching is robust to
    # case and hyphenation variants.
    normalized_title_filters = [normalize_text(t) for t in title_filters] if title_filters else None
    normalized_abstract_filters = [normalize_text(t) for t in abstract_filters] if abstract_filters else None
    # `since` (an explicit date) takes precedence over `days` for the cutoff.
    cutoff_date = None
    if since is not None:
        cutoff_date = since
    elif days is not None:
        cutoff_date = datetime.datetime.now(datetime.timezone.utc).date() - datetime.timedelta(days=days)

    # When a date window is given, bound the query directly so arXiv returns only
    # that window (keeping each query under the ~10k paging limit). The in-loop
    # cutoff check is then redundant and is disabled.
    if date_range is not None:
        start_d, end_d = date_range
        query = f"({query}) AND submittedDate:[{start_d.strftime('%Y%m%d')}0000 TO {end_d.strftime('%Y%m%d')}2359]"
        cutoff_date = None

    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )

    client = get_arxiv_client()
    for result in client.results(search):
        # Results are sorted by submitted date (newest first); stop once we pass the cutoff.
        if cutoff_date is not None and result.published.date() < cutoff_date:
            break

        # Text filtering: keep a paper if its TITLE matches one of the title
        # filters. As an opt-in recall booster, also keep papers whose ABSTRACT
        # matches one of `abstract_filters`, but only within `abstract_categories`
        # (when given) so cross-domain hits (e.g. medical/policy "recommendations")
        # stay out. Text is normalized so hyphenation/case variants still match.
        if normalized_title_filters:
            title_norm = normalize_text(result.title)
            keep = any(term in title_norm for term in normalized_title_filters)
            if not keep and normalized_abstract_filters:
                cat_ok = not abstract_categories or result.primary_category in abstract_categories
                if cat_ok:
                    abstract_norm = normalize_text(result.summary)
                    keep = any(term in abstract_norm for term in normalized_abstract_filters)
            if not keep:
                continue

        # Venue filter: keep only papers whose comment/journal_ref names a target venue.
        if venue_filters is not None:
            venue_text = " ".join(filter(None, [result.comment, result.journal_ref]))
            if not venue_text or not venue_filters.search(venue_text):
                continue

        paper_id = result.get_short_id()
        # The arxiv library already strips the version, but this is safe
        paper_key = paper_id.split('v')[0]
        
        logging.info(f"Found Paper: title='{result.title}', author='{get_authors(result.authors, True)}'")

        # REFACTORED: Store data in a structured dictionary for robustness
        papers[paper_key] = {
            "title": result.title,
            "authors": get_authors(result.authors),
            "first_author": get_authors(result.authors, first_author=True),
            "url": result.entry_id,
            "pdf_url": f"{ARXIV_URL_PREFIX}{paper_key}",
            "publish_date": result.published.date().isoformat(),
            "abstract": result.summary.replace("\n", " "),
            "primary_category": result.primary_category,
            "venue": extract_venue(result.comment, result.journal_ref),
            "venue_short": canonical_venue(result.comment, result.journal_ref),
            "comment": result.comment or "null",
            "journal_ref": result.journal_ref or "null",
        }
        
    return {topic: papers}


def update_json_file(filename: Path, new_data: dict):
    """Loads a JSON file, updates it with new data, and saves it."""
    try:
        with open(filename, "r", encoding='utf-8') as f:
            content = f.read()
            json_data = json.loads(content) if content else {}
    except FileNotFoundError:
        json_data = {}

    for topic, papers in new_data.items():
        if topic not in json_data:
            json_data[topic] = {}
        json_data[topic].update(papers)

    with open(filename, "w", encoding='utf-8') as f:
        json.dump(json_data, f, indent=4)


def main(**config):
    """Main execution function."""
    # --- Fetch new papers and save each topic to its own file ---
    logging.info("Starting daily paper fetching...")
    default_output = Path(config.get('json_output_path', './papers/papers.json'))
    output_paths = config.get('output_paths', {})
    only_topics = config.get('only_topics')
    since = config.get('since')
    for topic, query in config.get('keyword_queries', {}).items():
        # Skip topics not selected via --topic.
        if only_topics and topic not in only_topics:
            continue
        output_path = Path(output_paths.get(topic, default_output))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        title_filters = config.get('title_filters', {}).get(topic)
        venue_filters = config.get('venue_filters', {}).get(topic)
        abstract_filters = config.get('abstract_filters', {}).get(topic)
        abstract_categories = config.get('abstract_categories', {}).get(topic)

        if since is not None:
            # Backfill mode: chunk the range into monthly windows so each arXiv
            # query stays under the ~10k paging limit, saving after every window
            # so a mid-run failure never loses already-fetched papers.
            until = datetime.datetime.now(datetime.timezone.utc).date()
            total = 0
            for window_start, window_end in iter_month_windows(since, until):
                logging.info(f"Searching '{topic}' window {window_start} -> {window_end}")
                try:
                    papers_data = get_daily_papers(
                        topic=topic,
                        query=query,
                        max_results=config.get('max_results', 2),
                        title_filters=title_filters,
                        date_range=(window_start, window_end),
                        venue_filters=venue_filters,
                        abstract_filters=abstract_filters,
                        abstract_categories=abstract_categories,
                    )
                except Exception as exc:  # Keep going so one bad window doesn't abort the backfill.
                    logging.error(f"Window {window_start}->{window_end} failed: {exc}")
                    continue
                papers = papers_data.get(topic)
                if not papers:
                    continue
                update_json_file(output_path, {topic: papers})
                total += len(papers)
                logging.info(f"Saved {len(papers)} '{topic}' papers for {window_start} (running total: {total}) to '{output_path}'")
            logging.info(f"Finished '{topic}': {total} papers saved to '{output_path}'")
            continue

        logging.info(f"Searching for topic: '{topic}' with query: '{query}'")
        papers_data = get_daily_papers(
            topic=topic,
            query=query,
            max_results=config.get('max_results', 2),
            title_filters=title_filters,
            days=config.get('days'),
            since=since,
            venue_filters=venue_filters,
            abstract_filters=abstract_filters,
            abstract_categories=abstract_categories,
        )
        papers = papers_data.get(topic)
        if not papers: # Skip topics with no new papers
            continue

        # Use the topic's dedicated output file, falling back to the global path.
        update_json_file(output_path, {topic: papers})
        logging.info(f"Saved {len(papers)} '{topic}' papers to '{output_path}'")
    logging.info("Finished fetching papers.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated arXiv paper tracker.")
    parser.add_argument(
        '--config',
        type=Path,
        default=Path('config.yaml'),
        help='Path to the configuration YAML file.'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=None,
        help='Only fetch papers submitted within the last N days.'
    )
    parser.add_argument(
        '--max-results',
        type=int,
        default=None,
        help='Override max_results from the config file.'
    )
    parser.add_argument(
        '--since',
        type=lambda s: datetime.date.fromisoformat(s),
        default=None,
        help='Only fetch papers submitted on/after this date (YYYY-MM-DD). Overrides --days.'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=None,
        help='Override the output JSON path from the config file.'
    )
    parser.add_argument(
        '--topic',
        action='append',
        default=None,
        help='Only fetch the given topic (matches a key under `keywords`). Repeatable.'
    )
    # The 'update_paper_links' argument seems to be for a separate maintenance task.
    # It's better handled as a distinct script or a separate command.
    # For this refactoring, its logic is removed in favor of the more robust data pipeline.
    
    args = parser.parse_args()
    config = load_config(args.config)
    config['days'] = args.days
    config['since'] = args.since
    config['only_topics'] = set(args.topic) if args.topic else None
    if args.max_results is not None:
        config['max_results'] = args.max_results
    if args.output is not None:
        # An explicit --output forces every topic into one file (ignores per-topic outputs).
        config['json_output_path'] = str(args.output)
        config['output_paths'] = {}
    main(**config)