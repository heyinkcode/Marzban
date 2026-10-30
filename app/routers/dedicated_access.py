"""Authenticated generic integration endpoints; never accept payment claims."""
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from app.db import get_db
from app.db.models import Admin as DBAdmin, DedicatedNodeAdmin, DedicatedNodeOperation, Node
from app.db import dedicated_access as service
from app.models.admin import Admin
from app.models.dedicated_access import DedicatedAccessRequest, DedicatedAccessResult, NodeAccessRequest

class SafeAccessRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()
        async def handler(request):
            try:
                return await original(request)
            except RequestValidationError:
                # Pydantic's default response echoes invalid input (which may
                # accidentally contain a site's secret). Never return it here.
                return JSONResponse(status_code=422, content={"detail": {"code": "INVALID_DEDICATED_ACCESS_REQUEST"}},
                                    headers={"Cache-Control": "no-store"})
            except HTTPException as exc:
                exc.headers = {**(exc.headers or {}), "Cache-Control": "no-store"}
                raise
        return handler


router = APIRouter(prefix="/api", tags=["Dedicated Node access"], route_class=SafeAccessRoute)


def no_store(response: Response):
    response.headers["Cache-Control"] = "no-store"


def call(db, action):
    try:
        return action()
    except service.AccessError as exc:
        db.rollback()
        raise HTTPException(exc.status, detail={"code": exc.code}, headers={"Cache-Control": "no-store"}) from None
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, detail={"code": "DEDICATED_ACCESS_UNAVAILABLE"}, headers={"Cache-Control": "no-store"}) from None
    except Exception:
        db.rollback()
        # No transport/decryption/DB details or proxy credentials in responses.
        raise HTTPException(503, detail={"code": "DEDICATED_ACCESS_UNAVAILABLE"}, headers={"Cache-Control": "no-store"}) from None


@router.get("/dedicated-nodes")
def catalog(response: Response, db=Depends(get_db), actor=Depends(Admin.get_current)):
    """Safe catalog for a website backend. No addresses, ports or credentials."""
    no_store(response)
    return call(db, lambda: service.catalog(db, actor))


@router.get("/user/{username}/dedicated-nodes")
def user_access(username: str, response: Response, db=Depends(get_db), actor=Depends(Admin.get_current)):
    no_store(response)
    def action():
        service.authorized_user(db, actor, username)
        return {"capability": service.CAPABILITY, "nodes": [
            service.state(db, actor, username, node.id)
            for node in db.query(Node).filter(Node.access_mode == "restricted").order_by(Node.id)
            if service.can_allocate(db, actor, node.id)]}
    return call(db, action)


@router.get("/user/{username}/dedicated-nodes/{node_id}", response_model=DedicatedAccessResult)
def node_access(username: str, node_id: int, response: Response, db=Depends(get_db), actor=Depends(Admin.get_current)):
    no_store(response)
    return call(db, lambda: service.state(db, actor, username, node_id))


def mutate(username, node_id, request, granted, response, db, actor):
    from app import xray
    from app.xray.node_access import reconcile
    def action():
        # Same lock as reconnect/egress/credential reconciliation. Standard
        # deployment uses one active panel worker per Node, as relay does.
        with xray.operations.node_lifecycle_lock(node_id):
            operation, replay = service.change_grant(db, actor, username, node_id, request, granted)
            # Replay reads the original acceptance, never reapplies its old grant.
            # Reconciliation always loads the latest authoritative policy.
            reconcile(node_id)
            db.expire_all()
            result = service.state(db, actor, username, node_id, operation)
            response.status_code = 200 if result["sync_state"] == "synced" else 202
            return result
    return call(db, action)


@router.put("/user/{username}/dedicated-nodes/{node_id}", response_model=DedicatedAccessResult)
def grant(username: str, node_id: int, request: DedicatedAccessRequest, response: Response,
          db=Depends(get_db), actor=Depends(Admin.get_current)):
    no_store(response)
    return mutate(username, node_id, request, True, response, db, actor)


@router.delete("/user/{username}/dedicated-nodes/{node_id}", response_model=DedicatedAccessResult)
def revoke(username: str, node_id: int, request: DedicatedAccessRequest, response: Response,
           db=Depends(get_db), actor=Depends(Admin.get_current)):
    """DELETE body carries operation_id, exactly as grant does."""
    no_store(response)
    return mutate(username, node_id, request, False, response, db, actor)


