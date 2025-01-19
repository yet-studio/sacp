import unittest
import pytest
from src.analyzers.static import DependencyAnalyzer  # Fixed import path

class TestDependencyAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = DependencyAnalyzer()
        self.requirements_file = 'test_requirements.txt'
        # Create a test requirements file
        with open(self.requirements_file, 'w') as f:
            f.write('requests==2.20.0\nDjango==1.11.0')  # Known vulnerable versions

    def test_analyze_requirements(self):
        results = self.analyzer.analyze_requirements(self.requirements_file)
        self.assertGreater(len(results), 0, "Expected vulnerabilities not found.")

    def tearDown(self):
        import os
        os.remove(self.requirements_file)  # Clean up the test file

if __name__ == '__main__':
    unittest.main()
