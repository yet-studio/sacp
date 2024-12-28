"""
Tests for the SACP validation rules
"""

import unittest
from pathlib import Path
from src.validators.rules import (
    ValidationEngine,
    FileTypeRule,
    FileSizeRule,
    SyntaxRule,
    SecurityPatternRule,
    ModificationScopeRule
)


class TestValidationRules(unittest.TestCase):
    def setUp(self):
        self.engine = ValidationEngine()
        
    def test_file_type_validation(self):
        rule = FileTypeRule(allowed_extensions=['.py', '.txt'])
        self.engine.add_rule(rule)
        
        # Test valid file type
        result = self.engine.validate({'file_path': 'test.py'})
        self.assertTrue(self.engine.is_valid())
        
        # Test invalid file type
        result = self.engine.validate({'file_path': 'test.exe'})
        self.assertFalse(self.engine.is_valid())

    def test_security_patterns(self):
        patterns = {
            'hardcoded_secret': r'(?i)(password|secret|key)\s*=\s*["\'][^"\']+["\']',
            'sql_injection': r'(?i)execute\s*\(\s*["\'][^"\']*\%s[^"\']*["\']'
        }
        rule = SecurityPatternRule(patterns)
        self.engine.add_rule(rule)
        
        # Test safe code
        safe_code = """
        def get_user(user_id):
            return db.query(f"SELECT * FROM users WHERE id = {user_id}")
        """
        result = self.engine.validate({'code': safe_code})
        self.assertTrue(self.engine.is_valid())
        
        # Test unsafe code
        unsafe_code = """
        password = "hardcoded_secret123"
        query = "SELECT * FROM users WHERE name = %s"
        db.execute(query)
        """
        result = self.engine.validate({'code': unsafe_code})
        self.assertFalse(self.engine.is_valid())

    def test_syntax_validation(self):
        rule = SyntaxRule()
        self.engine.add_rule(rule)
        
        # Test valid syntax
        valid_code = """
        def hello():
            print("Hello, World!")
        """
        result = self.engine.validate({'code': valid_code})
        self.assertTrue(self.engine.is_valid())
        
        # Test invalid syntax
        invalid_code = """
        def hello()
            print("Missing colon")
        """
        result = self.engine.validate({'code': invalid_code})
        self.assertFalse(self.engine.is_valid())

    def test_modification_scope(self):
        allowed_paths = ['/project/src', '/project/tests']
        rule = ModificationScopeRule(allowed_paths)
        self.engine.add_rule(rule)
        
        # Test file in allowed path
        result = self.engine.validate({'file_path': '/project/src/main.py'})
        self.assertTrue(self.engine.is_valid())
        
        # Test file outside allowed path
        result = self.engine.validate({'file_path': '/project/config/settings.py'})
        self.assertFalse(self.engine.is_valid())


if __name__ == '__main__':
    unittest.main()
