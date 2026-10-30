"""Generic website integration contract; no payments or order mutations."""
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class DedicatedAccessRequest(BaseModel):
    operation_id: str
    external_reference: Optional[str] = Field(None, min_length=1, max_length=128)
    model_config = ConfigDict(extra="forbid")

    @field_validator("operation_id")
    @classmethod
    def canonical_uuid(cls, value):
        if str(UUID(value)) != value:
            raise ValueError("Use a canonical lowercase UUID")
        return value


class NodeAccessRequest(BaseModel):
    access_mode: Literal["public", "restricted"]
    confirm_public_access: bool = False
    model_config = ConfigDict(extra="forbid")


class DedicatedAccessResult(BaseModel):
    node_id: int
    username: str
    granted: bool
    effective: bool
    sync_state: Literal["synced", "pending", "error"]
    policy_revision: int
    applied_revision: Optional[int] = None
    operation_id: Optional[str] = None
    requested_granted: Optional[bool] = None
    external_reference: Optional[str] = None
    detail: Optional[str] = None
