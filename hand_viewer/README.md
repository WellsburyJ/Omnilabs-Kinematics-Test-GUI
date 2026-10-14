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

**What is deferred at startup:**
The three slowest dependencies no longer load when the app opens:

| Dependency | Loads when |
|------------|-----------|
| matplotlib | You click **Load 3D View** |
| pyserial | The port list is populated (just after the window appears) |
| bleak | You switch to Bluetooth (BLE) or scan for BLE devices |

If startup is still slow, the usual cause is low free disk space or memory pressure —
both make cold library loads page in very slowly.

## Usage

1. Select the COM port from the dropdown (auto-detects available serial ports)
2. Click "Connect" to start reading data
3. Place the glove flat on a table and click "Set Zero Point" to calibrate flex
4. Click **Load 3D View** to build the 3D hand model. This is deferred because loading
   matplotlib is the slowest part of startup; everything else works without it.
5. **Endpoint Lab** — host-side motor travel setup. **Auto Cal** does find min, find max,
   and apply margin for one finger in a single click; **Auto Cal Selected** runs that
   sequence on each Incl. finger that still needs ends. Find jogs until the encoder
   plateaus, then marks the end; tune **Find A**, **After A**, Plateau, Hold, and Jog
   as needed (saved to `hand_viewer/endpoint_lab_settings.json` between sessions).
   Manual jog, Set/Find, and Margin controls are still there for experimenting.
   **Open All / Close All** send simultaneous inset-min / inset-max `goto` on every finger
   that has both ends this session, at a lower **Multi A** limit (peak current scales with
   motor count). **Host Demo** then drives each included finger back to min and out to max,
   one finger at a time.

   The margin is applied **host-side**: the device keeps the full discovered range and the
   GUI simply never commands the last few percent. Note that once a motor has both ends,
   the firmware clamps jogs inside that range, so Find cannot widen it — press **Forget**
   (sends `cal clear N`) on that row, then re-run Auto Cal. Device `demo` remains
   on the Control Panel for smoke tests.
   Firmware notes: `references/FIRMWARE_ENDPOINT_HANDOVER.md`.

   **Hardware: Pull only** (selector at the top of Endpoint Lab, remembered between
   sessions) is for hands whose motors can only pull fingers open, with a passive return
   closing them. Start Auto Cal with the finger relaxed/closed: it marks min at that pose
   (firmware `goto` needs both ends), then finds max = fully open. **Open All** drives
   every calibrated finger to max (less the margin) and keeps holding; **Release All**
   idles so the fingers close. Find Min, Set Min, Margin Apply, and Close All are hidden
   in this mode, and the Middle open/close flip is not applied.

   **Open** (per finger row) does the same move as Open All for just that finger.

   **Jog rad/s** slows Fwd/Rev jogs and Find; **Move rad/s** slows every `goto` (Open,
   Open All, Close All, Host Demo, margin park). They only go slower than the firmware
   defaults, which are full speed for this application: jog 0.1–2 rad/s, goto 0.1–3 rad/s.
   Leave at "full" to send no speed argument.

   **Inv** (per finger row, both modes) swaps that finger's Fwd/Rev everywhere — Endpoint
   Lab and the Control Panel — and is saved to `hand_viewer/motor_invert.json` (default:
   Middle inverted). Toggling it clears that finger's ends, so re-run Auto Cal after.

## Calibration

The sensors provide relative angles. Simply press "Set Zero Point" when the glove is in a flat, neutral position (e.g., flat on a table). All subsequent angles will be relative to this zero point.

Motor travel ends (min/max) are set on the Control Panel or Endpoint Lab; they live in device RAM until power cycle.

## Data Format

The application expects ASCII serial/BLE lines from the OH1 core, for example:

```
values flex 12.30,45.60,78.90,101.10,121.30,ts,1002,
values motors 0.000,0.500,1.000,nan,0.250,ts,1000,
values angles 12.3,-5.1,40.0,nan,8.7,ts,1000,
values quat 0.998765,0.012345,-0.001234,0.045678,ts,1001,
values linaccel 0.123,-0.456,0.789,ts,1001,
```

Flex display order is **Thumb → Pinky** (same as `values flex` on the wire). Device motors/angles streams are **M1..M5 = Pinky→Thumb** (GUI remaps).
See `references/GUI_HANDOVER.md`, `hand_viewer/ESP32_COMMANDS.md`, and `references/FIRMWARE_ENDPOINT_HANDOVER.md`.


