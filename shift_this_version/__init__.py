"""
shift-this-version: Smart SemVer Bumper driven by Code Diff & AI
"""

from .analyzer import analyze, BumpAnalysis
from .updater import calculate_next_version, find_version_targets, apply_version_bump, VersionTarget
from .git_ops import get_filtered_diff, get_commits_since, get_latest_tag, get_diff_summary

__version__ = "1.4.0"

__all__ = [
    "analyze",
    "BumpAnalysis",
    "calculate_next_version",
    "find_version_targets",
    "apply_version_bump",
    "VersionTarget",
    "get_filtered_diff",
    "get_commits_since",
    "get_latest_tag",
    "get_diff_summary",
    "__version__"
]
