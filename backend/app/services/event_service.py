import asyncio
import time
from typing import List
from app.validate2 import ValidateData

EVENTS: List[ValidateData] = []
connected_clients: List[asyncio.Queue] = []

# Deduplication store: { (device_id, count): timestamp_seen }
# Used to detect replayed events within the timestamp tolerance window.
_DEDUP_WINDOW = 180  # seconds — matches the ±3 min timestamp tolerance in ValidateData
_seen_events: dict[tuple[str, int], float] = {}


def is_duplicate(device_id: str, count: int) -> bool:
    """
    Returns True if this (device_id, count) pair has already been seen
    within the deduplication window, indicating a replay attack.
    Lazily cleans up expired entries on each call.
    """
    now = time.time()
    cutoff = now - _DEDUP_WINDOW

    # Lazy cleanup — drop entries older than the window
    expired = [key for key, ts in _seen_events.items() if ts < cutoff]
    for key in expired:
        del _seen_events[key]

    key = (device_id, count)
    if key in _seen_events:
        return True  # duplicate

    _seen_events[key] = now
    return False
