"""
Admin-only API: list/add homes, sensor labels, add users to home, offline devices, notify homeowner.
No home address is ever stored or returned.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_admin
from app.models.request_models import (
    SetSensorLabelsRequest,
    AddUserToHomeRequest,
    NotifyHomeownerRequest,
    UpdateAlarmSystemRequest,
    UpdateUserRequest,
    LinkExistingUserToHomeRequest,
)
from app.services.notification_service import send_notification_to_system
from db import admin_queries
from db import access_control
from db.device_last_seen import get_offline_devices
from db.sensor_labels import set_sensor_labels, get_sensor_labels
from db.insertIntoDB import insert_user_by_admin, update_user_by_admin, unlink_user_from_home

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/homes")
def list_homes(_: Annotated[dict, Depends(get_current_admin)]):
    """List all homes (alarm systems) with device_id, last_seen, offline flag, sensor labels, user count. No address."""
    return admin_queries.list_homes()


@router.post("/homes")
def add_home(_: Annotated[dict, Depends(get_current_admin)]):
    """Create a new home (alarm_system + one microcontroller). Returns alarm_system_id, device_id (e.g. esp32_7)."""
    result = admin_queries.add_home()
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to create home")
    return result


@router.patch("/homes/{alarm_system_id}")
def update_home(
    alarm_system_id: int,
    body: UpdateAlarmSystemRequest,
    _: Annotated[dict, Depends(get_current_admin)],
):
    """Update alarm system display name."""
    if not admin_queries.update_home_name(alarm_system_id, body.name):
        raise HTTPException(status_code=404, detail="Alarm system not found")
    return {"status": "ok"}


@router.delete("/homes/{alarm_system_id}")
def delete_home(
    alarm_system_id: int,
    _: Annotated[dict, Depends(get_current_admin)],
):
    """Delete alarm system; users are unlinked (not deleted)."""
    ok, err = admin_queries.delete_home(alarm_system_id)
    if not ok:
        raise HTTPException(status_code=500, detail=err or "Failed to delete")
    return {"status": "ok"}


@router.get("/homes/{alarm_system_id}/sensors")
def get_sensors(
    alarm_system_id: int,
    _: Annotated[dict, Depends(get_current_admin)],
):
    """Get sensor labels for a home."""
    return {"labels": get_sensor_labels(alarm_system_id)}


@router.put("/homes/{alarm_system_id}/sensors")
def update_sensors(
    alarm_system_id: int,
    body: SetSensorLabelsRequest,
    _: Annotated[dict, Depends(get_current_admin)],
):
    """Set display names for sensors (e.g. Front door, Back window)."""
    if not set_sensor_labels(alarm_system_id, body.labels):
        raise HTTPException(status_code=500, detail="Failed to update sensor labels")
    return {"labels": get_sensor_labels(alarm_system_id)}


@router.get("/homes/{alarm_system_id}/users")
def list_users_for_home(
    alarm_system_id: int,
    _: Annotated[dict, Depends(get_current_admin)],
):
    """List users linked to this home (id, username, email, phone). No address."""
    return admin_queries.list_users_for_home(alarm_system_id)


@router.post("/homes/{alarm_system_id}/users")
def add_user_to_home(
    alarm_system_id: int,
    body: AddUserToHomeRequest,
    _: Annotated[dict, Depends(get_current_admin)],
):
    """Create a homeowner user for this home (they log in with email/password). Admin sets access_level."""
    if not insert_user_by_admin(
        username=body.username.strip(),
        email=body.email.strip().lower(),
        password=body.password,
        alarm_system_id=alarm_system_id,
        phone=body.phone.strip() if body.phone else None,
    ):
        raise HTTPException(status_code=400, detail="User already exists or invalid data")
    user_id = admin_queries.get_user_id_by_email(body.email)
    if user_id is not None:
        access_control.upsert_membership(user_id, alarm_system_id, body.access_level or "owner")
    return {"status": "ok", "message": "User created"}


@router.post("/homes/{alarm_system_id}/users/link")
def link_existing_user_to_home(
    alarm_system_id: int,
    body: LinkExistingUserToHomeRequest,
    _: Annotated[dict, Depends(get_current_admin)],
):
    """
    Link an existing DB account to this home and set their access_level.
    Body: { "email": "...", "access_level": "child" } OR { "user_id": 123, "access_level": "arm_only" }.
    """
    linked_user_id = admin_queries.link_existing_user_to_home(
        alarm_system_id=alarm_system_id,
        user_id=body.user_id,
        email=(body.email.strip().lower() if body.email else None),
    )
    if linked_user_id is None:
        raise HTTPException(status_code=400, detail="Could not link user (not found or already linked to another home)")
    access_control.upsert_membership(linked_user_id, alarm_system_id, body.access_level or "owner")
    return {"status": "ok", "message": "User linked"}


@router.put("/homes/{alarm_system_id}/users/{user_id}")
def update_user_in_home(
    alarm_system_id: int,
    user_id: int,
    body: UpdateUserRequest,
    _: Annotated[dict, Depends(get_current_admin)],
):
    """Update a user in this home (username, email, phone, or password)."""
    if not update_user_by_admin(
        user_id=user_id,
        alarm_system_id=alarm_system_id,
        username=body.username,
        email=body.email,
        phone=body.phone,
        password=body.password,
    ):
        raise HTTPException(status_code=400, detail="User not found or invalid data")
    if body.access_level is not None:
        access_control.upsert_membership(user_id, alarm_system_id, body.access_level)
    return {"status": "ok"}


@router.delete("/homes/{alarm_system_id}/users/{user_id}")
def remove_user_from_home(
    alarm_system_id: int,
    user_id: int,
    _: Annotated[dict, Depends(get_current_admin)],
):
    """Remove user from this home (unlink; does not delete account)."""
    if not unlink_user_from_home(user_id, alarm_system_id):
        raise HTTPException(status_code=404, detail="User not found in this home")
    try:
        access_control.remove_membership(user_id, alarm_system_id)
    except Exception:
        pass
    return {"status": "ok"}


@router.get("/offline")
def list_offline(_: Annotated[dict, Depends(get_current_admin)]):
    """List devices that have not been seen in the last 5 minutes (microcontroller_id, alarm_system_id, last_seen)."""
    rows = get_offline_devices(300)
    return [
        {"microcontroller_id": r[0], "alarm_system_id": r[1], "last_seen": r[2]}
        for r in rows
    ]


@router.post("/homes/{alarm_system_id}/notify")
def notify_homeowner(
    alarm_system_id: int,
    body: NotifyHomeownerRequest,
    _: Annotated[dict, Depends(get_current_admin)],
):
    """Send a push notification to all devices registered for this home (e.g. sensor offline alert)."""
    count = send_notification_to_system(alarm_system_id, body.title, body.body)
    return {"sent_to_devices": count}
