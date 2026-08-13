from __future__ import annotations

import asyncio
import json
import time
from typing import Any
from urllib import error, request

import aiohttp


class JudgeClient:
    def __init__(self, base_url: str, timeout: int = 600, max_attempts: int = 3):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_attempts = max_attempts

    def judge(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("/v1/judge", payload)

    def judge_batch(self, payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return self._post("/v1/judge/batch", {"requests": payloads})["responses"]

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        last_error: Exception | None = None
        for attempt in range(self.max_attempts):
            try:
                req = request.Request(self.base_url + path, data=body, headers=headers, method="POST")
                with request.urlopen(req, timeout=self.timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt + 1 < self.max_attempts:
                    time.sleep(min(2**attempt, 4))
        raise RuntimeError(f"judge request failed after {self.max_attempts} attempts: {last_error}") from last_error


class AsyncJudgeClient:
    def __init__(self, base_url: str, timeout: int = 600, max_attempts: int = 3):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_attempts = max_attempts
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> "AsyncJudgeClient":
        await self._get_session()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def judge(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._post("/v1/judge", payload)

    async def judge_batch(self, payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
        response = await self._post("/v1/judge/batch", {"requests": payloads})
        return response["responses"]

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        session = await self._get_session()
        last_error: Exception | None = None
        for attempt in range(self.max_attempts):
            try:
                async with session.post(self.base_url + path, json=payload) as response:
                    body = await response.text()
                    if response.status != 200:
                        raise RuntimeError(f"HTTP {response.status}: {body[:1000]}")
                    return json.loads(body)
            except (aiohttp.ClientError, asyncio.TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt + 1 < self.max_attempts:
                    await asyncio.sleep(min(2**attempt, 4))
        raise RuntimeError(f"judge request failed after {self.max_attempts} attempts: {last_error}") from last_error