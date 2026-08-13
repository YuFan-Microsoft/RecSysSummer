from __future__ import annotations

from typing import Annotated, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


SID_PATTERN = r"^<a_\d+><b_\d+><c_\d+>$"
MAX_REQUEST_CHARS = 100_000
CandidateId = Annotated[str, StringConstraints(min_length=1, max_length=128)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ItemMetadata(StrictModel):
    sid: str = Field(pattern=SID_PATTERN)
    title: str = Field(min_length=1, max_length=500)


class RolloutCandidate(StrictModel):
    candidate_id: CandidateId
    reasoning: str = Field(min_length=1, max_length=12000)
    predicted_item: ItemMetadata
    hard_valid: bool = True


class JudgeRequest(StrictModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=256)
    history: list[ItemMetadata] = Field(min_length=1, max_length=10)
    target: ItemMetadata
    candidates: list[RolloutCandidate] = Field(min_length=2, max_length=16)

    @model_validator(mode="after")
    def validate_candidate_ids(self) -> "JudgeRequest":
        candidate_ids = [candidate.candidate_id for candidate in self.candidates]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("candidate_id values must be unique within a request")
        total_chars = sum(len(item.sid) + len(item.title) for item in self.history)
        total_chars += len(self.target.sid) + len(self.target.title)
        total_chars += sum(
            len(candidate.reasoning)
            + len(candidate.predicted_item.sid)
            + len(candidate.predicted_item.title)
            for candidate in self.candidates
        )
        if total_chars > MAX_REQUEST_CHARS:
            raise ValueError(
                f"request contains {total_chars} text characters; maximum is {MAX_REQUEST_CHARS}"
            )
        return self


class JudgeBatchRequest(StrictModel):
    requests: list[JudgeRequest] = Field(min_length=1, max_length=64)


class ModelJudgeOutput(StrictModel):
    high: list[CandidateId] = Field(default_factory=list, max_length=16)
    medium: list[CandidateId] = Field(default_factory=list, max_length=16)
    low: list[CandidateId] = Field(default_factory=list, max_length=16)

    @model_validator(mode="after")
    def validate_partition_has_no_duplicates(self) -> "ModelJudgeOutput":
        candidate_ids = self.high + self.medium + self.low
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("candidate IDs must appear in exactly one tier")
        return self


class CandidateJudgment(StrictModel):
    candidate_id: CandidateId
    tier: Literal["high", "medium", "low"]
    normalized_reward: float = Field(ge=0.0, le=1.0)


class JudgeResponse(StrictModel):
    request_id: str
    model: str
    judgments: list[CandidateJudgment]
    latency_ms: int = Field(ge=0)


class JudgeBatchResponse(StrictModel):
    responses: list[JudgeResponse]