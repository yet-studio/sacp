"""
SafeAI CodeGuard Protocol - Safety Validator
Validates operations against safety constraints.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging

from .constraints import (
    SafetyConstraint,
    ResourceConstraint,
    OperationConstraint,
    AccessConstraint,
    ResourceError,
    OperationError,
    AccessError
)


@dataclass
class ValidationResult:
    """Result of a safety validation"""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class SafetyValidator:
    """Validates operations against multiple safety constraints"""
    
    def __init__(self):
        self.constraints: List[SafetyConstraint] = []
        self.logger = logging.getLogger(__name__)
        self.validation_history = []
    
    def add_constraint(self, constraint: SafetyConstraint) -> None:
        """Adds a safety constraint"""
        self.constraints.append(constraint)
    
    def remove_constraint(self, constraint: SafetyConstraint) -> None:
        """Removes a safety constraint"""
        self.constraints.remove(constraint)
    
    async def validate(self, context: Dict[str, Any]) -> ValidationResult:
        """Validates context against all constraints"""
        result = ValidationResult(valid=True)
        
        try:
            # Validate each constraint
            for constraint in self.constraints:
                try:
                    # Run validation in thread pool for CPU-bound constraints
                    is_valid = await asyncio.get_event_loop().run_in_executor(
                        None, constraint.validate, context
                    )
                    
                    if not is_valid:
                        result.valid = False
                        result.errors.append(
                            f"Constraint {constraint.__class__.__name__} failed"
                        )
                
                except Exception as e:
                    result.valid = False
                    result.errors.append(str(e))
                    self.logger.error(
                        f"Constraint validation error: {e}",
                        exc_info=True
                    )
            
            # Record validation
            self.validation_history.append(result)
            
            # Trim history
            if len(self.validation_history) > 1000:
                self.validation_history = self.validation_history[-1000:]
            
            return result
        
        except Exception as e:
            self.logger.error(
                f"Validation error: {e}",
                exc_info=True
            )
            result.valid = False
            result.errors.append(f"Validation error: {str(e)}")
            return result
    
    async def enforce(self, context: Dict[str, Any]) -> None:
        """Enforces all safety constraints"""
        for constraint in self.constraints:
            try:
                # Run enforcement in thread pool
                await asyncio.get_event_loop().run_in_executor(
                    None, constraint.enforce, context
                )
            
            except (ResourceError, OperationError, AccessError) as e:
                self.logger.error(
                    f"Constraint enforcement error: {e}",
                    exc_info=True
                )
                raise
            
            except Exception as e:
                self.logger.error(
                    f"Unexpected enforcement error: {e}",
                    exc_info=True
                )
                raise RuntimeError(f"Safety enforcement failed: {str(e)}")
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Gets validation statistics"""
        if not self.validation_history:
            return {}
        
        total = len(self.validation_history)
        valid = sum(1 for r in self.validation_history if r.valid)
        
        return {
            'total_validations': total,
            'successful_validations': valid,
            'failure_rate': (total - valid) / total if total > 0 else 0,
            'common_errors': self._get_common_errors(),
            'last_validation': self.validation_history[-1].timestamp
        }
    
    def _get_common_errors(self) -> Dict[str, int]:
        """Gets most common validation errors"""
        error_counts = {}
        
        for result in self.validation_history:
            for error in result.errors:
                error_counts[error] = error_counts.get(error, 0) + 1
        
        # Sort by frequency
        return dict(
            sorted(
                error_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        )
