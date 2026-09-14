from pathlib import Path
from shift_this_version.updater import (
    calculate_next_version,
    find_version_targets,
    apply_version_bump,
    VersionTarget
)
from shift_this_version.analyzer import extract_json_from_text, BumpAnalysis

def test_calculate_next_version():
    assert calculate_next_version("1.2.3", "patch") == "1.2.4"
    assert calculate_next_version("1.2.3", "minor") == "1.3.0"
    assert calculate_next_version("1.2.3", "major") == "2.0.0"
    assert calculate_next_version("1.2.3", "none") == "1.2.3"
    
    # Check 'v' prefix preservation
    assert calculate_next_version("v1.2.3", "patch") == "v1.2.4"
    assert calculate_next_version("v1.2.3", "minor") == "v1.3.0"
    assert calculate_next_version("v1.2.3", "major") == "v2.0.0"

def test_extract_json_from_text():
    # Plain JSON
    text1 = '{"bump_type": "minor", "confidence": 0.9, "reasoning": "New feature", "breaking_changes": [], "key_changes": ["Added CLI"]}'
    res1 = extract_json_from_text(text1)
    analysis1 = BumpAnalysis(**res1)
    assert analysis1.bump_type == "minor"
    assert analysis1.confidence == 0.9

    # Markdown fenced JSON
    text2 = '''```json
    {
        "bump_type": "major",
        "confidence": 1.0,
        "reasoning": "Removed legacy function",
        "breaking_changes": ["Removed old_api()"],
        "key_changes": ["Refactor"]
    }
    ```'''
    res2 = extract_json_from_text(text2)
    analysis2 = BumpAnalysis(**res2)
    assert analysis2.bump_type == "major"
    assert len(analysis2.breaking_changes) == 1

def test_find_and_bump_version_targets(tmp_path: Path):
    # สร้างไฟล์จำลอง: pyproject.toml
    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text('[project]\nname = "my-app"\nversion = "0.1.0"\n', encoding="utf-8")

    # สร้างไฟล์จำลอง: frontend config (TypeScript)
    frontend_dir = tmp_path / "src"
    frontend_dir.mkdir()
    ts_file = frontend_dir / "config.ts"
    ts_file.write_text('export const VERSION = "0.1.0";\nexport const API_URL = "https://api.example.com";\n', encoding="utf-8")

    # ค้นหา targets
    targets = find_version_targets(root_dir=tmp_path)
    assert len(targets) == 2
    
    target_names = {t.file_path.name for t in targets}
    assert "pyproject.toml" in target_names
    assert "config.ts" in target_names

    # ทดสอบ apply bump เป็น 0.2.0
    for t in targets:
        success = apply_version_bump(t, "0.2.0")
        assert success is True

    # ตรวจสอบว่าไฟล์ถูกแก้จริง
    assert 'version = "0.2.0"' in pyproject_file.read_text(encoding="utf-8")
    assert 'export const VERSION = "0.2.0";' in ts_file.read_text(encoding="utf-8")

def test_config_and_key_lookup(tmp_path: Path):
    from shift_this_version import config, analyzer
    config_file = tmp_path / "config.json"
    orig_file = config.CONFIG_FILE
    try:
        config.CONFIG_FILE = config_file
        config.CONFIG_DIR = tmp_path
        
        assert config.is_first_run() is True
        config.save_config({
            "default_provider": "anthropic",
            "api_keys": {
                "gemini": "test-key-gemini",
                "anthropic": "test-key-claude",
                "deepseek": "test-key-deepseek",
                "groq": "test-key-groq",
                "openrouter": "test-key-or"
            },
            "models": {
                "openrouter": "anthropic/claude-3.5-haiku"
            },
            "hosts": {
                "ollama": "http://192.168.1.50:11434"
            }
        })
        assert config.is_first_run() is False
        assert config.get_default_provider() == "anthropic"
        assert config.get_configured_key("anthropic") == "test-key-claude"
        assert config.get_configured_key("deepseek") == "test-key-deepseek"
        assert config.get_configured_key("groq") == "test-key-groq"
        assert config.get_configured_model("openrouter") == "anthropic/claude-3.5-haiku"
        assert config.get_configured_host("ollama") == "http://192.168.1.50:11434"
        assert analyzer.get_key_for_provider("anthropic") == "test-key-claude"
        assert analyzer.get_key_for_provider("deepseek") == "test-key-deepseek"
        assert analyzer.get_key_for_provider("groq") == "test-key-groq"
    finally:
        config.CONFIG_FILE = orig_file

if __name__ == "__main__":
    import tempfile
    test_calculate_next_version()
    print("[PASS] test_calculate_next_version passed")
    test_extract_json_from_text()
    print("[PASS] test_extract_json_from_text passed")
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_find_and_bump_version_targets(Path(tmp_dir))
    print("[PASS] test_find_and_bump_version_targets passed")
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_config_and_key_lookup(Path(tmp_dir))
    print("[PASS] test_config_and_key_lookup passed")
    print("\nAll unit tests passed successfully!")



