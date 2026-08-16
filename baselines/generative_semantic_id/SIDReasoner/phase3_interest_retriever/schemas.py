from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


SID_PATTERN = r"^<a_\d+><b_\d+><c_\d+>$"
InterestText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RankRequest(StrictModel):
    interest: InterestText
    target_sid: str = Field(pattern=SID_PATTERN)


class RankBatchRequest(StrictModel):
    requests: list[RankRequest] = Field(min_length=1, max_length=8192)


class RankResponse(StrictModel):
    rank: int = Field(ge=-1, le=100)

    @model_validator(mode="after")
    def validate_rank(self) -> "RankResponse":
        if self.rank == 0:
            raise ValueError("rank must be -1 or a 1-based Top-100 rank")
        return self


class RankBatchResponse(StrictModel):
    ranks: list[int] = Field(min_length=1, max_length=8192)

    @model_validator(mode="after")
    def validate_ranks(self) -> "RankBatchResponse":
        if any(rank < -1 or rank == 0 or rank > 100 for rank in self.ranks):
            raise ValueError("ranks must be -1 or a 1-based Top-100 rank")
        return self


__all__ = ["RankBatchRequest", "RankBatchResponse", "RankRequest", "RankResponse"]