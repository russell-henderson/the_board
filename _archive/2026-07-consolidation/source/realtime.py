"""In-process WebSocket fan-out for local dashboard clients."""
from __future__ import annotations

import asyncio
from typing import Any, Set

from fastapi import WebSocket


class ConnectionHub:
    def __init__(self) -> None:
        self.activity: Set[WebSocket] = set()
        self.chat: Set[WebSocket] = set()

    async def connect(self, socket: WebSocket, channel: str) -> None:
        await socket.accept()
        getattr(self, channel).add(socket)

    def disconnect(self, socket: WebSocket, channel: str) -> None:
        getattr(self, channel).discard(socket)

    async def broadcast(self, channel: str, message: Any) -> None:
        recipients = list(getattr(self, channel))
        failed = []
        for socket in recipients:
            try:
                await socket.send_json(message)
            except Exception:
                failed.append(socket)
        for socket in failed:
            self.disconnect(socket, channel)


hub = ConnectionHub()
