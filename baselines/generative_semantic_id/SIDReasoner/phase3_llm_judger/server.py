from __future__ import annotations

import argparse
import asyncio
from contextlib import asynccontextmanager
import json
import logging
import os
from pathlib import Path
import signal
import sys
import time
from typing import Any

import aiohttp
from fastapi import FastAPI, HTTPException
import uvicorn

from .prompts import build_messages
from .schemas import (
    CandidateJudgment,
    JudgeBatchRequest,
    JudgeBatchResponse,
    JudgeRequest,
    JudgeResponse,
    ModelJudgeOutput,
)


DEFAULT_MODEL_PATH = "/yufan/open_source_models/Qwen3_LLM/instruct_model/Qwen3-32B/"
MODEL_OUTPUT_SCHEMA = ModelJudgeOutput.model_json_schema()
logger = logging.getLogger(__name__)
TIER_REWARDS = {"high": 1.0, "medium": 0.5, "low": 0.0}


class JudgeService:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.backend_url = args.external_backend_url or f"http://{args.backend_host}:{args.backend_port}"
        self.backend_process: asyncio.subprocess.Process | None = None
        self.session: aiohttp.ClientSession | None = None
        self.semaphore = asyncio.Semaphore(args.max_concurrent_requests)
        self.gradio_share_token: str | None = None
        self.share_task: asyncio.Task[None] | None = None
        self.share_url: str | None = None

    async def start(self) -> None:
        if self.args.external_backend_url is None:
            await self._start_backend()
        timeout = aiohttp.ClientTimeout(total=self.args.request_timeout)
        self.session = aiohttp.ClientSession(timeout=timeout)
        await self._wait_for_backend()

    async def close(self) -> None:
        if self.share_task is not None:
            self.share_task.cancel()
            try:
                await self.share_task
            except asyncio.CancelledError:
                pass
            self.share_task = None
        if self.session is not None:
            await self.session.close()
            self.session = None
        if self.backend_process is not None and self.backend_process.returncode is None:
            self.backend_process.send_signal(signal.SIGTERM)
            try:
                await asyncio.wait_for(self.backend_process.wait(), timeout=30)
            except asyncio.TimeoutError:
                self.backend_process.kill()
                await self.backend_process.wait()

    async def start_share_tunnel(self) -> None:
        if not self.args.share or self.args.disable_gradio:
            return
        if self.gradio_share_token is None:
            logger.error("Gradio share requested before the UI was mounted")
            return
        if self.session is None:
            logger.error("Gradio share requested before the HTTP session was initialized")
            return

        local_gradio_url = f"http://127.0.0.1:{self.args.port}{self.args.gradio_path}/"
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            try:
                async with self.session.get(local_gradio_url) as response:
                    if response.status == 200:
                        break
            except (aiohttp.ClientError, asyncio.TimeoutError):
                pass
            await asyncio.sleep(0.25)
        else:
            logger.error("Gradio UI did not become reachable; share tunnel was not started")
            return

        try:
            from gradio import networking

            base_url = await asyncio.to_thread(
                networking.setup_tunnel,
                "127.0.0.1",
                self.args.port,
                self.gradio_share_token,
                None,
            )
        except Exception:
            logger.exception("Failed to establish the Gradio share tunnel")
            return

        self.share_url = base_url.rstrip("/")
        print(f"Gradio public UI: {self.share_url}{self.args.gradio_path}", flush=True)
        print(f"Public judge API: {self.share_url}/v1/judge", flush=True)

    async def _start_backend(self) -> None:
        if self.args.model.startswith("/") and not Path(self.args.model).is_dir():
            raise FileNotFoundError(f"local model directory does not exist: {self.args.model}")
        command = [
            sys.executable,
            "-m",
            "vllm.entrypoints.openai.api_server",
            "--model",
            self.args.model,
            "--served-model-name",
            self.args.served_model_name,
            "--host",
            self.args.backend_host,
            "--port",
            str(self.args.backend_port),
            "--tensor-parallel-size",
            str(self.args.tensor_parallel_size),
            "--dtype",
            self.args.dtype,
            "--gpu-memory-utilization",
            str(self.args.gpu_memory_utilization),
            "--max-model-len",
            str(self.args.max_model_len),
            "--max-num-seqs",
            str(self.args.max_num_seqs),
            "--enable-prefix-caching",
            "--trust-remote-code",
            "--disable-log-requests",
            "--generation-config",
            "vllm",
        ]
        environment = os.environ.copy()
        environment["CUDA_VISIBLE_DEVICES"] = self.args.cuda_visible_devices
        logger.info(
            "Starting vLLM backend model=%s address=%s:%d tensor_parallel_size=%d",
            self.args.model,
            self.args.backend_host,
            self.args.backend_port,
            self.args.tensor_parallel_size,
        )
        self.backend_process = await asyncio.create_subprocess_exec(
            *command,
            env=environment,
        )

    async def _wait_for_backend(self) -> None:
        deadline = time.monotonic() + self.args.backend_startup_timeout
        last_error = "backend has not responded"
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            while time.monotonic() < deadline:
                if self.backend_process is not None and self.backend_process.returncode is not None:
                    raise RuntimeError(
                        f"vLLM backend exited with code {self.backend_process.returncode}"
                    )
                try:
                    async with session.get(f"{self.backend_url}/health") as response:
                        if response.status == 200:
                            return
                        last_error = f"health returned HTTP {response.status}"
                except (aiohttp.ClientError, asyncio.TimeoutError) as error:
                    last_error = str(error)
                await asyncio.sleep(2)
        raise TimeoutError(
            f"vLLM backend was not ready after {self.args.backend_startup_timeout}s: {last_error}"
        )

    async def backend_healthy(self) -> bool:
        if self.session is None:
            return False
        try:
            async with self.session.get(f"{self.backend_url}/health") as response:
                return response.status == 200
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return False

    async def judge(self, request: JudgeRequest) -> JudgeResponse:
        async with self.semaphore:
            started_at = time.monotonic()
            output = await self._request_model(request)
            expected_ids = [candidate.candidate_id for candidate in request.candidates]
            tier_by_id = {
                candidate_id: tier
                for tier in ("high", "medium", "low")
                for candidate_id in getattr(output, tier)
            }
            if set(tier_by_id) != set(expected_ids) or len(tier_by_id) != len(expected_ids):
                raise ValueError("tiered candidate IDs do not exactly partition the request")

            judgments = []
            for candidate in request.candidates:
                tier = "low" if not candidate.hard_valid else tier_by_id[candidate.candidate_id]
                judgments.append(
                    CandidateJudgment(
                        candidate_id=candidate.candidate_id,
                        tier=tier,
                        normalized_reward=TIER_REWARDS[tier],
                    )
                )

            latency_ms = round((time.monotonic() - started_at) * 1000)
            return JudgeResponse(
                request_id=request.request_id,
                model=self.args.served_model_name,
                judgments=judgments,
                latency_ms=latency_ms,
            )

    async def _request_model(self, request: JudgeRequest) -> ModelJudgeOutput:
        if self.session is None:
            raise RuntimeError("judge service has not started")
        messages = build_messages(request)
        validation_issue = ""
        previous_content = ""
        for attempt in range(self.args.max_parse_attempts):
            request_messages = list(messages)
            if validation_issue:
                if previous_content:
                    request_messages.append({"role": "assistant", "content": previous_content})
                request_messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Your previous response violated the required JSON contract: "
                            f"{validation_issue}. Return a corrected complete JSON object."
                        ),
                    }
                )
            payload: dict[str, Any] = {
                "model": self.args.served_model_name,
                "messages": request_messages,
                "temperature": 0.0,
                "max_tokens": self.args.max_output_tokens,
                "chat_template_kwargs": {"enable_thinking": False},
                "guided_json": MODEL_OUTPUT_SCHEMA,
            }
            try:
                async with self.session.post(
                    f"{self.backend_url}/v1/chat/completions",
                    json=payload,
                ) as response:
                    body = await response.text()
                    if response.status != 200:
                        raise RuntimeError(f"vLLM returned HTTP {response.status}: {body[:1000]}")
                content = json.loads(body)["choices"][0]["message"]["content"]
                previous_content = content or ""
                parsed = ModelJudgeOutput.model_validate_json(_strip_json_fence(content))
                candidate_ids = parsed.high + parsed.medium + parsed.low
                expected_ids = [candidate.candidate_id for candidate in request.candidates]
                if len(candidate_ids) != len(set(candidate_ids)) or set(candidate_ids) != set(expected_ids):
                    raise ValueError("candidate IDs are missing, duplicated, or unexpected")
                return parsed
            except (KeyError, TypeError, json.JSONDecodeError, ValueError) as error:
                validation_issue = str(error)
                logger.warning(
                    "Judge parse attempt %d/%d failed for request_id=%s: %s",
                    attempt + 1,
                    self.args.max_parse_attempts,
                    request.request_id,
                    validation_issue,
                )
                if attempt + 1 == self.args.max_parse_attempts:
                    raise RuntimeError(
                        f"judge returned invalid structured output after {self.args.max_parse_attempts} attempts: "
                        f"{validation_issue}"
                    ) from error
        raise AssertionError("unreachable")


