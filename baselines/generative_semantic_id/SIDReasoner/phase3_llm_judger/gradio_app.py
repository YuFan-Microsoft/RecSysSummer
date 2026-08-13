from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import gradio as gr
from fastapi import FastAPI

from .schemas import JudgeRequest

if TYPE_CHECKING:
    from .server import JudgeService


EXAMPLE_REQUEST = {
    "request_id": "manual-test-001",
    "history": [
        {
            "sid": "<a_1><b_2><c_3>",
            "title": "Fallout 4 - PlayStation 4",
        }
    ],
    "target": {
        "sid": "<a_4><b_5><c_6>",
        "title": "The Forest - PlayStation 4",
    },
    "candidates": [
        {
            "candidate_id": "0",
            "reasoning": (
                "<history_summary>\n- <a_1><b_2><c_3> => The item includes gathering and crafting.\n"
                "</history_summary>\n<future_interests>\n"
                "- [exploit] <a_1><b_2><c_3> => More open-world action games with crafting.\n"
                "- [explore] <a_1><b_2><c_3> => Survival-building games, bridged by resource gathering.\n"
                "</future_interests>"
            ),
            "predicted_item": {
                "sid": "<a_7><b_8><c_9>",
                "title": "ARK: Survival Evolved - PlayStation 4",
            },
            "hard_valid": True,
        },
        {
            "candidate_id": "1",
            "reasoning": (
                "<history_summary>\n- <a_1><b_2><c_3> => The item is on a game platform.\n"
                "</history_summary>\n<future_interests>\n"
                "- [exploit] <a_1><b_2><c_3> => More games.\n"
                "- [explore] <a_1><b_2><c_3> => Other products from the same brand.\n"
                "</future_interests>"
            ),
            "predicted_item": {
                "sid": "<a_10><b_11><c_12>",
                "title": "DualShock 4 Wireless Controller",
            },
            "hard_valid": True,
        },
    ],
}


def _load_checkpoint_cases() -> dict[str, str]:
    root = Path(__file__).with_name("test_data")
    cases = {}
    for path in sorted(root.glob("record_*.json")):
        cases[path.stem] = path.read_text(encoding="utf-8")
    return cases


def build_demo(service: "JudgeService") -> gr.Blocks:
    checkpoint_cases = _load_checkpoint_cases()

    def load_case(case_name: str) -> str:
        if case_name not in checkpoint_cases:
            raise gr.Error(f"Unknown checkpoint case: {case_name}")
        return checkpoint_cases[case_name]

    async def judge_group(payload: str) -> dict[str, Any]:
        try:
            request_payload = json.loads(payload)
        except json.JSONDecodeError as error:
            raise gr.Error(f"Invalid JSON: {error}") from error
        try:
            judge_request = JudgeRequest.model_validate(request_payload)
            response = await service.judge(judge_request)
        except (RuntimeError, ValueError) as error:
            raise gr.Error(str(error)) from error
        return response.model_dump()

    with gr.Blocks(title="SIDReasoner Qwen3-32B Judge") as demo:
        gr.Markdown(
            "# SIDReasoner Qwen3-32B Judge\n"
            "Target-aware listwise scoring for one Phase-3 rollout group. "
            "Edit the JSON, then compare the candidate utility rewards."
        )
        if checkpoint_cases:
            with gr.Row():
                case_selector = gr.Dropdown(
                    choices=list(checkpoint_cases),
                    value=next(iter(checkpoint_cases)),
                    label="Checkpoint test case",
                )
                load_button = gr.Button("Load checkpoint case")
        with gr.Row():
            request_json = gr.Code(
                value=json.dumps(EXAMPLE_REQUEST, ensure_ascii=False, indent=2),
                language="json",
                label="Judge request",
            )
            response_json = gr.JSON(label="Judge response")
        submit = gr.Button("Judge rollout group", variant="primary")
        if checkpoint_cases:
            load_button.click(
                fn=load_case,
                inputs=case_selector,
                outputs=request_json,
            )
        submit.click(
            fn=judge_group,
            inputs=request_json,
            outputs=response_json,
            api_name="judge_group",
        )
        gr.Markdown(
            "Scores are target-aware. Shared SID numbers carry no semantic meaning; "
            "the judge must use item titles, reasoning, and predicted-item titles."
        )
    return demo


def mount_gradio(
    app: FastAPI,
    service: "JudgeService",
    path: str = "/gradio",
) -> FastAPI:
    demo = build_demo(service)
    service.gradio_share_token = demo.share_token
    return gr.mount_gradio_app(app, demo, path=path)