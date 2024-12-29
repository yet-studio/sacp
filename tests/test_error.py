"""
Tests for SafeAI CodeGuard Protocol error handling.
"""

import pytest
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from src.core.error import (
    SACPError,
    SafetyViolationError,
    ResourceExhaustedError,
    ConfigurationError,
    OperationError,
    ValidationError,
    SystemStateError,
    RecoveryError,
    ErrorHandler,
    RecoveryManager
)
from src.core.error.handler import handle_errors, get_error_handler

def test_base_error():
    """Test base SACP error"""
    error = SACPError(
        message="Test error",
        error_code="TEST_ERROR",
        details={'test': True},
        recovery_hint="Try again"
    )
    
    assert str(error) == "Test error"
    assert error.error_code == "TEST_ERROR"
    assert error.details == {'test': True}
    assert error.recovery_hint == "Try again"
    
    # Test error serialization
    error_dict = error.to_dict()
    assert error_dict['message'] == "Test error"
    assert error_dict['error_code'] == "TEST_ERROR"
    assert error_dict['details'] == {'test': True}
    assert error_dict['recovery_hint'] == "Try again"
    assert isinstance(error_dict['timestamp'], str)
    assert error_dict['type'] == "SACPError"


def test_safety_violation_error():
    """Test safety violation error"""
    error = SafetyViolationError(
        message="Safety constraint violated",
        constraint_name="max_speed",
        violation_details={'speed': 100, 'limit': 50}
    )
    
    assert isinstance(error, SACPError)
    assert error.error_code == "SAFETY_VIOLATION"
    assert error.details['constraint_name'] == "max_speed"
    assert error.details['violation_details'] == {
        'speed': 100,
        'limit': 50
    }


def test_resource_exhausted_error():
    """Test resource exhausted error"""
    error = ResourceExhaustedError(
        message="Memory limit exceeded",
        resource_type="memory",
        current_usage=1024,
        limit=512
    )
    
    assert isinstance(error, SACPError)
    assert error.error_code == "RESOURCE_EXHAUSTED"
    assert error.details['resource_type'] == "memory"
    assert error.details['current_usage'] == 1024
    assert error.details['limit'] == 512


def test_error_handler():
    """Test error handler"""
    handler = ErrorHandler()
    handled_errors = []
    
    # Register custom handler
    def custom_handler(error):
        handled_errors.append(error)
    
    handler.register_handler(
        SafetyViolationError,
        custom_handler
    )
    
    # Test error handling
    error = SafetyViolationError(
        message="Test violation",
        constraint_name="test",
        violation_details={}
    )
    
    handler.handle(error)
    assert len(handled_errors) == 1
    assert handled_errors[0] is error


def test_error_recovery():
    """Test error recovery"""
    manager = RecoveryManager()
    
    # Test resource recovery
    error = ResourceExhaustedError(
        message="Memory exhausted",
        resource_type="memory",
        current_usage=1024,
        limit=512
    )
    
    assert manager.attempt_recovery(error)
    
    # Test safety violation (should not recover)
    error = SafetyViolationError(
        message="Safety violated",
        constraint_name="test",
        violation_details={}
    )
    
    assert not manager.attempt_recovery(error)


def test_error_decorator():
    """Test error handling decorator"""
    handled_errors = []
    
    def custom_handler(error):
        handled_errors.append(error)
    
    handler = get_error_handler()
    handler.register_handler(Exception, custom_handler)
    
    @handle_errors
    def failing_function():
        raise ValueError("Test error")
    
    with pytest.raises(ValueError):
        failing_function()
    
    assert len(handled_errors) == 1
    assert isinstance(handled_errors[0], SACPError)
    assert "Test error" in str(handled_errors[0])


def test_recovery_strategy():
    """Test recovery strategy"""
    from src.core.error.recovery import RecoveryStrategy
    
    class TestStrategy(RecoveryStrategy):
        def _execute(self, error):
            return True
    
    strategy = TestStrategy(max_attempts=2)
    
    # First attempt should succeed
    assert strategy.can_attempt()
    assert strategy.attempt(None)
    
    # Second attempt should be blocked by cooldown
    assert not strategy.can_attempt()
    
    # Wait for cooldown
    strategy.last_attempt -= timedelta(seconds=5)
    
    # Second attempt should succeed
    assert strategy.can_attempt()
    assert strategy.attempt(None)
    
    # Third attempt should fail (max attempts reached)
    assert not strategy.can_attempt()
    assert not strategy.attempt(None)