def _strip_json_fence(content: str) -> str:
    text = (content or "").strip()
    if text.startswith("```json"):
        text = text[len("```json") :]
    elif text.startswith("```"):
        text = text[len("```") :]
    if text.endswith("```"):
        text = text[: -len("```")]
    return text.strip()


def create_app(service: JudgeService) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        await service.start()
        if service.args.share and not service.args.disable_gradio:
            service.share_task = asyncio.create_task(service.start_share_tunnel())
        try:
            yield
        finally:
            await service.close()

    app = FastAPI(
        title="SIDReasoner Qwen3-32B Judge",
        version="1.0.0",
        lifespan=lifespan,
    )

    @app.get("/healthz")
    async def healthz() -> dict[str, Any]:
        healthy = await service.backend_healthy()
        if not healthy:
            raise HTTPException(status_code=503, detail="vLLM backend is unavailable")
        return {
            "status": "ok",
            "model": service.args.served_model_name,
            "tensor_parallel_size": service.args.tensor_parallel_size,
            "backend_url": service.backend_url,
        }

    @app.post("/v1/judge", response_model=JudgeResponse)
    async def judge(request: JudgeRequest) -> JudgeResponse:
        try:
            return await service.judge(request)
        except (RuntimeError, ValueError) as error:
            raise HTTPException(status_code=502, detail=str(error)) from error

    @app.post("/v1/judge/batch", response_model=JudgeBatchResponse)
    async def judge_batch(request: JudgeBatchRequest) -> JudgeBatchResponse:
        try:
            responses = await asyncio.gather(
                *(service.judge(group) for group in request.requests)
            )
        except (RuntimeError, ValueError) as error:
            raise HTTPException(status_code=502, detail=str(error)) from error
        return JudgeBatchResponse(responses=responses)

    return app


