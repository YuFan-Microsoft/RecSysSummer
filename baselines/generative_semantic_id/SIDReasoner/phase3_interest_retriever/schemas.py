from __future__ import annotations

from typing import Annotated, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


SID_PATTERN = r"^<a_\d+><b_\d+><c_\d+>$"
InterestText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RetrieveRequest(StrictModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=256)
    target_sid: str = Field(pattern=SID_PATTERN)
    interests: list[InterestText] = Field(min_length=1, max_length=8)
    top_k: int = Field(default=20, ge=1, le=1000)


class RetrieveBatchRequest(StrictModel):
    requests: list[RetrieveRequest] = Field(min_length=1, max_length=256)

    @model_validator(mode="after")
    def validate_request_ids(self) -> "RetrieveBatchRequest":
        request_ids = [request.request_id for request in self.requests]
        if len(request_ids) != len(set(request_ids)):
            raise ValueError("request_id values must be unique within a batch")
        return self


class RetrievedItem(StrictModel):
    item_id: Optional[int] = Field(default=None, ge=0)
    sid: str = Field(pattern=SID_PATTERN)
    title: str = Field(min_length=1, max_length=1000)
    score: float = Field(ge=-1.0, le=1.0)
    rank: int = Field(ge=1)


class InterestResult(StrictModel):
    interest: str
    target_hit: bool
    target_rank: Optional[int] = Field(default=None, ge=1)
    items: list[RetrievedItem]

    @model_validator(mode="after")
    def validate_target_rank(self) -> "InterestResult":
        if self.target_hit != (self.target_rank is not None):
            raise ValueError("target_rank must be present exactly when target_hit is true")
        return self


class RetrieveResponse(StrictModel):
    request_id: str
    target_sid: str = Field(pattern=SID_PATTERN)
    any_hit: bool
    reward: float = Field(ge=0.0, le=1.0)
    results: list[InterestResult]
    latency_ms: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_reward(self) -> "RetrieveResponse":
        expected_hit = any(result.target_hit for result in self.results)
        if self.any_hit != expected_hit:
            raise ValueError("any_hit must match the per-interest results")
        if self.reward != float(self.any_hit):
            raise ValueError("reward must be the binary any-interest Hit@K")
        return self


class RetrieveBatchResponse(StrictModel):
    responses: list[RetrieveResponse]