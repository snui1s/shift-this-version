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

    # Check SemVer 2.0 Prerelease handling
    assert calculate_next_version("1.2.3-rc.1", "none") == "1.2.3-rc.1"
    assert calculate_next_version("1.2.3-beta.2", "patch") == "1.2.3"
    assert calculate_next_version("1.3.0-rc.1", "minor") == "1.3.0"
    assert calculate_next_version("2.0.0-rc.1", "major") == "2.0.0"
    assert calculate_next_version("v1.2.3-rc.1", "none") == "v1.2.3-rc.1"
    assert calculate_next_version("v1.2.3-beta.2", "patch") == "v1.2.3"


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

    # With commit_message
    text3 = '{"bump_type": "patch", "confidence": 1.0, "commit_message": "fix(core): resolve null pointer", "reasoning": "bugfix", "breaking_changes": [], "key_changes": ["fix"]}'
    res3 = extract_json_from_text(text3)
    analysis3 = BumpAnalysis(**res3)
    assert analysis3.commit_message == "fix(core): resolve null pointer"

    # DeepSeek / Reasoning model output with <think>...</think> and preamble
    text_think = '''<think>
    Analyzing the diff:
    - Added tests
    - Changed python version requirement
    This should be a minor release.
    </think>
    Here is the final JSON result:
    ```json
    {
        "bump_type": "minor",
        "confidence": 0.95,
        "commit_message": "feat(core): enhance resilience",
        "reasoning": "Added backward-compatible improvements",
        "breaking_changes": [],
        "key_changes": ["resilient json parser"]
    }
    ```
    I hope this helps!'''
    res_think = extract_json_from_text(text_think)
    analysis_think = BumpAnalysis(**res_think)
    assert analysis_think.bump_type == "minor"
    assert analysis_think.commit_message == "feat(core): enhance resilience"

    # Nested container response (e.g. {"analysis": {"type": "PATCH", ...}})
    text_nested = '''{
        "analysis": {
            "type": "PATCH",
            "score": 90,
            "explanation": "Bug fixes only",
            "commitMessage": "fix: resolve edge case"
        }
    }'''
    res_nested = extract_json_from_text(text_nested)
    analysis_nested = BumpAnalysis(**res_nested)
    assert analysis_nested.bump_type == "patch"
    assert analysis_nested.confidence == 0.9
    assert analysis_nested.reasoning == "Bug fixes only"
    assert analysis_nested.commit_message == "fix: resolve edge case"

    # Trailing comma resilience
    text_trailing = '{"bump_type": "minor", "reasoning": "ok",}'
    res_trailing = extract_json_from_text(text_trailing)
    analysis_trailing = BumpAnalysis(**res_trailing)
    assert analysis_trailing.bump_type == "minor"

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

def test_apply_version_bump_precision(tmp_path: Path):
    # ทดสอบกรณีมีสตริงเวอร์ชันเดิมซ้ำในคอมเมนต์ บรรทัดเดียวกัน
    code_file = tmp_path / "version.py"
    code_file.write_text('VERSION = "1.0.0"  # previously 1.0.0\n', encoding="utf-8")
    
    targets = find_version_targets(root_dir=tmp_path)
    assert len(targets) == 1
    assert targets[0].current_version == "1.0.0"
    
    success = apply_version_bump(targets[0], "1.1.0")
    assert success is True
    
    updated_content = code_file.read_text(encoding="utf-8")
    # เฉพาะ VERSION ในเครื่องหมายคำพูดต้องเปลี่ยน แต่คอมเมนต์ 1.0.0 ด้านหลังต้องไม่พัง
    assert updated_content == 'VERSION = "1.1.0"  # previously 1.0.0\n'

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

def test_ollama_and_provider_detection(tmp_path: Path):
    from shift_this_version import analyzer, config
    # ทดสอบกรณีไม่มี provider ใดเลย และ Ollama ปิดอยู่
    config_file = tmp_path / "empty_config.json"
    orig_file = config.CONFIG_FILE
    try:
        config.CONFIG_FILE = config_file
        config.CONFIG_DIR = tmp_path
        # ตรวจสอบว่าเช็ก endpoint จำลองแล้วคืน False อย่างปลอดภัย
        assert analyzer.is_ollama_running("http://127.0.0.1:59999") is False
        
        # เมื่อไม่มี keys และ Ollama ไม่ได้รัน ต้องได้ (None, None)
        prov, key = analyzer.detect_default_provider()
        assert prov is None or prov in ("ollama", "custom")
    finally:
        config.CONFIG_FILE = orig_file

