import os
import json
import time
import threading
import urllib.request
from pathlib import Path
from typing import Optional, Tuple
from rich.console import Console
from rich.panel import Panel

from .config import CONFIG_DIR
from .updater import parse_semver

CACHE_FILE = CONFIG_DIR / "update_cache.json"
CACHE_TTL = 43200  # 12 hours in seconds
PACKAGE_NAME = "shift-this-version"

def is_newer_version(current_ver: str, latest_ver: str) -> bool:
    """Compare two semver strings to determine if latest_ver is strictly newer than current_ver."""
    try:
        c_clean = current_ver.lstrip("v").strip()
        l_clean = latest_ver.lstrip("v").strip()
        c_maj, c_min, c_patch, c_pre = parse_semver(c_clean)
        l_maj, l_min, l_patch, l_pre = parse_semver(l_clean)

        c_tuple = (c_maj, c_min, c_patch)
        l_tuple = (l_maj, l_min, l_patch)

        if l_tuple > c_tuple:
            return True
        elif l_tuple < c_tuple:
            return False
        else:
            # Same major.minor.patch: if current has prerelease and latest has none, latest is newer
            if c_pre and not l_pre:
                return True
            return False
    except Exception:
        return False

def fetch_latest_pypi_version(package_name: str = PACKAGE_NAME, timeout: float = 2.5) -> Optional[str]:
    """Fetch the latest released version from the official PyPI JSON API."""
    try:
        url = f"https://pypi.org/pypi/{package_name}/json"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": f"{package_name}-update-checker"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("info", {}).get("version")
    except Exception:
        return None

def load_update_cache() -> Tuple[Optional[str], float]:
    """Read update_cache.json returning (latest_version, last_check_timestamp)."""
    if not CACHE_FILE.is_file():
        return None, 0.0
    try:
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        return data.get("latest_version"), float(data.get("last_check", 0.0))
    except Exception:
        return None, 0.0

def save_update_cache(latest_version: str) -> None:
    """Save latest version and current timestamp to update_cache.json."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "latest_version": latest_version,
            "last_check": time.time()
        }
        CACHE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass

def refresh_cache_in_background():
    """Fetch PyPI version in a background worker thread and update cache file."""
    latest = fetch_latest_pypi_version()
    if latest:
        save_update_cache(latest)

def check_for_update_notice(current_ver: str) -> Optional[str]:
    """
    Check if a newer version is available.
    1. Read cache first for 0ms latency.
    2. If cache is missing or expired (> 12h), spawn background thread to refresh.
    3. Returns latest_version string if a newer version is available, else None.
    """
    now = time.time()
    cached_ver, last_check = load_update_cache()

    # If cache is expired or empty, trigger background refresh
    if now - last_check > CACHE_TTL:
        t = threading.Thread(target=refresh_cache_in_background, daemon=True)
        t.start()

    # Compare cached version against current version
    if cached_ver and is_newer_version(current_ver, cached_ver):
        return cached_ver
    return None

def show_update_notification_if_available(console: Console, current_ver: str) -> None:
    """Display update notification panel if a newer version is detected."""
    try:
        latest = check_for_update_notice(current_ver)
        if latest:
            print_update_banner(console, current_ver, latest)
    except Exception:
        pass

def print_update_banner(console: Console, current_ver: str, latest_ver: str) -> None:
    """Render a sleek, eye-catching update notification panel using Rich (Windows-safe)."""
    try:
        content = (
            f"[bold yellow]A new version of {PACKAGE_NAME} is available![/bold yellow] "
            f"[dim]v{current_ver}[/dim] -> [bold green]v{latest_ver}[/bold green]\n\n"
            f"[white]To update, run:[/white]\n"
            f"  - [bold cyan]uv tool update {PACKAGE_NAME}[/bold cyan]   [dim](if installed via uv)[/dim]\n"
            f"  - [bold cyan]pip install --upgrade {PACKAGE_NAME}[/bold cyan] [dim](if installed via pip)[/dim]"
        )
        console.print(Panel(
            content,
            title="[bold yellow]Update Available[/bold yellow]",
            border_style="yellow",
            expand=False
        ))
    except Exception:
        pass
