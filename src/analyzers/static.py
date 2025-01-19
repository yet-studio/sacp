"""
SafeAI CodeGuard Protocol - Static Analysis System
Implements code analysis, pattern recognition, and security scanning.
"""

import ast
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from pathlib import Path
import re
from enum import Enum, auto
import logging
import astroid
from pylint.lint import Run
from pylint.reporters import JSONReporter
import bandit
from bandit.core import manager, config
import safety.util
import safety.safety


class AnalysisType(Enum):
    """Types of static analysis"""
    PATTERN_MATCH = auto()    # Pattern-based code analysis
    SECURITY_SCAN = auto()    # Security vulnerability scanning
    STYLE_CHECK = auto()      # Code style conformance
    DEP_CHECK = auto()        # Dependency validation


class Severity(Enum):
    """Severity levels for analysis findings"""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


@dataclass
class AnalysisResult:
    """Result of a static analysis check"""
    analysis_type: AnalysisType
    severity: Severity
    file_path: str
    line_number: int
    message: str
    code: Optional[str] = None
    fix_suggestion: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PatternAnalyzer:
    """Analyzes code for specific patterns and anti-patterns"""

    def __init__(self):
        self.patterns: Dict[str, Dict] = {
            'hardcoded_secrets': {
                'pattern': r'(?i)(password|secret|key|token)\s*=\s*["\'][^"\']+["\']',
                'severity': Severity.CRITICAL,
                'message': 'Hardcoded secret detected'
            },
            'sql_injection': {
                'pattern': r'(?i)execute\s*\(\s*["\'][^"\']*\%s[^"\']*["\']',
                'severity': Severity.CRITICAL,
                'message': 'Potential SQL injection vulnerability'
            },
            'debug_code': {
                'pattern': r'(?i)(print|console\.log)\s*\(',
                'severity': Severity.WARNING,
                'message': 'Debug code detected'
            },
            'unsafe_pickle': {
                'pattern': r'pickle\.loads?\(',
                'severity': Severity.ERROR,
                'message': 'Unsafe pickle usage detected'
            }
        }

    def analyze_file(self, file_path: str) -> List[AnalysisResult]:
        """Analyze a file for pattern matches"""
        results = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                
                for pattern_name, pattern_info in self.patterns.items():
                    matches = re.finditer(pattern_info['pattern'], content)
                    for match in matches:
                        line_no = content.count('\n', 0, match.start()) + 1
                        results.append(AnalysisResult(
                            analysis_type=AnalysisType.PATTERN_MATCH,
                            severity=pattern_info['severity'],
                            file_path=file_path,
                            line_number=line_no,
                            message=pattern_info['message'],
                            code=lines[line_no - 1].strip(),
                            metadata={'pattern_name': pattern_name}
                        ))
        except Exception as e:
            logging.error(f"Error analyzing {file_path}: {str(e)}")
        
        return results


class SecurityAnalyzer:
    """Analyzes code for security issues using Bandit and custom rules"""
    
    def __init__(self):
        self.pattern_analyzer = PatternAnalyzer()

    def analyze_file(self, file_path: str, rules: Optional[Dict] = None) -> List[AnalysisResult]:
        """Analyze a single file for security issues"""
        results = []
        
        # First run Bandit analysis
        try:
            import bandit
            from bandit.core import manager
            from bandit.core import config
            from bandit.core import metrics
            from bandit.core import issue

            # Initialize Bandit manager with basic config
            b_mgr = manager.BanditManager(
                config.BanditConfig(),
                'file'
            )

            # Run analysis
            b_mgr.discover_files([file_path])
            b_mgr.run_tests()

            # Convert Bandit issues to our format
            for issue in b_mgr.get_issue_list():
                severity = self._convert_severity(issue.severity)
                results.append(AnalysisResult(
                    analysis_type=AnalysisType.SECURITY_SCAN,
                    severity=severity,
                    file_path=file_path,
                    line_number=issue.lineno,
                    message=f"{issue.test_id}: {issue.text}",
                    metadata={
                        'test_id': issue.test_id,
                        'confidence': issue.confidence,
                        'cwe': getattr(issue, 'cwe', None)
                    }
                ))

        except Exception as e:
            logging.error(f"Error running security analysis on {file_path}: {str(e)}")
            
        # Then run custom rule analysis if provided
        if rules:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    for rule_name, rule_info in rules.items():
                        pattern = rule_info.get('pattern')
                        if pattern:
                            matches = re.finditer(pattern, content)
                            for match in matches:
                                line_no = content.count('\n', 0, match.start()) + 1
                                results.append(AnalysisResult(
                                    analysis_type=AnalysisType.PATTERN_MATCH,
                                    severity=Severity.ERROR,  # Custom rules are treated as errors
                                    file_path=file_path,
                                    line_number=line_no,
                                    message=rule_info.get('description', f'Violated rule: {rule_name}'),
                                    code=lines[line_no - 1].strip(),
                                    metadata={'rule_name': rule_name}
                                ))
            except Exception as e:
                logging.error(f"Error applying custom rules to {file_path}: {str(e)}")
            
        return results

    def _convert_severity(self, bandit_severity: str) -> Severity:
        """Convert Bandit severity to our severity level"""
        severity_map = {
            'LOW': Severity.INFO,
            'MEDIUM': Severity.WARNING,
            'HIGH': Severity.ERROR
        }
        return severity_map.get(bandit_severity, Severity.WARNING)


