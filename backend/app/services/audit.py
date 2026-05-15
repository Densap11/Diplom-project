from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User


def create_audit_log(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    actor: User | None = None,
    details: str | None = None,
) -> AuditLog:
    log = AuditLog(
        actor_id=actor.id if actor is not None else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )
    db.add(log)
    db.flush()
    return log


def list_audit_logs(db: Session, limit: int = 100, offset: int = 0) -> list[AuditLog]:
    query = select(AuditLog).order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
    return list(db.scalars(query).all())
