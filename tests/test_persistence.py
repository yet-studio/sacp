"""
Tests for SafeAI CodeGuard Protocol data persistence.
"""

import pytest
from datetime import datetime, timedelta
from typing import Generator

from src.core.persistence import (
    Database,
    init_db,
    SafetyMetric,
    SafetyAlert,
    SystemHealth,
    OperationLog,
    ResourceUsage
)
from src.core.persistence.models import AlertLevel


@pytest.fixture
def db() -> Generator[Database, None, None]:
    """Test database fixture"""
    database = init_db('sqlite:///:memory:', echo=False)
    yield database


def test_safety_metric(db):
    """Test safety metric persistence"""
    # Create metric
    metric = SafetyMetric(
        name='test_metric',
        value=42.0,
        unit='test_unit',
        meta_data={'test': True}
    )
    db.add(metric)
    
    # Query metric
    result = db.get(SafetyMetric, metric.id)
    assert result is not None
    assert result.name == 'test_metric'
    assert result.value == 42.0
    assert result.unit == 'test_unit'
    assert result.meta_data == {'test': True}
    assert isinstance(result.timestamp, datetime)


def test_safety_alert(db):
    """Test safety alert persistence"""
    # Create alert
    alert = SafetyAlert(
        level=AlertLevel.WARNING,
        source='test_source',
        message='test alert',
        details={'test': True}
    )
    db.add(alert)
    
    # Query alert
    result = db.get(SafetyAlert, alert.id)
    assert result is not None
    assert result.level == AlertLevel.WARNING
    assert result.source == 'test_source'
    assert result.message == 'test alert'
    assert result.details == {'test': True}
    assert not result.resolved
    assert result.resolved_at is None
    
    # Resolve alert
    alert.resolved = True
    alert.resolved_at = datetime.now()
    alert.resolution_notes = 'Fixed'
    db.update(alert)
    
    # Check resolution
    result = db.get(SafetyAlert, alert.id)
    assert result.resolved
    assert result.resolved_at is not None
    assert result.resolution_notes == 'Fixed'


def test_system_health(db):
    """Test system health persistence"""
    # Create health status
    health = SystemHealth(
        healthy=True,
        checks={'test_check': True},
        metrics={'test_metric': 42.0}
    )
    db.add(health)
    
    # Query health
    result = db.get(SystemHealth, health.id)
    assert result is not None
    assert result.healthy
    assert result.checks == {'test_check': True}
    assert result.metrics == {'test_metric': 42.0}
    assert isinstance(result.timestamp, datetime)


def test_operation_log(db):
    """Test operation log persistence"""
    # Create operation log
    start_time = datetime.now()
    operation = OperationLog(
        operation_type='test_op',
        status='running',
        user='test_user',
        details={'test': True},
        impact_score=0.5,
        started_at=start_time
    )
    db.add(operation)
    
    # Query operation
    result = db.get(OperationLog, operation.id)
    assert result is not None
    assert result.operation_type == 'test_op'
    assert result.status == 'running'
    assert result.user == 'test_user'
    assert result.details == {'test': True}
    assert result.impact_score == 0.5
    assert result.started_at == start_time
    assert result.completed_at is None
    assert result.error_message is None
    
    # Complete operation
    operation.status = 'completed'
    operation.completed_at = datetime.now()
    db.update(operation)
    
    # Check completion
    result = db.get(OperationLog, operation.id)
    assert result.status == 'completed'
    assert result.completed_at is not None


def test_resource_usage(db):
    """Test resource usage persistence"""
    # Create resource usage
    usage = ResourceUsage(
        cpu_percent=50.0,
        memory_mb=1024.0,
        disk_mb=2048.0,
        network_bytes=1000000,
        meta_data={'test': True}
    )
    db.add(usage)
    
    # Query usage
    result = db.get(ResourceUsage, usage.id)
    assert result is not None
    assert result.cpu_percent == 50.0
    assert result.memory_mb == 1024.0
    assert result.disk_mb == 2048.0
    assert result.network_bytes == 1000000
    assert result.meta_data == {'test': True}
    assert isinstance(result.timestamp, datetime)


def test_database_query_filters(db):
    """Test database query filters"""
    # Create test data
    for i in range(5):
        metric = SafetyMetric(
            name=f'metric_{i}',
            value=float(i),
            unit='test'
        )
        db.add(metric)
    
    # Query with filters
    results = db.query(SafetyMetric, name='metric_2')
    assert len(results) == 1
    assert results[0].name == 'metric_2'
    assert results[0].value == 2.0
    
    # Query all
    all_results = db.query(SafetyMetric)
    assert len(all_results) == 5
