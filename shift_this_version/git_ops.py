import subprocess
from typing import List, Tuple, Optional

# Pathspec exclusions for noise files across all Git operations
EXCLUDE_PATTERNS: List[str] = [
    ":(exclude)*.lock",
    ":(exclude)*lock.json",
    ":(exclude)*.min.*",
    ":(exclude)docs/*",
    ":(exclude)*.png",
    ":(exclude)*.jpg",
    ":(exclude)*.jpeg",
    ":(exclude)*.gif",
    ":(exclude)*.svg",
    ":(exclude)*.ico"
]

def run_git(args: List[str], timeout: Optional[float] = 30.0) -> str:
    """
    Execute a git command with timeout and return stdout as a stripped string.
    Raises subprocess.CalledProcessError or subprocess.SubprocessError on timeout/failure.
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
            timeout=timeout
        )
        if result.stdout is None:
            return ""
        return result.stdout.strip()
    except subprocess.TimeoutExpired as e:
        raise subprocess.SubprocessError(
            f"Git command timed out after {timeout}s: git {' '.join(args)}"
        ) from e


def get_latest_tag() -> Optional[str]:
    """Retrieve the latest reachable Git tag from the current commit."""
    try:
        return run_git(["describe", "--tags", "--abbrev=0"])
    except (subprocess.CalledProcessError, subprocess.SubprocessError):
        return None

def tag_exists(tag_name: str) -> bool:
    """Check if a Git tag exists in local repository."""
    try:
        output = run_git(["tag", "-l", tag_name])
        return bool(output.strip() == tag_name)
    except (subprocess.CalledProcessError, subprocess.SubprocessError):
        return False

def get_commits_since(tag: Optional[str]) -> List[str]:
    """Retrieve list of one-line commit logs from the latest tag up to HEAD."""
    rev_range = f"{tag}..HEAD" if tag else "HEAD"
    try:
        logs = run_git(["log", rev_range, "--oneline"])
        return [line for line in logs.split("\n") if line]
    except (subprocess.CalledProcessError, subprocess.SubprocessError):
        return []

def get_committed_diff(tag: Optional[str]) -> str:
    """Extract diff of committed changes between tag and HEAD excluding noise files."""
    rev_range = f"{tag}..HEAD" if tag else "HEAD"
    try:
        return run_git(["diff", rev_range, "--"] + EXCLUDE_PATTERNS)
    except (subprocess.CalledProcessError, subprocess.SubprocessError):
        return ""

def get_uncommitted_diff() -> str:
    """Extract diff of uncommitted working tree changes excluding noise files."""
    try:
        return run_git(["diff", "HEAD", "--"] + EXCLUDE_PATTERNS)
    except (subprocess.CalledProcessError, subprocess.SubprocessError):
        return ""

def get_filtered_diff(tag: Optional[str]) -> str:
    """
    Extract source code Git diff excluding noise files.
    Compares the latest tag against current working tree (commits + uncommitted edits).
    """
    cmd = ["diff"]
    if tag:
        cmd.append(tag)
    cmd += ["--"] + EXCLUDE_PATTERNS
    try:
        return run_git(cmd)
    except (subprocess.CalledProcessError, subprocess.SubprocessError):
        return ""

def get_diff_stat(tag: Optional[str]) -> str:
    """Retrieve git diff --stat to view summary of file changes."""
    cmd = ["diff", "--stat"]
    if tag:
        cmd.append(tag)
    try:
        return run_git(cmd)
    except (subprocess.CalledProcessError, subprocess.SubprocessError):
        return ""

def get_diff_summary(tag: Optional[str], max_chars: int = 15000) -> str:
    """
    Retrieve diff intelligently separated into committed vs uncommitted changes,
    truncated if exceeding max_chars to prevent token overflow.
    """
    committed_diff = get_committed_diff(tag)
    uncommitted_diff = get_uncommitted_diff()

    sections = []
    if committed_diff.strip():
        sections.append(f"=== Committed Changes ({tag or 'initial'}..HEAD) ===\n{committed_diff}")
    if uncommitted_diff.strip():
        sections.append(f"=== Uncommitted Working Tree Edits ===\n{uncommitted_diff}")

    raw_diff = "\n\n".join(sections)
    if not raw_diff:
        # Fallback to standard filtered diff if revision range is empty
        raw_diff = get_filtered_diff(tag)
    
    if not raw_diff:
        return ""

    if len(raw_diff) <= max_chars:
        return raw_diff
    
    # Prepend diff --stat and truncate diff body
    stat = get_diff_stat(tag)
    header_info = f"--- Diff Stat Summary ---\n{stat}\n\n--- Truncated Diff Snippet ---\n"
    remaining_budget = max_chars - len(header_info) - 200
    
    truncated_diff = raw_diff[:max(1000, remaining_budget)]
    notice = f"\n\n[... Diff truncated: showing {len(truncated_diff)} of {len(raw_diff)} total characters to fit AI context budget ...]"
    return header_info + truncated_diff + notice

def has_uncommitted_changes() -> bool:
    """Check if the repository has uncommitted or dirty changes."""
    try:
        output = run_git(["status", "--porcelain"])
        return bool(output.strip())
    except (subprocess.CalledProcessError, subprocess.SubprocessError):
        return False

def get_current_branch() -> str:
    """Retrieve current active Git branch name."""
    try:
        branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        return branch if branch else "main"
    except (subprocess.CalledProcessError, subprocess.SubprocessError):
        return "main"

def commit_version_bump(files: List[str], version: str, stage_all: bool = False, message: Optional[str] = None) -> bool:
    """Stage modified version files only and create a release commit."""
    try:
        if not files:
            return False
        if stage_all:
            run_git(["add", "-u"])
        run_git(["add"] + files)
        commit_msg = message or f"chore(release): shift version to {version}"
        run_git(["commit", "-m", commit_msg])
        return True
    except (subprocess.CalledProcessError, subprocess.SubprocessError):
        return False

def create_git_tag(tag_name: str, message: Optional[str] = None) -> Tuple[bool, str]:
    """Create an annotated Git release tag (e.g. v1.2.0). Returns (success, message)."""
    if tag_exists(tag_name):
        return False, f"Tag '{tag_name}' already exists in local repository."
    try:
        msg = message or f"Release {tag_name}"
        run_git(["tag", "-a", tag_name, "-m", msg])
        return True, f"Created Git Tag: {tag_name}"
    except subprocess.CalledProcessError as e:
        err = str(e.stderr or e.stdout or str(e)).strip()
        return False, err
    except subprocess.SubprocessError as e:
        return False, str(e)

def push_to_remote(tag_name: Optional[str] = None, remote: str = "origin") -> Tuple[bool, str]:
    """Push current branch and release tag to remote git repository."""
    branch = get_current_branch()
    try:
        # 1. Push branch (60s network timeout)
        run_git(["push", remote, branch], timeout=60.0)
        # 2. Push tag if created
        if tag_name:
            run_git(["push", remote, tag_name], timeout=60.0)
        return True, f"{branch} & {tag_name or ''}".strip(" & ")
    except subprocess.CalledProcessError as e:
        err_msg = str(e.stderr or e.stdout or str(e))
        return False, err_msg.strip()
    except subprocess.SubprocessError as e:
        return False, str(e)

def get_latest_diff_sample(tag: Optional[str]) -> Tuple[str, str]:
    """
    Retrieve the most recent diff sample:
    - If there are uncommitted changes in the working tree, return their diff first.
    - If working tree is clean, return the diff of the latest commit.
    - Returns (label, diff_content)
    """
    # 1. First priority: Uncommitted working tree edits (what user just modified)
    try:
        uncommitted = run_git(["diff", "HEAD", "--"] + EXCLUDE_PATTERNS)
        if uncommitted.strip():
            status_lines = [line.strip().split()[-1] for line in run_git(["status", "--porcelain"]).split("\n") if line.strip()]
            files_str = ", ".join(status_lines[:3])
            if len(status_lines) > 3:
                files_str += f" (+{len(status_lines)-3} more)"
            return f"Latest Uncommitted Changes ({files_str})", uncommitted
    except Exception:
        pass

    # 2. Second priority: Latest commit diff
    try:
        latest_commit = run_git(["log", "-1", "--oneline"])
        commit_diff = run_git(["diff", "HEAD~1", "HEAD", "--"] + EXCLUDE_PATTERNS)
        if commit_diff.strip():
            return f"Latest Commit Diff ({latest_commit})", commit_diff
    except Exception:
        pass

    # 3. Fallback: Tag diff
    tag_diff = get_filtered_diff(tag)
    return "Changes Since Latest Release", tag_diff