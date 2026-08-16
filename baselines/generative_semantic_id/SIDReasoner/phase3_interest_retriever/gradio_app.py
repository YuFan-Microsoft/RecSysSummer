from __future__ import annotations

from typing import TYPE_CHECKING

import gradio as gr
from fastapi import FastAPI

from .schemas import RankRequest

if TYPE_CHECKING:
    from .server import InterestRetrieverService


def parse_interest_input(value: str) -> str:
    """Validate one pure-text interest without rewriting its content."""
    interest = str(value).strip()
    if not interest:
        raise ValueError("provide one non-empty interest")
    if "\n" in interest or "\r" in interest:
        raise ValueError("provide exactly one interest, without line breaks")
    return interest


def build_demo(service: "InterestRetrieverService") -> gr.Blocks:
    example_item = service.index.metadata[0]
    example_sid = example_item["sid"]
    example_title = example_item["title"]
    example_interest = f"Products related to {example_title}."

    async def rank_interest(
        target_sid: str,
        interest_text: str,
    ) -> int:
        try:
            request = RankRequest(
                target_sid=target_sid.strip(),
                interest=parse_interest_input(interest_text),
            )
            return await service.rank(request)
        except (RuntimeError, ValueError) as error:
            raise gr.Error(str(error)) from error

    with gr.Blocks(title="SIDReasoner Interest Retriever") as demo:
        gr.Markdown(
            "# SIDReasoner Interest Retriever\n"
            "Return the target SID's 1-based Top-100 rank for one pure-text interest. "
            "A miss returns -1."
        )
        target_sid = gr.Textbox(
            value=example_sid,
            label="Target SID",
            info="Ground-truth three-token SID.",
        )
        interest_text = gr.Textbox(
            value=example_interest,
            lines=2,
            label="Interest",
            info="Pure text after the first => delimiter; exactly one interest.",
        )
        submit = gr.Button("Get target rank", variant="primary")
        rank = gr.Number(label="Rank", precision=0)
        submit.click(
            fn=rank_interest,
            inputs=[target_sid, interest_text],
            outputs=rank,
            api_name="rank_interest",
        )
        gr.Markdown(
            "Rank is 1–100 when the target SID appears in Top-100; otherwise -1."
        )
    return demo


def mount_gradio(
    app: FastAPI,
    service: "InterestRetrieverService",
    path: str = "/gradio",
) -> FastAPI:
    demo = build_demo(service)
    service.gradio_share_token = demo.share_token
    return gr.mount_gradio_app(app, demo, path=path)