from typing import Annotated, Literal

from pydantic import Field, StrictBool, StrictInt, StrictStr, model_validator

from app.models.usage_continuity import ByteCount, ContractModel, Digest

Epoch = Annotated[StrictInt, Field(gt=0, le=253402300799)]
Reason = Annotated[StrictStr, Field(min_length=5, max_length=240)]


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


class EntitlementApply(ContractModel):
    operation_id: Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")]
    guard: Digest
    command: EntitlementCommand
    confirmed: StrictBool = False
