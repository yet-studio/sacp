"""
SafeAI CodeGuard Protocol - Dynamic Control System
Implements real-time monitoring, resource limits, rate limiting, and rollback capabilities.
"""

import time
import threading
import queue
import logging
import psutil
import resource
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Callable, Any
from enum import Enum, auto
from datetime import datetime, timedelta
import json
from pathlib import Path
import shutil
import hashlib
from ..core.error import ResourceLimitError

class ResourceType(Enum):
    """Types of resources to monitor"""
    CPU = auto()
    MEMORY = auto()
    DISK = auto()
    NETWORK = auto()
    FILE_OPS = auto()


class ControlAction(Enum):
    """Actions that can be taken by the control system"""
    WARN = auto()
    THROTTLE = auto()
    SUSPEND = auto()
    TERMINATE = auto()
    ROLLBACK = auto()


@dataclass
class ResourceLimit:
    """Resource usage limit configuration"""
    resource_type: ResourceType
    soft_limit: float  # Triggers warning
    hard_limit: float  # Triggers action
    window_seconds: int = 60  # Time window for averaging
    action: ControlAction = ControlAction.WARN


@dataclass
class RateLimit:
    """Rate limiting configuration"""
    operations_per_minute: int
    burst_limit: int
    cooldown_seconds: int = 60


@dataclass
class Snapshot:
    """System state snapshot for rollback"""
    timestamp: datetime
    files: Dict[str, bool]  # path -> exists
    resource_usage: Dict[ResourceType, float]
    metadata: Dict[str, Any]


class ResourceMonitor:
    """Monitors system resource usage"""

    def __init__(self):
        self.process = psutil.Process()
        self._last_network = psutil.net_io_counters()
        self._last_disk = psutil.disk_io_counters()
        self._last_check = time.time()

    def get_cpu_usage(self) -> float:
        """Get CPU usage percentage"""
        return self.process.cpu_percent(interval=0.1)

    def get_memory_usage(self) -> float:
        """Get memory usage in MB"""
        return self.process.memory_info().rss / 1024 / 1024

    def get_disk_usage(self) -> float:
        """Get disk I/O in MB/s"""
        current = psutil.disk_io_counters()
        time_diff = time.time() - self._last_check
        
        bytes_per_sec = (
            (current.read_bytes + current.write_bytes) -
            (self._last_disk.read_bytes + self._last_disk.write_bytes)
        ) / time_diff
        
        self._last_disk = current
        self._last_check = time.time()
        
        return bytes_per_sec / 1024 / 1024

    def get_network_usage(self) -> float:
        """Get network I/O in MB/s"""
        current = psutil.net_io_counters()
        time_diff = time.time() - self._last_check
        
        bytes_per_sec = (
            (current.bytes_sent + current.bytes_recv) -
            (self._last_network.bytes_sent + self._last_network.bytes_recv)
        ) / time_diff
        
        self._last_network = current
        self._last_check = time.time()
        
        return bytes_per_sec / 1024 / 1024


class RateLimiter:
    """Implements token bucket algorithm for rate limiting"""

    def __init__(self, rate_limit: RateLimit):
        self.rate_limit = rate_limit
        self.tokens = rate_limit.burst_limit
        self.last_update = time.time()
        self.lock = threading.Lock()

    def try_acquire(self) -> bool:
        """Try to acquire a token. Returns True if successful."""
        with self.lock:
            now = time.time()
            # Replenish tokens
            time_passed = now - self.last_update
            new_tokens = int(time_passed * (self.rate_limit.operations_per_minute / 60))
            self.tokens = min(
                self.rate_limit.burst_limit,
                self.tokens + new_tokens
            )
            self.last_update = now

            if self.tokens > 0:
                self.tokens -= 1
                return True
            return False

    def get_wait_time(self) -> float:
        """Get estimated wait time in seconds until next token"""
        if self.tokens > 0:
            return 0
        return (60 / self.rate_limit.operations_per_minute)


