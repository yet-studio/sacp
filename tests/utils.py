"""
SafeAI CodeGuard Protocol - Test Utilities
Helper functions and utilities for testing.
"""

import asyncio
import contextlib
import os
import tempfile
from typing import Any, Dict, Generator, Optional
from datetime import datetime, timedelta

from src.core.error import SACPError


def create_temp_file(content: str) -> Generator[str, None, None]:
    """Create a temporary file with given content"""
    with tempfile.NamedTemporaryFile(
        mode='w',
        delete=False
    ) as temp:
        temp.write(content)
        temp_path = temp.name
    
    try:
        yield temp_path
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


async def wait_for_condition(
    condition_func,
    timeout: float = 5.0,
    check_interval: float = 0.1
) -> bool:
    """Wait for a condition to become true"""
    end_time = datetime.now() + timedelta(seconds=timeout)
    
    while datetime.now() < end_time:
        if await condition_func():
            return True
        await asyncio.sleep(check_interval)
    
    return False


def assert_error_details(
    error: SACPError,
    expected_code: str,
    expected_details: Optional[Dict[str, Any]] = None
) -> None:
    """Assert error details match expected values"""
    assert isinstance(error, SACPError)
    assert error.error_code == expected_code
    
    if expected_details:
        for key, value in expected_details.items():
            assert error.details.get(key) == value


@contextlib.contextmanager
def mock_environment(**env_vars) -> Generator[None, None, None]:
    """Temporarily modify environment variables"""
    original = dict(os.environ)
    os.environ.update(env_vars)
    
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(original)


def assert_timestamp_recent(
    timestamp: datetime,
    max_age_seconds: float = 1.0
) -> None:
    """Assert a timestamp is recent"""
    age = datetime.now() - timestamp
    assert age <= timedelta(seconds=max_age_seconds)


def assert_dict_subset(subset: Dict, full: Dict) -> None:
    """Assert that one dict is a subset of another"""
    for key, value in subset.items():
        assert key in full
        assert full[key] == value
