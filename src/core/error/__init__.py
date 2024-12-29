"""
SafeAI CodeGuard Protocol - Error Handling
Core functionality for error handling and recovery.
"""

from .exceptions import (
    SACPError,
    SafetyViolationError,
    ResourceExhaustedError,
    ConfigurationError,
    OperationError,
    ValidationError,
    SystemStateError,
    RecoveryError
)
from .handler import ErrorHandler
from .recovery import RecoveryManager

__all__ = [
    'SACPError',
    'SafetyViolationError',
    'ResourceExhaustedError',
    'ConfigurationError',
    'OperationError',
    'ValidationError',
    'SystemStateError',
    'RecoveryError',
    'ErrorHandler',
    'RecoveryManager'
]
