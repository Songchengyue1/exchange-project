from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.audit_log import AuditLogRepository


def log_admin_action(
    db: Session,
    admin_id: int,
    action: str,
    target_type: str,
    target_id: int,
    detail: str | None = None,
) -> None:
    AuditLogRepository(db).create(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
    )
