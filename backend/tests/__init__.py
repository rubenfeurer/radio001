"""
Radio Backend Tests Package

This package contains comprehensive tests for the radio backend system:
- Unit tests for individual components
- API tests for endpoint functionality
- Integration tests for complete workflows
- WebSocket tests for real-time communication
- Fixtures and utilities for test data
"""

# Test configuration
TEST_CONFIG = {
    "mock_hardware": True,
    "test_data_dir": "tests/fixtures",
    "default_timeout": 10.0,
    "test_station_urls": [
        "https://test1.example.com/stream",
        "https://test2.example.com/stream",
        "https://test3.example.com/stream"
    ]
}

__version__ = "1.0.0"
__all__ = ["TEST_CONFIG"]
