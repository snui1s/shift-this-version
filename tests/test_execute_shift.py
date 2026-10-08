"""End-to-end tests of execute_shift() against a throwaway git repo, with the LLM mocked."""
import subprocess

import pytest
import typer

from shift_this_version import analyzer, check_update, cli, config, git_ops


def _git(repo, *args):
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path, monkeypatch):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test")
    _git(tmp_path, "config", "commit.gpgsign", "false")
    _git(tmp_path, "config", "tag.gpgsign", "false")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "1.0.0"\n', encoding="utf-8"
    )
    (tmp_path / "app.py").write_text("def hello():\n    return 1\n", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "chore: initial")
    _git(tmp_path, "tag", "-a", "v1.0.0", "-m", "v1.0.0")
    (tmp_path / "app.py").write_text(
        "def hello():\n    return 1\n\ndef goodbye():\n    return 2\n", encoding="utf-8"
    )
    _git(tmp_path, "commit", "-q", "-am", "feat: add goodbye")

    monkeypatch.chdir(tmp_path)
    # Isolate from the developer's real config / network
    monkeypatch.setattr(config, "get_default_provider", lambda: "gemini")
    monkeypatch.setattr(config, "get_configured_model", lambda p: None)
    monkeypatch.setattr(config, "get_configured_host", lambda p: None)
    monkeypatch.setattr(check_update, "show_update_notification_if_available", lambda *a, **k: None)
    return tmp_path


def _fake_analysis(bump="minor"):
    return analyzer.BumpAnalysis(
        bump_type=bump,
        confidence=0.9,
        commit_message="feat: add goodbye",
        reasoning="New public function added.",
        key_changes=["goodbye()"],
    )


def test_execute_shift_bumps_commits_and_tags(repo, monkeypatch):
    monkeypatch.setattr(analyzer, "analyze", lambda **kw: _fake_analysis("minor"))

    cli.execute_shift(provider="gemini", yes=True, push=False)

    assert 'version = "1.1.0"' in (repo / "pyproject.toml").read_text(encoding="utf-8")
    assert git_ops.tag_exists("v1.1.0")
    assert _git(repo, "status", "--porcelain") == ""
    assert _git(repo, "rev-list", "-n1", "v1.1.0") == _git(repo, "rev-parse", "HEAD")


def test_execute_shift_dry_run_changes_nothing(repo, monkeypatch):
    monkeypatch.setattr(analyzer, "analyze", lambda **kw: _fake_analysis("major"))
    head_before = _git(repo, "rev-parse", "HEAD")

    with pytest.raises(typer.Exit) as exc:
        cli.execute_shift(provider="gemini", yes=True, dry_run=True, push=False)
    assert exc.value.exit_code == 0

    assert 'version = "1.0.0"' in (repo / "pyproject.toml").read_text(encoding="utf-8")
    assert not git_ops.tag_exists("v2.0.0")
    assert _git(repo, "rev-parse", "HEAD") == head_before


def test_execute_shift_no_tag_no_commit(repo, monkeypatch):
    monkeypatch.setattr(analyzer, "analyze", lambda **kw: _fake_analysis("patch"))
    head_before = _git(repo, "rev-parse", "HEAD")

    cli.execute_shift(provider="gemini", yes=True, tag=False, commit=False, push=False)

    assert 'version = "1.0.1"' in (repo / "pyproject.toml").read_text(encoding="utf-8")
    assert not git_ops.tag_exists("v1.0.1")
    assert _git(repo, "rev-parse", "HEAD") == head_before


def test_execute_shift_ai_failure_noninteractive_exits_without_changes(repo, monkeypatch):
    def boom(**kw):
        raise ConnectionError("provider down")

    monkeypatch.setattr(analyzer, "analyze", boom)

    with pytest.raises(typer.Exit) as exc:
        cli.execute_shift(provider="gemini", yes=True, push=False)

    assert exc.value.exit_code == 1
    assert 'version = "1.0.0"' in (repo / "pyproject.toml").read_text(encoding="utf-8")
    assert _git(repo, "status", "--porcelain") == ""


def test_execute_shift_no_changes_since_tag_exits_cleanly(repo, monkeypatch):
    _git(repo, "tag", "-a", "v1.0.1", "-m", "v1.0.1")  # tag HEAD -> nothing new
    monkeypatch.setattr(analyzer, "analyze", lambda **kw: pytest.fail("AI must not be called"))

    with pytest.raises(typer.Exit) as exc:
        cli.execute_shift(provider="gemini", yes=True, push=False)

    assert exc.value.exit_code == 0
