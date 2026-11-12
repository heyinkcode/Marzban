"""Explicit, narrow first-paid-period proof; never reinterpret the v1 reason."""
from datetime import datetime, timezone
from typing import Literal

from pydantic import StrictStr, field_validator

from app.models.usage_continuity import ByteCount, ContractModel, RepairRequest

CAPABILITY = "usage-continuity-repair-v2"


def parse_utc(value):
    parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    if parsed.strftime("%Y-%m-%dT%H:%M:%S.%fZ") != value:
        raise ValueError("use canonical UTC with six fractional digits and Z")
    return parsed.replace(tzinfo=timezone.utc)


class PaidPeriodEvidence(ContractModel):
    starts_at: StrictStr
    ends_at: StrictStr
    last_observed_at: StrictStr
    last_observed_used_traffic: ByteCount

    @field_validator("starts_at", "ends_at", "last_observed_at")
    @classmethod
    def canonical_utc(cls, value):
        parse_utc(value)
        return value


class FirstPaidPeriodRepairRequest(RepairRequest):
    reason: Literal["restore_first_paid_period_reset"]
    paid_period_evidence: PaidPeriodEvidence
