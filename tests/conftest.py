"""
SafeAI CodeGuard Protocol - Test Configuration
Global test fixtures and configuration.
"""

import os
import pytest
import tempfile
import asyncio
from typing import Generator, AsyncGenerator
from datetime import datetime

from src.core.persistence import Database, init_db
from src.core.monitoring import (
    MetricsCollector,
    HealthMonitor,
    AlertManager,
    PerformanceMonitor
)
from src.core.error import ErrorHandler


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def db() -> Generator[Database, None, None]:
    """Test database fixture"""
    database = init_db('sqlite:///:memory:', echo=False)
    yield database


@pytest.fixture
def error_handler() -> Generator[ErrorHandler, None, None]:
    """Test error handler fixture"""
    handler = ErrorHandler()
    yield handler


@pytest.fixture
async def metrics_collector() -> AsyncGenerator[MetricsCollector, None]:
    """Test metrics collector fixture"""
    collector = MetricsCollector()
    yield collector
    await collector.stop()


@pytest.fixture
async def health_monitor(
    metrics_collector: MetricsCollector
) -> AsyncGenerator[HealthMonitor, None]:
    """Test health monitor fixture"""
    monitor = HealthMonitor(metrics_collector)
    yield monitor
    await monitor.stop()


@pytest.fixture
async def alert_manager() -> AsyncGenerator[AlertManager, None]:
    """Test alert manager fixture"""
    manager = AlertManager()
    yield manager
    await manager.stop()


@pytest.fixture
async def performance_monitor() -> AsyncGenerator[PerformanceMonitor, None]:
    """Test performance monitor fixture"""
    monitor = PerformanceMonitor()
    yield monitor
    await monitor.stop()


@pytest.fixture(autouse=True)
def test_env() -> Generator[None, None, None]:
    """Set up test environment variables"""
    # Store original environment
    original_env = dict(os.environ)
    
    # Set test environment variables
    os.environ.update({
        'SACP_ENV': 'test',
        'SACP_DATABASE_URL': 'sqlite:///:memory:',
        'SACP_LOG_LEVEL': 'DEBUG'
    })
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(autouse=True)
def event_loop():
    """Create and use a new event loop for each test"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