@router.get("/dedicated-node-operations/{operation_id}", response_model=DedicatedAccessResult)
def operation(operation_id: str, response: Response, db=Depends(get_db), actor=Depends(Admin.get_current)):
    no_store(response)
    def action():
        row = db.get(DedicatedNodeOperation, operation_id)
        if row is None:
            raise service.AccessError("OPERATION_NOT_FOUND", 404)
        # Restrict receipts by current ownership and allocation, not just UUID.
        user = service.authorized_user(db, actor, row.username)
        if user.id != row.user_id or user.created_at != row.user_created_at:
            raise service.AccessError("USER_IDENTITY_CHANGED")
        return service.state(db, actor, row.username, row.node_id, row)
    return call(db, action)


@router.get("/node/{node_id}/access")
def get_policy(node_id: int, response: Response, db=Depends(get_db), actor=Depends(Admin.check_sudo_admin)):
    no_store(response)
    from app.xray.node_access import runtime_state
    def action():
        node = service.authorized_node(db, actor, node_id)
        return {"node_id": node.id, "access_mode": node.access_mode, **runtime_state(node)}
    return call(db, action)


@router.put("/node/{node_id}/access")
def set_policy(node_id: int, request: NodeAccessRequest, response: Response,
               db=Depends(get_db), actor=Depends(Admin.check_sudo_admin)):
    no_store(response)
    from app import xray
    from app.xray.node_access import reconcile, runtime_state
    def action():
        with xray.operations.node_lifecycle_lock(node_id):
            node = service.authorized_node(db, actor, node_id)
            if node.access_mode != request.access_mode:
                try:
                    service.validate_distinct_core(db, node.address, request.access_mode, node.id)
                except ValueError:
                    raise service.AccessError("DEDICATED_NODE_REQUIRES_DISTINCT_CORE") from None
                if request.access_mode == "public" and not request.confirm_public_access:
                    raise service.AccessError("CONFIRM_PUBLIC_ACCESS_REQUIRED")
                if request.access_mode == "restricted":
                    from app.db.models import NodeRelay
                    if db.query(NodeRelay).filter(NodeRelay.source_node_id == node_id).first() is not None:
                        raise service.AccessError("REMOVE_SHARED_RELAYS_BEFORE_RESTRICTING")
                # Do not label a previously public, unreachable core as protected.
                live = xray.nodes.get(node_id)
                if request.access_mode == "restricted" and (live is None or not live.connected or not live.started):
                    raise service.AccessError("CONNECT_PUBLIC_NODE_BEFORE_RESTRICTING")
                node.access_mode = request.access_mode
                node.access_revision += 1
                if live is not None:
                    live.access_mode = request.access_mode
                db.commit()
            reconcile(node_id)
            db.refresh(node)
            result = {"node_id": node.id, "access_mode": node.access_mode, **runtime_state(node)}
            response.status_code = 200 if result["sync_state"] == "synced" else 202
            return result
    return call(db, action)


@router.get("/admin/{username}/dedicated-nodes")
def admin_nodes(username: str, response: Response, db=Depends(get_db), actor=Depends(Admin.check_sudo_admin)):
    no_store(response)
    def action():
        admin = db.query(DBAdmin).filter(DBAdmin.username == username).first()
        if admin is None:
            raise service.AccessError("ADMIN_NOT_FOUND", 404)
        return {"username": username, "node_ids": [row.node_id for row in db.query(DedicatedNodeAdmin).filter_by(admin_id=admin.id)]}
    return call(db, action)


def set_admin_node(username, node_id, allowed, response, db, actor):
    no_store(response)
    def action():
        node = service.authorized_node(db, actor, node_id)
        if node.access_mode != "restricted":
            raise service.AccessError("NODE_IS_NOT_DEDICATED")
        admin = db.query(DBAdmin).filter(DBAdmin.username == username).first()
        if admin is None:
            raise service.AccessError("ADMIN_NOT_FOUND", 404)
        row = db.get(DedicatedNodeAdmin, (node_id, admin.id))
        if allowed and row is None:
            db.add(DedicatedNodeAdmin(node_id=node_id, admin_id=admin.id))
        elif not allowed and row is not None:
            db.delete(row)
        db.commit()
        return {"username": username, "node_id": node_id, "can_allocate": allowed}
    return call(db, action)


@router.put("/admin/{username}/dedicated-nodes/{node_id}")
def allow_admin(username: str, node_id: int, response: Response,
                db=Depends(get_db), actor=Depends(Admin.check_sudo_admin)):
    return set_admin_node(username, node_id, True, response, db, actor)


@router.delete("/admin/{username}/dedicated-nodes/{node_id}")
def deny_admin(username: str, node_id: int, response: Response,
               db=Depends(get_db), actor=Depends(Admin.check_sudo_admin)):
    return set_admin_node(username, node_id, False, response, db, actor)
