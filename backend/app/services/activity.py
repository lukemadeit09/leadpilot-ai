from uuid import UUID

from sqlalchemy.orm import Session

from app.models import ActivityLog


def log_activity(
    db: Session,
    owner_id: UUID,
    organization_id: UUID,
    action: str,
    detail: str,
    lead_id: UUID | None = None,
    metadata: dict | None = None,
) -> ActivityLog:
    activity = ActivityLog(
        owner_id=owner_id,
        organization_id=organization_id,
        lead_id=lead_id,
        action=action,
        detail=detail,
        metadata_json=metadata or {},
    )
    db.add(activity)
    return activity
