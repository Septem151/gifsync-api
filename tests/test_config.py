"""Test cases related to GifSync API's configuration."""
from gifsync_api import __version__


def test_version_matches_expected():
    """Assert that the version of gifsync_api matches the expected version."""
    assert __version__ == "0.1.0"