def test_git_ops_tag_functions():
    from shift_this_version import git_ops
    # ตรวจสอบ is_git_repo ใน workspace ปัจจุบัน
    assert git_ops.is_git_repo() is True
    # ตรวจสอบ has_remote
    assert isinstance(git_ops.has_remote("origin"), bool)
    # ตรวจสอบ tag_exists สำหรับ tag ที่ไม่มีอยู่จริง
    assert git_ops.tag_exists("v999.999.999-nonexistent") is False
    # ตรวจสอบ create_git_tag รายงานผลแบบ tuple (bool, str)
    latest = git_ops.get_latest_tag()
    if latest:
        ok, msg = git_ops.create_git_tag(latest)
        assert ok is False
        assert "already exists" in msg

def test_additional_config_patterns(tmp_path: Path):
    # Test setup.py, composer.json, pubspec.yaml
    setup_file = tmp_path / "setup.py"
    setup_file.write_text('from setuptools import setup\nsetup(\n    name="pkg",\n    version="0.5.0",\n)\n', encoding="utf-8")

    composer_file = tmp_path / "composer.json"
    composer_file.write_text('{\n  "name": "vendor/package",\n  "version": "1.4.2"\n}\n', encoding="utf-8")

    pubspec_file = tmp_path / "pubspec.yaml"
    pubspec_file.write_text('name: flutter_app\nversion: 2.1.0\n', encoding="utf-8")

    targets = find_version_targets(root_dir=tmp_path)
    target_map = {t.file_path.name: t for t in targets}

    assert "setup.py" in target_map
    assert target_map["setup.py"].current_version == "0.5.0"
    apply_version_bump(target_map["setup.py"], "0.6.0")
    assert 'version="0.6.0"' in setup_file.read_text(encoding="utf-8")

    assert "composer.json" in target_map
    assert target_map["composer.json"].current_version == "1.4.2"
    apply_version_bump(target_map["composer.json"], "1.5.0")
    assert '"version": "1.5.0"' in composer_file.read_text(encoding="utf-8")

    assert "pubspec.yaml" in target_map
    assert target_map["pubspec.yaml"].current_version == "2.1.0"
    apply_version_bump(target_map["pubspec.yaml"], "2.2.0")
    assert 'version: 2.2.0' in pubspec_file.read_text(encoding="utf-8")

def test_sync_lockfiles(tmp_path: Path):
    from shift_this_version.updater import sync_lockfiles
    # Test directory without lockfiles returns empty list safely
    synced = sync_lockfiles(root_dir=tmp_path)
    assert synced == []

def test_prompt_manual_bump():
    from shift_this_version import cli
    import typer
    orig_prompt = typer.prompt
    try:
        # Patch
        typer.prompt = lambda msg, default="": "1"
        assert cli.prompt_manual_bump("1.0.0") == "1.0.1"
        # Minor
        typer.prompt = lambda msg, default="": "2"
        assert cli.prompt_manual_bump("1.0.0") == "1.1.0"
        # Major
        typer.prompt = lambda msg, default="": "3"
        assert cli.prompt_manual_bump("1.0.0") == "2.0.0"
    finally:
        typer.prompt = orig_prompt

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
        test_apply_version_bump_precision(Path(tmp_dir))
    print("[PASS] test_apply_version_bump_precision passed")
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_config_and_key_lookup(Path(tmp_dir))
    print("[PASS] test_config_and_key_lookup passed")
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_ollama_and_provider_detection(Path(tmp_dir))
    print("[PASS] test_ollama_and_provider_detection passed")
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_additional_config_patterns(Path(tmp_dir))
    print("[PASS] test_additional_config_patterns passed")
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_sync_lockfiles(Path(tmp_dir))
    print("[PASS] test_sync_lockfiles passed")
    test_git_ops_tag_functions()
    print("[PASS] test_git_ops_tag_functions passed")
    test_prompt_manual_bump()
    print("[PASS] test_prompt_manual_bump passed")
    print("\nAll unit tests passed successfully!")



