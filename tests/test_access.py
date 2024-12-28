"""
Tests for the SACP access control framework
"""

import unittest
from datetime import datetime, timedelta
from src.core.access import (
    Permission,
    AccessToken,
    AccessPolicy,
    AccessManager,
    AccessMonitor
)
from src.core.protocol import SafetyLevel, AccessScope


class TestAccessControl(unittest.TestCase):
    def setUp(self):
        self.access_manager = AccessManager()
        self.access_monitor = AccessMonitor()

    def test_permission_levels(self):
        # Test READ_ONLY permissions
        read_policy = AccessPolicy(SafetyLevel.READ_ONLY)
        self.assertIn(Permission.READ, read_policy.permissions)
        self.assertIn(Permission.ANALYZE, read_policy.permissions)
        self.assertNotIn(Permission.MODIFY, read_policy.permissions)

        # Test SUGGEST_ONLY permissions
        suggest_policy = AccessPolicy(SafetyLevel.SUGGEST_ONLY)
        self.assertIn(Permission.SUGGEST, suggest_policy.permissions)
        self.assertNotIn(Permission.MODIFY, suggest_policy.permissions)

        # Test CONTROLLED permissions
        controlled_policy = AccessPolicy(SafetyLevel.CONTROLLED)
        self.assertIn(Permission.MODIFY, controlled_policy.permissions)
        self.assertNotIn(Permission.EXECUTE, controlled_policy.permissions)

        # Test FULL_ACCESS permissions
        full_policy = AccessPolicy(SafetyLevel.FULL_ACCESS)
        self.assertEqual(len(full_policy.permissions), len(Permission))

    def test_token_creation(self):
        token = self.access_manager.create_token(
            safety_level=SafetyLevel.CONTROLLED,
            access_scope=AccessScope.PROJECT,
            path_patterns=[r"src/.*\.py$"],
            owner="test_user",
            duration=timedelta(hours=1)
        )

        self.assertIsNotNone(token.token_id)
        self.assertEqual(token.safety_level, SafetyLevel.CONTROLLED)
        self.assertEqual(token.access_scope, AccessScope.PROJECT)
        self.assertIn(Permission.MODIFY, token.permissions)

    def test_access_validation(self):
        token = self.access_manager.create_token(
            safety_level=SafetyLevel.CONTROLLED,
            access_scope=AccessScope.PROJECT,
            path_patterns=[r"src/.*\.py$"],
            owner="test_user"
        )

        # Test valid access
        self.assertTrue(
            self.access_manager.validate_access(
                token.token_id,
                Permission.MODIFY,
                "src/main.py"
            )
        )

        # Test invalid path
        self.assertFalse(
            self.access_manager.validate_access(
                token.token_id,
                Permission.MODIFY,
                "src/secrets.env"
            )
        )

        # Test invalid permission
        self.assertFalse(
            self.access_manager.validate_access(
                token.token_id,
                Permission.EXECUTE,
                "src/main.py"
            )
        )

    def test_token_expiration(self):
        token = self.access_manager.create_token(
            safety_level=SafetyLevel.CONTROLLED,
            access_scope=AccessScope.PROJECT,
            path_patterns=[r"src/.*\.py$"],
            owner="test_user",
            duration=timedelta(seconds=1)
        )

        # Token should be valid initially
        self.assertTrue(
            self.access_manager.validate_access(
                token.token_id,
                Permission.READ,
                "src/main.py"
            )
        )

        # Wait for token to expire
        import time
        time.sleep(1.1)

        # Token should be invalid after expiration
        self.assertFalse(
            self.access_manager.validate_access(
                token.token_id,
                Permission.READ,
                "src/main.py"
            )
        )

    def test_token_revocation(self):
        token = self.access_manager.create_token(
            safety_level=SafetyLevel.CONTROLLED,
            access_scope=AccessScope.PROJECT,
            path_patterns=[r"src/.*\.py$"],
            owner="test_user"
        )

        # Token should be valid initially
        self.assertTrue(
            self.access_manager.validate_access(
                token.token_id,
                Permission.READ,
                "src/main.py"
            )
        )

        # Revoke token
        self.access_manager.revoke_token(token.token_id)

        # Token should be invalid after revocation
        self.assertFalse(
            self.access_manager.validate_access(
                token.token_id,
                Permission.READ,
                "src/main.py"
            )
        )

    def test_access_monitoring(self):
        token = self.access_manager.create_token(
            safety_level=SafetyLevel.CONTROLLED,
            access_scope=AccessScope.PROJECT,
            path_patterns=[r"src/.*\.py$"],
            owner="test_user"
        )

        # Log some access attempts
        self.access_monitor.log_access(
            token.token_id,
            Permission.READ,
            "src/main.py",
            granted=True
        )
        self.access_monitor.log_access(
            token.token_id,
            Permission.MODIFY,
            "src/secrets.env",
            granted=False
        )

        # Test access history filtering
        history = self.access_monitor.get_access_history(token_id=token.token_id)
        self.assertEqual(len(history), 2)

        # Test path pattern filtering
        py_files = self.access_monitor.get_access_history(path_pattern=r".*\.py$")
        self.assertEqual(len(py_files), 1)

        # Test time-based filtering
        recent = self.access_monitor.get_access_history(
            start_time=datetime.now() - timedelta(seconds=1)
        )
        self.assertEqual(len(recent), 2)


if __name__ == '__main__':
    unittest.main()
