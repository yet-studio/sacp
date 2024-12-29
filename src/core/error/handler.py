"""
SafeAI CodeGuard Protocol - Error Handler
Core error handling functionality.
"""

import logging
import traceback
from typing import Optional, Dict, Any, Type, Callable
from datetime import datetime
from functools import wraps

from .exceptions import SACPError, RecoveryError
from .recovery import RecoveryManager


class ErrorHandler:
    """Central error handling system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.recovery_manager = RecoveryManager()
        self._error_handlers: Dict[
            Type[Exception],
            Callable[[Exception], None]
        ] = {}
    
    def register_handler(
        self,
        error_type: Type[Exception],
        handler: Callable[[Exception], None]
    ) -> None:
        """Register a handler for a specific error type"""
        self._error_handlers[error_type] = handler
    
    def handle(self, error: Exception) -> None:
        """Handle an error"""
        try:
            # Convert to SACP error if needed
            if not isinstance(error, SACPError):
                error = self._wrap_error(error)
            
            # Log the error
            self._log_error(error)
            
            # Try to find and execute specific handler
            handler = self._find_handler(error)
            if handler:
                handler(error)
            
            # Attempt recovery
            self.recovery_manager.attempt_recovery(error)
        
        except Exception as e:
            # Log recovery failure
            self.logger.error(
                "Error recovery failed",
                exc_info=True
            )
            raise RecoveryError(
                message="Error recovery failed",
                original_error=error,
                recovery_hint="Manual intervention may be required"
            ) from e
    
    def _wrap_error(self, error: Exception) -> SACPError:
        """Wrap a standard exception in a SACP error"""
        return SACPError(
            message=str(error),
            error_code='UNKNOWN_ERROR',
            details={
                'original_type': error.__class__.__name__,
                'traceback': traceback.format_exc()
            }
        )
    
    def _log_error(self, error: SACPError) -> None:
        """Log error details"""
        self.logger.error(
            f"{error.__class__.__name__}: {error.message}",
            extra={
                'error_details': error.to_dict()
            }
        )
    
    def _find_handler(
        self,
        error: Exception
    ) -> Optional[Callable[[Exception], None]]:
        """Find the most specific handler for an error"""
        for error_type, handler in self._error_handlers.items():
            if isinstance(error, error_type):
                return handler
        return None


# Global error handler instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get global error handler instance"""
    global _error_handler
    if not _error_handler:
        _error_handler = ErrorHandler()
    return _error_handler


def handle_errors(func):
    """Decorator for automatic error handling"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            get_error_handler().handle(e)
            raise
    return wrapper
