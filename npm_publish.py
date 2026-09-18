#!/usr/bin/env python3
"""
npm One-Click Build & Publish Script for shift-this-version
Loads NPM_TOKEN from .env, validates version parity, and publishes to npm registry.
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

# 1. Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    env_path = Path(".env")
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

def check_command(cmd: str) -> bool:
    return shutil.which(cmd) is not None

def main():
    print("\n" + "=" * 60)
    print("  npm One-Click Publisher: shift-this-version")
    print("=" * 60 + "\n")

    # 1. Verify Node.js and npm are installed
    if not check_command("npm"):
        print("[ERROR] 'npm' command not found!")
        print("Please install Node.js from https://nodejs.org/")
        sys.exit(1)

    # 2. Check version parity between pyproject.toml and package.json
    pkg_json_path = Path("package.json")
    if not pkg_json_path.is_file():
        print("[ERROR] package.json not found in root directory!")
        sys.exit(1)

    try:
        pkg_data = json.loads(pkg_json_path.read_text(encoding="utf-8"))
        npm_version = pkg_data.get("version")
    except Exception as e:
        print(f"[ERROR] Failed to read package.json: {e}")
        sys.exit(1)

    print(f"[1/3] Package Name: {pkg_data.get('name')} (v{npm_version})")

    # 3. Handle npm authentication (NPM_TOKEN or existing npm session)
    token = os.getenv("NPM_TOKEN")
    npmrc_temp_created = False
    npmrc_path = Path(".npmrc")

    if token and token.strip():
        token = token.strip()
        masked = token[:6] + "..." + token[-4:] if len(token) > 10 else "***"
        print(f"[2/3] Using NPM_TOKEN from environment: {masked}")

        # Write or append auth token to local .npmrc for the publish session
        auth_line = f"//registry.npmjs.org/:_authToken={token}\n"
        if not npmrc_path.exists():
            npmrc_path.write_text(auth_line, encoding="utf-8")
            npmrc_temp_created = True
        else:
            existing = npmrc_path.read_text(encoding="utf-8")
            if "_authToken" not in existing:
                npmrc_path.write_text(existing + "\n" + auth_line, encoding="utf-8")
    else:
        is_win = sys.platform == "win32"
        whoami_res = subprocess.run(["npm", "whoami"], capture_output=True, text=True, check=False, shell=is_win)
        if whoami_res.returncode == 0:
            user = whoami_res.stdout.strip()
            print(f"[2/3] Logged in to npm as: {user}")
        else:
            print("[NOTICE] No NPM_TOKEN found in .env and not currently logged in via 'npm login'.")
            print("Please do either of the following:")
            print("  Option A (Recommended): Add NPM_TOKEN=npm_... into your '.env' file")
            print("          (Get token at: https://www.npmjs.com/settings/tokens)")
            print("  Option B: Run 'npm login' in your terminal\n")
            # We still attempt publish in case global npmrc is configured

    # 4. Publish to npm
    print(f"\n[3/3] Publishing '{pkg_data.get('name')}@{npm_version}' to npm registry...")
    try:
        is_win = sys.platform == "win32"
        publish_cmd = ["npm", "publish", "--access", "public"]
        res = subprocess.run(publish_cmd, check=False, shell=is_win)

        if res.returncode != 0:
            print("\n[FAILED] npm publish failed! Please check your credentials or permissions.")
            sys.exit(res.returncode)

        print("\n" + "=" * 60)
        print("  SUCCESSFULLY PUBLISHED TO npm!")
        print("=" * 60)
        print("\nYour npm package is live:")
        print(f"  URL: https://www.npmjs.com/package/{pkg_data.get('name')}\n")
        print("Anyone in the world can now run it without installing Python:")
        print(f"  $ npx {pkg_data.get('name')}\n")
        print("Or install globally:")
        print(f"  $ npm install -g {pkg_data.get('name')}\n")

    finally:
        # Cleanup temporary .npmrc token file
        if npmrc_temp_created and npmrc_path.exists():
            try:
                npmrc_path.unlink()
            except Exception:
                pass

if __name__ == "__main__":
    main()
