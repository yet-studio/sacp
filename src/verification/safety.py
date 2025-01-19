"""
SafeAI CodeGuard Protocol - Safety Verification System
Implements formal verification, test automation, compliance checking, and safety validation.
"""

import ast
import inspect
import logging
from typing import Dict, List, Optional, Set, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
import threading
from pathlib import Path
import json
import re
import unittest
import coverage
import z3
from mypy import api as mypy_api
from ..core.protocol import ComplianceLevel
import io


class VerificationType(Enum):
    """Types of safety verification"""
    FORMAL = auto()       # Formal methods verification
    PROPERTY = auto()     # Safety property validation
    COMPLIANCE = auto()   # Compliance rule checking
    TEST = auto()         # Test suite verification


@dataclass
class SafetyProperty:
    """Represents a safety property to verify"""
    name: str
    description: str
    property_type: str  # invariant, precondition, postcondition
    expression: str
    severity: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationResult:
    """Result of a verification check"""
    success: bool
    verification_type: VerificationType
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


class FormalVerifier:
    """Implements formal verification methods"""

    def __init__(self):
        self.solver = z3.Solver()
        self.verified_properties: Dict[str, bool] = {}

    def verify_invariants(
        self,
        code_path: str,
        properties: List[SafetyProperty]
    ) -> VerificationResult:
        """Verify code invariants using Z3 solver"""
        try:
            with open(code_path, 'r') as f:
                code = f.read()
            
            tree = ast.parse(code)
            violations = []
            
            # Extract variables and constraints from code
            variables, constraints = self._extract_constraints(tree)
            
            # Add constraints to solver
            for var_name, var_type in variables.items():
                if var_type == int:
                    variables[var_name] = z3.Int(var_name)
                elif var_type == bool:
                    variables[var_name] = z3.Bool(var_name)
                elif var_type == float:
                    variables[var_name] = z3.Real(var_name)
            
            # Add code constraints
            for constraint in constraints:
                self.solver.add(eval(constraint, variables))
            
            # Verify each property
            for prop in properties:
                try:
                    # Convert property expression to Z3 formula
                    formula = eval(prop.expression, variables)
                    self.solver.push()
                    self.solver.add(z3.Not(formula))
                    
                    if self.solver.check() == z3.sat:
                        # Found counterexample
                        model = self.solver.model()
                        violations.append({
                            'property': prop.name,
                            'counterexample': {
                                str(var): str(model[var])
                                for var in model
                            }
                        })
                    else:
                        self.verified_properties[prop.name] = True
                    
                    self.solver.pop()
                    
                except Exception as e:
                    violations.append({
                        'property': prop.name,
                        'error': str(e)
                    })
            
            return VerificationResult(
                success=len(violations) == 0,
                verification_type=VerificationType.FORMAL,
                message="All properties satisfied" if len(violations) == 0 else "Property violations detected",
                details={"violations": violations} if violations else {}
            )
            
        except Exception as e:
            logging.error(f"Formal verification error: {str(e)}")
            return VerificationResult(
                success=False,
                verification_type=VerificationType.FORMAL,
                message=f"Validation failed: {str(e)}",
                details={"error": str(e)}
            )

    def _extract_constraints(
        self,
        tree: ast.AST
    ) -> Tuple[Dict[str, type], List[str]]:
        """Extract variables and constraints from AST"""
        variables = {}
        constraints = []
        
        for node in ast.walk(tree):
            # Extract variable declarations
            if isinstance(node, ast.AnnAssign) and isinstance(node.annotation, ast.Name):
                var_name = node.target.id
                type_name = node.annotation.id
                if type_name == 'int':
                    variables[var_name] = int
                elif type_name == 'bool':
                    variables[var_name] = bool
                elif type_name == 'float':
                    variables[var_name] = float
            
            # Extract assert statements as constraints
            elif isinstance(node, ast.Assert) and isinstance(node.test, ast.Compare):
                constraints.append(ast.unparse(node.test))
        
        return variables, constraints


