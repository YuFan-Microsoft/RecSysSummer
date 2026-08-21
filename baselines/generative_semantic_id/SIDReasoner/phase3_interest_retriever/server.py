from __future__ import annotations

import argparse
import asyncio
from contextlib import asynccontextmanager
import logging
import time
from typing import Any

import aiohttp
from fastapi import FastAPI, HTTPException
import uvicorn

from .embedder import (
    DEFAULT_QUERY_MAX_LENGTH,
    SUPPORTED_DOMAINS,
    Qwen3Embedder,
    query_instruction_for_domain,
)
from .index import InterestIndex
from .schemas import (
    RankBatchRequest,
    RankBatchResponse,
    RankRequest,
    RankResponse,
)


logger = logging.getLogger(__name__)


class InterestRetrieverService:
    def __init__(
        self,
        index: InterestIndex,
        embedder: Any,
        query_batch_size: int = 128,
        max_concurrent_requests: int = 1,
    ) -> None:
        self.index = index
        self.embedder = embedder
        self.query_batch_size = query_batch_size
        self.max_concurrent_requests = max_concurrent_requests
        self.semaphore: Any = None
        self.share_enabled = False
        self.server_port = 8092
        self.gradio_path = "/gradio"
        self.request_timeout = 60
        self.gradio_share_token: Any = None
        self.share_task: Any = None
        self.share_url: Any = None

    def configure_public_share(
        self,
        enabled: bool,
        server_port: int,
        gradio_path: str,
        request_timeout: int,
    ) -> None:
        self.share_enabled = enabled
        self.server_port = server_port
        self.gradio_path = gradio_path
        self.request_timeout = request_timeout

    async def close(self) -> None:
        if self.share_task is not None:
            self.share_task.cancel()
            try:
                await self.share_task
            except asyncio.CancelledError:
                pass
            self.share_task = None

    async def start_share_tunnel(self) -> None:
        if not self.share_enabled:
            return
        if self.gradio_share_token is None:
            raise RuntimeError("Gradio share requested before the UI was mounted")

        local_gradio_url = (
            f"http://127.0.0.1:{self.server_port}{self.gradio_path}/"
        )
        timeout = aiohttp.ClientTimeout(total=self.request_timeout)
        deadline = time.monotonic() + 60
        async with aiohttp.ClientSession(timeout=timeout) as session:
            while time.monotonic() < deadline:
                try:
                    async with session.get(local_gradio_url) as response:
                        if response.status == 200:
                            break
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    pass
                await asyncio.sleep(0.25)
            else:
                raise RuntimeError("Gradio UI did not become reachable for public sharing")

        from gradio import networking

        base_url = await asyncio.to_thread(
            networking.setup_tunnel,
            "127.0.0.1",
            self.server_port,
            self.gradio_share_token,
            None,
        )
        self.share_url = base_url.rstrip("/")
        print(f"Public Gradio UI: {self.share_url}{self.gradio_path}", flush=True)
        print(f"Public rank API: {self.share_url}/v1/rank", flush=True)
        print(f"Public batch rank API: {self.share_url}/v1/rank/batch", flush=True)

    def _get_semaphore(self) -> asyncio.Semaphore:
        if self.semaphore is None:
            self.semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        return self.semaphore

    def _validate_target_sids(self, target_sids: list[str]) -> None:
        missing = sorted(set(target_sids) - set(self.index.sid_to_rows))
        if missing:
            raise ValueError(
                f"target_sid is absent from the loaded catalog: {missing[0]}"
            )

    async def rank_many(self, requests: list[RankRequest]) -> list[int]:
        self._validate_target_sids([request.target_sid for request in requests])
        unique_interests = list(dict.fromkeys(request.interest for request in requests))
        async with self._get_semaphore():
            embeddings = await asyncio.to_thread(
                self.embedder.encode_queries,
                unique_interests,
                self.index.query_instruction,
                self.query_batch_size,
            )
            retrieved = await asyncio.to_thread(self.index.search, embeddings, 100)

        if len(retrieved) != len(unique_interests):
            raise RuntimeError("retrieval result count does not match unique interests")
        items_by_interest = dict(zip(unique_interests, retrieved))
        return [
            next(
                (
                    item["rank"]
                    for item in items_by_interest[request.interest]
                    if item["sid"] == request.target_sid
                ),
                -1,
            )
            for request in requests
        ]

    async def rank(self, request: RankRequest) -> int:
        return (await self.rank_many([request]))[0]

