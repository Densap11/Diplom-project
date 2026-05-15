from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_permissions
from app.models.user import User
from app.schemas.audit_log import AuditLogRead
from app.services.audit import list_audit_logs

router = APIRouter()


@router.get(
    "",
    response_model=list[AuditLogRead],
    summary="Журнал административных действий",
    description="Возвращает аудит важных действий администраторов и организаторов.",
)
def read_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("audit:read")),
) -> list[AuditLogRead]:
    logs = list_audit_logs(db=db, limit=limit, offset=offset)
    return [AuditLogRead.model_validate(log) for log in logs]
