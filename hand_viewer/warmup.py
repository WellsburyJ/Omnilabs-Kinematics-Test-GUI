#!/usr/bin/env python3
"""
Pre-import warmup script for Hand Viewer.

Run this once after installing dependencies to pre-warm the library cache.
On macOS, this helps avoid slow code signature verification on subsequent runs.

Usage:
    python hand_viewer/warmup.py
    
Or with quarantine removal (macOS only, requires the venv path):
    python hand_viewer/warmup.py --remove-quarantine
"""

import sys
import time
import platform
import subprocess
import os

def print_header():
    print("=" * 60)
    print("HAND VIEWER - LIBRARY WARMUP SCRIPT")
    print("=" * 60)
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Machine: {platform.machine()}")
    print(f"Python: {platform.python_version()}")
    print()

def timed_import(name, import_func):
    """Import a module and print timing."""
    print(f"  Importing {name}...", end=" ", flush=True)
    start = time.time()
    try:
        import_func()
        elapsed = time.time() - start
        print(f"OK ({elapsed:.2f}s)")
        return True
    except Exception as e:
        elapsed = time.time() - start
        print(f"FAILED ({elapsed:.2f}s) - {e}")
        return False

def remove_quarantine_macos():
    """Remove quarantine flag from venv on macOS.
    
    This is a persistent operation - once removed, it stays removed.
    This is what makes subsequent runs faster.
    """
    if platform.system() != "Darwin":
        print("  Skipping quarantine removal (not macOS)")
        return
    
    # Find the venv directory
    venv_paths = ["venv", ".venv", "env", "../venv", "../.venv"]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    
    venv_path = None
    for p in venv_paths:
        full_path = os.path.join(project_dir, p)
        if os.path.isdir(full_path):
            venv_path = full_path
            break
    
    if not venv_path:
        print("  Could not find venv directory, skipping quarantine removal")
        return
    
    print(f"  Removing quarantine flag from: {venv_path}")
    print("  (This is persistent - you only need to do this once)")
    try:
        result = subprocess.run(
            ["xattr", "-r", "-d", "com.apple.quarantine", venv_path],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("  ✓ Quarantine flag removed successfully (persists across runs)")
        else:
            # Check if files still have quarantine
            check_result = subprocess.run(
                ["xattr", "-r", "com.apple.quarantine", venv_path],
                capture_output=True,
                text=True
            )
            if check_result.returncode != 0 and not check_result.stdout.strip():
                print("  ✓ Quarantine flag already removed (persists)")
            else:
                print("  ⚠ Some files may still have quarantine flags")
    except Exception as e:
        print(f"  ✗ Failed to remove quarantine flag: {e}")

def compile_bytecode():
    """Compile all Python files to bytecode (.pyc) for faster imports."""
    print("[STEP 1] Compiling Python bytecode...")
    import py_compile
    import glob
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    hand_viewer_dir = script_dir
    
    # Find all Python files
    py_files = []
    for root, dirs, files in os.walk(hand_viewer_dir):
        # Skip __pycache__ directories
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for file in files:
            if file.endswith('.py'):
                py_files.append(os.path.join(root, file))
    
    print(f"  Found {len(py_files)} Python files to compile...")
    compiled = 0
    for py_file in py_files:
        try:
            py_compile.compile(py_file, doraise=True)
            compiled += 1
        except py_compile.PyCompileError as e:
            print(f"  Warning: Failed to compile {py_file}: {e}")
    
    print(f"  Compiled {compiled}/{len(py_files)} files")
    print()

def warmup():
    """Pre-import all heavy libraries."""
    print_header()
    
    # Check for quarantine removal flag
    if "--remove-quarantine" in sys.argv:
        print("[STEP 0] Removing macOS quarantine flag...")
        remove_quarantine_macos()
        print()
    
    # Compile bytecode first
    compile_bytecode()
    
    print("[STEP 2] Pre-importing heavy libraries...")
    print("         (This may take a while on first run)")
    print()
    
    total_start = time.time()
    success_count = 0
    total_count = 0
    
    # PySide6 / Qt
    total_count += 1
    if timed_import("PySide6.QtWidgets", lambda: __import__("PySide6.QtWidgets")):
        success_count += 1
    
    total_count += 1
    if timed_import("PySide6.QtCore", lambda: __import__("PySide6.QtCore")):
        success_count += 1
    
    total_count += 1
    if timed_import("PySide6.QtGui", lambda: __import__("PySide6.QtGui")):
        success_count += 1
    
    # NumPy
    total_count += 1
    if timed_import("numpy", lambda: __import__("numpy")):
        success_count += 1
    
    # Matplotlib (the slowest)
    total_count += 1
    if timed_import("matplotlib", lambda: __import__("matplotlib")):
        success_count += 1
    
    total_count += 1
    if timed_import("matplotlib.backends.backend_qt5agg", 
                    lambda: __import__("matplotlib.backends.backend_qt5agg")):
        success_count += 1
    
    total_count += 1
    if timed_import("matplotlib.figure", lambda: __import__("matplotlib.figure")):
        success_count += 1
    
    total_count += 1
    if timed_import("mpl_toolkits.mplot3d", lambda: __import__("mpl_toolkits.mplot3d")):
        success_count += 1
    
    # PySerial
    total_count += 1
    if timed_import("serial", lambda: __import__("serial")):
        success_count += 1
    
    total_elapsed = time.time() - total_start
    
    print()
    print("-" * 60)
    print(f"Warmup complete: {success_count}/{total_count} libraries loaded")
    print(f"Total time: {total_elapsed:.2f}s")
    print()
    
    # Create a marker file to indicate warmup was run
    script_dir = os.path.dirname(os.path.abspath(__file__))
    marker_file = os.path.join(script_dir, ".warmup_complete")
    try:
        with open(marker_file, 'w') as f:
            f.write(f"Warmup completed: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Platform: {platform.system()} {platform.machine()}\n")
        print(f"[STEP 3] Created warmup marker: {marker_file}")
    except Exception as e:
        print(f"  Warning: Could not create marker file: {e}")
    print()
    
    if platform.system() == "Darwin":
        print("IMPORTANT: The quarantine flag removal persists across runs.")
        print("           Binary libraries will still load each time Python")
        print("           starts, but without quarantine verification they")
        print("           should load much faster (seconds instead of minutes).")
        print()
        if "--remove-quarantine" not in sys.argv:
            print("TIP: Run with --remove-quarantine to speed up binary loading:")
            print("     python hand_viewer/warmup.py --remove-quarantine")
            print()
    
    print("You can now run the app:")
    print("    python hand_viewer/app.py")
    print()
    print("NOTE: Each new Python process will still load binary libraries,")
    print("      but after warmup they should load in seconds, not minutes.")
    print()

if __name__ == "__main__":
    warmup()

