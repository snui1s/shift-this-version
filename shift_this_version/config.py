import os
import json
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
    CONFIG_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    # จำกัดสิทธิ์ไฟล์ให้อ่านได้เฉพาะเจ้าของ (ถ้าเป็นไปได้บน unix)
    try:
        CONFIG_FILE.chmod(0o600)
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

