"""Homeowner-only: manage members of their home (not platform admin)."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.security import AuthenticatedUser, get_current_user
from app.services.event_service import get_alarm_system_id_for_user
from db import admin_queries
from db.home_roles import get_home_role
from db.insertIntoDB import unlink_user_from_home, update_user_by_admin

router = APIRouter(prefix="/api/home", tags=["home"])


class PatchMemberBody(BaseModel):
    home_role: str = Field(..., min_length=3, max_length=20)


@router.get("/members")
def list_home_members(current_user: Annotated[AuthenticatedUser, Depends(get_current_user)]):
    alarm_system_id = get_alarm_system_id_for_user(current_user.user_id)
    if alarm_system_id is None:
        return []
    if (get_home_role(current_user.user_id) or "") != "owner":
        raise HTTPException(status_code=403, detail="Only the homeowner can manage members")
    return admin_queries.list_users_for_home(alarm_system_id)


@router.patch("/members/{member_id}")
def patch_home_member(
    member_id: int,
    body: PatchMemberBody,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
):
    alarm_system_id = get_alarm_system_id_for_user(current_user.user_id)
    if alarm_system_id is None:
        raise HTTPException(status_code=400, detail="No alarm system linked")
    if (get_home_role(current_user.user_id) or "") != "owner":
        raise HTTPException(status_code=403, detail="Only the homeowner can change roles")
    if member_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="You cannot change your own role here")

    ok = update_user_by_admin(
        member_id,
        alarm_system_id,
        home_role=body.home_role,
    )
    if not ok:
        raise HTTPException(
            status_code=400,
            detail="Update failed (invalid role, or another owner already exists)",
        )
    return {"status": "ok"}


@router.delete("/members/{member_id}")
def remove_home_member(
    member_id: int,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
):
    alarm_system_id = get_alarm_system_id_for_user(current_user.user_id)
    if alarm_system_id is None:
        raise HTTPException(status_code=400, detail="No alarm system linked")
    if (get_home_role(current_user.user_id) or "") != "owner":
        raise HTTPException(status_code=403, detail="Only the homeowner can remove members")
    if member_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="You cannot remove yourself")

    if not unlink_user_from_home(member_id, alarm_system_id):
        raise HTTPException(status_code=404, detail="User not found in this home")
    return {"status": "ok"}
