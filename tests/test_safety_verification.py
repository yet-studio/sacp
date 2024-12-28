"""
Tests for the SACP safety verification system
"""

import unittest
import tempfile
from pathlib import Path
import json
from datetime import datetime

from src.verification.safety import (
    VerificationType,
    ComplianceLevel,
    SafetyProperty,
    VerificationResult,
    FormalVerifier,
    PropertyValidator,
    ComplianceChecker,
    TestAutomator,
    SafetyVerification
)


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

    def test_formal_verification(self):
        # Create test file with variables and constraints
        code = """
        x: int
        y: int
        
        assert x > 0
        assert y > x
        """
        
        file_path = self.create_test_file(code)
        
        # Define safety properties
        properties = [
            SafetyProperty(
                name="positive_values",
                description="Values must be positive",
                property_type="invariant",
                expression="x > 0 and y > 0",
                severity="CRITICAL"
            )
        ]
        
        verifier = FormalVerifier()
        result = verifier.verify_invariants(file_path, properties)
        
        self.assertTrue(result.success)
        self.assertEqual(result.verification_type, VerificationType.FORMAL)

    def test_property_validation(self):
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
        
        self.assertFalse(result.success)
        self.assertTrue(any('eval' in v.get('message', '')
                          for v in result.violations))

    def test_compliance_checking(self):
        # Create test file with compliance violations
        code = """
        import os
        
        def unsafe_function():
            os.system("rm -rf /")  # Shell injection
            
        secret_key = "abc123"  # Hardcoded secret
        """
        
        file_path = self.create_test_file(code)
        
        checker = ComplianceChecker(ComplianceLevel.STRICT)
        result = checker.check_compliance(file_path)
        
        self.assertFalse(result.success)
        self.assertTrue(
            any('shell injection' in v.get('details', '').lower()
                for v in result.violations)
        )

    def test_test_automation(self):
        # Create test directory
        test_dir = Path(self.temp_dir) / "tests"
        test_dir.mkdir()
        
        # Create test file
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
        
        automator = TestAutomator()
        result = automator.run_tests(str(test_dir))
        
        self.assertFalse(result.success)
        self.assertTrue(any(v['type'] == 'test_failure'
                          for v in result.violations))

    def test_full_verification(self):
        # Create a small project
        src_dir = Path(self.temp_dir) / "src"
        src_dir.mkdir()
        
        # Create source file
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
            
            class TestMain(unittest.TestCase):
                def test_process_data(self):
                    from src.main import process_data
                    self.assertEqual(process_data(1, 2), 3)
            """)
        
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
        
        # Run full verification
        results = self.verifier.verify_codebase(
            self.temp_dir,
            properties
        )
        
        # Check results
        self.assertTrue(any(r.success for r in results))
        
        # Get summary
        summary = self.verifier.get_verification_summary()
        self.assertGreater(summary['total_checks'], 0)
        self.assertIn('FORMAL', summary['by_type'])

    def test_critical_violations(self):
        # Create file with multiple violations
        code = """
        import os
        import subprocess
        
        password = "secret123"
        
        def unsafe_function(cmd: str) -> None:
            os.system(cmd)  # Shell injection
            eval(cmd)      # Unsafe eval
            
        def untyped_function(x):  # Missing type hints
            return x + 1
        """
        
        file_path = self.create_test_file(code)
        
        properties = [
            SafetyProperty(
                name="no_shell_injection",
                description="No shell injection vulnerabilities",
                property_type="invariant",
                expression="'os.system' not in code",
                severity="CRITICAL"
            ),
            SafetyProperty(
                name="no_eval",
                description="No use of eval()",
                property_type="invariant",
                expression="'eval' not in code",
                severity="CRITICAL"
            )
        ]
        
        results = self.verifier.verify_codebase(
            self.temp_dir,
            properties
        )
        
        # Check for critical violations
        summary = self.verifier.get_verification_summary()
        critical_violations = summary['critical_violations']
        
        self.assertGreater(len(critical_violations), 0)
        self.assertTrue(
            any('shell injection' in str(v).lower()
                for v in critical_violations)
        )


if __name__ == '__main__':
    unittest.main()
