from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import uuid4

import gradio as gr
from fastapi import FastAPI

from .schemas import RetrieveRequest

if TYPE_CHECKING:
    from .server import InterestRetrieverService


def parse_interest_input(value: str) -> list[str]:
    """Parse one complete interest per non-empty line without rewriting it."""
    interests = [line.strip() for line in str(value).splitlines() if line.strip()]
    if not interests:
        raise ValueError("provide at least one interest line")
    if len(interests) > 8:
        raise ValueError("at most 8 interest lines are allowed")
    return interests


def flatten_results(response: dict[str, Any]) -> list[list[Any]]:
    rows = []
    for interest_index, result in enumerate(response["results"], start=1):
        for item in result["items"]:
            rows.append(
                [
                    interest_index,
                    result["interest"],
                    result["target_hit"],
                    result["target_rank"],
                    item["rank"],
                    item.get("item_id"),
                    item["sid"],
                    item["title"],
                    round(float(item["score"]), 6),
                ]
            )
    return rows


def build_demo(service: "InterestRetrieverService") -> gr.Blocks:
    example_item = service.index.metadata[0]
    example_sid = example_item["sid"]
    example_title = example_item["title"]
    example_interests = (
        f"- [exploit] {example_sid} => Products related to {example_title}.\n"
        f"- [explore] {example_sid} => Adjacent gaming products for the same audience."
    )

    async def retrieve_interests(
        target_sid: str,
        interests_text: str,
        top_k: float,
    ) -> tuple[dict[str, Any], list[list[Any]]]:
        try:
            interests = parse_interest_input(interests_text)
            request = RetrieveRequest(
                request_id=f"gradio-{uuid4()}",
                target_sid=target_sid.strip(),
                interests=interests,
                top_k=int(top_k),
            )
            response = await service.retrieve(request)
        except (RuntimeError, ValueError) as error:
            raise gr.Error(str(error)) from error

        response_payload = response.model_dump()
        return response_payload, flatten_results(response_payload)

    with gr.Blocks(title="SIDReasoner Interest Retriever") as demo:
        gr.Markdown(
            "# SIDReasoner Interest Retriever\n"
            "Test whether any generated future-interest line retrieves the target SID."
        )
        with gr.Row():
            target_sid = gr.Textbox(
                value=example_sid,
                label="Target SID",
                info="Ground-truth three-token SID used only for Hit@K evaluation.",
            )
            top_k = gr.Slider(
                minimum=1,
                maximum=100,
                value=20,
                step=1,
                label="Top K",
            )
        interests_text = gr.Textbox(
            value=example_interests,
            lines=6,
            label="Future interests",
            info="One complete interest per non-empty line; lines are embedded unchanged.",
        )
        submit = gr.Button("Retrieve interests", variant="primary")
        response_json = gr.JSON(label="Block reward and per-interest response")
        result_table = gr.Dataframe(
            headers=[
                "interest_index",
                "interest",
                "target_hit",
                "target_rank",
                "rank",
                "item_id",
                "sid",
                "title",
                "score",
            ],
            datatype=["number", "str", "bool", "number", "number", "number", "str", "str", "number"],
            interactive=False,
            label="Retrieved catalog items",
        )
        submit.click(
            fn=retrieve_interests,
            inputs=[target_sid, interests_text, top_k],
            outputs=[response_json, result_table],
            api_name="retrieve_interests",
        )
        gr.Markdown(
            "Reward is 1 when any interest contains the target SID in its Top-K. "
            "A missed exploit or explore line receives no individual penalty."
        )
    return demo


def mount_gradio(
    app: FastAPI,
    service: "InterestRetrieverService",
    path: str = "/gradio",
) -> FastAPI:
    return gr.mount_gradio_app(app, build_demo(service), path=path)