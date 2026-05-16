from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.database import get_db
from app.models import Task, User
from app.schemas import TaskCreate, TaskRead, TaskUpdate
from app.services.activity import log_activity

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
def list_tasks(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[Task]:
    return list(db.scalars(select(Task).where(Task.owner_id == current_user.id).order_by(desc(Task.created_at))).all())


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Task:
    task = Task(owner_id=current_user.id, **payload.model_dump())
    db.add(task)
    log_activity(db, current_user.id, "task_created", f"Task created: {task.title}", task.lead_id)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(task_id: UUID, payload: TaskUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Task:
    task = db.scalar(select(Task).where(Task.id == task_id, Task.owner_id == current_user.id))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    task = db.scalar(select(Task).where(Task.id == task_id, Task.owner_id == current_user.id))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
