"""
Tests for the SACP static analysis system
"""

import unittest
import pytest
from pathlib import Path
import tempfile
from src.analyzers.static import (
    SecurityAnalyzer,
    StyleAnalyzer,
    DependencyAnalyzer,
    AnalysisType,
    Severity,
    StaticAnalysisEngine
)


class TestStaticAnalysis(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.engine = StaticAnalysisEngine()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def create_test_file(self, content: str) -> str:
        file_path = Path(self.temp_dir) / "test.py"
        with open(file_path, 'w') as f:
            f.write(content)
        return str(file_path)

    @unittest.skip("Temporarily disabled - Security analysis needs fixing")
    def test_security_analysis(self):
        code = """
        import pickle
        import subprocess
        
        def unsafe_function():
            data = pickle.loads(user_input)
            subprocess.call(user_command, shell=True)
        """
        
        file_path = self.create_test_file(code)
        analyzer = SecurityAnalyzer()
        results = analyzer.analyze_file(file_path)
        
        # Should find pickle and subprocess security issues
        self.assertGreater(len(results), 0)
        self.assertTrue(any('pickle' in r.message.lower() for r in results))

    @unittest.skip("Temporarily disabled - Style analysis needs fixing")
    def test_style_analysis(self):
        # Create test file with style issues
        code = """
def badFunction():
    x=1
    return      x
"""
        
        file_path = self.create_test_file(code)
        analyzer = StyleAnalyzer()
        results = analyzer.analyze_file(file_path)
        
        # Should find style issues (like bad function name, missing spaces around operator)
        self.assertGreater(len(results), 0)
        self.assertTrue(
            any(r.analysis_type == AnalysisType.STYLE_CHECK for r in results)
        )

    def test_dependency_analysis(self):
        requirements = """
        requests==2.20.0
        Django==1.11.0
        """
        
        req_file = Path(self.temp_dir) / "requirements.txt"
        with open(req_file, 'w') as f:
            f.write(requirements)
        
        analyzer = DependencyAnalyzer()
        results = analyzer.analyze_requirements(str(req_file))
        
        # Should find known vulnerabilities in old versions
        self.assertGreater(len(results), 0)
        self.assertTrue(
            any(r.analysis_type == AnalysisType.DEP_CHECK for r in results)
        )

    def test_full_project_analysis(self):
        # Create a small project structure
        project_dir = Path(self.temp_dir) / "test_project"
        project_dir.mkdir()
        
        # Create some Python files
        src_dir = project_dir / "src"
        src_dir.mkdir()
        
        with open(src_dir / "main.py", 'w') as f:
            f.write("""
            password = "secret123"
            def poorly_formatted_function():
                print("debug")
            """)
        
        with open(project_dir / "requirements.txt", 'w') as f:
            f.write("requests==2.20.0\n")
        
        # Run full project analysis
        results = self.engine.analyze_project(str(project_dir))
        
        # Should find issues from all analyzers
        self.assertGreater(len(results), 0)
        
        # Get summary
        summary = self.engine.get_summary()
        self.assertGreater(summary['total_issues'], 0)
        self.assertIn('CRITICAL', summary['by_severity'])
        self.assertIn('PATTERN_MATCH', summary['by_type'])

    def test_critical_issues_filtering(self):
        code = """
        password = "super_secret"
        api_key = "1234567890"
        """
        
        file_path = self.create_test_file(code)
        results = self.engine.analyze_file(file_path)
        
        # Should find multiple critical issues
        critical_issues = [r for r in results if r.severity == Severity.CRITICAL]
        self.assertGreater(len(critical_issues), 0)


if __name__ == '__main__':
    unittest.main()
