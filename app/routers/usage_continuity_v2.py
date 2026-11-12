"""Separate v2 routes: original v1 history and reason remain unchanged."""
from uuid import UUID

from fastapi import APIRouter, Depends, Response

from app.db import Session, get_db
from app.db import usage_continuity as accounting
from app.models.admin import Admin
from app.models.usage_continuity_v2 import FirstPaidPeriodRepairRequest
from app.routers.usage_continuity import _call

router = APIRouter(prefix="/api/usage-continuity/v2", tags=["Usage continuity v2"])


@router.get("/users/{username}/preview")
def preview_first_paid_period(username: str, response: Response, db: Session = Depends(get_db),
                              admin: Admin = Depends(Admin.check_sudo_admin)):
    return _call(response, accounting.preview_first_paid_period, db, username)


@router.post("/users/{username}/repairs")
def repair_first_paid_period(username: str, request: FirstPaidPeriodRepairRequest, response: Response,
                             db: Session = Depends(get_db), admin: Admin = Depends(Admin.check_sudo_admin)):
    return _call(response, accounting.apply_first_paid_period, db, username, request, admin.username)


@router.get("/repairs/{operation_id}")
def receipt_first_paid_period(operation_id: UUID, response: Response, db: Session = Depends(get_db),
                              admin: Admin = Depends(Admin.check_sudo_admin)):
    return _call(response, accounting.receipt_first_paid_period, db, operation_id)
