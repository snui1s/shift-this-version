import re
from pathlib import Path
from typing import List, Optional, Tuple, NamedTuple

class VersionTarget(NamedTuple):
    file_path: Path
    target_type: str        # 'config' หรือ 'code_var'
    current_version: str
    line_number: int
    matched_line: str
    pattern_name: str       # เช่น 'pyproject.toml', 'package.json', 'VERSION'

SEMVER_REGEX = r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)(?:-(?P<prerelease>[0-9A-Za-z.-]+))?(?:\+(?P<build>[0-9A-Za-z.-]+))?"

# รูปแบบของไฟล์ Config มาตรฐาน
CONFIG_PATTERNS = [
    # pyproject.toml: version = "1.2.3"
    {
        "filename": "pyproject.toml",
        "regex": re.compile(rf'^(?P<prefix>\s*version\s*=\s*["\'])(?P<version>{SEMVER_REGEX})(?P<suffix>["\'])', re.MULTILINE),
        "name": "pyproject.toml"
    },
    # package.json: "version": "1.2.3"
    {
        "filename": "package.json",
        "regex": re.compile(rf'^(?P<prefix>\s*"version"\s*:\s*["\'])(?P<version>{SEMVER_REGEX})(?P<suffix>["\'])', re.MULTILINE),
        "name": "package.json"
    },
    # Cargo.toml: version = "1.2.3"
    {
        "filename": "Cargo.toml",
        "regex": re.compile(rf'^(?P<prefix>\s*version\s*=\s*["\'])(?P<version>{SEMVER_REGEX})(?P<suffix>["\'])', re.MULTILINE),
        "name": "Cargo.toml"
    },
    # setup.cfg: version = 1.2.3
    {
        "filename": "setup.cfg",
        "regex": re.compile(rf'^(?P<prefix>\s*version\s*=\s*)(?P<version>{SEMVER_REGEX})(?P<suffix>\s*)$', re.MULTILINE),
        "name": "setup.cfg"
    },
]

# รูปแบบตัวแปรใน Code เช่น VERSION = "1.0.0", export const VERSION = "1.0.0", __version__ = "1.0.0"
CODE_VAR_REGEX = re.compile(
    rf'^(?P<prefix>\s*(?:export\s+)?(?:const\s+|let\s+|var\s+)?(?:__version__|VERSION|APP_VERSION)\s*[:=]\s*["\'])(?P<version>{SEMVER_REGEX})(?P<suffix>["\'].*)$',
    re.MULTILINE
)

# นามสกุลไฟล์โค้ดที่อนุญาตให้ค้นหาตัวแปร
ALLOWED_CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".vue", ".svelte", ".go", ".rs", ".java"
}

# โฟลเดอร์ที่ต้องข้ามเสมอ
IGNORE_DIRS = {
    ".git", ".venv", "venv", "env", "node_modules", "dist", "build",
    "__pycache__", ".pytest_cache", ".next", ".nuxt", "coverage", ".turbo",
    "tests", "test", "spec", "docs"
}

def parse_semver(version_str: str) -> Tuple[int, int, int, Optional[str]]:
    """แยกส่วน major, minor, patch ออกจากสตริงเวอร์ชัน"""
    clean_ver = version_str.lstrip("v")
    match = re.match(SEMVER_REGEX, clean_ver)
    if not match:
        raise ValueError(f"Invalid SemVer string: '{version_str}'")
    
    major = int(match.group("major"))
    minor = int(match.group("minor"))
    patch = int(match.group("patch"))
    prerelease = match.group("prerelease")
    return major, minor, patch, prerelease

def calculate_next_version(current_ver: str, bump_type: str) -> str:
    """คำนวณเลข SemVer ถัดไปตาม bump_type ('major', 'minor', 'patch', 'none')"""
    has_v_prefix = current_ver.startswith("v")
    major, minor, patch, prerelease = parse_semver(current_ver)
    
    bump = bump_type.lower()
    
    # 1. กรณีไม่มีการเปลี่ยนเวอร์ชัน ให้คงค่าเดิมไว้ (รวมถึง prerelease)
    if bump == "none":
        return current_ver

    # 2. กรณีเวอร์ชันปัจจุบันเป็น prerelease (เช่น 1.2.3-rc.1, 1.2.3-beta.2)
    if prerelease:
        if bump == "patch":
            # ปล่อย stable patch จาก prerelease (1.2.3-rc.1 -> 1.2.3)
            next_ver = f"{major}.{minor}.{patch}"
        elif bump == "minor":
            # ถ้าเป็น prerelease ของ minor อยู่แล้ว (เช่น 1.3.0-rc.1) -> 1.3.0
            next_ver = f"{major}.{minor}.0" if (patch == 0 and minor > 0) else f"{major}.{minor + 1}.0"
        elif bump == "major":
            # ถ้าเป็น prerelease ของ major อยู่แล้ว (เช่น 2.0.0-rc.1) -> 2.0.0
            next_ver = f"{major}.0.0" if (minor == 0 and patch == 0 and major > 0) else f"{major + 1}.0.0"
        else:
            raise ValueError(f"Unknown bump type: {bump_type}")
    else:
        # 3. กรณีปกติ (Stable release อยู่แล้ว)
        if bump == "major":
            next_ver = f"{major + 1}.0.0"
        elif bump == "minor":
            next_ver = f"{major}.{minor + 1}.0"
        elif bump == "patch":
            next_ver = f"{major}.{minor}.{patch + 1}"
        else:
            raise ValueError(f"Unknown bump type: {bump_type}")
        
    return f"v{next_ver}" if has_v_prefix else next_ver


