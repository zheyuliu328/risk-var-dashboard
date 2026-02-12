"""Basic tests."""


def test_import():
    """Test that main module can be imported."""
    import main
    assert main is not None


def test_download_data():
    """Test data download function exists."""
    from download_data import main as download_main
    assert callable(download_main)
