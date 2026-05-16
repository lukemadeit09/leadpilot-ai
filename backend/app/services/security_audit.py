from uuid import UUID

from sqlalchemy.orm import Session

from app.models import SecurityAuditLog


def log_security_event(
    db: Session,
    action: str,
    detail: str,
    *,
    owner_id: UUID | None = None,
    organization_id: UUID | None = None,
    ip_address: str | None = None,
    metadata: dict | None = None,
) -> SecurityAuditLog:
    event = SecurityAuditLog(
        owner_id=owner_id,
        organization_id=organization_id,
        action=action,
        detail=detail,
        ip_address=ip_address,
        metadata_json=metadata or {},
    )
    db.add(event)
    return event