class SnapshotManager:
    """Manages system state snapshots for rollback"""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.snapshots_dir = self.base_dir / ".snapshots"
        self.snapshots_dir.mkdir(exist_ok=True)
        self.resource_monitor = ResourceMonitor()

    def create_snapshot(self, metadata: Dict[str, Any] = None) -> Snapshot:
        """Create a new snapshot of the current state"""
        snapshot = Snapshot(
            timestamp=datetime.now(),
            files={},
            resource_usage={
                ResourceType.CPU: self.resource_monitor.get_cpu_usage(),
                ResourceType.MEMORY: self.resource_monitor.get_memory_usage(),
                ResourceType.DISK: self.resource_monitor.get_disk_usage(),
                ResourceType.NETWORK: self.resource_monitor.get_network_usage()
            },
            metadata=metadata or {}
        )

        # Create backup directory for this snapshot
        backup_dir = self.snapshots_dir / f"backup_{snapshot.timestamp.isoformat()}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Store files and create backups
        for file_path in self.base_dir.rglob("*"):
            if file_path.is_file() and ".snapshots" not in str(file_path):
                rel_path = file_path.relative_to(self.base_dir)
                backup_path = backup_dir / rel_path
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(file_path), str(backup_path))
                snapshot.files[str(rel_path)] = True

        # Save snapshot
        snapshot_path = self.snapshots_dir / f"snapshot_{snapshot.timestamp.isoformat()}.json"
        with open(snapshot_path, "w") as f:
            json.dump({
                "timestamp": snapshot.timestamp.isoformat(),
                "files": snapshot.files,
                "resource_usage": {k.name: v for k, v in snapshot.resource_usage.items()},
                "metadata": snapshot.metadata
            }, f, indent=2)

        return snapshot

    def get_snapshots(self) -> List[Snapshot]:
        """Get list of available snapshots"""
        snapshots = []
        for snapshot_file in self.snapshots_dir.glob("snapshot_*.json"):
            with open(snapshot_file) as f:
                data = json.load(f)
                snapshots.append(Snapshot(
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    files=data["files"],
                    resource_usage={
                        ResourceType[k]: v for k, v in data["resource_usage"].items()
                    },
                    metadata=data["metadata"]
                ))
        return sorted(snapshots, key=lambda s: s.timestamp)

    def rollback_to_snapshot(self, snapshot: Snapshot) -> bool:
        """Rollback system to a previous snapshot"""
        backup_dir = self.snapshots_dir / f"backup_{snapshot.timestamp.isoformat()}"
        if not backup_dir.exists():
            logging.error(f"Backup directory not found: {backup_dir}")
            return False

        try:
            # Remove files that didn't exist in snapshot
            for file_path in self.base_dir.rglob("*"):
                if file_path.is_file() and ".snapshots" not in str(file_path):
                    rel_path = file_path.relative_to(self.base_dir)
                    if str(rel_path) not in snapshot.files:
                        file_path.unlink()

            # Restore files from backup
            for rel_path in snapshot.files:
                src_path = backup_dir / rel_path
                dst_path = self.base_dir / rel_path
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                if src_path.exists():
                    shutil.copy2(str(src_path), str(dst_path))
                else:
                    logging.error(f"Backup file not found: {src_path}")
                    return False

            return True
        except Exception as e:
            logging.error(f"Error during rollback: {str(e)}")
            return False


