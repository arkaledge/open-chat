"""
Example test file to verify pytest is working.
Replace this with actual tests for your application.
"""
import pytest


def test_example():
    """Basic sanity check test."""
    assert True


def test_basic_math():
    """Test basic math operations."""
    assert 1 + 1 == 2
    assert 2 * 2 == 4


@pytest.mark.asyncio
async def test_async_example():
    """Test async functionality."""
    async def async_function():
        return "Hello, World!"

    result = await async_function()
    assert result == "Hello, World!"
