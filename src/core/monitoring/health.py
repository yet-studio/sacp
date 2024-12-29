"""
SafeAI CodeGuard Protocol - Health Monitoring
Monitors system health and component status.
"""

from typing import Dict, List, Callable, Any, Optional
from datetime import datetime
import asyncio
import logging


class HealthMonitor:
    """Monitors system health and component status"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.health_checks: Dict[str, Callable[[], bool]] = {}
        self.health_status: Dict[str, bool] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    def add_check(self, name: str, check: Callable[[], bool]) -> None:
        """Adds a health check"""
        self.health_checks[name] = check
    
    def remove_check(self, name: str) -> None:
        """Removes a health check"""
        self.health_checks.pop(name, None)
        self.health_status.pop(name, None)
    
    async def start(self, interval_seconds: float = 1.0) -> None:
        """Starts health monitoring"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(
            self._monitor_loop(interval_seconds)
        )
    
    async def stop(self) -> None:
        """Stops health monitoring"""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            await self._task
            self._task = None
    
    async def _monitor_loop(self, interval: float) -> None:
        """Main monitoring loop"""
        while self._running:
            try:
                await self._check_health()
                await asyncio.sleep(interval)
            except Exception as e:
                self.logger.error(f"Health check error: {e}", exc_info=True)
                await asyncio.sleep(interval)
    
    async def _check_health(self) -> None:
        """Runs health checks"""
        for name, check in self.health_checks.items():
            try:
                # Run check in thread pool to avoid blocking
                is_healthy = await asyncio.get_event_loop().run_in_executor(
                    None, check
                )
                self.health_status[name] = is_healthy
                
                if not is_healthy:
                    self.logger.warning(f"Health check failed: {name}")
            
            except Exception as e:
                self.logger.error(
                    f"Error in health check {name}: {e}",
                    exc_info=True
                )
                self.health_status[name] = False
    
    def get_status(self) -> Dict[str, Any]:
        """Gets current health status"""
        # Initialize health status for any checks that haven't run yet
        for name in self.health_checks:
            if name not in self.health_status:
                self.health_status[name] = False
                
        return {
            'healthy': all(self.health_status.values()) if self.health_status else False,
            'checks': self.health_status.copy(),
            'timestamp': datetime.now().isoformat()
        }
