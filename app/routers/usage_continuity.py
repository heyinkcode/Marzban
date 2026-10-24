"""Sudo-only, intentionally separate from normal user PUT/reset APIs."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.exc import OperationalError

from app.db import Session, get_db
from app.db import usage_continuity as accounting
from app.models.admin import Admin
from app.models.usage_continuity import RepairRequest

router = APIRouter(prefix="/api/usage-continuity/v1", tags=["Usage continuity"])


def _call(response, function, *args):
    response.headers["Cache-Control"] = "no-store"
    try:
        return function(*args)
    except accounting.RecoveryError as exc:
        raise HTTPException(exc.status, detail=exc.detail, headers={"Cache-Control": "no-store"}) from exc
    except OperationalError as exc:
        # Never expose SQL, credentials or DB paths in API errors.
        raise HTTPException(503, detail={"code": "database_busy"},
                            headers={"Cache-Control": "no-store"}) from exc


@router.get("/users/{username}/preview")
def preview(username: str, response: Response, db: Session = Depends(get_db),
            admin: Admin = Depends(Admin.check_sudo_admin)):
    return _call(response, accounting.preview, db, username)


@router.post("/users/{username}/repairs")
def apply(username: str, request: RepairRequest, response: Response,
          db: Session = Depends(get_db), admin: Admin = Depends(Admin.check_sudo_admin)):
    return _call(response, accounting.apply, db, username, request, admin.username)


@router.get("/repairs/{operation_id}")
def receipt(operation_id: UUID, response: Response, db: Session = Depends(get_db),
            admin: Admin = Depends(Admin.check_sudo_admin)):
    return _call(response, accounting.receipt, db, operation_id)