class StyleAnalyzer:
    """Analyzes code style using Pylint"""

    def analyze_file(self, file_path: str) -> List[AnalysisResult]:
        """Analyze a file for style issues"""
        results = []
        
        try:
            reporter = JSONReporter()
            Run([file_path], reporter=reporter, exit=False)
            
            for message in reporter.messages:
                results.append(AnalysisResult(
                    analysis_type=AnalysisType.STYLE_CHECK,
                    severity=self._convert_severity(message.category),
                    file_path=file_path,
                    line_number=message.line,
                    message=message.msg,
                    code=message.msg_id,
                    metadata={'symbol': message.symbol}
                ))
        except Exception as e:
            logging.error(f"Error style checking {file_path}: {str(e)}")
        
        return results

    def _convert_severity(self, pylint_category: str) -> Severity:
        """Convert Pylint category to our severity level"""
        mapping = {
            'convention': Severity.INFO,
            'refactor': Severity.INFO,
            'warning': Severity.WARNING,
            'error': Severity.ERROR,
            'fatal': Severity.CRITICAL
        }
        return mapping.get(pylint_category, Severity.WARNING)


class DependencyAnalyzer:
    """Analyzes project dependencies for security issues"""
    
    def analyze_requirements(self, requirements_file: str) -> List[AnalysisResult]:
        """Analyze requirements.txt for known vulnerabilities"""
        results = []
        try:
            # Read and parse requirements file
            with open(requirements_file, 'r') as f:
                requirements = [line.strip() for line in f.readlines() 
                              if line.strip() and not line.startswith('#')]
            
            # Use safety to check for vulnerabilities
            from safety.safety import safety
            checked = safety.check(requirements)
            
            # Process the results
            for vuln in checked:
                if isinstance(vuln, tuple) and len(vuln) >= 5:
                    name, version, spec, reason, vuln_id = vuln[:5]
                    severity = self._convert_severity('high')  # Safety doesn't provide severity
                    results.append(AnalysisResult(
                        analysis_type=AnalysisType.DEP_CHECK,
                        severity=severity,
                        file_path=requirements_file,
                        line_number=0,  # Requirements file
                        message=f"Vulnerability in {name}=={version}: {reason}",
                        metadata={
                            'package': name,
                            'version': version,
                            'vuln_id': vuln_id,
                            'spec': spec,
                            'reason': reason
                        }
                    ))
        except Exception as e:
            logging.error(f"Error analyzing requirements: {str(e)}")
            results.append(AnalysisResult(
                analysis_type=AnalysisType.DEP_CHECK,
                severity=Severity.ERROR,
                file_path=requirements_file,
                line_number=0,
                message=f"Error analyzing dependencies: {str(e)}",
                metadata={'error': str(e)}
            ))
        return results

    def _convert_severity(self, safety_severity: str) -> Severity:
        """Convert Safety severity to our severity level"""
        severity_map = {
            'low': Severity.INFO,
            'medium': Severity.WARNING,
            'high': Severity.ERROR,
            'critical': Severity.CRITICAL
        }
        return severity_map.get(safety_severity.lower(), Severity.WARNING)


class StaticAnalysisEngine:
    """Main engine for running all static analysis checks"""

    def __init__(self):
        self.pattern_analyzer = PatternAnalyzer()
        self.security_analyzer = SecurityAnalyzer()
        self.style_analyzer = StyleAnalyzer()
        self.dependency_analyzer = DependencyAnalyzer()
        self.results: List[AnalysisResult] = []

    def analyze_file(self, file_path: str, security_rules: Optional[Dict] = None) -> List[AnalysisResult]:
        """Run all applicable analyzers on a file"""
        self.results = []
        
        # Only analyze Python files
        if not file_path.endswith('.py'):
            return []
        
        # Run all analyzers
        self.results.extend(self.pattern_analyzer.analyze_file(file_path))
        self.results.extend(self.security_analyzer.analyze_file(file_path, security_rules))
        self.results.extend(self.style_analyzer.analyze_file(file_path))
        
        return self.results

    def analyze_project(self, project_path: str, security_rules: Optional[Dict] = None) -> List[AnalysisResult]:
        """Analyze an entire project"""
        self.results = []
        project_path = Path(project_path)
        
        # Analyze Python files
        for py_file in project_path.rglob('*.py'):
            self.results.extend(self.analyze_file(str(py_file), security_rules))
        
        # Analyze dependencies
        requirements_file = project_path / 'requirements.txt'
        if requirements_file.exists():
            self.results.extend(
                self.dependency_analyzer.analyze_requirements(str(requirements_file))
            )
        
        return self.results

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of analysis results"""
        return {
            'total_issues': len(self.results),
            'by_severity': self._count_by_severity(),
            'by_type': self._count_by_type(),
            'critical_issues': self._get_critical_issues()
        }

    def _count_by_severity(self) -> Dict[str, int]:
        """Count issues by severity"""
        counts = {}
        for result in self.results:
            severity = result.severity.name
            counts[severity] = counts.get(severity, 0) + 1
        return counts

    def _count_by_type(self) -> Dict[str, int]:
        """Count issues by analysis type"""
        counts = {}
        for result in self.results:
            analysis_type = result.analysis_type.name
            counts[analysis_type] = counts.get(analysis_type, 0) + 1
        return counts

    def _get_critical_issues(self) -> List[AnalysisResult]:
        """Get all critical severity issues"""
        return [r for r in self.results if r.severity == Severity.CRITICAL]
