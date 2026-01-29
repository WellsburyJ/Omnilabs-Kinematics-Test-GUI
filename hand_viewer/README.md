# Hand Viewer - 3D Kinematic Model

A Python desktop application that reads angle sensor data from an ESP32-connected soft robotic glove and displays it as a real-time 3D kinematic hand model.

## Setup (One-Time)

1. Install Python 3.8 or higher
2. Create a virtual environment (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or: venv\Scripts\activate  # On Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r hand_viewer/requirements.txt
   ```
4. **(One-time) Run the warmup script** to speed up future startups:
   ```bash
   python hand_viewer/warmup.py --remove-quarantine
   ```
   This significantly speeds up startup on macOS by:
   - Removing macOS quarantine flags (persists permanently - this is the main benefit)
   - Compiling Python bytecode (.pyc files)
   
   **Important:** Python's import cache is per-process, so libraries still need to be
   imported each time you run the app. However, after warmup removes quarantine flags,
   imports are much faster (seconds instead of minutes). The quarantine removal persists
   permanently, so you only need to run warmup once.

## Running the Application (Every Time)

1. Navigate to the project directory:
   ```bash
   cd "/Users/jacobwellsbury/Documents/Documents/OmniLabs/ESP Files/KineticModel"
   ```

2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

3. Connect your ESP32 (`com_receive` board) via USB

4. Run the application:
   ```bash
   python hand_viewer/app.py
   ```
   
   Or with verbose output for debugging:
   ```bash
   python hand_viewer/app.py --verbose
   ```

## Quick Start Script

You can create a simple startup script to automate steps 1-4:

**On macOS/Linux:** Create `start.sh`:
```bash
#!/bin/bash
cd "/Users/jacobwellsbury/Documents/Documents/OmniLabs/ESP Files/KineticModel"
source venv/bin/activate
python hand_viewer/app.py "$@"
```

Then make it executable and run:
```bash
chmod +x start.sh
./start.sh
```

## Slow Startup on macOS?

**Why imports happen every time:**
Python's import cache is per-process. When you close the app, the Python process ends.
When you reopen it, it's a new process, so libraries need to be imported again. This is
normal Python behavior and cannot be changed.

**What warmup does:**
The warmup script removes macOS quarantine flags from binary libraries. This is a
permanent file attribute change that persists across all future runs. Without quarantine,
macOS doesn't need to verify every binary on each import, making imports much faster.

**To speed up imports:**
Run the warmup script once (one-time operation):
```bash
python hand_viewer/warmup.py --remove-quarantine
```

After warmup, imports should take seconds instead of minutes. You can verify warmup
worked by running:
```bash
python hand_viewer/check_imports.py
```

**Note:** Even after warmup, you'll still see import messages each time you start the app.
This is normal - the imports are just much faster now (typically 1-5 seconds total
instead of 2-3 minutes).

## Usage

1. Select the COM port from the dropdown (auto-detects available serial ports)
2. Click "Connect" to start reading data
3. Place the glove flat on a table and click "Set Zero Point" to calibrate
4. The 3D hand model will update in real-time as you move your fingers

## Calibration

The sensors provide relative angles. Simply press "Set Zero Point" when the glove is in a flat, neutral position (e.g., flat on a table). All subsequent angles will be relative to this zero point.

## Data Format

The application expects ASCII serial output from the ESP32 in the format:
```
Flex #<n>: <v0> <v1> <v2> <v3> <v4>
```

Where the 5 values correspond to: Pinky, Ring, Middle, Index, Thumb (in that order).


