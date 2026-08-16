from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Optional
from urllib import error, request

import aiohttp


def normalize_service_base_url(endpoint: str) -> str:
    base_url = endpoint.rstrip("/")
    for suffix in ("/v1/rank/batch", "/v1/rank"):
        if base_url.endswith(suffix):
            return base_url[: -len(suffix)]
    return base_url


class InterestRetrieverClient:
    def __init__(self, base_url: str, timeout: int = 60, max_attempts: int = 3):
        self.base_url = normalize_service_base_url(base_url)
        self.timeout = timeout
        self.max_attempts = max_attempts

    def rank(self, interest: str, target_sid: str) -> int:
        return int(
            self._post(
                "/v1/rank",
                {"interest": interest, "target_sid": target_sid},
            )["rank"]
        )

    def rank_batch(self, payloads: list[dict[str, str]]) -> list[int]:
        response = self._post("/v1/rank/batch", {"requests": payloads})
        return [int(rank) for rank in response["ranks"]]

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        last_error: Optional[Exception] = None
        for attempt in range(self.max_attempts):
            try:
                req = request.Request(self.base_url + path, data=body, headers=headers, method="POST")
                with request.urlopen(req, timeout=self.timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt + 1 < self.max_attempts:
                    time.sleep(min(2**attempt, 4))
        raise RuntimeError(
            f"retrieval request failed after {self.max_attempts} attempts: {last_error}"
        ) from last_error


class AsyncInterestRetrieverClient:
    def __init__(self, base_url: str, timeout: int = 60, max_attempts: int = 3):
        self.base_url = normalize_service_base_url(base_url)
        self.timeout = timeout
        self.max_attempts = max_attempts
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "AsyncInterestRetrieverClient":
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
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self._session

    async def rank(self, interest: str, target_sid: str) -> int:
        response = await self._post(
            "/v1/rank",
            {"interest": interest, "target_sid": target_sid},
        )
        return int(response["rank"])

    async def rank_batch(self, payloads: list[dict[str, str]]) -> list[int]:
        response = await self._post("/v1/rank/batch", {"requests": payloads})
        return [int(rank) for rank in response["ranks"]]

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        session = await self._get_session()
        last_error: Optional[Exception] = None
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
        raise RuntimeError(
            f"retrieval request failed after {self.max_attempts} attempts: {last_error}"
        ) from last_error