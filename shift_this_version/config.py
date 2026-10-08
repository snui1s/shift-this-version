import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

CONFIG_DIR = Path.home() / ".shift-this-version"
CONFIG_FILE = CONFIG_DIR / "config.json"

def get_config_path() -> Path:
    """คืนค่า path ของไฟล์ config"""
    return CONFIG_FILE

def load_config() -> Dict[str, Any]:
    """โหลดค่า config จาก ~/.shift-this-version/config.json"""
    if not CONFIG_FILE.is_file():
        return {}
    try:
        content = CONFIG_FILE.read_text(encoding="utf-8")
        return json.loads(content)
    except Exception:
        return {}

def save_config(data: Dict[str, Any]) -> None:
    """บันทึกค่า config ลง ~/.shift-this-version/config.json"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    # Create the file owner-only from the start so API keys are never briefly world-readable
    fd = os.open(CONFIG_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(json.dumps(data, indent=2, ensure_ascii=False))
    _restrict_permissions(CONFIG_FILE)

def _restrict_permissions(path: Path) -> None:
    """Best-effort: make the file readable only by the current user (POSIX chmod / Windows ACL)."""
    try:
        path.chmod(0o600)
    except Exception:
        pass
    if os.name == "nt":
        # chmod is a no-op for ACLs on Windows; drop inherited access and grant only the current user
        try:
            user = os.environ.get("USERNAME")
            if user:
                subprocess.run(
                    ["icacls", str(path), "/inheritance:r", "/grant:r", f"{user}:F"],
                    capture_output=True, timeout=10, check=False,
                )
        except Exception:
            pass

def is_first_run() -> bool:
    """ตรวจสอบว่าเป็นครั้งแรกที่รันเครื่องมือหรือไม่"""
    return not CONFIG_FILE.is_file()

def get_configured_key(provider: str) -> Optional[str]:
    """ดึง API Key ของ provider ที่บันทึกไว้ใน config"""
    cfg = load_config()
    keys = cfg.get("api_keys", {})
    return keys.get(provider.lower())

def get_default_provider() -> Optional[str]:
    """ดึงค่า default provider จาก config"""
    cfg = load_config()
    return cfg.get("default_provider")

def get_configured_model(provider: str) -> Optional[str]:
    """ดึงค่า model ที่บันทึกไว้สำหรับ provider นั้นๆ"""
    cfg = load_config()
    models = cfg.get("models", {})
    return models.get(provider.lower())

def get_configured_host(provider: str) -> Optional[str]:
    """ดึงค่า host/base_url ที่บันทึกไว้สำหรับ provider นั้นๆ (เช่น ollama, custom)"""
    cfg = load_config()
    hosts = cfg.get("hosts", {})
    return hosts.get(provider.lower())

