"""
SafeAI CodeGuard Protocol - Custom Exceptions
Defines all custom exceptions used in the system.
"""

from typing import Optional, Dict, Any
from datetime import datetime


class SACPError(Exception):
    """Base exception for all SACP errors"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        recovery_hint: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or 'SACP_ERROR'
        self.details = details or {}
        self.recovery_hint = recovery_hint
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format"""
        return {
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details,
            'recovery_hint': self.recovery_hint,
            'timestamp': self.timestamp.isoformat(),
            'type': self.__class__.__name__
        }


class SafetyViolationError(SACPError):
    """Raised when a safety constraint is violated"""
    
    def __init__(
        self,
        message: str,
        constraint_name: str,
        violation_details: Dict[str, Any],
        **kwargs
    ):
        super().__init__(
            message,
            error_code='SAFETY_VIOLATION',
            details={
                'constraint_name': constraint_name,
                'violation_details': violation_details
            },
            **kwargs
        )


class ResourceExhaustedError(SACPError):
    """Raised when system resources are exhausted"""
    
    def __init__(
        self,
        message: str,
        resource_type: str,
        current_usage: float,
        limit: float,
        **kwargs
    ):
        super().__init__(
            message,
            error_code='RESOURCE_EXHAUSTED',
            details={
                'resource_type': resource_type,
                'current_usage': current_usage,
                'limit': limit
            },
            **kwargs
        )


class ConfigurationError(SACPError):
    """Raised when there's an error in system configuration"""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        invalid_value: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code='CONFIG_ERROR',
            details={
                'config_key': config_key,
                'invalid_value': invalid_value
            },
            **kwargs
        )


class OperationError(SACPError):
    """Raised when an operation fails"""
    
    def __init__(
        self,
        message: str,
        operation_name: str,
        operation_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code='OPERATION_ERROR',
            details={
                'operation_name': operation_name,
                'operation_id': operation_id
            },
            **kwargs
        )


class ValidationError(SACPError):
    """Raised when input validation fails"""
    
    def __init__(
        self,
        message: str,
        field_name: str,
        invalid_value: Any,
        constraints: Dict[str, Any],
        **kwargs
    ):
        super().__init__(
            message,
            error_code='VALIDATION_ERROR',
            details={
                'field_name': field_name,
                'invalid_value': invalid_value,
                'constraints': constraints
            },
            **kwargs
        )


class SystemStateError(SACPError):
    """Raised when system is in an invalid state"""
    
    def __init__(
        self,
        message: str,
        current_state: str,
        expected_state: str,
        **kwargs
    ):
        super().__init__(
            message,
            error_code='SYSTEM_STATE_ERROR',
            details={
                'current_state': current_state,
                'expected_state': expected_state
            },
            **kwargs
        )


class RecoveryError(SACPError):
    """Raised when error recovery fails"""
    
    def __init__(
        self,
        message: str,
        original_error: Optional[Exception] = None,
        recovery_strategy: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code='RECOVERY_ERROR',
            details={
                'original_error': str(original_error) if original_error else None,
                'recovery_strategy': recovery_strategy
            },
            **kwargs
        )
