"""
Tests for SafeAI CodeGuard Protocol monitoring system.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from src.core.monitoring import (
    MetricsCollector,
    HealthMonitor,
    AlertManager,
    PerformanceMonitor
)


@pytest.fixture
def metrics_collector():
    return MetricsCollector()


@pytest.fixture
def health_monitor():
    return HealthMonitor()


@pytest.fixture
def alert_manager():
    return AlertManager()


@pytest.fixture
def performance_monitor():
    return PerformanceMonitor(history_size=10)


@pytest.mark.asyncio
async def test_metrics_collector(metrics_collector):
    """Test metrics collection"""
    await metrics_collector.start(interval_seconds=0.1)
    await asyncio.sleep(0.2)  # Allow time for collection
    
    metrics = metrics_collector.get_metrics()
    assert metrics
    assert 'system' in metrics
    assert 'process' in metrics
    assert 'network' in metrics
    
    await metrics_collector.stop()


@pytest.mark.asyncio
async def test_health_monitor(health_monitor):
    """Test health monitoring"""
    # Add test checks
    health_monitor.add_check('test_pass', lambda: True)
    health_monitor.add_check('test_fail', lambda: False)
    
    await health_monitor.start(interval_seconds=0.1)
    await asyncio.sleep(0.2)  # Allow time for checks
    
    status = health_monitor.get_status()
    assert not status['healthy']  # One check fails
    assert status['checks']['test_pass']
    assert not status['checks']['test_fail']
    
    await health_monitor.stop()


@pytest.mark.asyncio
async def test_alert_manager(alert_manager):
    """Test alert management"""
    alerts_received = []
    
    def test_handler(alert):
        alerts_received.append(alert)
    
    # Add handlers
    alert_manager.add_handler('warning', test_handler)
    alert_manager.add_handler('error', test_handler)
    
    # Emit alerts
    await alert_manager.emit(
        'warning',
        'test',
        'test warning',
        {'detail': 'warning detail'}
    )
    await alert_manager.emit(
        'error',
        'test',
        'test error',
        {'detail': 'error detail'}
    )
    
    # Check alerts
    alerts = alert_manager.get_alerts()
    assert len(alerts) == 2
    assert alerts[0].level == 'warning'
    assert alerts[1].level == 'error'
    assert len(alerts_received) == 2


@pytest.mark.asyncio
async def test_performance_monitor(performance_monitor):
    """Test performance monitoring"""
    await performance_monitor.start(interval_seconds=0.1)
    await asyncio.sleep(0.3)  # Allow time for collection
    
    # Get recent metrics
    metrics = performance_monitor.get_metrics(
        timeframe=timedelta(seconds=1)
    )
    assert len(metrics) > 0
    
    # Check metrics content
    latest = metrics[-1]
    assert isinstance(latest.cpu_percent, float)
    assert isinstance(latest.memory_percent, float)
    assert isinstance(latest.disk_io, dict)
    assert isinstance(latest.network_io, dict)
    assert isinstance(latest.process_count, int)
    assert isinstance(latest.thread_count, int)
    
    await performance_monitor.stop()
