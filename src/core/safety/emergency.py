"""
SafeAI CodeGuard Protocol - Emergency Stop
Emergency stop mechanism for immediate halt of AI operations.
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json


@dataclass
class EmergencyEvent:
    """Emergency stop event"""
    reason: str
    context: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


class EmergencyStop:
    """Emergency stop mechanism"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.active = False
        self.events: List[EmergencyEvent] = []
        self.handlers: List[Callable[[EmergencyEvent], None]] = []
        self._lock = asyncio.Lock()
    
    def add_handler(
        self,
        handler: Callable[[EmergencyEvent], None]
    ) -> None:
        """Adds an emergency stop handler"""
        self.handlers.append(handler)
    
    async def trigger(
        self,
        reason: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Triggers emergency stop"""
        async with self._lock:
            if self.active:
                return
            
            self.active = True
            event = EmergencyEvent(
                reason=reason,
                context=context or {}
            )
            self.events.append(event)
            
            # Notify handlers
            for handler in self.handlers:
                try:
                    handler(event)
                except Exception as e:
                    self.logger.error(
                        f"Handler error: {e}",
                        exc_info=True
                    )
            
            self.logger.critical(
                f"Emergency stop triggered: {reason}",
                extra={'context': context}
            )
    
    async def reset(
        self,
        user: str,
        reason: str
    ) -> None:
        """Resets emergency stop"""
        async with self._lock:
            if not self.active:
                return
            
            self.active = False
            self.events.append(
                EmergencyEvent(
                    reason=f"Reset by {user}: {reason}",
                    context={
                        'user': user,
                        'action': 'reset'
                    }
                )
            )
            
            self.logger.info(
                f"Emergency stop reset by {user}: {reason}"
            )
    
    def is_active(self) -> bool:
        """Checks if emergency stop is active"""
        return self.active
    
    def get_last_event(self) -> Optional[EmergencyEvent]:
        """Gets the last emergency event"""
        return self.events[-1] if self.events else None
    
    def get_history(
        self,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Gets emergency stop history"""
        events = self.events[-limit:] if limit else self.events
        return [
            {
                'reason': e.reason,
                'context': e.context,
                'timestamp': e.timestamp.isoformat()
            }
            for e in events
        ]
