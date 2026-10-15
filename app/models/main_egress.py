"""Strict main-only API models; remote Node API semantics are unchanged."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.node import NodeEgressModify


class MainEgressModify(NodeEgressModify):
    port: int = Field(ge=1, le=65535, strict=True)
    model_config = ConfigDict(extra="forbid")


class MainEgressProbe(BaseModel):
    profile: MainEgressModify
    timeout_seconds: Literal[5, 10] = 5
    attempts: Literal[1, 3] = 1
    model_config = ConfigDict(extra="forbid")

    @field_validator("timeout_seconds", "attempts", mode="before")
    @classmethod
    def strict_integer(cls, value):
        if type(value) is not int:
            raise ValueError("Expected an integer diagnostic limit")
        return value
