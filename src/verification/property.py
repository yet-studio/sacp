"""
Module for validating safety properties in code
"""

import ast
import re
import logging
from typing import List, Dict, Any
from .safety import SafetyProperty, VerificationResult, VerificationType

class PropertyValidator:
    """Validates safety properties in Python code"""
    
    def __init__(self):
        self.ast_cache = {}

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
                verification_type=VerificationType.STATIC,
                message="All properties satisfied" if success else "Property violations detected",
                details={"violations": violations} if violations else {}
            )
            
        except Exception as e:
            logging.error(f"Error during property validation: {str(e)}")
            return VerificationResult(
                success=False,
                verification_type=VerificationType.STATIC,
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
