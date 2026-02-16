import asyncio
from typing import List
from app.validate2 import ValidateData

EVENTS: List[ValidateData] = []
connected_clients: List[asyncio.Queue] = []
