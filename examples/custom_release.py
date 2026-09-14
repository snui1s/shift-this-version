"""s
ตัวอย่างการนำ shift_this_version ไปใช้ในสคริปต์ Automation หรือ CI/CD Bot
"""

import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from pathlib import Path
import shift_this_version as stv

def run_custom_release_pipeline():
    print("=== 🚀 Starting Custom Release Pipeline ===")

    # 1. ให้ library ค้นหาไฟล์และตัวแปรทั้งหมดในโปรเจกต์ที่จะต้องแก้
    targets = stv.find_version_targets()
    print(f"\n[1] ตรวจพบไฟล์ที่ต้องอัปเดตเวอร์ชัน {len(targets)} จุด:")
    for t in targets:
        print(f"    • [{t.target_type}] {t.file_path} (เวอร์ชันปัจจุบัน: {t.current_version})")

    # 2. จำลองสถานการณ์ Diff & Commit
    # ในการใช้งานจริง สามารถเรียก:
    # diff = stv.get_filtered_diff(tag=stv.get_latest_tag())
    # commits = stv.get_commits_since(tag=stv.get_latest_tag())
    sample_commits = [
        "feat: add OAuth2 login support",
        "fix: resolve race condition in token refresh"
    ]
    sample_diff = """
    diff --git a/auth.py b/auth.py
    +def login_with_oauth2(provider: str):
    +    # new feature added backwards-compatibly
    +    pass
    """

    print("\n[2] จำลองการดึง Diff และ Commits...")
    print(f"    Commits: {sample_commits}")

    # 3. ส่งให้ AI วิเคราะห์
    # เมื่อเรียก stv.analyze() จะได้ Pydantic Object กลับมาตรงๆ 
    # สามารถเข้าถึง attributes ได้ง่าย: result.bump_type, result.reasoning, result.breaking_changes
    print("\n[3] ตรรกะการตัดสินใจในโค้ด (Business Logic):")
    
    # สมมติผลลัพธ์จาก AI (หรือเรียก stv.analyze(diff, commits) จริง)
    simulated_result_type = "minor"
    print(f"    AI วิเคราะห์ว่า: {simulated_result_type.upper()}")

    current_ver = targets[0].current_version if targets else "0.1.0"
    next_ver = stv.calculate_next_version(current_ver, simulated_result_type)
    print(f"    เวอร์ชันถัดไปที่คำนวณได้: {current_ver} -> {next_ver}")

    # 4. ใช้เงื่อนไขพิเศษเฉพาะขององค์กรเรา
    if simulated_result_type == "major":
        print("\n[!] ⚠️ ตรวจพบ BREAKING CHANGE: ส่งแจ้งเตือนเข้า Slack และรอ Security Team อนุมัติ...")
        # send_slack_alert(...)
    else:
        print(f"\n[4] อัปเดตไฟล์เวอร์ชันทั้งหมดเป็น {next_ver}...")
        for t in targets:
            # ใช้ dry_run=True ในตัวอย่างเพื่อไม่ให้ไปกระทบไฟล์จริง
            stv.apply_version_bump(t, next_ver, dry_run=True)
            print(f"    ✓ [DRY-RUN] อัปเดต {t.file_path} สำเร็จ")

    print("\n=== ✅ Pipeline Finished ===")

if __name__ == "__main__":
    run_custom_release_pipeline()
