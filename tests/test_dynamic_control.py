"""
Tests for the SACP dynamic control system
"""

import unittest
import tempfile
import time
import threading
from pathlib import Path
import json
import shutil
import os

from src.control.dynamic import (
    ResourceType,
    ControlAction,
    ResourceLimit,
    RateLimit,
    ResourceMonitor,
    RateLimiter,
    SnapshotManager,
    DynamicControlSystem
)


class TestDynamicControl(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.resource_limits = [
            ResourceLimit(
                resource_type=ResourceType.CPU,
                soft_limit=70.0,
                hard_limit=90.0,
                action=ControlAction.THROTTLE
            ),
            ResourceLimit(
                resource_type=ResourceType.MEMORY,
                soft_limit=1000.0,  # MB
                hard_limit=2000.0,  # MB
                action=ControlAction.TERMINATE
            )
        ]
        self.rate_limit = RateLimit(
            operations_per_minute=60,
            burst_limit=10,
            cooldown_seconds=60
        )
        self.control_system = DynamicControlSystem(
            self.temp_dir,
            self.resource_limits,
            self.rate_limit
        )

    def tearDown(self):
        self.control_system.stop()
        shutil.rmtree(self.temp_dir)

    def test_resource_monitoring(self):
        # Start monitoring
        self.control_system.start()
        time.sleep(2)  # Let it collect some data
        
        # Check resource usage
        usage = self.control_system.get_resource_usage()
        self.assertIn(ResourceType.CPU, usage)
        self.assertIn(ResourceType.MEMORY, usage)
        self.assertIn(ResourceType.DISK, usage)
        self.assertIn(ResourceType.NETWORK, usage)
        
        # Check history
        history = self.control_system.get_usage_history(ResourceType.CPU, minutes=1)
        self.assertGreater(len(history), 0)

    def test_rate_limiting(self):
        limiter = RateLimiter(self.rate_limit)
        
        # Should allow burst
        for _ in range(self.rate_limit.burst_limit):
            self.assertTrue(limiter.try_acquire())
        
        # Should deny after burst
        self.assertFalse(limiter.try_acquire())
        
        # Should have non-zero wait time
        self.assertGreater(limiter.get_wait_time(), 0)

    def test_snapshot_management(self):
        # Create some test files
        test_file = Path(self.temp_dir) / "test.txt"
        with open(test_file, "w") as f:
            f.write("test content")
        
        # Create snapshot
        snapshot = self.control_system.create_snapshot({"test": "metadata"})
        self.assertIn(str(test_file), snapshot.files)
        
        # Modify file
        with open(test_file, "w") as f:
            f.write("modified content")
        
        # Rollback
        success = self.control_system.rollback_to_snapshot(snapshot)
        self.assertTrue(success)
        
        # Verify content
        with open(test_file) as f:
            self.assertEqual(f.read(), "test content")

    def test_control_actions(self):
        action_triggered = threading.Event()
        
        def on_throttle(context):
            self.assertEqual(context["resource_type"], ResourceType.CPU)
            action_triggered.set()
        
        # Register callback
        self.control_system.register_callback(ControlAction.THROTTLE, on_throttle)
        
        # Simulate high CPU usage
        def cpu_intensive():
            while not action_triggered.is_set():
                pass  # Burn CPU
        
        # Start CPU-intensive thread
        thread = threading.Thread(target=cpu_intensive)
        thread.daemon = True
        thread.start()
        
        # Wait for action to trigger
        action_triggered.wait(timeout=10)
        self.assertTrue(action_triggered.is_set())

    def test_resource_limits(self):
        warnings = []
        throttles = []
        
        def on_warn(context):
            warnings.append(context)
        
        def on_throttle(context):
            throttles.append(context)
        
        self.control_system.register_callback(ControlAction.WARN, on_warn)
        self.control_system.register_callback(ControlAction.THROTTLE, on_throttle)
        
        # Start system
        self.control_system.start()
        
        # Simulate load
        def generate_load():
            data = []
            for _ in range(1000000):
                data.append(os.urandom(1024))  # Allocate memory
                time.sleep(0.001)
        
        thread = threading.Thread(target=generate_load)
        thread.daemon = True
        thread.start()
        
        # Wait for actions
        time.sleep(5)
        
        # Should have triggered some warnings or throttles
        self.assertTrue(len(warnings) > 0 or len(throttles) > 0)


if __name__ == '__main__':
    unittest.main()