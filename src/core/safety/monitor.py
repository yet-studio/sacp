"""
SafeAI CodeGuard Protocol - Safety Monitor
Real-time monitoring of safety constraints and system health.
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import json

from .constraints import (
    ResourceConstraint,
    OperationConstraint,
    AccessConstraint
)


@dataclass
class HealthStatus:
    """System health status"""
    healthy: bool
    checks: Dict[str, bool]
    metrics: Dict[str, float]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Alert:
    """Safety alert"""
    level: str
    message: str
    context: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


class SafetyMonitor:
    """Monitors safety constraints and system health"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.alert_handlers: List[Callable[[Alert], None]] = []
        self.health_checks: Dict[str, Callable[[], bool]] = {}
        self.metrics: Dict[str, float] = {}
        self.alerts: List[Alert] = []
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    def add_alert_handler(
        self,
        handler: Callable[[Alert], None]
    ) -> None:
        """Adds an alert handler"""
        self.alert_handlers.append(handler)
    
    def add_health_check(
        self,
        name: str,
        check: Callable[[], bool]
    ) -> None:
        """Adds a health check"""
        self.health_checks[name] = check
    
    def update_metric(
        self,
        name: str,
        value: float
    ) -> None:
        """Updates a metric value"""
        self.metrics[name] = value
    
    async def start(
        self,
        interval_seconds: float = 1.0
    ) -> None:
        """Starts the monitor"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(
            self._monitor_loop(interval_seconds)
        )
    
    async def stop(self) -> None:
        """Stops the monitor"""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            await self._task
            self._task = None
    
    async def _monitor_loop(
        self,
        interval: float
    ) -> None:
        """Main monitoring loop"""
        while self._running:
            try:
                # Check system health
                status = await self._check_health()
                
                # Generate alerts if needed
                if not status.healthy:
                    await self._generate_alerts(status)
                
                # Update metrics
                await self._update_metrics()
                
                # Clean old alerts
                self._clean_old_alerts()
                
                # Wait for next check
                await asyncio.sleep(interval)
            
            except Exception as e:
                self.logger.error(
                    f"Monitor error: {e}",
                    exc_info=True
                )
                await asyncio.sleep(interval)
    
    async def _check_health(self) -> HealthStatus:
        """Checks system health"""
        checks = {}
        
        # Run all health checks
        for name, check in self.health_checks.items():
            try:
                # Run check in thread pool
                is_healthy = await asyncio.get_event_loop().run_in_executor(
                    None, check
                )
                checks[name] = is_healthy
            
            except Exception as e:
                self.logger.error(
                    f"Health check error: {e}",
                    exc_info=True
                )
                checks[name] = False
        
        # System is healthy if all checks pass
        healthy = all(checks.values())
        
        return HealthStatus(
            healthy=healthy,
            checks=checks,
            metrics=self.metrics.copy()
        )
    
    async def _generate_alerts(
        self,
        status: HealthStatus
    ) -> None:
        """Generates alerts based on health status"""
        # Check each failed health check
        for name, passed in status.checks.items():
            if not passed:
                alert = Alert(
                    level='error',
                    message=f"Health check failed: {name}",
                    context={
                        'check': name,
                        'metrics': status.metrics
                    }
                )
                self.alerts.append(alert)
                
                # Notify handlers
                for handler in self.alert_handlers:
                    try:
                        handler(alert)
                    except Exception as e:
                        self.logger.error(
                            f"Alert handler error: {e}",
                            exc_info=True
                        )
    
    async def _update_metrics(self) -> None:
        """Updates system metrics"""
        try:
            # Update resource metrics
            resource_constraint = next(
                (c for c in self.health_checks.keys()
                 if isinstance(c, ResourceConstraint)),
                None
            )
            
            if resource_constraint:
                self.metrics.update({
                    'memory_usage': resource_constraint.process.memory_info().rss,
                    'cpu_usage': resource_constraint.process.cpu_percent(),
                    'violation_count': len(resource_constraint.violations)
                })
            
            # Update operation metrics
            operation_constraint = next(
                (c for c in self.health_checks.keys()
                 if isinstance(c, OperationConstraint)),
                None
            )
            
            if operation_constraint:
                self.metrics.update({
                    'operations_per_minute': len(
                        operation_constraint.operation_history
                    ),
                    'avg_impact_score': sum(
                        op['impact_score']
                        for op in operation_constraint.operation_history
                    ) / len(operation_constraint.operation_history)
                    if operation_constraint.operation_history else 0
                })
        
        except Exception as e:
            self.logger.error(
                f"Metrics update error: {e}",
                exc_info=True
            )
    
    def _clean_old_alerts(
        self,
        max_age_hours: int = 24
    ) -> None:
        """Removes old alerts"""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        self.alerts = [
            alert for alert in self.alerts
            if alert.timestamp > cutoff
        ]
    
    def get_status(self) -> Dict[str, Any]:
        """Gets current monitor status"""
        return {
            'healthy': all(
                check() for check in self.health_checks.values()
            ),
            'metrics': self.metrics,
            'alerts': [
                {
                    'level': a.level,
                    'message': a.message,
                    'timestamp': a.timestamp.isoformat()
                }
                for a in self.alerts[-10:]  # Last 10 alerts
            ],
            'timestamp': datetime.now().isoformat()
        }
