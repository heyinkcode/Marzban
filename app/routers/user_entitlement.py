"""Shared dashboard and API operations for a user's time and traffic."""
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Response

from app import xray
from app.db import GetDB, Session, crud, get_db
from app.db import user_entitlement as service
from app.db.usage_continuity import utc
from app.models.admin import Admin
from app.models.user import UserStatus
from app.models.user_entitlement import EntitlementApply, EntitlementCommand
from app.routers.usage_continuity import _call

router = APIRouter(prefix="/api/user/{username}/entitlement", tags=["User entitlement"])


def _sync_status(result):
    with GetDB() as db:
        user = crud.get_user(db, result["username"])
        if user is None or user.id != result["user_id"] or utc(user.created_at) != result["account_created_at"]:
            return
        if user.status in (UserStatus.active, UserStatus.on_hold):
            xray.operations.update_user(user)
        else:
            xray.operations.remove_user(user, device_emails=crud.get_user_device_account_emails(db, user.id))
        xray.operations.sync_all_node_device_policies()


@router.get("")
def overview(username: str, response: Response, db: Session = Depends(get_db),
             admin: Admin = Depends(Admin.get_current)):
    return _call(response, service.get_overview, db, username, admin)


@router.post("/preview")
def preview(username: str, command: EntitlementCommand, response: Response, db: Session = Depends(get_db),
            admin: Admin = Depends(Admin.get_current)):
    return _call(response, service.preview, db, username, command, admin)


@router.post("/operations")
def apply(username: str, request: EntitlementApply, response: Response, bg: BackgroundTasks,
          db: Session = Depends(get_db), admin: Admin = Depends(Admin.get_current)):
    result = _call(response, service.apply, db, username, request, admin)
    if result["before"]["status"] != result["after"]["status"]:
        bg.add_task(_sync_status, result)
    return result


@router.get("/operations/{operation_id}")
def receipt(username: str, operation_id: UUID, response: Response, db: Session = Depends(get_db),
            admin: Admin = Depends(Admin.get_current)):
    return _call(response, service.get_receipt, db, username, str(operation_id), admin)