class DynamicControlSystem:
    """Main system for dynamic control and monitoring"""

    def __init__(
        self,
        base_dir: str,
        resource_limits: List[ResourceLimit],
        rate_limit: RateLimit
    ):
        self.base_dir = Path(base_dir)
        self.resource_limits = resource_limits
        self.resource_monitor = ResourceMonitor()
        self.rate_limiter = RateLimiter(rate_limit)
        self.snapshot_manager = SnapshotManager(base_dir)
        
        self._stop_event = threading.Event()
        self._monitor_thread = None
        self._running = False
        
        # Resource usage history
        self.usage_history: Dict[ResourceType, List[tuple[float, float]]] = {
            rt: [] for rt in ResourceType
        }
        self.history_lock = threading.Lock()
        
        # Callbacks for different actions
        self.action_callbacks: Dict[ControlAction, List[Callable]] = {
            action: [] for action in ControlAction
        }

    def start(self):
        """Start the dynamic control system"""
        if self._running:
            return

        self._running = True
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

    def stop(self):
        """Stop the dynamic control system"""
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join()
        self._running = False

    def register_callback(self, action: ControlAction, callback: Callable):
        """Register a callback for a specific control action"""
        self.action_callbacks[action].append(callback)

    def get_resource_usage(self) -> Dict[ResourceType, float]:
        """Get current resource usage"""
        return {
            ResourceType.CPU: self.resource_monitor.get_cpu_usage(),
            ResourceType.MEMORY: self.resource_monitor.get_memory_usage(),
            ResourceType.DISK: self.resource_monitor.get_disk_usage(),
            ResourceType.NETWORK: self.resource_monitor.get_network_usage()
        }

    def get_usage_history(self, resource_type: ResourceType, minutes: int = 1) -> List[tuple[float, float]]:
        """Get resource usage history for the specified time window
        
        Args:
            resource_type: Type of resource to get history for
            minutes: Number of minutes of history to return
            
        Returns:
            List of (timestamp, usage) tuples
        """
        with self.history_lock:
            if resource_type not in self.usage_history:
                return []
                
            cutoff = time.time() - (minutes * 60)
            return [
                (ts, usage) for ts, usage in self.usage_history[resource_type]
                if ts >= cutoff
            ]

    def create_snapshot(self, metadata: Optional[Dict[str, Any]] = None) -> Snapshot:
        """Create a new snapshot of the current state"""
        return self.snapshot_manager.create_snapshot(metadata)

    def rollback_to_snapshot(self, snapshot: Snapshot) -> bool:
        """Rollback system to a previous snapshot"""
        return self.snapshot_manager.rollback_to_snapshot(snapshot)

    def get_snapshots(self) -> List[Snapshot]:
        """Get system state snapshots"""
        return self.snapshot_manager.get_snapshots()

    def _monitor_loop(self):
        """Main monitoring loop"""
        while not self._stop_event.is_set():
            try:
                self._check_resources()
                time.sleep(1)  # Check every second
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")

    def _check_resources(self):
        """Check system resource usage"""
        current_usage = self.get_resource_usage()
        current_time = time.time()

        # Update history
        with self.history_lock:
            for rt, usage in current_usage.items():
                self.usage_history[rt].append((current_time, usage))
                # Keep last hour of data
                cutoff = current_time - 3600
                self.usage_history[rt] = [
                    (ts, usage) for ts, usage in self.usage_history[rt]
                    if ts >= cutoff
                ]

        # Check limits with more frequent updates for CPU
        for limit in self.resource_limits:
            usage = current_usage[limit.resource_type]
            
            # More aggressive CPU checking
            if limit.resource_type == ResourceType.CPU:
                # Use raw CPU value for immediate response
                if usage > limit.hard_limit:
                    # Trigger callbacks immediately for high CPU
                    for callback in self.action_callbacks[limit.action]:
                        try:
                            callback({
                                "resource_type": limit.resource_type,
                                "usage": usage,
                                "limit": limit.hard_limit,
                                "action": limit.action.name
                            })
                        except Exception as e:
                            logging.error(f"Error in action callback: {e}")
                    continue
                
                # For non-critical CPU, use averaged value
                recent_usage = self.get_usage_history(ResourceType.CPU, minutes=0.05)
                if recent_usage:
                    usage = sum(u for _, u in recent_usage) / len(recent_usage)
            
            if usage > limit.hard_limit:
                # Trigger callbacks
                for callback in self.action_callbacks[limit.action]:
                    try:
                        callback({
                            "resource_type": limit.resource_type,
                            "usage": usage,
                            "limit": limit.hard_limit,
                            "action": limit.action.name
                        })
                    except Exception as e:
                        logging.error(f"Error in action callback: {e}")
            elif usage > limit.soft_limit:
                # Trigger warning callbacks
                for callback in self.action_callbacks[ControlAction.WARN]:
                    try:
                        callback({
                            "resource_type": limit.resource_type,
                            "usage": usage,
                            "limit": limit.soft_limit,
                            "action": ControlAction.WARN.name
                        })
                    except Exception as e:
                        logging.error(f"Error in action callback: {e}")

    def __del__(self):
        """Cleanup on deletion"""
        self.stop()
