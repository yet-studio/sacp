"""
SafeAI CodeGuard Protocol - Alert Management
Manages system alerts and notifications.
"""

from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging


@dataclass
class Alert:
    """System alert"""
    level: str  # info, warning, error, critical
    source: str  # component that generated the alert
    message: str  # alert message
    details: Dict[str, Any]  # additional context
    timestamp: datetime = field(default_factory=datetime.now)


class AlertManager:
    """Manages system alerts and notifications"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.alerts: List[Alert] = []
        self.handlers: Dict[str, List[Callable[[Alert], None]]] = {
            'info': [],
            'warning': [],
            'error': [],
            'critical': []
        }
    
    def add_handler(
        self,
        level: str,
        handler: Callable[[Alert], None]
    ) -> None:
        """Adds an alert handler for a specific level"""
        if level in self.handlers:
            self.handlers[level].append(handler)
    
    def remove_handler(
        self,
        level: str,
        handler: Callable[[Alert], None]
    ) -> None:
        """Removes an alert handler"""
        if level in self.handlers:
            self.handlers[level] = [
                h for h in self.handlers[level]
                if h != handler
            ]
    
    async def emit(
        self,
        level: str,
        source: str,
        message: str,
        details: Dict[str, Any] = None
    ) -> None:
        """Emits a new alert"""
        if level not in self.handlers:
            self.logger.warning(f"Invalid alert level: {level}")
            return
        
        alert = Alert(
            level=level,
            source=source,
            message=message,
            details=details or {}
        )
        self.alerts.append(alert)
        
        # Notify handlers
        for handler in self.handlers[level]:
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None, handler, alert
                )
            except Exception as e:
                self.logger.error(
                    f"Error in alert handler: {e}",
                    exc_info=True
                )
    
    def get_alerts(
        self,
        level: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 100
    ) -> List[Alert]:
        """Gets filtered alerts"""
        filtered = self.alerts
        
        if level:
            filtered = [a for a in filtered if a.level == level]
        
        if source:
            filtered = [a for a in filtered if a.source == source]
        
        return filtered[-limit:]  # Return most recent alerts
