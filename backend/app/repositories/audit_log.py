from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.admin_audit_log import AdminAuditLog


class AuditLogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        admin_id: int,
        action: str,
        target_type: str,
        target_id: int,
        detail: str | None = None,
    ) -> AdminAuditLog:
        row = AdminAuditLog(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row