class PropertyValidator:
    """Validates safety properties in code"""
    
    def __init__(self):
        self.validated_properties: Dict[str, bool] = {}

    def validate_properties(self, file_path: str, properties: List[SafetyProperty]) -> VerificationResult:
        """Validate safety properties in a Python file"""
        try:
            # Read and parse the file
            with open(file_path, 'r') as f:
                code = f.read()
                tree = ast.parse(code)
            
            violations = []
            
            # Check each property
            for prop in properties:
                if prop.property_type == "invariant":
                    # For invariants, we check if the expression evaluates to True
                    if not self._check_invariant(code, prop):
                        violations.append({
                            "property": prop.name,
                            "description": prop.description,
                            "severity": prop.severity
                        })
            
            success = len(violations) == 0
            return VerificationResult(
                success=success,
                verification_type=VerificationType.PROPERTY,
                message="All properties satisfied" if success else "Property violations detected",
                details={"violations": violations} if violations else {}
            )
            
        except Exception as e:
            logging.error(f"Error during property validation: {str(e)}")
            return VerificationResult(
                success=False,
                verification_type=VerificationType.PROPERTY,
                message=f"Validation failed: {str(e)}",
                details={"error": str(e)}
            )

    def _check_invariant(self, code: str, prop: SafetyProperty) -> bool:
        """Check if an invariant property holds"""
        try:
            # Handle special cases with custom checks
            if "not in code" in prop.expression:
                # Check for presence of specific text
                search_term = prop.expression.split("'")[1]
                return search_term not in code
            
            # For other cases, evaluate the expression in the context of the code
            context = {"code": code}
            return eval(prop.expression, {"__builtins__": {}}, context)
            
        except Exception as e:
            logging.error(f"Error checking invariant {prop.name}: {str(e)}")
            return False


class ComplianceChecker:
    """Checks code compliance against safety rules"""

    def __init__(self, compliance_level: ComplianceLevel):
        self.compliance_level = compliance_level
        self.rules = self._load_compliance_rules()

    def _load_compliance_rules(self) -> Dict[str, Any]:
        """Load compliance rules based on level"""
        rules = {
            'no_eval_exec': {
                'description': 'No use of eval() or exec()',
                'pattern': r'(eval|exec)\s*\('
            },
            'no_shell_injection': {
                'description': 'No shell injection vulnerabilities',
                'pattern': r'os\.system\(|subprocess\.call\('
            },
            'no_hardcoded_secrets': {
                'description': 'No hardcoded secrets',
                'pattern': r'(password|secret|key)\s*=\s*["\'][^"\']+["\']'
            }
        }

        # Add standard rules
        if self.compliance_level == ComplianceLevel.STANDARD:
            rules['standard_rule'] = {
                'description': 'Standard compliance rule',
                'pattern': r'some_pattern'
            }

        return rules

    def check_compliance(
        self,
        code_path: str,
        custom_rules: Optional[Dict[str, Any]] = None
    ) -> VerificationResult:
        """Check code compliance with safety rules"""
        try:
            logging.debug(f"Checking compliance for file: {code_path}")
            logging.debug(f"Loaded rules: {self.rules}")
            violations = []
            rules = {**self.rules}
            if custom_rules:
                rules.update(custom_rules)
            
            with open(code_path, 'r') as f:
                code = f.read()
            
            tree = ast.parse(code)
            
            # Check each rule
            for rule_name, rule_data in rules.items():
                try:
                    if not self._check_rule(tree, rule_data):
                        violations.append({
                            'rule': rule_name,
                            'details': rule_data['description']
                        })
                except Exception as e:
                    violations.append({
                        'rule': rule_name,
                        'error': str(e)
                    })
            
            return VerificationResult(
                success=len(violations) == 0,
                verification_type=VerificationType.COMPLIANCE,
                message="All rules satisfied" if len(violations) == 0 else "Compliance violations detected",
                details={"violations": violations} if violations else {}
            )
            
        except Exception as e:
            logging.error(f"Compliance check error: {str(e)}")
            return VerificationResult(
                success=False,
                verification_type=VerificationType.COMPLIANCE,
                message=f"Validation failed: {str(e)}",
                details={"error": str(e)}
            )

    def _check_rule(self, tree: ast.AST, rule_data: Dict[str, Any]) -> bool:
        """Check if code complies with a rule"""
        if 'pattern' in rule_data:
            code = ast.unparse(tree)
            matches = re.findall(rule_data['pattern'], code)
            return len(matches) == 0
        return True


