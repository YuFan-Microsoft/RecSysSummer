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
# Everywhere else gpt-5.4-mini is batch-only, so it's not latency-benchmarked.
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

# Global-Batch deployment name that now exists on EVERY endpoint (async Batch API only).
BATCH_MODEL = "gpt-5.4-mini-batch"

# --- Batch throughput test (optional; blocks until the batch job finishes) ---
# Batch is async, so it has no per-request latency; the metric here is END-TO-END wall-clock
# for a whole batch of N requests plus aggregate throughput (req/s, tok/s).
RUN_BATCH_BENCHMARK = True    # set True to time an actual batch job (can take minutes to hours)
BATCH_BENCHMARK_N = 100       # number of requests in the batch throughput test
BATCH_POLL_SECONDS = 30       # status poll interval while waiting for the job

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
              "batch_only": False, "error": None}
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


def submit_batch_job(endpoint, model, requests, poll=False, poll_seconds=60):
    """
    Run inference on a Global-Batch deployment (the ones that reject /chat/completions).
    `requests` is a list of dicts: {"custom_id": str, "messages": [...]}.
    Global Batch is asynchronous (target 24h turnaround, ~50% cheaper) so it is NOT
    comparable to real-time latency. This helper uploads a JSONL file and starts the job.
    """
    import io
    import json

    client = get_GPT5_client(endpoint)

    lines = []
    for req in requests:
        lines.append(json.dumps({
            "custom_id": req["custom_id"],
            "method": "POST",
            "url": "/chat/completions",
            "body": {
                "model": model,
                "messages": req["messages"],
                "max_completion_tokens": req.get("max_completion_tokens", MAX_COMPLETION_TOKENS),
            },
        }))
    jsonl_bytes = ("\n".join(lines)).encode("utf-8")

    batch_file = client.files.create(
        file=("batch_input.jsonl", io.BytesIO(jsonl_bytes)),
        purpose="batch",
    )
    batch_job = client.batches.create(
        input_file_id=batch_file.id,
        endpoint="/chat/completions",
        completion_window="24h",
    )
    print(f"submitted batch {batch_job.id} on {endpoint} ({model}), status={batch_job.status}")

    if poll:
        while batch_job.status not in ("completed", "failed", "canceled", "expired"):
            time.sleep(poll_seconds)
            batch_job = client.batches.retrieve(batch_job.id)
            print(f"  {batch_job.id}: {batch_job.status}")
    return batch_job


def benchmark_batch(endpoint, model, n=None, poll_seconds=None):
    """
    End-to-end speed test for a Global-Batch deployment: submit N identical text-only
    requests, wait until the job finishes, and report wall-clock time + throughput.
    This is a THROUGHPUT metric (not per-request latency) and can take minutes to hours,
    so it is off by default (RUN_BATCH_BENCHMARK). Poll granularity bounds the timing error.
    """
    import json

    n = n or BATCH_BENCHMARK_N
    poll_seconds = poll_seconds or BATCH_POLL_SECONDS

    requests = [
        {
            "custom_id": f"task-{i}",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT},
            ],
        }
        for i in range(n)
    ]

    t0 = time.perf_counter()
    job = submit_batch_job(endpoint, model, requests, poll=True, poll_seconds=poll_seconds)
    elapsed = time.perf_counter() - t0

    print("\n" + "=" * 88)
    print(f"BATCH THROUGHPUT  {endpoint} ({model})")
    print("=" * 88)
    print(f"final status       : {job.status}")
    print(f"requests submitted : {n}")
    print(f"wall-clock         : {elapsed:.0f}s  ({elapsed / 60:.1f} min)")

    if job.status != "completed":
        print("job did not complete; no throughput computed")
        return job

    # download output and tally completed requests + tokens
    client = get_GPT5_client(endpoint)
    completed = 0
    completion_tokens = 0
    if job.output_file_id:
        content = client.files.content(job.output_file_id).text
        for line in content.strip().split("\n"):
            if not line:
                continue
            obj = json.loads(line)
            body = (obj.get("response") or {}).get("body") or {}
            usage = body.get("usage") or {}
            completion_tokens += usage.get("completion_tokens", 0)
            completed += 1

    print(f"requests completed : {completed}")
    if elapsed > 0 and completed:
        print(f"throughput         : {completed / elapsed:.2f} req/s")
    if elapsed > 0 and completion_tokens:
        print(f"output throughput  : {completion_tokens / elapsed:.1f} tok/s")
    return job


