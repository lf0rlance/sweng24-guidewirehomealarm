import asyncio
from typing import List, Tuple, Optional

from db.connectToAlarmSystem import (
    get_alarm_system_id_by_user_id,
    get_alarm_system_id_by_device_id,
)

# (event_dict, alarm_system_id, was_armed_when_received)
EVENTS: List[Tuple[dict, Optional[int], bool]] = []

# (queue, alarm_system_id)
connected_clients: List[Tuple[asyncio.Queue, Optional[int]]] = []


def get_alarm_system_id_for_user(user_id: int) -> Optional[int]:
    return get_alarm_system_id_by_user_id(user_id)


def get_alarm_system_id_for_device(device_id: str) -> Optional[int]:
    return get_alarm_system_id_by_device_id(device_id)
