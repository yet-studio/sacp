"""
SafeAI CodeGuard Protocol - Performance Monitoring
Monitors system performance metrics and bottlenecks.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import psutil
import logging


@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot"""
    cpu_percent: float
    memory_percent: float
    disk_io: Dict[str, float]
    network_io: Dict[str, float]
    process_count: int
    thread_count: int
    timestamp: datetime


class PerformanceMonitor:
    """Monitors system performance"""
    
    def __init__(self, history_size: int = 3600):
        self.logger = logging.getLogger(__name__)
        self.history_size = history_size
        self.metrics_history: List[PerformanceMetrics] = []
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self, interval_seconds: float = 1.0) -> None:
        """Starts performance monitoring"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(
            self._monitor_loop(interval_seconds)
        )
    
    async def stop(self) -> None:
        """Stops performance monitoring"""
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
                await self._collect_metrics()
                await asyncio.sleep(interval)
            except Exception as e:
                self.logger.error(f"Performance monitoring error: {e}", exc_info=True)
                await asyncio.sleep(interval)
    
    async def _collect_metrics(self) -> None:
        """Collects performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk I/O metrics
            try:
                disk_io = psutil.disk_io_counters()
                disk_metrics = {
                    'read_bytes': disk_io.read_bytes,
                    'write_bytes': disk_io.write_bytes,
                    'read_count': disk_io.read_count,
                    'write_count': disk_io.write_count
                } if disk_io else {}
            except (psutil.Error, PermissionError):
                disk_metrics = {}
            
            # Network I/O metrics
            try:
                net_io = psutil.net_io_counters()
                net_metrics = {
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv
                }
            except (psutil.Error, PermissionError):
                net_metrics = {}
            
            # Process and thread metrics
            try:
                process_count = len(psutil.pids())
                thread_count = 0
                for proc in psutil.process_iter(['num_threads']):
                    try:
                        threads = proc.info.get('num_threads', 0)
                        if threads is not None:
                            thread_count += threads
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            except (psutil.Error, PermissionError):
                process_count = 0
                thread_count = 0
            
            # Create metrics snapshot
            metrics = PerformanceMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_io=disk_metrics,
                network_io=net_metrics,
                process_count=process_count,
                thread_count=thread_count,
                timestamp=datetime.now()
            )
            
            # Update history
            self.metrics_history.append(metrics)
            
            # Trim history if needed
            if len(self.metrics_history) > self.history_size:
                self.metrics_history = self.metrics_history[-self.history_size:]
        
        except Exception as e:
            self.logger.error(f"Error collecting performance metrics: {e}", exc_info=True)
    
    def get_metrics(
        self,
        timeframe: Optional[timedelta] = None
    ) -> List[PerformanceMetrics]:
        """Gets performance metrics history"""
        if not timeframe:
            return self.metrics_history
        
        cutoff = datetime.now() - timeframe
        return [
            m for m in self.metrics_history
            if m.timestamp > cutoff
        ]
