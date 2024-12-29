"""
Tests for the SACP audit logging system
"""

import unittest
from datetime import datetime, timedelta
import tempfile
from pathlib import Path
import json
import time

from src.core.audit import (
    AuditEventType,
    AuditSeverity,
    AuditEvent,
    AuditStore,
    AuditLogger,
    AuditAnalyzer
)
from src.core.protocol import SafetyLevel, AccessScope
from src.core.access import Permission


class TestAuditSystem(unittest.TestCase):
    def setUp(self):
        # Create temporary directory for audit logs
        self.temp_dir = tempfile.mkdtemp()
        self.store = AuditStore(Path(self.temp_dir))
        self.logger = AuditLogger(self.store)
        self.analyzer = AuditAnalyzer(self.store)

    def tearDown(self):
        self.logger.stop()
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_event_logging(self):
        # Log a test event
        self.logger.log_event(
            event_type=AuditEventType.FILE_READ,
            severity=AuditSeverity.INFO,
            safety_level=SafetyLevel.CONTROLLED,
            access_scope=AccessScope.PROJECT,
            user_id="test_user",
            token_id="test_token",
            resource_path="/test/file.py",
            operation=Permission.READ,
            details={"size": 1024},
            metadata={"version": "1.0"}
        )

        # Wait for event to be processed
        self.logger.event_queue.join()
        time.sleep(0.1)  # Give a bit more time for file writing

        # Query the event
        events = self.store.query_events(
            start_time=datetime.now() - timedelta(seconds=10)
        )

        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event.event_type, AuditEventType.FILE_READ)
        self.assertEqual(event.user_id, "test_user")
        self.assertEqual(event.resource_path, "/test/file.py")

    def test_event_filtering(self):
        # Log multiple events
        for i in range(5):
            self.logger.log_event(
                event_type=AuditEventType.FILE_READ,
                severity=AuditSeverity.INFO,
                safety_level=SafetyLevel.CONTROLLED,
                access_scope=AccessScope.PROJECT,
                user_id=f"user_{i}",
                resource_path=f"/test/file_{i}.py",
                operation=Permission.READ
            )

        self.logger.log_event(
            event_type=AuditEventType.ACCESS_DENIED,
            severity=AuditSeverity.WARNING,
            safety_level=SafetyLevel.CONTROLLED,
            access_scope=AccessScope.PROJECT,
            user_id="user_0",
            resource_path="/test/secret.py",
            operation=Permission.MODIFY
        )

        # Wait for events to be processed
        self.logger.event_queue.join()
        time.sleep(0.1)

        # Test filtering by user
        user_events = self.store.query_events(user_id="user_0")
        self.assertEqual(len(user_events), 2)

        # Test filtering by event type
        denied_events = self.store.query_events(
            event_types=[AuditEventType.ACCESS_DENIED]
        )
        self.assertEqual(len(denied_events), 1)

        # Test filtering by severity
        warning_events = self.store.query_events(
            severity=AuditSeverity.WARNING
        )
        self.assertEqual(len(warning_events), 1)

    def test_anomaly_detection(self):
        # Log some normal events
        for _ in range(8):
            self.logger.log_event(
                event_type=AuditEventType.ACCESS_GRANTED,
                severity=AuditSeverity.INFO,
                safety_level=SafetyLevel.CONTROLLED,
                access_scope=AccessScope.PROJECT,
                user_id="test_user",
                operation=Permission.READ
            )

        # Log some denied events
        for _ in range(2):
            self.logger.log_event(
                event_type=AuditEventType.ACCESS_DENIED,
                severity=AuditSeverity.WARNING,
                safety_level=SafetyLevel.CONTROLLED,
                access_scope=AccessScope.PROJECT,
                user_id="test_user",
                operation=Permission.MODIFY
            )

        # Wait for events to be processed
        self.logger.event_queue.join()
        time.sleep(0.1)

        # Get activity summary
        summary = self.analyzer.get_activity_summary(
            start_time=datetime.now() - timedelta(minutes=5),
            end_time=datetime.now()
        )

        self.assertEqual(summary['total_events'], 10)
        self.assertEqual(summary['by_type']['ACCESS_GRANTED'], 8)
        self.assertEqual(summary['by_type']['ACCESS_DENIED'], 2)
        self.assertEqual(summary['access_denied_rate'], 0.2)

    def test_file_rotation(self):
        # Set a very small file size limit for testing
        self.store.file_size_limit = 100  # bytes
        
        # Log enough events to trigger rotation
        for i in range(10):
            self.logger.log_event(
                event_type=AuditEventType.FILE_READ,
                severity=AuditSeverity.INFO,
                safety_level=SafetyLevel.CONTROLLED,
                access_scope=AccessScope.PROJECT,
                user_id="test_user",
                details={"large": "x" * 200}  # Make event data large enough to force rotation
            )
            time.sleep(0.01)  # Give a small delay to ensure different timestamps

        # Wait for events to be processed
        self.logger.event_queue.join()
        time.sleep(0.1)  # Give a bit more time for file writing

        # Check that multiple log files were created
        log_files = list(Path(self.temp_dir).glob("audit_*.jsonl"))
        self.assertGreater(len(log_files), 1, f"Expected multiple log files, got {len(log_files)}")

        # Verify all events can still be queried
        all_events = self.store.query_events()
        self.assertEqual(len(all_events), 10)


if __name__ == '__main__':
    unittest.main()
