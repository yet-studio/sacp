"""
Tests for SafeAI CodeGuard Protocol safety constraints.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from src.core.safety.constraints import (
    ResourceConstraint,
    OperationConstraint,
    AccessConstraint,
    ResourceError,
    OperationError,
    AccessError
)
from src.core.safety.validator import SafetyValidator
from src.core.safety.monitor import SafetyMonitor
from src.core.safety.emergency import EmergencyStop


@pytest.fixture
def resource_constraint():
    return ResourceConstraint(
        max_memory_mb=1024,
        max_cpu_percent=80.0,
        max_disk_mb=1000
    )


@pytest.fixture
def operation_constraint():
    return OperationConstraint(
        max_operations_per_minute=60,
        max_file_size_mb=10,
        restricted_patterns={'eval', 'exec'},
        allowed_operations={'read', 'write'},
        max_impact_score=0.8
    )


@pytest.fixture
def access_constraint():
    return AccessConstraint(
        allowed_paths={'/safe', '/test'},
        restricted_paths={'/admin', '/config'},
        required_permissions={
            'read': {'basic'},
            'write': {'write', 'basic'}
        }
    )


@pytest.fixture
def validator(
    resource_constraint,
    operation_constraint,
    access_constraint
):
    validator = SafetyValidator()
    validator.add_constraint(resource_constraint)
    validator.add_constraint(operation_constraint)
    validator.add_constraint(access_constraint)
    return validator


@pytest.fixture
def monitor():
    return SafetyMonitor()


@pytest.fixture
def emergency():
    return EmergencyStop()


@pytest.mark.asyncio
async def test_resource_constraint(resource_constraint):
    """Test resource constraints validation"""
    # Valid context
    context = {
        'modified_files': []
    }
    assert resource_constraint.validate(context, force=True)
    
    # Invalid context (large files)
    context = {
        'modified_files': [
            type('File', (), {'size': 2000 * 1024 * 1024})()
        ]
    }
    assert not resource_constraint.validate(context, force=True)
    
    with pytest.raises(ResourceError):
        resource_constraint.enforce(context)


@pytest.mark.asyncio
async def test_operation_constraint(operation_constraint):
    """Test operation constraints validation"""
    # Valid operation
    context = {
        'operation': {
            'type': 'read',
            'content': 'safe code',
            'file_size': 1000
        }
    }
    assert operation_constraint.validate(context)
    
    # Invalid operation (restricted pattern)
    context = {
        'operation': {
            'type': 'write',
            'content': 'eval("code")',
            'file_size': 1000
        }
    }
    assert not operation_constraint.validate(context)
    
    with pytest.raises(OperationError):
        operation_constraint.enforce(context)


@pytest.mark.asyncio
async def test_access_constraint(access_constraint):
    """Test access control validation"""
    # Valid access
    context = {
        'operation': {
            'type': 'read',
            'file_path': '/safe/file.txt'
        },
        'user': {
            'permissions': {'basic'}
        }
    }
    assert access_constraint.validate(context)
    
    # Invalid access (restricted path)
    context = {
        'operation': {
            'type': 'write',
            'file_path': '/admin/config.txt'
        },
        'user': {
            'permissions': {'basic', 'write'}
        }
    }
    assert not access_constraint.validate(context)
    
    with pytest.raises(AccessError):
        access_constraint.enforce(context)


@pytest.mark.asyncio
async def test_validator(validator):
    """Test safety validator"""
    # Valid operation
    context = {
        'operation': {
            'type': 'read',
            'file_path': '/safe/file.txt',
            'content': 'safe code',
            'file_size': 1000
        },
        'user': {
            'permissions': {'basic'}
        },
        'modified_files': []
    }
    result = await validator.validate(context)
    assert result.valid
    
    # Invalid operation
    context['operation']['content'] = 'eval("unsafe")'
    result = await validator.validate(context)
    assert not result.valid
    assert len(result.errors) > 0


@pytest.mark.asyncio
async def test_monitor(monitor):
    """Test safety monitor"""
    def health_check():
        return True
    
    monitor.add_health_check('test', health_check)
    monitor.update_metric('test_metric', 1.0)
    
    await monitor.start(interval_seconds=0.1)
    await asyncio.sleep(0.2)
    
    status = monitor.get_status()
    assert status['healthy']
    assert 'test_metric' in status['metrics']
    
    await monitor.stop()


@pytest.mark.asyncio
async def test_emergency(emergency):
    """Test emergency stop"""
    assert not emergency.is_active()
    
    # Trigger emergency
    await emergency.trigger('test emergency', {'test': True})
    assert emergency.is_active()
    
    # Check event
    event = emergency.get_last_event()
    assert event.reason == 'test emergency'
    assert event.context['test']
    
    # Reset emergency
    await emergency.reset('test_user', 'test complete')
    assert not emergency.is_active()
    
    # Check history
    history = emergency.get_history()
    assert len(history) == 2  # trigger + reset


if __name__ == '__main__':
    pytest.main([__file__])
