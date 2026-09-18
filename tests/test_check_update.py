import os
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

from shift_this_version import check_update

def test_is_newer_version():
    # Patch bump
    assert check_update.is_newer_version("1.6.1", "1.6.2") is True
    # Minor bump
    assert check_update.is_newer_version("1.6.1", "1.7.0") is True
    # Major bump
    assert check_update.is_newer_version("1.6.1", "2.0.0") is True

    # Same version
    assert check_update.is_newer_version("1.6.1", "1.6.1") is False
    assert check_update.is_newer_version("v1.6.1", "1.6.1") is False

    # Older version
    assert check_update.is_newer_version("1.6.1", "1.5.0") is False
    assert check_update.is_newer_version("2.0.0", "1.9.9") is False

    # Prerelease comparisons
    assert check_update.is_newer_version("1.6.1-rc.1", "1.6.1") is True

def test_cache_save_and_load(tmp_path: Path):
    mock_cache_file = tmp_path / "update_cache.json"
    
    with patch.object(check_update, "CACHE_FILE", mock_cache_file), \
         patch.object(check_update, "CONFIG_DIR", tmp_path):
        
        # Initial state: no cache
        ver, last_check = check_update.load_update_cache()
        assert ver is None
        assert last_check == 0.0

        # Save cache
        check_update.save_update_cache("1.7.0")
        assert mock_cache_file.is_file()

        # Load cache
        ver, last_check = check_update.load_update_cache()
        assert ver == "1.7.0"
        assert time.time() - last_check < 5.0

def test_check_for_update_notice_with_cached_newer(tmp_path: Path):
    mock_cache_file = tmp_path / "update_cache.json"
    
    with patch.object(check_update, "CACHE_FILE", mock_cache_file), \
         patch.object(check_update, "CONFIG_DIR", tmp_path):
        
        # 1. Case: Cached version is newer -> returns the new version
        check_update.save_update_cache("2.0.0")
        res = check_update.check_for_update_notice("1.6.1")
        assert res == "2.0.0"

        # 2. Case: Cached version is older -> returns None
        check_update.save_update_cache("1.5.0")
        res_old = check_update.check_for_update_notice("1.6.1")
        assert res_old is None

def test_print_update_banner():
    from rich.console import Console
    # Create test console with string capture
    console = Console(record=True, width=100)
    check_update.print_update_banner(console, "1.6.1", "1.7.0")
    output = console.export_text()
    assert "A new version of shift-this-version is available!" in output
    assert "v1.6.1" in output
    assert "v1.7.0" in output
    assert "uv tool update shift-this-version" in output
