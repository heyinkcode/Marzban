from typing import Annotated, Literal

from pydantic import Field, StrictBool, StrictInt, StrictStr, model_validator

from app.models.usage_continuity import ByteCount, ContractModel, Digest

Epoch = Annotated[StrictInt, Field(gt=0, le=253402300799)]
Reason = Annotated[StrictStr, Field(min_length=5, max_length=240)]
OperationId = Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")]


class EntitlementCommand(ContractModel):
    action: Literal["extend", "add", "renew", "restore"]
    expires_at: Epoch | None = None
    extra_bytes: ByteCount | None = None
    reset_id: Annotated[StrictInt, Field(gt=0)] | None = None
    reason: Reason | None = None

    @model_validator(mode="after")
    def check_fields(self):
        fields = {
            "extend": ({"expires_at"}, {"expires_at"}),
            "add": ({"extra_bytes"}, {"extra_bytes"}),
            "renew": (set(), {"expires_at"}),
            "restore": ({"reset_id", "reason"}, {"reset_id", "reason"}),
        }
        required, allowed = fields[self.action]
        supplied = {k for k in ("expires_at", "extra_bytes", "reset_id", "reason") if getattr(self, k) is not None}
        if not required <= supplied <= allowed or self.reason is not None and len(self.reason.strip()) < 5:
            raise ValueError("Command fields do not match the action")
        return self


class SubscriptionPeriodCommand(ContractModel):
    action: Literal["attach_period", "adjust_period", "open_period"]
    period_id: OperationId
    starts_at: Epoch | None = None
    expires_at: Epoch | None = None
    quota_bytes: ByteCount | None = None
    extra_bytes: ByteCount | None = None

    @model_validator(mode="after")
    def validate_period_action(self):
        fields = {field for field in ("starts_at", "expires_at", "quota_bytes", "extra_bytes")
                  if getattr(self, field) is not None}
        if self.action == "attach_period":
            valid = fields == {"starts_at"} and self.starts_at is not None
        elif self.action == "open_period":
            valid = (fields == {"starts_at", "quota_bytes"} and self.starts_at is not None
                     and self.quota_bytes is not None and int(self.quota_bytes) > 0)
        else:
            valid = (bool(fields) and fields <= {"expires_at", "extra_bytes"}
                     and all(getattr(self, field) is not None for field in fields)
                     and (self.extra_bytes is None or int(self.extra_bytes) > 0))
        if not valid:
            raise ValueError("Period fields do not match the action")
        return self


EntitlementOperation = EntitlementCommand | SubscriptionPeriodCommand


class EntitlementApply(ContractModel):
    operation_id: OperationId
    guard: Digest
    command: EntitlementOperation
    confirmed: StrictBool = False
