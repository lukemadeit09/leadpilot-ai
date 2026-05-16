from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.auth.security import get_current_organization, get_current_user
from app.database import get_db
from app.models import ActivityLog, OrganizationMember, User
from app.schemas import ActivityRead

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("", response_model=list[ActivityRead])
def list_activity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(get_current_organization),
) -> list[ActivityLog]:
    return list(
        db.scalars(
            select(ActivityLog).where(ActivityLog.organization_id == membership.organization_id).order_by(desc(ActivityLog.created_at)).limit(50)
        ).all()
    )
