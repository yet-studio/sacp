"""
SafeAI CodeGuard Protocol - Validation Rules
Defines the core validation rules and checks for AI operations.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import re
import ast


@dataclass
class ValidationResult:
    """Represents the result of a validation check"""
    is_valid: bool
    rule_id: str
    message: str
    severity: str  # 'error', 'warning', 'info'
    context: Optional[Dict[str, Any]] = None


class BaseRule:
    """Base class for all validation rules"""
    
    def __init__(self, rule_id: str, severity: str = 'error'):
        self.rule_id = rule_id
        self.severity = severity

    def validate(self, context: Dict[str, Any]) -> ValidationResult:
        """Base validation method to be implemented by specific rules"""
        raise NotImplementedError


class FileTypeRule(BaseRule):
    """Validates file types against allowed extensions"""
    
    def __init__(self, allowed_extensions: List[str]):
        super().__init__('FILE_TYPE_CHECK')
        self.allowed_extensions = allowed_extensions

    def validate(self, context: Dict[str, Any]) -> ValidationResult:
        file_path = Path(context.get('file_path', ''))
        extension = file_path.suffix.lower()
        
        is_valid = extension in self.allowed_extensions
        message = (
            f"File type '{extension}' is allowed"
            if is_valid
            else f"File type '{extension}' is not in allowed types: {self.allowed_extensions}"
        )
        
        return ValidationResult(
            is_valid=is_valid,
            rule_id=self.rule_id,
            message=message,
            severity=self.severity
        )


class FileSizeRule(BaseRule):
    """Validates file size against maximum allowed size"""
    
    def __init__(self, max_size_bytes: int):
        super().__init__('FILE_SIZE_CHECK')
        self.max_size_bytes = max_size_bytes

    def validate(self, context: Dict[str, Any]) -> ValidationResult:
        file_path = Path(context.get('file_path', ''))
        if not file_path.exists():
            return ValidationResult(
                is_valid=False,
                rule_id=self.rule_id,
                message=f"File not found: {file_path}",
                severity=self.severity
            )

        file_size = file_path.stat().st_size
        is_valid = file_size <= self.max_size_bytes
        
        message = (
            f"File size ({file_size} bytes) is within limit"
            if is_valid
            else f"File size ({file_size} bytes) exceeds maximum allowed size ({self.max_size_bytes} bytes)"
        )
        
        return ValidationResult(
            is_valid=is_valid,
            rule_id=self.rule_id,
            message=message,
            severity=self.severity
        )


class SyntaxRule(BaseRule):
    """Validates Python code syntax"""
    
    def __init__(self):
        super().__init__('SYNTAX_CHECK')

    def validate(self, context: Dict[str, Any]) -> ValidationResult:
        """Validate Python code syntax"""
        code = context.get('code', '')
        if not code:
            return ValidationResult(
                is_valid=False,
                rule_id=self.rule_id,
                message="No code provided for syntax check",
                severity=self.severity
            )

        # Remove any leading whitespace to avoid indentation errors
        code = code.strip()
        if not code:
            return ValidationResult(
                is_valid=False,
                rule_id=self.rule_id,
                message="Empty code after stripping whitespace",
                severity=self.severity
            )

        try:
            ast.parse(code)
            return ValidationResult(
                is_valid=True,
                rule_id=self.rule_id,
                message="Code syntax is valid",
                severity=self.severity
            )
        except SyntaxError as e:
            return ValidationResult(
                is_valid=False,
                rule_id=self.rule_id,
                message=f"Syntax error: {str(e)}",
                severity=self.severity,
                context={'error': str(e), 'line': e.lineno, 'offset': e.offset}
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                rule_id=self.rule_id,
                message=f"Error parsing code: {str(e)}",
                severity=self.severity
            )


class SecurityPatternRule(BaseRule):
    """Validates code against known security patterns"""
    
    def __init__(self, patterns: Dict[str, str]):
        """
        Initialize with patterns dictionary where:
        - key: pattern name
        - value: regex pattern to match
        """
        super().__init__('SECURITY_PATTERN_CHECK')
        self.patterns = {name: re.compile(pattern) for name, pattern in patterns.items()}

    def validate(self, context: Dict[str, Any]) -> ValidationResult:
        code = context.get('code', '')
        violations = []
        
        for name, pattern in self.patterns.items():
            matches = pattern.finditer(code)
            for match in matches:
                violations.append({
                    'pattern': name,
                    'line': code.count('\n', 0, match.start()) + 1,
                    'match': match.group()
                })
        
        is_valid = len(violations) == 0
        message = (
            "No security pattern violations found"
            if is_valid
            else f"Found {len(violations)} security pattern violation(s)"
        )
        
        return ValidationResult(
            is_valid=is_valid,
            rule_id=self.rule_id,
            message=message,
            severity=self.severity,
            context={'violations': violations} if violations else None
        )


class ModificationScopeRule(BaseRule):
    """Validates that code modifications are within allowed scope"""
    
    def __init__(self, allowed_paths: List[str]):
        super().__init__('MODIFICATION_SCOPE_CHECK')
        self.allowed_paths = [Path(p) for p in allowed_paths]

    def validate(self, context: Dict[str, Any]) -> ValidationResult:
        file_path = Path(context.get('file_path', ''))
        
        # Check if file_path is within any allowed path
        is_allowed = any(
            str(file_path).startswith(str(allowed_path))
            for allowed_path in self.allowed_paths
        )
        
        message = (
            f"File {file_path} is within allowed scope"
            if is_allowed
            else f"File {file_path} is outside allowed modification scope"
        )
        
        return ValidationResult(
            is_valid=is_allowed,
            rule_id=self.rule_id,
            message=message,
            severity=self.severity
        )


class ValidationEngine:
    """Main engine for running validation rules"""
    
    def __init__(self):
        self.rules: List[BaseRule] = []
        self.results: List[ValidationResult] = []

    def add_rule(self, rule: BaseRule):
        """Add a validation rule to the engine"""
        self.rules.append(rule)

    def validate(self, context: Dict[str, Any]) -> List[ValidationResult]:
        """Run all validation rules against the given context"""
        self.results = []
        
        for rule in self.rules:
            result = rule.validate(context)
            self.results.append(result)
        
        return self.results

    def is_valid(self) -> bool:
        """Check if all validations passed"""
        return all(result.is_valid for result in self.results)

    def get_errors(self) -> List[ValidationResult]:
        """Get all validation errors"""
        return [r for r in self.results if not r.is_valid and r.severity == 'error']

    def get_warnings(self) -> List[ValidationResult]:
        """Get all validation warnings"""
        return [r for r in self.results if not r.is_valid and r.severity == 'warning']
