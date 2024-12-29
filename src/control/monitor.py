"""
SafeAI CodeGuard Protocol - Resource Monitoring
"""

import psutil
import time
from typing import Dict, Optional

class ResourceMonitor:
    """Monitors system resource usage"""
    
    def __init__(self):
        self._process = psutil.Process()
        self._last_net_io = self._get_net_io()
        self._last_net_time = time.time()

    def get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        try:
            return psutil.cpu_percent(interval=0.1)
        except Exception:
            return 0.0

    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            return self._process.memory_info().rss / (1024 * 1024)  # Convert to MB
        except Exception:
            return 0.0

    def get_disk_usage(self) -> float:
        """Get current disk usage percentage"""
        try:
            return psutil.disk_usage('/').percent
        except Exception:
            return 0.0

    def get_network_usage(self) -> float:
        """Get current network usage in MB/s"""
        try:
            current_net_io = self._get_net_io()
            current_time = time.time()
            
            # Calculate bytes per second
            time_diff = current_time - self._last_net_time
            if time_diff > 0:
                bytes_per_sec = sum(
                    current - last
                    for current, last in zip(
                        current_net_io,
                        self._last_net_io
                    )
                ) / time_diff
                
                # Update last values
                self._last_net_io = current_net_io
                self._last_net_time = current_time
                
                return bytes_per_sec / (1024 * 1024)  # Convert to MB/s
            return 0.0
        except Exception:
            return 0.0

    def _get_net_io(self) -> tuple[int, int]:
        """Get current network IO counters"""
        try:
            net_io = psutil.net_io_counters()
            return (net_io.bytes_sent, net_io.bytes_recv)
        except Exception:
            return (0, 0)
