#!/usr/bin/env python3
"""
Test runner script for shift-this-version.
Runs pytest if available, or falls back to direct execution of test functions.
"""

import sys
import subprocess

def main():
    print("=" * 60)
    print("  Running shift-this-version Test Suite")
    print("=" * 60 + "\n")

    # 1. Try running pytest
    try:
        import pytest
        exit_code = pytest.main(["-v", "--tb=short", "tests"])
        sys.exit(exit_code)
    except ImportError:
        pass

    # 2. Fallback: run via python subprocess if pytest CLI is in PATH
    res = subprocess.run([sys.executable, "tests/test_core.py"])
    sys.exit(res.returncode)

if __name__ == "__main__":
    main()