def find_version_targets(
    root_dir: Path = Path("."),
    custom_var_names: Optional[List[str]] = None
) -> List[VersionTarget]:
    """
    ค้นหาไฟล์ทั้งหมดในโปรเจกต์ที่มีการระบุเวอร์ชัน
    1. ไฟล์ config มาตรฐาน (pyproject.toml, package.json, Cargo.toml)
    2. ตัวแปรในโค้ด (เช่น VERSION, __version__, APP_VERSION)
    """
    targets: List[VersionTarget] = []
    seen_files = set()

    # 1. ค้นหาไฟล์ Config มาตรฐานที่ root
    for cfg in CONFIG_PATTERNS:
        cfg_path = root_dir / cfg["filename"]
        if cfg_path.is_file():
            try:
                content = cfg_path.read_text(encoding="utf-8")
                lines = content.splitlines()
                for idx, line in enumerate(lines):
                    match = cfg["regex"].search(line)
                    if match:
                        targets.append(VersionTarget(
                            file_path=cfg_path,
                            target_type="config",
                            current_version=match.group("version"),
                            line_number=idx + 1,
                            matched_line=line.strip(),
                            pattern_name=cfg["name"]
                        ))
                        seen_files.add(cfg_path.resolve())
                        break
            except Exception:
                pass

    # 2. เตรียม regex สำหรับตัวแปรโค้ด
    var_pattern = CODE_VAR_REGEX
    if custom_var_names:
        names_group = "|".join(re.escape(n) for n in custom_var_names)
        var_pattern = re.compile(
            rf'^(?P<prefix>.*?(?:export\s+)?(?:const|let|var)?\s*(?:{names_group})\s*[:=]\s*["\'])(?P<version>{SEMVER_REGEX})(?P<suffix>["\'].*)$',
            re.MULTILINE
        )

    # ค้นหาในไฟล์โค้ด (ลึกไม่เกิน 4 ชั้น เพื่อความรวดเร็วและปลอดภัย)
    for p in root_dir.rglob("*"):
        if any(ignored in p.parts for ignored in IGNORE_DIRS):
            continue
        if not p.is_file() or p.suffix.lower() not in ALLOWED_CODE_EXTENSIONS:
            continue
        if p.resolve() in seen_files:
            continue
        # ข้ามไฟล์ขนาดใหญ่เกิน 1MB
        try:
            if p.stat().st_size > 1_000_000:
                continue
            content = p.read_text(encoding="utf-8")
        except Exception:
            continue

        # ข้ามไฟล์ที่ขึ้นต้นด้วย test_ หรือลงท้ายด้วย _test / .test / .spec
        lower_stem = p.stem.lower()
        if lower_stem.startswith("test_") or lower_stem.endswith(("_test", ".test", ".spec")):
            continue

        for idx, line in enumerate(content.splitlines()):
            stripped = line.strip()
            if stripped.startswith(("#", "//", "/*", "*", '"""', "'''")):
                continue

            match = var_pattern.search(line)
            if match:
                targets.append(VersionTarget(
                    file_path=p,
                    target_type="code_var",
                    current_version=match.group("version"),
                    line_number=idx + 1,
                    matched_line=line.strip(),
                    pattern_name="code_variable"
                ))


    return targets

def apply_version_bump(
    target: VersionTarget,
    new_version: str,
    dry_run: bool = False
) -> bool:
    """
    เขียนเลขเวอร์ชันใหม่ลงในไฟล์เป้าหมายอย่างแม่นยำด้วย Regex span
    """
    clean_new_ver = new_version.lstrip("v")
    try:
        content = target.file_path.read_text(encoding="utf-8")
        lines = content.splitlines(keepends=True)
        
        target_idx = target.line_number - 1
        if 0 <= target_idx < len(lines):
            old_line = lines[target_idx]
            
            # 1. ลองค้นหาด้วย pattern ที่ตรงกับ filename / config pattern
            new_line = old_line
            matched = False
            for cfg in CONFIG_PATTERNS:
                m = cfg["regex"].search(old_line)
                if m and m.group("version") == target.current_version:
                    start, end = m.span("version")
                    new_line = old_line[:start] + clean_new_ver + old_line[end:]
                    matched = True
                    break

            # 2. ถ้าไม่ใช่ config pattern ให้ลองค้นหาด้วย code var pattern
            if not matched:
                m = CODE_VAR_REGEX.search(old_line)
                if m and m.group("version") == target.current_version:
                    start, end = m.span("version")
                    new_line = old_line[:start] + clean_new_ver + old_line[end:]
                    matched = True

            # 3. กรณีทั่วไป หา match ของ SEMVER_REGEX ที่มีค่าตรงกับ target.current_version
            if not matched:
                for m in re.finditer(SEMVER_REGEX, old_line):
                    if m.group(0) == target.current_version:
                        start, end = m.span(0)
                        new_line = old_line[:start] + clean_new_ver + old_line[end:]
                        matched = True
                        break

            # 4. Fallback ถ้า regex ไม่ตรง (เช่น format พิเศษ) ใช้ตำแหน่งสุดท้ายของ string ในบรรทัด
            if not matched:
                idx = old_line.rfind(target.current_version)
                if idx != -1:
                    new_line = old_line[:idx] + clean_new_ver + old_line[idx + len(target.current_version):]

            if old_line != new_line:
                lines[target_idx] = new_line
                if not dry_run:
                    target.file_path.write_text("".join(lines), encoding="utf-8")
                return True
    except Exception as e:
        print(f"Error updating {target.file_path}: {e}")
    return False
