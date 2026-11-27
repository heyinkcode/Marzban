"""Sudo-only contract for one recovered reset in a renewed allowance."""
from uuid import UUID

from fastapi import APIRouter, Depends, Response

from app.db import Session, get_db
from app.db import usage_continuity_paid_extension as service
from app.models.admin import Admin
from app.routers.usage_continuity import _call

router = APIRouter(prefix="/api/usage-continuity/paid-extension-v1", tags=["Paid extension usage continuity"])


@router.get("/users/{username}/preview")
def preview(username: str, response: Response, db: Session = Depends(get_db),
            admin: Admin = Depends(Admin.check_sudo_admin)):
    return _call(response, service.preview, db, username)


@router.post("/users/{username}/repairs")
def apply(username: str, request: service.PaidExtensionRequest, response: Response,
          db: Session = Depends(get_db), admin: Admin = Depends(Admin.check_sudo_admin)):
    return _call(response, service.apply, db, username, request, admin.username)


@router.get("/repairs/{operation_id}")
def receipt(operation_id: UUID, response: Response, db: Session = Depends(get_db),
            admin: Admin = Depends(Admin.check_sudo_admin)):
    return _call(response, service.receipt, db, operation_id)
