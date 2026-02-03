#!/usr/bin/env python3
"""
Quick diagnostic script to check import speeds.
Run this to see if warmup is working properly.
"""

import sys
import time
import os

def check_import(name, import_func):
    """Check how long an import takes."""
    print(f"Importing {name}...", end=" ", flush=True)
    start = time.time()
    try:
        import_func()
        elapsed = time.time() - start
        status = "✓" if elapsed < 5.0 else "⚠"
        print(f"{status} {elapsed:.2f}s")
        return elapsed
    except Exception as e:
        elapsed = time.time() - start
        print(f"✗ FAILED ({elapsed:.2f}s) - {e}")
        return elapsed

print("=" * 60)
print("IMPORT SPEED DIAGNOSTIC")
print("=" * 60)
print()

# Check warmup status
warmup_marker = os.path.join(os.path.dirname(__file__), '.warmup_complete')
if os.path.exists(warmup_marker):
    print("✓ Warmup marker found")
    with open(warmup_marker, 'r') as f:
        print(f"  {f.read().strip()}")
else:
    print("⚠ Warmup marker NOT found")
    print("  Run: python hand_viewer/warmup.py --remove-quarantine")
print()

# Check quarantine status (macOS only)
if sys.platform == 'darwin':
    import subprocess
    venv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'venv')
    if os.path.exists(venv_path):
        result = subprocess.run(
            ["xattr", "-r", "com.apple.quarantine", venv_path],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            print("⚠ Quarantine flags still present!")
            print("  Run: python hand_viewer/warmup.py --remove-quarantine")
        else:
            print("✓ Quarantine flags removed")
    print()

print("Testing import speeds:")
print("-" * 60)

total_time = 0
total_time += check_import("PySide6.QtWidgets", lambda: __import__("PySide6.QtWidgets"))
total_time += check_import("numpy", lambda: __import__("numpy"))
total_time += check_import("matplotlib", lambda: __import__("matplotlib"))
total_time += check_import("matplotlib.backends.backend_qt5agg", 
                          lambda: __import__("matplotlib.backends.backend_qt5agg"))

print("-" * 60)
print(f"Total import time: {total_time:.2f}s")
print()

if total_time < 10:
    print("✓ Imports are fast! Warmup is working.")
elif total_time < 30:
    print("⚠ Imports are moderate. May need to run warmup again.")
else:
    print("✗ Imports are slow. Run warmup:")
    print("    python hand_viewer/warmup.py --remove-quarantine")
print()