if __name__ == "__main__":
    # Real-time (Global Standard) deployments to latency-benchmark.
    realtime_pairs = []
    for endpoint in ENDPOINTS:
        for model in REALTIME_MODELS:
            if model == "gpt-5.4-mini" and endpoint not in REALTIME_MINI_ENDPOINTS:
                continue  # no standard gpt-5.4-mini here; only the batch deployment exists
            realtime_pairs.append((endpoint, model))

    # Global-Batch deployments: one per endpoint, named BATCH_MODEL. Async, not timed here.
    batch_pairs = [(endpoint, BATCH_MODEL) for endpoint in ENDPOINTS]

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

    for endpoint, model in batch_pairs:
        results[(endpoint, model)] = {"ok": False, "latency": None, "tokens": None,
                                      "tok_per_s": None, "batch_only": True, "error": None}
        print(f"BATCH {endpoint:<38} {model:<20} (global-batch, async only)")

    ordered_pairs = realtime_pairs + batch_pairs

    # summary
    print("\n" + "=" * 92)
    print(f"SUMMARY  (text-only, reasoning_effort={REASONING_EFFORT}, "
          f"max_tokens={MAX_COMPLETION_TOKENS}, repeats={REPEATS})")
    print("=" * 92)
    print(f"{'endpoint':<38} {'model':<20} {'status':<8} {'avg latency':>12} {'tok/s':>8}")
    print("-" * 92)

    total = ok_count = 0
    for endpoint, model in ordered_pairs:
        r = results[(endpoint, model)]
        total += 1
        if r["ok"]:
            ok_count += 1
            status = "OK"
            latency = f"{r['latency']:.2f}s"
            tok_per_s = f"{r['tok_per_s']:.1f}" if r["tok_per_s"] else "-"
        else:
            status = "BATCH" if r["batch_only"] else "FAIL"
            latency = tok_per_s = "-"
        print(f"{endpoint:<38} {model:<20} {status:<8} {latency:>12} {tok_per_s:>8}")

    batch_only = sum(1 for r in results.values() if r["batch_only"])
    hard_fail = total - ok_count - batch_only
    print("-" * 92)
    print(f"working: {ok_count}/{total}   batch-only: {batch_only}/{total}   failed: {hard_fail}/{total}")

    # fastest working combos
    working = [(k, r) for k, r in results.items() if r["ok"]]
    if working:
        working.sort(key=lambda kv: kv[1]["latency"])
        print("\nFASTEST WORKING (by avg latency)")
        print("-" * 88)
        for (endpoint, model), r in working[:5]:
            print(f"{endpoint:<38} {model:<14} {r['latency']:.2f}s")

    # batch-only deployments (need the async Batch API, not /chat/completions)
    batch_list = [k for k, r in results.items() if r["batch_only"]]
    if batch_list:
        print("\nBATCH-ONLY DEPLOYMENTS  (use submit_batch_job(); async ~24h, ~50% cheaper)")
        print("-" * 88)
        for endpoint, model in batch_list:
            print(f"{endpoint} | {model}")

    # hard failures
    failures = [(k, r["error"]) for k, r in results.items()
                if not r["ok"] and not r["batch_only"]]
    if failures:
        print("\nFAILURE DETAILS")
        print("-" * 88)
        for (endpoint, model), error in failures:
            print(f"{endpoint} | {model}\n    {error}")

    # optional: end-to-end throughput test on one global-batch deployment
    if RUN_BATCH_BENCHMARK and batch_pairs:
        bench_endpoint, bench_model = batch_pairs[0]
        print(f"\nRunning batch throughput test on {bench_endpoint} "
              f"({bench_model}), N={BATCH_BENCHMARK_N} (blocks until the job finishes)...")
        benchmark_batch(bench_endpoint, bench_model)