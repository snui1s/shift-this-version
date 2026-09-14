import subprocess
from typing import List, Tuple, Optional

def run_git(args: List[str]) -> str:
    """รันคำสั่ง git และคืนค่า output เป็น string"""
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()

def get_latest_tag() -> Optional[str]:
    """หา Tag ล่าสุดของ Repo"""
    try:
        # หา tag ล่าสุดที่เข้าถึงได้จาก commit ปัจจุบัน
        return run_git(["describe", "--tags", "--abbrev=0"])
    except subprocess.CalledProcessError:
        return None

def get_commits_since(tag: Optional[str]) -> List[str]:
    """ดึงรายชื่อ Commit logs ตั้งแต่ tag ล่าสุดจนถึง HEAD"""
    rev_range = f"{tag}..HEAD" if tag else "HEAD"
    try:
        logs = run_git(["log", rev_range, "--oneline"])
        return [line for line in logs.split("\n") if line]
    except subprocess.CalledProcessError:
        return []

def get_filtered_diff(tag: Optional[str]) -> str:
    """
    ดึง Git Diff เฉพาะ source code
    ตัดไฟล์ noise เช่น lockfiles, minified files, หรือ docs ทิ้ง
    """
    rev_range = f"{tag}..HEAD" if tag else "HEAD"
    
    # Pathspec exclusion: ไม่เอา lockfile และ markdown ที่ไม่เกี่ยว
    exclude_patterns = [
        ":(exclude)*.lock",
        ":(exclude)*lock.json",
        ":(exclude)*.min.*",
        ":(exclude)docs/*",
        ":(exclude)*.png",
        ":(exclude)*.jpg"
    ]
    
    cmd = ["diff", rev_range, "--"] + exclude_patterns
    try:
        return run_git(cmd)
    except subprocess.CalledProcessError:
        return ""

def get_diff_stat(tag: Optional[str]) -> str:
    """ดึง git diff --stat เพื่อดูภาพรวมการเปลี่ยนแปลงไฟล์"""
    rev_range = f"{tag}..HEAD" if tag else "HEAD"
    try:
        return run_git(["diff", "--stat", rev_range])
    except subprocess.CalledProcessError:
        return ""

def get_diff_summary(tag: Optional[str], max_chars: int = 15000) -> str:
    """
    ดึง diff และตัดทอนเนื้อหาอย่างชาญฉลาดหากเกิน max_chars
    เพื่อป้องกัน token overflow และรักษา header/โครงสร้างสำคัญไว้
    """
    raw_diff = get_filtered_diff(tag)
    if not raw_diff:
        return ""
    
    if len(raw_diff) <= max_chars:
        return raw_diff
    
    # หากยาวเกิน ให้แทรก diff --stat ไว้ด้านบน และตัดเนื้อหา
    stat = get_diff_stat(tag)
    header_info = f"--- Diff Stat Summary ---\n{stat}\n\n--- Truncated Diff Snippet ---\n"
    remaining_budget = max_chars - len(header_info) - 200
    
    truncated_diff = raw_diff[:max(1000, remaining_budget)]
    notice = f"\n\n[... Diff truncated: showing {len(truncated_diff)} of {len(raw_diff)} total characters to fit AI context budget ...]"
    return header_info + truncated_diff + notice

def has_uncommitted_changes() -> bool:
    """ตรวจสอบว่ามีไฟล์ uncommitted/dirty อยู่หรือไม่"""
    try:
        output = run_git(["status", "--porcelain"])
        return bool(output.strip())
    except subprocess.CalledProcessError:
        return False

def commit_version_bump(files: List[str], version: str) -> bool:
    """ทำ git add และ git commit สำหรับการ bump version"""
    try:
        run_git(["add"] + files)
        commit_msg = f"chore(release): bump version to {version}"
        run_git(["commit", "-m", commit_msg])
        return True
    except subprocess.CalledProcessError:
        return False

def create_git_tag(tag_name: str, message: Optional[str] = None) -> bool:
    """สร้าง git tag (เช่น v1.2.0)"""
    try:
        msg = message or f"Release {tag_name}"
        run_git(["tag", "-a", tag_name, "-m", msg])
        return True
    except subprocess.CalledProcessError:
        return False