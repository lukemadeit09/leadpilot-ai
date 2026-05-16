from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.database import get_db
from app.models import Lead, LeadStatus, Task, TaskStatus, User
from app.schemas import DashboardMetrics, LeadCreate, LeadRead, LeadUpdate
from app.services.activity import log_activity

router = APIRouter(prefix="/leads", tags=["leads"])
dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=list[LeadRead])
def list_leads(
    search: str | None = None,
    status_filter: LeadStatus | None = Query(default=None, alias="status"),
    sort: str = "created_at",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Lead]:
    stmt = select(Lead).where(Lead.owner_id == current_user.id)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(or_(Lead.name.ilike(like), Lead.email.ilike(like), Lead.company.ilike(like), Lead.message.ilike(like)))
    if status_filter:
        stmt = stmt.where(Lead.status == status_filter)
    order_by = Lead.score if sort == "score" else Lead.status if sort == "status" else Lead.created_at
    return list(db.scalars(stmt.order_by(desc(order_by))).all())


@router.post("", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Lead:
    lead = Lead(owner_id=current_user.id, **payload.model_dump())
    db.add(lead)
    db.flush()
    log_activity(db, current_user.id, "lead_created", "Lead was created manually.", lead.id)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("/{lead_id}", response_model=LeadRead)
def get_lead(lead_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Lead:
    lead = db.scalar(select(Lead).where(Lead.id == lead_id, Lead.owner_id == current_user.id))
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.patch("/{lead_id}", response_model=LeadRead)
def update_lead(lead_id: UUID, payload: LeadUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Lead:
    lead = db.scalar(select(Lead).where(Lead.id == lead_id, Lead.owner_id == current_user.id))
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    updates = payload.model_dump(exclude_unset=True)
    previous_status = lead.status
    for key, value in updates.items():
        setattr(lead, key, value)
    if "status" in updates and previous_status != lead.status:
        log_activity(db, current_user.id, "status_changed", f"Lead status changed to {lead.status.value}.", lead.id)
    db.commit()
    db.refresh(lead)
    return lead


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(lead_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    lead = db.scalar(select(Lead).where(Lead.id == lead_id, Lead.owner_id == current_user.id))
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    db.delete(lead)
    db.commit()


@dashboard_router.get("/metrics", response_model=DashboardMetrics)
def dashboard_metrics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> DashboardMetrics:
    leads = db.scalars(select(Lead).where(Lead.owner_id == current_user.id)).all()
    pending_tasks = db.scalar(select(func.count()).select_from(Task).where(Task.owner_id == current_user.id, Task.status == TaskStatus.pending)) or 0
    average_score = round(sum(lead.score for lead in leads) / len(leads), 1) if leads else 0
    pipeline = {status.value: 0 for status in LeadStatus}
    for lead in leads:
        pipeline[lead.status.value] += 1
    from app.models import ActivityLog

    recent_activity = db.scalars(
        select(ActivityLog).where(ActivityLog.owner_id == current_user.id).order_by(desc(ActivityLog.created_at)).limit(8)
    ).all()
    return DashboardMetrics(
        total_leads=len(leads),
        qualified_leads=sum(1 for lead in leads if lead.status == LeadStatus.qualified),
        average_score=average_score,
        pending_tasks=pending_tasks,
        pipeline=pipeline,
        recent_activity=list(recent_activity),
    )
