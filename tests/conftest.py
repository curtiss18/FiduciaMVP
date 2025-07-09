"""
Pytest configuration and shared fixtures for integration tests.
"""

import pytest
import asyncio
import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set test environment
os.environ["PYTEST_CURRENT_TEST"] = "true"

# Import all fixtures to make them available
try:
    from .fixtures import *
except ImportError:
    # Fallback for different import contexts
    pass


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
