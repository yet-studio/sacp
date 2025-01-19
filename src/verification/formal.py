"""
Module for formal verification of safety properties using Z3 solver
"""

import ast
import logging
from typing import List, Dict, Any, Optional
from z3 import Solver, Int, Bool, And, Or, Not, parse_smt2_string, sat, unsat
from .safety import SafetyProperty, VerificationResult, VerificationType

class FormalVerifier:
    """Verifies formal properties using Z3 SMT solver"""
    
    def __init__(self):
        self.solver = Solver()
        self.variables: Dict[str, Any] = {}

    def verify_invariants(self, file_path: str, properties: List[SafetyProperty]) -> VerificationResult:
        """Verify invariant properties using Z3 solver"""
        try:
            # Parse the Python file
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())
            
            # Extract variables and constraints from AST
            self._extract_variables(tree)
            constraints = self._extract_constraints(tree)
            
            # Add all constraints to solver
            for constraint in constraints:
                self.solver.add(constraint)
            
            # Add property constraints
            for prop in properties:
                if prop.property_type == "invariant":
                    constraint = self._parse_expression(prop.expression)
                    self.solver.add(constraint)
            
            # Check satisfiability
            result = self.solver.check()
            success = result == sat
            
            return VerificationResult(
                success=success,
                verification_type=VerificationType.FORMAL,
                message="All invariants satisfied" if success else "Invariant violation detected",
                details={
                    "solver_result": str(result),
                    "model": str(self.solver.model()) if success else None
                }
            )
            
        except Exception as e:
            logging.error(f"Error during formal verification: {str(e)}")
            return VerificationResult(
                success=False,
                verification_type=VerificationType.FORMAL,
                message=f"Verification failed: {str(e)}",
                details={"error": str(e)}
            )

    def _extract_variables(self, tree: ast.AST) -> None:
        """Extract variable declarations from AST"""
        for node in ast.walk(tree):
            if isinstance(node, ast.AnnAssign):
                var_name = node.target.id
                var_type = node.annotation.id
                if var_type == 'int':
                    self.variables[var_name] = Int(var_name)
                elif var_type == 'bool':
                    self.variables[var_name] = Bool(var_name)

    def _extract_constraints(self, tree: ast.AST) -> List[Any]:
        """Extract constraints from assert statements"""
        constraints = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assert):
                constraint = self._parse_expression(ast.unparse(node.test))
                if constraint is not None:
                    constraints.append(constraint)
        return constraints

    def _parse_expression(self, expr: str) -> Optional[Any]:
        """Parse a Python expression into Z3 constraints"""
        try:
            # Replace Python operators with Z3 equivalents
            expr = expr.replace('and', '&&').replace('or', '||').replace('not', '!')
            
            # Create SMT-LIB expression
            vars_decl = '\n'.join(f'(declare-const {name} {type(var).__name__.lower()})' 
                                for name, var in self.variables.items())
            smt_expr = f'(assert {expr})'
            
            # Parse SMT-LIB string
            parsed = parse_smt2_string(f'{vars_decl}\n{smt_expr}')
            return parsed[-1] if parsed else None
            
        except Exception as e:
            logging.error(f"Error parsing expression '{expr}': {str(e)}")
            return None