def create_app(service: InterestRetrieverService) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if service.share_enabled:
            service.share_task = asyncio.create_task(service.start_share_tunnel())
        try:
            yield
        finally:
            await service.close()

    app = FastAPI(
        title="SIDReasoner Interest Retriever",
        version="1.0.0",
        lifespan=lifespan,
    )

    @app.get("/healthz")
    async def healthz() -> dict[str, Any]:
        return {
            "status": "ok",
            "model": service.index.model_name_or_path,
            "category": service.index.manifest.get("category"),
            "item_count": len(service.index.metadata),
            "embedding_dim": service.index.embeddings.shape[1],
        }

    @app.post("/v1/rank", response_model=RankResponse)
    async def rank(request: RankRequest) -> RankResponse:
        try:
            return RankResponse(rank=await service.rank(request))
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except RuntimeError as error:
            raise HTTPException(status_code=502, detail=str(error)) from error

    @app.post("/v1/rank/batch", response_model=RankBatchResponse)
    async def rank_batch(request: RankBatchRequest) -> RankBatchResponse:
        try:
            return RankBatchResponse(ranks=await service.rank_many(request.requests))
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except RuntimeError as error:
            raise HTTPException(status_code=502, detail=str(error)) from error

    return app


def create_serving_app(
    service: InterestRetrieverService,
    gradio_path: str = "/gradio",
    disable_gradio: bool = False,
) -> FastAPI:
    app = create_app(service)
    if disable_gradio:
        return app
    from .gradio_app import mount_gradio

    return mount_gradio(app, service, path=gradio_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve Qwen3 interest-to-item retrieval.")
    parser.add_argument("--index-dir", required=True)
    parser.add_argument(
        "--domain",
        choices=SUPPORTED_DOMAINS,
        default=None,
        help="Optionally require the loaded index to match this domain.",
    )
    parser.add_argument("--model", default=None, help="Override the model recorded in the index manifest.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8092)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--dtype", choices=("float32", "float16", "bfloat16"), default="float16")
    parser.add_argument("--max-length", type=int, default=DEFAULT_QUERY_MAX_LENGTH)
    parser.add_argument("--query-batch-size", type=int, default=128)
    parser.add_argument("--max-concurrent-requests", type=int, default=1)
    parser.add_argument("--use-flash-attention", action="store_true")
    parser.add_argument("--gradio-path", default="/gradio")
    parser.add_argument("--disable-gradio", action="store_true")
    parser.add_argument("--request-timeout", type=int, default=60)
    parser.add_argument(
        "--share",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Expose the mounted Gradio UI and rank REST APIs through gradio.live.",
    )
    args = parser.parse_args()
    if args.query_batch_size < 1:
        parser.error("--query-batch-size must be positive")
    if args.max_concurrent_requests < 1:
        parser.error("--max-concurrent-requests must be positive")
    if args.request_timeout < 1:
        parser.error("--request-timeout must be positive")
    if args.share and args.disable_gradio:
        parser.error("--share requires the Gradio UI; remove --disable-gradio")
    return args


def validate_query_runtime(index: InterestIndex, args: argparse.Namespace) -> None:
    category = str(index.manifest.get("category", ""))
    requested_domain = getattr(args, "domain", None)
    if requested_domain is not None and category != requested_domain:
        raise ValueError(
            f"loaded index domain {category!r} does not match requested domain "
            f"{requested_domain!r}"
        )
    expected_instruction = query_instruction_for_domain(category)
    if index.query_instruction != expected_instruction:
        raise ValueError(
            f"index query instruction does not match the validated {category} instruction; "
            "rebuild the index"
        )
    expected_dtype = index.manifest.get("dtype")
    if expected_dtype is not None and args.dtype != expected_dtype:
        raise ValueError(
            f"query dtype {args.dtype} does not match index dtype {expected_dtype}"
        )
    expected_query_max_length = index.manifest.get("query_max_length")
    if (
        expected_query_max_length is not None
        and args.max_length != expected_query_max_length
    ):
        raise ValueError(
            "query max length does not match index manifest: "
            f"{args.max_length} != {expected_query_max_length}"
        )
    expected_attention = index.manifest.get("attention_backend")
    actual_attention = "flash_attention_2" if args.use_flash_attention else "transformers_default"
    if expected_attention is not None and actual_attention != expected_attention:
        raise ValueError(
            f"query attention backend {actual_attention} does not match index {expected_attention}"
        )


def main() -> None:
    args = parse_args()
    index = InterestIndex(args.index_dir)
    validate_query_runtime(index, args)
    embedder = Qwen3Embedder(
        model_name_or_path=args.model or index.model_name_or_path,
        device=args.device,
        dtype=args.dtype,
        max_length=args.max_length,
        use_flash_attention=args.use_flash_attention,
    )
    service = InterestRetrieverService(
        index=index,
        embedder=embedder,
        query_batch_size=args.query_batch_size,
        max_concurrent_requests=args.max_concurrent_requests,
    )
    service.configure_public_share(
        enabled=args.share,
        server_port=args.port,
        gradio_path=args.gradio_path,
        request_timeout=args.request_timeout,
    )
    app = create_serving_app(
        service,
        gradio_path=args.gradio_path,
        disable_gradio=args.disable_gradio,
    )
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()