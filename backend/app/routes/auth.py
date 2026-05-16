from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.auth.security import create_access_token, get_current_user, hash_password, verify_password
from app.database import get_db
from app.models import Organization, OrganizationMember, OrganizationRole, User
from app.schemas import Token, UserCreate, UserLogin, UserRead
from app.services.rate_limit import rate_limit_auth
from app.services.security_audit import log_security_event

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limit_auth)])
def register(payload: UserCreate, request: Request, db: Session = Depends(get_db)) -> Token:
    existing = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if existing:
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = User(
        email=str(payload.email).lower(),
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.flush()
    organization = Organization(name=f"{payload.full_name}'s Workspace")
    db.add(organization)
    db.flush()
    db.add(OrganizationMember(organization_id=organization.id, user_id=user.id, role=OrganizationRole.owner))
    log_security_event(
        db,
        "user_registered",
        "User registered and workspace was created",
        owner_id=user.id,
        organization_id=organization.id,
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(user)
    return Token(access_token=create_access_token(user.id), user=UserRead.model_validate(user))


@router.post("/login", response_model=Token, dependencies=[Depends(rate_limit_auth)])
def login(payload: UserLogin, request: Request, db: Session = Depends(get_db)) -> Token:
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    now = datetime.now(timezone.utc)
    ip_address = request.client.host if request.client else None
    locked_until = _as_aware_utc(user.locked_until) if user and user.locked_until else None
    if user and locked_until and locked_until > now:
        log_security_event(db, "login_blocked", "Login blocked for temporarily locked user", owner_id=user.id, ip_address=ip_address)
        db.commit()
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Account is temporarily locked after repeated failed logins")

    if not user or not verify_password(payload.password, user.hashed_password):
        if user:
            settings = get_settings()
            user.failed_login_count += 1
            user.last_failed_login_at = now
            if user.failed_login_count >= settings.failed_login_lock_threshold:
                user.locked_until = now + timedelta(minutes=settings.failed_login_lock_minutes)
            log_security_event(db, "login_failed", "Invalid password for existing user", owner_id=user.id, ip_address=ip_address)
            db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    user.failed_login_count = 0
    user.locked_until = None
    log_security_event(db, "login_succeeded", "User login succeeded", owner_id=user.id, ip_address=ip_address)
    db.commit()
    return Token(access_token=create_access_token(user.id), user=UserRead.model_validate(user))


def _as_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
