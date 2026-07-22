import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI

ENDPOINTS = [
    "feedscopilot-azureopenai-au",
    "feedscopilot-azureopenai-ca-east",
    "feedscopilot-azureopenai-eastus",
    "feedscopilot-azureopenai-eastus2",
    "feedscopilot-azureopenai-jp",
    "feedscopilot-azureopenai-northus",
    "feedscopilot-azureopenai-southus",
    "feedscopilot-azureopenai-sweden",
    "feedscopilot-azureopenai-uksouth",
    "feedscopilot-azureopenai-westus3",
]

# Real-time (Global Standard) deployments — latency-benchmarked.
# gpt-5.2 / gpt-5.4 exist on every endpoint; the *standard* gpt-5.4-mini only on some.
REALTIME_MODELS = ["gpt-5.2", "gpt-5.4", "gpt-5.4-mini"]

# Endpoints where a real-time (standard) gpt-5.4-mini deployment exists.
# Everywhere else there is no standard gpt-5.4-mini, so it's skipped.
REALTIME_MINI_ENDPOINTS = {
    "feedscopilot-azureopenai-au",
    "feedscopilot-azureopenai-eastus",
    "feedscopilot-azureopenai-eastus2",
    "feedscopilot-azureopenai-jp",
}

# --- Benchmark config (kept identical across endpoints/models for a fair speed comparison) ---
# Text-only, deterministic-length prompt so every model does roughly the same amount of work.
SYSTEM_PROMPT = "You are a helpful assistant. Answer concisely."
USER_PROMPT = (
    "In exactly three sentences, explain what a recommender system is. "
    "Do not use bullet points or headings."
)
MAX_COMPLETION_TOKENS = 256      # hard cap so no model runs away
REASONING_EFFORT = "minimal"     # GPT-5 family: minimal|low|medium|high. Low effort => less variable reasoning latency
REPEATS = 3                      # timed runs per (endpoint, model), latency is averaged
WARMUP = True                    # one untimed call first to avoid cold-start bias
SWEEP_CONCURRENCY = 4            # parallel (endpoint, model) probes. Set to 1 for the most precise latency numbers.


def get_GPT5_client(endpoint):

    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://cognitiveservices.azure.com/.default"
    )

    if endpoint not in ENDPOINTS:
        raise ValueError(f"Unsupported endpoint: {endpoint}")

    return AzureOpenAI(
        api_version="2024-12-01-preview",
        azure_endpoint=f"https://{endpoint}.openai.azure.com/",
        azure_ad_token_provider=token_provider
    )


def _one_call(client, model):
    """Single text-only chat completion with fixed params. Returns (latency_s, completion_tokens)."""
    kwargs = dict(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ],
        max_completion_tokens=MAX_COMPLETION_TOKENS,
    )
    if REASONING_EFFORT:
        kwargs["reasoning_effort"] = REASONING_EFFORT

    start = time.perf_counter()
    response = client.chat.completions.create(**kwargs)
    latency = time.perf_counter() - start

    completion_tokens = None
    if response.usage is not None:
        completion_tokens = response.usage.completion_tokens
    return latency, completion_tokens


def benchmark(endpoint, model):
    """Warm up, then time REPEATS calls. Returns a result dict."""
    result = {"ok": False, "latency": None, "tokens": None, "tok_per_s": None,
              "error": None}
    try:
        client = get_GPT5_client(endpoint)

        if WARMUP:
            try:
                _one_call(client, model)
            except Exception:
                pass  # if warmup fails, the timed loop below will surface the real error

        latencies, token_counts = [], []
        for _ in range(REPEATS):
            latency, tokens = _one_call(client, model)
            latencies.append(latency)
            if tokens is not None:
                token_counts.append(tokens)

        avg_latency = sum(latencies) / len(latencies)
        result["ok"] = True
        result["latency"] = avg_latency
        if token_counts:
            avg_tokens = sum(token_counts) / len(token_counts)
            result["tokens"] = avg_tokens
            result["tok_per_s"] = avg_tokens / avg_latency if avg_latency > 0 else None
        print(f"OK    {endpoint:<38} {model:<20} {avg_latency:6.2f}s")
    except Exception as error:
        msg = str(error)
        result["error"] = msg
        print(f"FAIL  {endpoint:<38} {model:<20} {msg[:60]}")
    return result


if __name__ == "__main__":
    # Real-time (Global Standard) deployments to latency-benchmark.
    realtime_pairs = []
    for endpoint in ENDPOINTS:
        for model in REALTIME_MODELS:
            if model == "gpt-5.4-mini" and endpoint not in REALTIME_MINI_ENDPOINTS:
                continue  # no standard gpt-5.4-mini deployment on this endpoint
            realtime_pairs.append((endpoint, model))

    results = {}

    if SWEEP_CONCURRENCY <= 1:
        for endpoint, model in realtime_pairs:
            results[(endpoint, model)] = benchmark(endpoint, model)
    else:
        with ThreadPoolExecutor(max_workers=SWEEP_CONCURRENCY) as pool:
            future_to_pair = {
                pool.submit(benchmark, endpoint, model): (endpoint, model)
                for endpoint, model in realtime_pairs
            }
            for future in as_completed(future_to_pair):
                results[future_to_pair[future]] = future.result()

    # summary
    print("\n" + "=" * 92)
    print(f"SUMMARY  (text-only, reasoning_effort={REASONING_EFFORT}, "
          f"max_tokens={MAX_COMPLETION_TOKENS}, repeats={REPEATS})")
    print("=" * 92)
    print(f"{'endpoint':<38} {'model':<20} {'status':<8} {'avg latency':>12} {'tok/s':>8}")
    print("-" * 92)

    total = ok_count = 0
    for endpoint, model in realtime_pairs:
        r = results[(endpoint, model)]
        total += 1
        if r["ok"]:
            ok_count += 1
            status = "OK"
            latency = f"{r['latency']:.2f}s"
            tok_per_s = f"{r['tok_per_s']:.1f}" if r["tok_per_s"] else "-"
        else:
            status = "FAIL"
            latency = tok_per_s = "-"
        print(f"{endpoint:<38} {model:<20} {status:<8} {latency:>12} {tok_per_s:>8}")

    print("-" * 92)
    print(f"working: {ok_count}/{total}   failed: {total - ok_count}/{total}")

    # fastest working combos
    working = [(k, r) for k, r in results.items() if r["ok"]]
    if working:
        working.sort(key=lambda kv: kv[1]["latency"])
        print("\nFASTEST WORKING (by avg latency)")
        print("-" * 88)
        for (endpoint, model), r in working[:5]:
            print(f"{endpoint:<38} {model:<14} {r['latency']:.2f}s")

    # failures
    failures = [(k, r["error"]) for k, r in results.items() if not r["ok"]]
    if failures:
        print("\nFAILURE DETAILS")
        print("-" * 88)
        for (endpoint, model), error in failures:
            print(f"{endpoint} | {model}\n    {error}")