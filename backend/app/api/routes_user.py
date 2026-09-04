"""用户作息路由。"""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from ..db.database import get_db
from ..schemas.user import OnboardingIn, ProfileUpdateIn
from ..services import session_service

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/profile")
def get_profile(conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return session_service.profile_view(conn)


@router.put("/profile")
def update_profile(
    body: ProfileUpdateIn, conn: sqlite3.Connection = Depends(get_db)
) -> dict:
    patch = body.model_dump(exclude_none=True)
    session_service.update_profile(conn, patch)
    return session_service.profile_view(conn)


@router.post("/onboarding")
def complete_onboarding(
    body: OnboardingIn, conn: sqlite3.Connection = Depends(get_db)
) -> dict:
    if body.done:
        session_service.mark_setup_done(conn)
    return {"ok": True, "needs_setup": session_service.needs_setup(conn)}
