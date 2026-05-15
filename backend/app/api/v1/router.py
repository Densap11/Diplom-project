from fastapi import APIRouter

from app.api.v1.audit_logs import router as audit_logs_router
from app.api.v1.auth import router as auth_router
from app.api.v1.categories import router as categories_router
from app.api.v1.event_comments import router as event_comments_router
from app.api.v1.event_tags import router as event_tags_router
from app.api.v1.events import router as events_router
from app.api.v1.health import router as health_router
from app.api.v1.registrations import router as registrations_router
from app.api.v1.roles import router as roles_router
from app.api.v1.users import router as users_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(audit_logs_router, prefix="/audit-logs", tags=["audit"])
router.include_router(categories_router, prefix="/categories", tags=["categories"])
router.include_router(roles_router, prefix="/roles", tags=["roles"])
router.include_router(event_tags_router, prefix="/events", tags=["event-tags"])
router.include_router(event_comments_router, prefix="/events", tags=["event-comments"])
router.include_router(events_router, prefix="/events", tags=["events"])
router.include_router(registrations_router, tags=["registrations"])
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(health_router, tags=["health"])