class TestAutomator:
    """Automates safety test execution"""

    def __init__(self):
        self.test_suites: Dict[str, unittest.TestSuite] = {}
        self.coverage = coverage.Coverage()

    def run_tests(
        self,
        test_path: str,
        coverage_threshold: float = 80.0
    ) -> VerificationResult:
        """Run automated tests with coverage analysis"""
        try:
            violations = []
            
            # Start coverage measurement
            self.coverage.start()
            
            # Discover and run tests
            loader = unittest.TestLoader()
            suite = loader.discover(test_path)
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)
            
            # Stop coverage measurement
            self.coverage.stop()
            
            # Analyze results
            if result.failures:
                for failure in result.failures:
                    violations.append({
                        'type': 'test_failure',
                        'test': str(failure[0]),
                        'details': failure[1]
                    })
            
            if result.errors:
                for error in result.errors:
                    violations.append({
                        'type': 'test_error',
                        'test': str(error[0]),
                        'details': error[1]
                    })
            
            try:
                self.coverage.save()
                coverage_percent = self.coverage.report(file=io.StringIO())
                
                if coverage_percent < coverage_threshold:
                    violations.append({
                        'type': 'coverage',
                        'message': f'Coverage {coverage_percent:.1f}% below threshold {coverage_threshold}%'
                    })
            except Exception as e:
                violations.append({
                    'type': 'coverage_error',
                    'message': f'Failed to analyze coverage: {str(e)}'
                })
            
            return VerificationResult(
                success=len(violations) == 0,
                verification_type=VerificationType.TEST,
                message="All tests passed" if len(violations) == 0 else "Test failures detected",
                details={"violations": violations} if violations else {}
            )
            
        except Exception as e:
            logging.error(f"Test automation error: {str(e)}")
            return VerificationResult(
                success=False,
                verification_type=VerificationType.TEST,
                message=f"Test automation failed: {str(e)}",
                details={"error": str(e)}
            )


class SafetyVerification:
    """Main system for safety verification"""

    def __init__(
        self,
        compliance_level: ComplianceLevel = ComplianceLevel.STANDARD
    ):
        self.formal_verifier = FormalVerifier()
        self.property_validator = PropertyValidator()
        self.compliance_checker = ComplianceChecker(compliance_level)
        self.test_automator = TestAutomator()
        
        self.verification_results: List[VerificationResult] = []
        self.results_lock = threading.Lock()

    def verify_codebase(
        self,
        code_dir: str,
        properties: List[SafetyProperty],
        custom_rules: Optional[Dict[str, Any]] = None,
        coverage_threshold: float = 80.0
    ) -> List[VerificationResult]:
        """Run all verification checks on a codebase"""
        results = []
        
        try:
            logging.debug(f"Verifying codebase in directory: {code_dir}")
            logging.debug(f"Properties being checked: {properties}")
            logging.debug(f"Custom rules being applied: {custom_rules}")
            
            # Find all Python files
            code_files = list(Path(code_dir).rglob("*.py"))
            
            # Run formal verification
            for file in code_files:
                result = self.formal_verifier.verify_invariants(
                    str(file),
                    properties
                )
                results.append(result)
            
            # Validate safety properties
            for file in code_files:
                result = self.property_validator.validate_properties(
                    str(file),
                    properties
                )
                results.append(result)
            
            # Check compliance
            for file in code_files:
                result = self.compliance_checker.check_compliance(
                    str(file),
                    custom_rules
                )
                results.append(result)
            
            # Run tests
            test_dir = Path(code_dir) / "tests"
            if test_dir.exists():
                result = self.test_automator.run_tests(
                    str(test_dir),
                    coverage_threshold
                )
                results.append(result)
            
            # Store results
            with self.results_lock:
                self.verification_results.extend(results)
            
            return results
            
        except Exception as e:
            logging.error(f"Verification error: {str(e)}")
            return results

    def get_verification_summary(self) -> Dict[str, Any]:
        """Get summary of verification results"""
        with self.results_lock:
            return {
                'total_checks': len(self.verification_results),
                'passed': len([r for r in self.verification_results if r.success]),
                'failed': len([r for r in self.verification_results if not r.success]),
                'by_type': self._count_by_type(),
                'critical_violations': self._get_critical_violations()
            }

    def _count_by_type(self) -> Dict[str, Dict[str, int]]:
        """Count results by verification type"""
        counts = {}
        for result in self.verification_results:
            vtype = result.verification_type.name
            if vtype not in counts:
                counts[vtype] = {'passed': 0, 'failed': 0}
            if result.success:
                counts[vtype]['passed'] += 1
            else:
                counts[vtype]['failed'] += 1
        return counts

    def _get_critical_violations(self) -> List[Dict[str, Any]]:
        """Get all critical violations"""
        critical = []
        for result in self.verification_results:
            if not result.success:
                for violation in result.details.get('violations', []):
                    if violation.get('severity') == 'CRITICAL':
                        critical.append({
                            'type': result.verification_type.name,
                            'violation': violation
                        })
        return critical
