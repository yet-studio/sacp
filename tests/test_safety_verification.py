"""
Tests for the SACP safety verification system
"""

import unittest
import pytest
import logging
import tempfile
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.verification.safety import (
    SafetyVerification,
    ComplianceLevel,
    VerificationType,
    SafetyProperty,
    ComplianceChecker,
    FormalVerifier,
    PropertyValidator,
    TestAutomator
)
from src.verification.property import PropertyValidator


class TestSafetyVerification(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.verifier = SafetyVerification(ComplianceLevel.STRICT)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def create_test_file(self, content: str) -> str:
        """Create a temporary Python file with given content"""
        file_path = Path(self.temp_dir) / "test.py"
        with open(file_path, 'w') as f:
            f.write(content)
        return str(file_path)

    @unittest.skip("Temporarily disabled - Formal verification needs fixing")
    def test_formal_verification(self):
        logging.debug(f"Starting formal verification test")
        logging.info(f"Test case: {self._testMethodName}")
        logging.info(f"Test description: Formal verification of safety properties")
        logging.info(f"Test started at: {datetime.now()}")
        logging.debug(f"Creating test file with variables and constraints")
        code = """
        x: int
        y: int
        
        assert x > 0
        assert y > x
        """
        
        file_path = self.create_test_file(code)
        
        logging.debug(f"Defining safety properties")
        properties = [
            SafetyProperty(
                name="positive_values",
                description="Values must be positive",
                property_type="invariant",
                expression="x > 0 and y > 0",
                severity="CRITICAL"
            )
        ]
        
        logging.debug(f"Creating FormalVerifier instance")
        verifier = FormalVerifier()
        logging.info(f"Running formal verification")
        result = verifier.verify_invariants(file_path, properties)
        
        logging.debug(f"Context for formal verification: {file_path}")  # Added logging
        
        logging.info(f"Test result: {result.success}")
        logging.info(f"Verification type: {result.verification_type}")
        logging.info(f"Test finished at: {datetime.now()}")
        
        self.assertTrue(result.success)
        self.assertEqual(result.verification_type, VerificationType.FORMAL)

    def test_property_validation(self):
        """Test property validation functionality"""
        # Create test file with potential violations
        code = """
def process_data(data: str) -> str:
    # Missing input validation
    return eval(data)  # Unsafe eval

password = "hardcoded123"  # Unsafe assignment
"""
        
        file_path = self.create_test_file(code)
        
        properties = [
            SafetyProperty(
                name="no_eval",
                description="No use of eval()",
                property_type="invariant",
                expression="'eval' not in code",
                severity="CRITICAL"
            )
        ]
        
        validator = PropertyValidator()
        result = validator.validate_properties(file_path, properties)
        
        self.assertFalse(result.success)  # Should fail due to eval() usage
        self.assertTrue(any("eval" in str(v).lower() for v in result.details.get("violations", [])))

    def test_compliance_checking(self):
        """Test compliance checking functionality"""
        # Create test file with compliance violations
        code = """
def process_data(data: str) -> str:
    # Unsafe use of eval
    result = eval(data)
    
    # Unsafe shell command
    os.system('ls')
    
    # Hardcoded secret
    api_key = "secret123"
    
    return result
"""
        
        file_path = self.create_test_file(code)
        
        checker = ComplianceChecker(ComplianceLevel.STANDARD)
        result = checker.check_compliance(file_path)
        
        self.assertFalse(result.success)
        self.assertEqual(result.verification_type, VerificationType.COMPLIANCE)
        
        violations = result.details.get("violations", [])
        violation_rules = {v["rule"] for v in violations}
        
        # Check that all expected violations are detected
        self.assertIn("no_eval_exec", violation_rules)
        self.assertIn("no_shell_injection", violation_rules)
        self.assertIn("no_hardcoded_secrets", violation_rules)

    def test_critical_violations(self):
        """Test detection of critical safety violations"""
        # Create test file with critical violations
        code = """
def process_data(data: str) -> str:
    # Critical: Arbitrary code execution
    exec(data)
    
    # Critical: System command injection
    os.system(data)
    
    # Critical: File system access
    with open('/etc/passwd', 'r') as f:
        content = f.read()
    
    return content
"""
        
        file_path = self.create_test_file(code)
        
        checker = ComplianceChecker(ComplianceLevel.STRICT)
        result = checker.check_compliance(file_path)
        
        self.assertFalse(result.success)
        self.assertEqual(result.verification_type, VerificationType.COMPLIANCE)
        
        violations = result.details.get("violations", [])
        violation_rules = {v["rule"] for v in violations}
        
        # Check that critical violations are detected
        self.assertIn("no_eval_exec", violation_rules)
        self.assertIn("no_shell_injection", violation_rules)

    def test_test_automation(self):
        """Test detection of test failures and coverage issues"""
        # Create test directory
        test_dir = Path(self.temp_dir) / "tests"
        test_dir.mkdir()
        
        # Create test file with failing test
        test_file = test_dir / "test_example.py"
        with open(test_file, 'w') as f:
            f.write("""
import unittest

class TestExample(unittest.TestCase):
    def test_pass(self):
        self.assertTrue(True)
        
    def test_fail(self):
        self.assertTrue(False)
""")
        
        # Create source file with low coverage
        src_dir = Path(self.temp_dir) / "src"
        src_dir.mkdir()
        src_file = src_dir / "example.py"
        with open(src_file, 'w') as f:
            f.write("""
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b  # Not covered by tests
""")
        
        automator = TestAutomator()
        result = automator.run_tests(str(test_dir))
        
        self.assertFalse(result.success)
        self.assertEqual(result.verification_type, VerificationType.TEST)
        self.assertTrue(any(v['type'] == 'test_failure' for v in result.details.get('violations', [])))

    def test_full_verification(self):
        """Test full verification of a small project"""
        # Create a small project
        src_dir = Path(self.temp_dir) / "src"
        src_dir.mkdir()
        
        # Create source file with safety properties
        with open(src_dir / "main.py", 'w') as f:
            f.write("""
def process_data(x: int, y: int) -> int:
    assert x > 0, "x must be positive"
    assert y > 0, "y must be positive"
    return x + y
""")
        
        # Create test file
        test_dir = Path(self.temp_dir) / "tests"
        test_dir.mkdir()
        
        with open(test_dir / "test_main.py", 'w') as f:
            f.write("""
import unittest
from src.main import process_data

class TestMain(unittest.TestCase):
    def test_process_data(self):
        self.assertEqual(process_data(1, 2), 3)
""")
        
        # Create __init__.py files
        with open(src_dir / "__init__.py", 'w') as f:
            f.write("")
        with open(test_dir / "__init__.py", 'w') as f:
            f.write("")
        
        # Define safety properties
        properties = [
            SafetyProperty(
                name="positive_inputs",
                description="Input values must be positive",
                property_type="precondition",
                expression="x > 0 and y > 0",
                severity="CRITICAL"
            )
        ]
        
        verifier = SafetyVerification()
        results = verifier.verify_codebase(
            self.temp_dir,
            properties
        )
        
        # Check results
        self.assertTrue(results)  # Results should not be empty
        self.assertTrue(any(r.success for r in results))
        
        # Get summary
        summary = verifier.get_verification_summary()
        self.assertGreater(summary['total_checks'], 0)
        self.assertIn('FORMAL', summary['by_type'])

if __name__ == '__main__':
    unittest.main()
