import logging
import os
from typing import Any, Optional
from uuid import uuid4

import json
import asyncio
import aiohttp

from .base_tool import BaseTool
from .schemas import OpenAIFunctionToolSchema, OpenAIFunctionSchema, OpenAIFunctionParametersSchema, OpenAIFunctionPropertySchema
from verl.utils.rollout_trace import rollout_trace_op

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("VERL_LOGGING_LEVEL", "WARN"))


class CRSItemRetrieveTool(BaseTool):
    """
    _tool_schema = OpenAIFunctionToolSchema.model_validate({
        "type": "function",
        "function": {
            "name": "retrieve_items",
            "description": "Retrieve the information of the most relevant items given a natural-language search query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The natural-language search query."
                    }
                },
                "required": ["query"]
            },
        }
    })


    A tool that calls the local ItemRetrieveAPI (/search) to fetch candidate items for a natural language query.

    Config keys (all optional):
    - service_url: str, default "http://127.0.0.1:8001/search"
    - timeout: int, default 300 (seconds)
    """

    def __init__(self, config: dict, tool_schema: OpenAIFunctionToolSchema):
        super().__init__(config, tool_schema)
        self._instance_dict = {}
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Create or reuse a shared aiohttp session."""
        # default total timeout; per-request can override
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=float(self.config.get("timeout", 300)))
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    def get_openai_tool_schema(self) -> OpenAIFunctionToolSchema:
        return self.tool_schema

    async def create(self, instance_id: Optional[str] = None, intention: Optional[str] = None, **kwargs) -> str:
        if instance_id is None:
            instance_id = str(uuid4())
        # Initialize per-instance defaults (stored in state, not as class members)
        self._instance_dict[instance_id] = {
            "query": "",
            "top_k": 10,  # hard-coded per requirement
            "result": None,
            "intention": intention,
            "service_url": self.config.get("service_url", "http://127.0.0.1:8001/search"),
            "timeout": int(self.config.get("timeout", 300)),
        }
        return instance_id

    @rollout_trace_op
    async def execute(self, instance_id: str, parameters: dict[str, Any], **kwargs) -> tuple[str, float, dict]:
        query = parameters.get("query", "")
        if not isinstance(query, str):
            query = str(query)
        self._instance_dict[instance_id]["query"] = query

        # Use per-instance fixed top_k by default; optionally accept override from parameters
        top_k = self._instance_dict[instance_id]["top_k"]
        # Call local API
        payload = {"query": query, "top_k": top_k}
        # Async request with retries
        data, status, error_msg = await self._request_items(instance_id, payload)

        # Prepare output
        if data and isinstance(data, dict):
            # Keep original JSON format string; do not parse/reshape content
            tool_text = json.dumps(data, ensure_ascii=False)
            self._instance_dict[instance_id]["result"] = tool_text
            items = data.get("items")
            tool_metrics = {
                "status_code": status,
                "top_k": top_k,
                "num_items": (len(items) if isinstance(items, list) else 0),
            }
        else:
            tool_text = error_msg or "No response. You may try again later."
            tool_metrics = {"status_code": status, "top_k": top_k, "error": error_msg}

        # No step penalty for this tool
        return tool_text, 0.0, tool_metrics

    async def calc_reward(self, instance_id: str, **kwargs) -> float:
        return 0.0

    async def release(self, instance_id: str, **kwargs) -> None:
        del self._instance_dict[instance_id]

    async def _request_items(self, instance_id: str, payload: dict) -> tuple[dict | None, int | None, str | None]:
        """POST to the item retrieve service asynchronously with retries.

        Returns (data, status, error_msg).
        """
        service_url = self._instance_dict[instance_id]['service_url']
        timeout_total = float(self._instance_dict[instance_id]['timeout'])

        session = await self._get_session()

        max_retries = 1
        retry_count = 0
        last_error: str | None = None

        while retry_count < max_retries:
            try:
                logger.info("Calling ItemRetrieveAPI asynchronously.")
                async with session.post(
                    service_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=timeout_total),
                ) as resp:
                    status = resp.status
                    # Raise for non-2xx
                    resp.raise_for_status()
                    # Try parse JSON
                    try:
                        data = await resp.json()
                        return data, status, None
                    except aiohttp.ContentTypeError:
                        text = await resp.text()
                        last_error = f"Invalid JSON response (status {status}): {text[:200]}"
                        logger.warning(last_error)
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_error = f"Request error: {e}"
                logger.warning(last_error)

            retry_count += 1
            await asyncio.sleep(0.1)

        return None, None, (last_error or "Failed after retries")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._session and not self._session.closed:
            await self._session.close()
