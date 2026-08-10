"""
Basic tests to verify the testing setup works.
"""

def test_basic():
    """A basic test to verify pytest is working."""
    assert True


def test_math():
    """Test basic math operations."""
    assert 1 + 1 == 2
    assert 2 * 3 == 6


def test_string():
    """Test string operations."""
    assert "hello" + " world" == "hello world"
    assert "test".upper() == "TEST"
