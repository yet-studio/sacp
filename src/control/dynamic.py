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
    files: Dict[str, str]  # path -> hash
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

        # Hash all files
        for file_path in self.base_dir.rglob("*"):
            if file_path.is_file() and ".snapshots" not in str(file_path):
                with open(file_path, "rb") as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
                snapshot.files[str(file_path)] = file_hash

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
        # Verify files haven't been tampered with
        for file_path, expected_hash in snapshot.files.items():
            try:
                with open(file_path, "rb") as f:
                    current_hash = hashlib.sha256(f.read()).hexdigest()
                if current_hash != expected_hash:
                    # Restore file from backup
                    backup_path = self.snapshots_dir / f"backup_{snapshot.timestamp.isoformat()}" / file_path
                    if backup_path.exists():
                        shutil.copy2(str(backup_path), file_path)
                    else:
                        logging.error(f"Backup not found for {file_path}")
                        return False
            except Exception as e:
                logging.error(f"Error during rollback: {str(e)}")
                return False
        return True


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
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        
        # Resource usage history
        self.usage_history: Dict[ResourceType, List[float]] = {
            rt: [] for rt in ResourceType
        }
        self.history_lock = threading.Lock()
        
        # Callbacks for different actions
        self.action_callbacks: Dict[ControlAction, List[Callable]] = {
            action: [] for action in ControlAction
        }

    def start(self):
        """Start the monitoring system"""
        self.running = True
        self.monitor_thread.start()
        logging.info("Dynamic control system started")

    def stop(self):
        """Stop the monitoring system"""
        self.running = False
        self.monitor_thread.join()
        logging.info("Dynamic control system stopped")

    def register_callback(self, action: ControlAction, callback: Callable):
        """Register a callback for a specific control action"""
        self.action_callbacks[action].append(callback)

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Check resource usage
                cpu = self.resource_monitor.get_cpu_usage()
                memory = self.resource_monitor.get_memory_usage()
                disk = self.resource_monitor.get_disk_usage()
                network = self.resource_monitor.get_network_usage()
                
                # Update history
                with self.history_lock:
                    self.usage_history[ResourceType.CPU].append(cpu)
                    self.usage_history[ResourceType.MEMORY].append(memory)
                    self.usage_history[ResourceType.DISK].append(disk)
                    self.usage_history[ResourceType.NETWORK].append(network)
                    
                    # Keep last hour of data
                    window = 3600  # 1 hour in seconds
                    for resource_type in ResourceType:
                        self.usage_history[resource_type] = \
                            self.usage_history[resource_type][-window:]
                
                # Check limits
                current_usage = {
                    ResourceType.CPU: cpu,
                    ResourceType.MEMORY: memory,
                    ResourceType.DISK: disk,
                    ResourceType.NETWORK: network
                }
                
                for limit in self.resource_limits:
                    usage = current_usage[limit.resource_type]
                    if usage > limit.hard_limit:
                        self._trigger_action(limit.action, {
                            "resource_type": limit.resource_type,
                            "current_usage": usage,
                            "limit": limit.hard_limit
                        })
                    elif usage > limit.soft_limit:
                        self._trigger_action(ControlAction.WARN, {
                            "resource_type": limit.resource_type,
                            "current_usage": usage,
                            "limit": limit.soft_limit
                        })
            
            except Exception as e:
                logging.error(f"Error in monitor loop: {str(e)}")
            
            time.sleep(1)  # Check every second

    def _trigger_action(self, action: ControlAction, context: Dict[str, Any]):
        """Trigger control action and associated callbacks"""
        logging.info(f"Triggering action {action.name} with context {context}")
        for callback in self.action_callbacks[action]:
            try:
                callback(context)
            except Exception as e:
                logging.error(f"Error in action callback: {str(e)}")

    def check_rate_limit(self) -> bool:
        """Check if operation is allowed under rate limit"""
        return self.rate_limiter.try_acquire()

    def create_snapshot(self, metadata: Dict[str, Any] = None) -> Snapshot:
        """Create a new system snapshot"""
        return self.snapshot_manager.create_snapshot(metadata)

    def rollback_to_snapshot(self, snapshot: Snapshot) -> bool:
        """Rollback to a previous snapshot"""
        return self.snapshot_manager.rollback_to_snapshot(snapshot)

    def get_resource_usage(self) -> Dict[ResourceType, float]:
        """Get current resource usage"""
        return {
            ResourceType.CPU: self.resource_monitor.get_cpu_usage(),
            ResourceType.MEMORY: self.resource_monitor.get_memory_usage(),
            ResourceType.DISK: self.resource_monitor.get_disk_usage(),
            ResourceType.NETWORK: self.resource_monitor.get_network_usage()
        }

    def get_usage_history(
        self,
        resource_type: ResourceType,
        minutes: int = 60
    ) -> List[float]:
        """Get resource usage history"""
        with self.history_lock:
            history = self.usage_history[resource_type]
            return history[-minutes * 60:]  # Last N minutes of data
