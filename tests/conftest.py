"""
Pytest configuration and shared fixtures for integration tests.
"""

import pytest
import asyncio
import os

# Set test environment
os.environ["PYTEST_CURRENT_TEST"] = "true"

# Import all fixtures to make them available
from tests.fixtures import *


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Configure pytest-asyncio
pytest_plugins = ["pytest_asyncio"]
