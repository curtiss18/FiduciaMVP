"""
Test-specific configuration settings for FiduciaMVP.
"""

import os
from typing import Optional
from config.settings import Settings


class TestSettings(Settings):
    """Test environment settings with database isolation."""
    
    # API Keys (Optional for tests)
    searchapi_key: Optional[str] = None
    
    # Test Database - Separate container
    database_url: str = "postgresql+asyncpg://fiducia_user:fiducia_password@localhost:5433/fiducia_mvp_test"
    
    # Test Redis - Separate instance 
    redis_url: str = "redis://localhost:6380"
    
    # Test-specific overrides
    debug: bool = True
    log_level: str = "DEBUG"  # More verbose logging for tests
    
    # Faster timeouts for tests
    api_timeout: int = 30
    
    # Test data management
    cleanup_test_data: bool = True
    preserve_failed_test_data: bool = True
    
    # Performance test settings
    performance_test_enabled: bool = True
    performance_timeout_seconds: int = 5  # Max time for performance tests
    concurrent_test_users: int = 10
    
    class Config:
        env_file = ".env.test"  # Allow test-specific overrides


def get_test_settings() -> TestSettings:
    """Get test settings, checking for test environment."""
    if os.getenv("PYTEST_CURRENT_TEST"):
        return TestSettings()
    else:
        raise RuntimeError("Test settings should only be used during testing!")


# Singleton instance for tests
test_settings = None

def get_settings_for_test():
    """Get or create test settings instance."""
    global test_settings
    if test_settings is None:
        test_settings = TestSettings()
    return test_settings
