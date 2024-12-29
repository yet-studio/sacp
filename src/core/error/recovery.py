"""
SafeAI CodeGuard Protocol - Error Recovery
Error recovery strategies and management.
"""

import logging
from typing import Dict, Type, Callable, Any, Optional
from datetime import datetime, timedelta

from .exceptions import (
    SACPError,
    RecoveryError,
    SafetyViolationError,
    ResourceExhaustedError
)


class RecoveryStrategy:
    """Base class for recovery strategies"""
    
    def __init__(self, max_attempts: int = 3):
        self.max_attempts = max_attempts
        self.attempts = 0
        self.last_attempt = None
        self.logger = logging.getLogger(__name__)
    
    def can_attempt(self) -> bool:
        """Check if recovery can be attempted"""
        if self.attempts >= self.max_attempts:
            return False
        
        if self.last_attempt:
            # Enforce cooldown period
            cooldown = timedelta(seconds=2 ** self.attempts)
            if datetime.now() - self.last_attempt < cooldown:
                return False
        
        return True
    
    def attempt(self, error: SACPError) -> bool:
        """Attempt recovery from error"""
        if not self.can_attempt():
            return False
        
        try:
            self.attempts += 1
            self.last_attempt = datetime.now()
            return self._execute(error)
        
        except Exception as e:
            self.logger.error(
                f"Recovery attempt failed: {e}",
                exc_info=True
            )
            return False
    
    def _execute(self, error: SACPError) -> bool:
        """Execute recovery strategy"""
        raise NotImplementedError


class ResourceRecoveryStrategy(RecoveryStrategy):
    """Recovery strategy for resource exhaustion"""
    
    def _execute(self, error: ResourceExhaustedError) -> bool:
        """Attempt to recover from resource exhaustion"""
        resource_type = error.details['resource_type']
        current_usage = error.details['current_usage']
        limit = error.details['limit']
        
        self.logger.info(
            f"Attempting to recover from {resource_type} "
            f"exhaustion ({current_usage}/{limit})"
        )
        
        if resource_type == 'memory':
            # Trigger garbage collection
            import gc
            gc.collect()
            return True
        
        elif resource_type == 'disk':
            # Clear temporary files
            import tempfile
            import shutil
            temp_dir = tempfile.gettempdir()
            try:
                shutil.rmtree(temp_dir)
                return True
            except:
                return False
        
        return False


class SafetyRecoveryStrategy(RecoveryStrategy):
    """Recovery strategy for safety violations"""
    
    def _execute(self, error: SafetyViolationError) -> bool:
        """Attempt to recover from safety violation"""
        constraint = error.details['constraint_name']
        violation = error.details['violation_details']
        
        self.logger.info(
            f"Attempting to recover from safety violation: "
            f"{constraint}"
        )
        
        # Log violation for analysis
        self._log_violation(constraint, violation)
        
        # Always return False for safety violations
        # They require manual intervention
        return False
    
    def _log_violation(
        self,
        constraint: str,
        violation: Dict[str, Any]
    ) -> None:
        """Log safety violation details"""
        self.logger.warning(
            "Safety Violation Details",
            extra={
                'constraint': constraint,
                'violation': violation,
                'timestamp': datetime.now().isoformat()
            }
        )


class RecoveryManager:
    """Manages error recovery strategies"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._strategies: Dict[
            Type[SACPError],
            RecoveryStrategy
        ] = {
            ResourceExhaustedError: ResourceRecoveryStrategy(),
            SafetyViolationError: SafetyRecoveryStrategy()
        }
    
    def register_strategy(
        self,
        error_type: Type[SACPError],
        strategy: RecoveryStrategy
    ) -> None:
        """Register a recovery strategy for an error type"""
        self._strategies[error_type] = strategy
    
    def attempt_recovery(self, error: SACPError) -> bool:
        """Attempt to recover from an error"""
        strategy = self._find_strategy(error)
        if not strategy:
            return False
        
        self.logger.info(
            f"Attempting recovery for {error.__class__.__name__}"
        )
        return strategy.attempt(error)
    
    def _find_strategy(
        self,
        error: SACPError
    ) -> Optional[RecoveryStrategy]:
        """Find the most specific recovery strategy"""
        for error_type, strategy in self._strategies.items():
            if isinstance(error, error_type):
                return strategy
        return None
