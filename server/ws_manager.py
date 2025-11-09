"""
WebSocket connection manager for real-time agent progress updates
"""
from fastapi import WebSocket
from typing import Dict, Set
import json
import asyncio


class ConnectionManager:
    """Manages WebSocket connections for agent progress updates"""
    
    def __init__(self):
        # session_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Register a new WebSocket connection for a session"""
        await websocket.accept()
        async with self._lock:
            if session_id not in self.active_connections:
                self.active_connections[session_id] = set()
            self.active_connections[session_id].add(websocket)
        print(f"WebSocket connected for session: {session_id}")
    
    async def disconnect(self, websocket: WebSocket, session_id: str):
        """Remove a WebSocket connection"""
        async with self._lock:
            if session_id in self.active_connections:
                self.active_connections[session_id].discard(websocket)
                if not self.active_connections[session_id]:
                    del self.active_connections[session_id]
        print(f"WebSocket disconnected for session: {session_id}")
    
    async def send_to_session(self, session_id: str, message: dict):
        """Send a message to all connections for a specific session"""
        if session_id not in self.active_connections:
            return
        
        dead_connections = set()
        message_json = json.dumps(message)
        
        for websocket in self.active_connections[session_id]:
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                print(f"Error sending to WebSocket: {e}")
                dead_connections.add(websocket)
        
        # Clean up dead connections
        if dead_connections:
            async with self._lock:
                self.active_connections[session_id] -= dead_connections
                if not self.active_connections[session_id]:
                    del self.active_connections[session_id]
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        message_json = json.dumps(message)
        dead_connections = []
        
        async with self._lock:
            for session_id, connections in self.active_connections.items():
                for websocket in connections:
                    try:
                        await websocket.send_text(message_json)
                    except Exception:
                        dead_connections.append((session_id, websocket))
        
        # Clean up dead connections
        if dead_connections:
            async with self._lock:
                for session_id, websocket in dead_connections:
                    if session_id in self.active_connections:
                        self.active_connections[session_id].discard(websocket)
                        if not self.active_connections[session_id]:
                            del self.active_connections[session_id]


# Global connection manager instance
manager = ConnectionManager()

