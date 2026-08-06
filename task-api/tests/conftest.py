"""Pytest configuration for task-api tests."""
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Initialize s21_agent package
import pytest

@pytest.fixture(autouse=True)
def setup_paths():
    """Setup Python path for tests."""
    src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
