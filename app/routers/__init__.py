from fastapi import APIRouter
from . import (
    admin, 
    core, 
    node, 
    subscription, 
    system, 
    user_template, 
    user,
    usage_continuity,
    usage_continuity_v2,
    dedicated_access,
    home,
)

api_router = APIRouter()

routers = [
    admin.router,
    core.router,
    node.router,
    subscription.router,
    system.router,
    user_template.router,
    user.router,
    usage_continuity.router,
    usage_continuity_v2.router,
    dedicated_access.router,
    home.router,
]

for router in routers:
    api_router.include_router(router)

__all__ = ["api_router"]
