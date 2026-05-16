from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import OrganizationAPIKey


class OrganizationAPIKeyService:
    key_prefix = "lp_live_"

    def create_key(self, db: Session, organization_id: UUID, user_id: UUID, name: str) -> tuple[OrganizationAPIKey, str]:
        raw_key = f"{self.key_prefix}{secrets.token_urlsafe(32)}"
        api_key = OrganizationAPIKey(
            organization_id=organization_id,
            created_by_id=user_id,
            name=name,
            key_prefix=raw_key[:16],
            key_hash=self.hash_key(raw_key),
        )
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        return api_key, raw_key

    def authenticate(self, db: Session, raw_key: str | None) -> OrganizationAPIKey:
        if not raw_key or not raw_key.startswith(self.key_prefix):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
        key_hash = self.hash_key(raw_key)
        api_key = db.scalar(
            select(OrganizationAPIKey).where(
                OrganizationAPIKey.key_hash == key_hash,
                OrganizationAPIKey.revoked_at.is_(None),
            )
        )
        if not api_key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
        api_key.last_used_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(api_key)
        return api_key

    @staticmethod
    def hash_key(raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
