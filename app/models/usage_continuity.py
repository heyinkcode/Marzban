"""Versioned, credential-free accounting recovery contract (bytes are strings)."""
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, field_validator

CAPABILITY = "usage-continuity-repair-v1"
ByteCount = Annotated[StrictStr, Field(pattern=r"^(0|[1-9][0-9]{0,18})$")]
Digest = Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ResetSnapshot(ContractModel):
    id: StrictInt
    reset_at: StrictStr
    used_traffic_at_reset: ByteCount


class ExpectedSnapshot(ContractModel):
    user_id: StrictInt
    username: StrictStr
    created_at: StrictStr
    status: StrictStr
    data_limit: ByteCount | None
    expire: StrictInt | None
    reset_strategy: StrictStr
    device_limit: StrictInt
    device_limit_mode: StrictStr
    device_limit_action: StrictStr
    has_next_plan: bool = Field(strict=True)
    identity_seal: Digest
    history_sha256: Digest
    history_count: StrictInt
    initial_reset: ResetSnapshot | None
    latest_reset: ResetSnapshot | None
    observed_used_traffic: ByteCount
    observed_lifetime_used_traffic: ByteCount


class RepairRequest(ContractModel):
    operation_id: UUID
    reason: Literal["restore_single_monthly_reset"]
    evidence_sha256: Digest
    expected: ExpectedSnapshot

    @field_validator("operation_id", mode="before")
    @classmethod
    def canonical_uuid(cls, value):
        if not isinstance(value, str) or str(UUID(value)) != value:
            raise ValueError("operation_id must be a canonical lowercase UUID string")
        return value
