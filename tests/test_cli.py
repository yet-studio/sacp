"""
Tests for the SACP command-line interface
"""

import unittest
import tempfile
from pathlib import Path
import json
import yaml
from datetime import datetime

from src.cli.main import CommandLineInterface, OutputFormat


class TestCommandLineInterface(unittest.TestCase):
    def setUp(self):
        self.cli = CommandLineInterface()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def create_test_file(self, content: str) -> Path:
        """Create a temporary test file"""
        file_path = Path(self.temp_dir) / "test.py"
        file_path.write_text(content)
        return file_path

    def create_config_file(self, config: dict) -> Path:
        """Create a temporary config file"""
        config_path = Path(self.temp_dir) / "sacp.yaml"
        with open(config_path, "w") as f:
            yaml.safe_dump(config, f)
        return config_path

    def test_verify_command(self):
        # Create test file with violations
        test_file = self.create_test_file("""
        def unsafe_function():
            eval("1 + 1")  # Unsafe eval
        """)
        
        # Create config file
        config = {
            "properties": [
                {
                    "name": "no_eval",
                    "description": "No use of eval()",
                    "property_type": "invariant",
                    "expression": "'eval' not in code",
                    "severity": "CRITICAL"
                }
            ]
        }
        config_file = self.create_config_file(config)
        
        # Run verify command
        args = [
            "verify",
            str(test_file),
            "--config", str(config_file),
            "--format", "json"
        ]
        
        exit_code = self.cli.run(args)
        self.assertEqual(exit_code, 1)  # Should fail due to eval() usage

    def test_check_command(self):
        # Create test file with compliance issues
        test_file = self.create_test_file("""
        import os
        
        def unsafe_function():
            os.system("rm -rf /")  # Shell injection
        """)
        
        # Create custom rules
        rules = {
            "no_shell_injection": {
                "description": "No shell injection vulnerabilities",
                "pattern": r"os\.system\("
            }
        }
        rules_file = Path(self.temp_dir) / "rules.yaml"
        with open(rules_file, "w") as f:
            yaml.safe_dump(rules, f)
        
        # Run check command
        args = [
            "check",
            str(test_file),
            "--rules", str(rules_file),
            "--format", "json"
        ]
        
        exit_code = self.cli.run(args)
        self.assertEqual(exit_code, 1)  # Should fail due to shell injection

    def test_analyze_command(self):
        # Create test file
        test_file = self.create_test_file("""
        def process_data(data: str) -> str:
            return data.upper()
        """)
        
        # Create context file
        context = {
            "user": "test_user",
            "permissions": ["READ"]
        }
        context_file = Path(self.temp_dir) / "context.yaml"
        with open(context_file, "w") as f:
            yaml.safe_dump(context, f)
        
        # Run analyze command
        args = [
            "analyze",
            str(test_file),
            "--context", str(context_file),
            "--format", "json"
        ]
        
        exit_code = self.cli.run(args)
        self.assertEqual(exit_code, 0)  # Should pass for safe code

    def test_init_command(self):
        # Run init command
        args = ["init", "--dir", self.temp_dir]
        exit_code = self.cli.run(args)
        
        # Check if config file was created
        config_path = Path(self.temp_dir) / "sacp.yaml"
        self.assertTrue(config_path.exists())
        
        # Verify config content
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        self.assertEqual(config["version"], "1.0.0")
        self.assertEqual(config["compliance_level"], "standard")
        self.assertTrue("properties" in config)
        self.assertTrue("custom_rules" in config)
        self.assertEqual(exit_code, 0)

    def test_output_formats(self):
        # Create test file
        test_file = self.create_test_file("print('Hello, World!')")
        
        # Test JSON output
        args = ["verify", str(test_file), "--format", "json"]
        self.cli.run(args)
        
        # Test YAML output
        args = ["verify", str(test_file), "--format", "yaml"]
        self.cli.run(args)
        
        # Test text output
        args = ["verify", str(test_file), "--format", "text"]
        self.cli.run(args)

    def test_error_handling(self):
        # Test non-existent file
        args = ["verify", "non_existent.py"]
        exit_code = self.cli.run(args)
        self.assertEqual(exit_code, 1)
        
        # Test invalid config
        args = ["verify", "test.py", "--config", "invalid.yaml"]
        exit_code = self.cli.run(args)
        self.assertEqual(exit_code, 1)
        
        # Test invalid command
        args = ["invalid_command"]
        exit_code = self.cli.run(args)
        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