def create_serving_app(service: JudgeService) -> FastAPI:
    app = create_app(service)
    if service.args.disable_gradio:
        return app
    from .gradio_app import mount_gradio

    return mount_gradio(
        app,
        service,
        path=service.args.gradio_path,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve a target-aware Qwen3-32B Phase-3 judge on 8 GPUs.")
    parser.add_argument("--model", default=DEFAULT_MODEL_PATH)
    parser.add_argument("--served-model-name", default="qwen3-32b-phase3-judge")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8090)
    parser.add_argument("--backend-host", default="127.0.0.1")
    parser.add_argument("--backend-port", type=int, default=8091)
    parser.add_argument("--external-backend-url", default=None)
    parser.add_argument("--tensor-parallel-size", type=int, default=8)
    parser.add_argument("--cuda-visible-devices", default="0,1,2,3,4,5,6,7")
    parser.add_argument("--dtype", default="bfloat16")
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.90)
    parser.add_argument("--max-model-len", type=int, default=32768)
    parser.add_argument("--max-num-seqs", type=int, default=32)
    parser.add_argument("--max-output-tokens", type=int, default=512)
    parser.add_argument("--max-concurrent-requests", type=int, default=32)
    parser.add_argument("--max-parse-attempts", type=int, default=2)
    parser.add_argument("--backend-startup-timeout", type=int, default=1800)
    parser.add_argument("--request-timeout", type=int, default=600)
    parser.add_argument("--gradio-path", default="/gradio")
    parser.add_argument("--disable-gradio", action="store_true")
    parser.add_argument(
        "--share",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Expose the mounted Gradio UI and REST API through a gradio.live tunnel.",
    )
    args = parser.parse_args()
    if args.tensor_parallel_size < 1:
        parser.error("--tensor-parallel-size must be positive")
    if args.max_concurrent_requests < 1:
        parser.error("--max-concurrent-requests must be positive")
    if args.max_parse_attempts < 1:
        parser.error("--max-parse-attempts must be positive")
    return args


def main() -> None:
    args = parse_args()
    service = JudgeService(args)
    uvicorn.run(create_serving_app(service), host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()