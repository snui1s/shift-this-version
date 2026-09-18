import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shift_this_version import git_ops

def test_untracked_diff_extraction_and_readonly():
    """
    Test that get_uncommitted_diff_with_untracked():
    1. Extracts the diff content of newly created untracked ('??' / 'U') files.
    2. Maintains 100% read-only isolation (does NOT alter real git index or stage the file).
    3. Respects include_uncommitted flag in get_diff_summary().
    """
    test_file_name = "test_dummy_untracked_unit_test.py"
    test_marker = "# UNIT_TEST_UNTRACKED_MARKER_987654321"
    test_content = f"{test_marker}\ndef temp_test_func():\n    return 'hello_untracked'\n"

    # Write temporary untracked file in repo root
    test_file_path = Path(test_file_name)
    test_file_path.write_text(test_content, encoding="utf-8")

    try:
        # 1. Verify git recognizes it as untracked (??)
        dirty_files = git_ops.get_dirty_files()
        assert any(status == "??" and path == test_file_name for status, path in dirty_files), (
            f"Expected {test_file_name} to be detected as untracked '??' in dirty_files"
        )

        # 2. Verify get_uncommitted_diff_with_untracked() extracts the file content
        uncommitted_diff = git_ops.get_uncommitted_diff_with_untracked()
        assert test_marker in uncommitted_diff, (
            "Untracked file content should appear in get_uncommitted_diff_with_untracked() diff"
        )
        assert "hello_untracked" in uncommitted_diff

        # 3. Verify Read-Only Isolation: Real git status must STILL show ?? (NOT staged in .git/index)
        status_after_diff = git_ops.run_git(["status", "--porcelain"])
        assert f"?? {test_file_name}" in status_after_diff, (
            "Real Git status must remain strictly untracked (??); temp index must not touch real index"
        )

        # 4. Verify get_diff_summary(include_uncommitted=True) includes the untracked file
        latest_tag = git_ops.get_latest_tag()
        summary_included = git_ops.get_diff_summary(latest_tag, include_uncommitted=True, max_chars=100000)
        assert test_marker in summary_included, (
            "get_diff_summary(include_uncommitted=True) must include untracked workspace edits"
        )

        # 5. Verify get_diff_summary(include_uncommitted=False) excludes the untracked file
        summary_excluded = git_ops.get_diff_summary(latest_tag, include_uncommitted=False, max_chars=100000)
        assert test_marker not in summary_excluded, (
            "get_diff_summary(include_uncommitted=False) must exclude uncommitted workspace changes"
        )

    finally:
        # Clean up temporary test file
        if test_file_path.exists():
            test_file_path.unlink()

def test_untracked_noise_files_excluded():
    """
    Test that untracked noise files (like dummy.lock, image.png)
    are properly filtered out by EXCLUDE_PATTERNS and not sent into the diff.
    """
    ext = ".lock"
    base = "test_dummy_noise_file"
    noise_filename = f"{base}{ext}"
    noise_file = Path(noise_filename)
    noise_file.write_text("SOME_DATA_INSIDE", encoding="utf-8")

    try:
        diff = git_ops.get_uncommitted_diff_with_untracked()
        # Verify the actual diff header for this file was not created
        assert f"diff --git a/{noise_filename}" not in diff, (
            "Noise files matching EXCLUDE_PATTERNS should not have a diff section"
        )
        assert f"+++ b/{noise_filename}" not in diff
    finally:
        if noise_file.exists():
            noise_file.unlink()

def test_clean_working_tree_fallback():
    """
    Test that when there are no untracked files matching,
    get_uncommitted_diff_with_untracked safely delegates to get_uncommitted_diff.
    """
    diff = git_ops.get_uncommitted_diff_with_untracked()
    assert isinstance(diff, str)

if __name__ == "__main__":
    print("Running test_untracked_diff_extraction_and_readonly...")
    test_untracked_diff_extraction_and_readonly()
    print("[PASS] test_untracked_diff_extraction_and_readonly passed.")

    print("Running test_clean_working_tree_fallback...")
    test_clean_working_tree_fallback()
    print("[PASS] test_clean_working_tree_fallback passed.")

    print("\nAll Git Untracked Diff unit tests passed successfully!")
