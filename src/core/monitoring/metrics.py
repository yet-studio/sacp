"""
SafeAI CodeGuard Protocol - Metrics Collection
Collects and manages system metrics.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
import psutil
import logging


class MetricsCollector:
    """Collects and manages system metrics"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics: Dict[str, Any] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._process = psutil.Process()
    
    async def start(self, interval_seconds: float = 1.0) -> None:
        """Starts metrics collection"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(
            self._collect_loop(interval_seconds)
        )
    
    async def stop(self) -> None:
        """Stops metrics collection"""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            await self._task
            self._task = None
    
    async def _collect_loop(self, interval: float) -> None:
        """Main collection loop"""
        while self._running:
            try:
                await self._collect_metrics()
                await asyncio.sleep(interval)
            except Exception as e:
                self.logger.error(f"Metrics collection error: {e}", exc_info=True)
                await asyncio.sleep(interval)
    
    async def _collect_metrics(self) -> None:
        """Collects system metrics"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Process metrics
            process = self._process
            process_cpu = process.cpu_percent(interval=0.1)
            process_memory = process.memory_info()
            
            # Network metrics
            net_io = psutil.net_io_counters()
            
            # Update metrics
            self.metrics.update({
                'timestamp': datetime.now().isoformat(),
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available': memory.available,
                    'disk_percent': disk.percent,
                    'disk_free': disk.free
                },
                'process': {
                    'cpu_percent': process_cpu,
                    'memory_rss': process_memory.rss,
                    'memory_vms': process_memory.vms,
                    'threads': process.num_threads()
                },
                'network': {
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv,
                    'errin': net_io.errin,
                    'errout': net_io.errout
                }
            })
        
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}", exc_info=True)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Gets current metrics"""
        return self.metrics.copy()
