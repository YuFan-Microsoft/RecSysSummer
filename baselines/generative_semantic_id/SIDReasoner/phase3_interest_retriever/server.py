from __future__ import annotations

import argparse
import asyncio
import time
from typing import Any

from fastapi import FastAPI, HTTPException
import uvicorn

from .embedder import Qwen3Embedder
from .index import InterestIndex
from .schemas import (
    InterestResult,
    RetrieveBatchRequest,
    RetrieveBatchResponse,
    RetrieveRequest,
    RetrieveResponse,
    RetrievedItem,
)


class InterestRetrieverService:
    def __init__(
        self,
        index: InterestIndex,
        embedder: Any,
        query_batch_size: int = 32,
        max_concurrent_requests: int = 1,
    ) -> None:
        self.index = index
        self.embedder = embedder
        self.query_batch_size = query_batch_size
        self.max_concurrent_requests = max_concurrent_requests
        self.semaphore: Any = None

    def _get_semaphore(self) -> asyncio.Semaphore:
        if self.semaphore is None:
            self.semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        return self.semaphore

    async def retrieve(self, request: RetrieveRequest) -> RetrieveResponse:
        if request.target_sid not in self.index.sid_to_rows:
            raise ValueError(f"target_sid is absent from the loaded catalog: {request.target_sid}")

        started_at = time.monotonic()
        async with self._get_semaphore():
            embeddings = await asyncio.to_thread(
                self.embedder.encode_queries,
                request.interests,
                self.index.query_instruction,
                self.query_batch_size,
            )
            retrieved = await asyncio.to_thread(self.index.search, embeddings, request.top_k)

        results = []
        for interest, items in zip(request.interests, retrieved):
            target_rank = next(
                (item["rank"] for item in items if item["sid"] == request.target_sid),
                None,
            )
            results.append(
                InterestResult(
                    interest=interest,
                    target_hit=target_rank is not None,
                    target_rank=target_rank,
                    items=[RetrievedItem.model_validate(item) for item in items],
                )
            )

        any_hit = any(result.target_hit for result in results)
        return RetrieveResponse(
            request_id=request.request_id,
            target_sid=request.target_sid,
            any_hit=any_hit,
            reward=float(any_hit),
            results=results,
            latency_ms=round((time.monotonic() - started_at) * 1000),
        )


def create_app(service: InterestRetrieverService) -> FastAPI:
    app = FastAPI(title="SIDReasoner Interest Retriever", version="1.0.0")

    @app.get("/healthz")
    async def healthz() -> dict[str, Any]:
        return {
            "status": "ok",
            "model": service.index.model_name_or_path,
            "category": service.index.manifest.get("category"),
            "item_count": len(service.index.metadata),
            "embedding_dim": service.index.embeddings.shape[1],
        }

    @app.post("/v1/retrieve", response_model=RetrieveResponse)
    async def retrieve(request: RetrieveRequest) -> RetrieveResponse:
        try:
            return await service.retrieve(request)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except RuntimeError as error:
            raise HTTPException(status_code=502, detail=str(error)) from error

    @app.post("/v1/retrieve/batch", response_model=RetrieveBatchResponse)
    async def retrieve_batch(request: RetrieveBatchRequest) -> RetrieveBatchResponse:
        try:
            responses = await asyncio.gather(
                *(service.retrieve(item) for item in request.requests)
            )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except RuntimeError as error:
            raise HTTPException(status_code=502, detail=str(error)) from error
        return RetrieveBatchResponse(responses=responses)

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
    parser.add_argument("--model", default=None, help="Override the model recorded in the index manifest.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8092)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--dtype", choices=("float32", "float16", "bfloat16"), default="bfloat16")
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--query-batch-size", type=int, default=32)
    parser.add_argument("--max-concurrent-requests", type=int, default=1)
    parser.add_argument("--use-flash-attention", action="store_true")
    parser.add_argument("--gradio-path", default="/gradio")
    parser.add_argument("--disable-gradio", action="store_true")
    args = parser.parse_args()
    if args.query_batch_size < 1:
        parser.error("--query-batch-size must be positive")
    if args.max_concurrent_requests < 1:
        parser.error("--max-concurrent-requests must be positive")
    return args


def main() -> None:
    args = parse_args()
    index = InterestIndex(args.index_dir)
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
    app = create_serving_app(
        service,
        gradio_path=args.gradio_path,
        disable_gradio=args.disable_gradio,
    )
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()