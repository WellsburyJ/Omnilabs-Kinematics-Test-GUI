# OMNIHUMAN-O1 Core — GUI Handover

Client integration guide for a GUI that talks to the ESP32 core over **USB Serial** and/or **BLE**.

Firmware: `OH1-CORE-v1.0_01092026` (unified FOC + RS485 glove IMU).

---

## 1. What the device is

The core is a 5-motor hand/rail controller plus a receiver for a glove board:

| Subsystem | What it provides to the GUI |
|-----------|-----------------------------|
| Motors M1–M5 | Position (0..1 when calibrated), angles (deg), motion commands |
| Palm IMU | Quaternion + linear acceleration (from RS485 glove) |
| Finger IMUs | Five flexion angles in degrees (thumb..pinky) |

The GUI does **not** talk to the glove directly. The core already parses RS485 and republishes text lines.

---

## 2. Transport A — USB Serial

| Setting | Value |
|---------|-------|
| Baud | **115200** |
| Data | 8N1 |
| Line ending for commands | `\n` (CR optional; firmware ignores `\r`) |
| Encoding | ASCII text |

Open the ESP32 USB CDC / serial port (not the glove UPDI programmer).

Commands and telemetry share the same port. Expect mixed traffic: human-readable status lines plus structured `values …` lines.

---

## 3. Transport B — BLE (Nordic UART)

| Setting | Value |
|---------|-------|
| Advertise name | **`OMNIHUMAN-O1`** |
| Role | Peripheral (one client) |
| Service UUID | `6E400001-B5A3-F393-E0A9-E50E24DCCA9E` |
| RX (GUI → device) | `6E400002-B5A3-F393-E0A9-E50E24DCCA9E` — Write / Write-without-response |
| TX (device → GUI) | `6E400003-B5A3-F393-E0A9-E50E24DCCA9E` — Notify (+ Read), CCCD `0x2902` |

This is the standard **Nordic UART Service (NUS)** layout (same as legacy `ah-rc-03`).

### Sending a command over BLE

Write UTF-8 bytes to the **RX** characteristic, ending with `\n`:

```
goto 1 0.5\n
```

Without a newline the device buffers and will not execute (buffer max 256; overflow clears the buffer).

### Receiving over BLE

Subscribe to **notifications** on the **TX** characteristic. Each notify is typically one text line ending in `\n`.

---

## 4. Command protocol (identical on Serial and BLE)

- Case-insensitive (firmware lowercases).
- Motor index `N` is **1..5**.
- Echo: on Serial, commands are acknowledged as `>: <cmd>`. Most command feedback is **Serial-only**; BLE clients mainly see `values …` streams plus a few special notifies (below).

### Motion & calibration

| Command | Meaning |
|---------|---------|
| `min` / `max` | Mark current pose as min/max for **all** motors |
| `min N` / `max N` | Same for motor N only |
| `fwd N [seconds]` | Velocity jog forward (default duration 2 s, ~2 rad/s) |
| `rev N [seconds]` | Velocity jog reverse |
| `goto N <0..1>` | Move to calibrated fraction of travel (needs min+max) |
| `hold N` | Hold current angle indefinitely |
| `torque N <amps>` | Torque command (±, clamped) |
| `idle` / `idle N` | Stop / coast |
| `demo` | Each calibrated motor: goto min, then goto max |
| `en N` / `dis N` | Driver enable pin high / low |
| `pwm50 N` / `pwm50 off` | Debug: 50% duty all phases |

### System

| Command | Meaning |
|---------|---------|
| `start` | Enable telemetry stream (`txValues = true`). Alias: `debug off` |
| `stop` | Disable telemetry stream. Alias: `debug on` |
| `get version` | Reply `version:<string>` (also notified on BLE) |
| `status` | Per-motor ready/foc/cal/mode/angle (Serial) |
| `sensors` | Quick encoder dump (Serial) |
| `muxscan` | TCA9548A channel scan (Serial) |
| `fault` / `fault clear` | Read / clear driver fault latch |
| `realign N` | Re-run FOC alignment |
| `focdebug on\|off` | Extra FOC fields in motion traces |
| `imu reset` | Reset Madgwick filter |
| `help` | Print command list (Serial) |

### Recommended GUI command set (MVP)

1. Connect → send `get version`  
2. `start` to enable streams  
3. Calibration UI: `min` / `max` (or per-motor)  
4. Control: `goto N p`, `fwd`/`rev`, `idle`, `demo`  
5. `stop` when leaving the page / disconnecting  

---

## 5. Telemetry lines (`values …`)

Gated by `start` / `stop`. Default after boot: **streaming is ON** (`txValues = true`).

Every structured line is stamped by the firmware:

```
<prefix> <csv fields>,ts,<millis>,
```

Example:

```
values motors 0.123,0.456,nan,0.789,0.012,ts,12345,
```

Parser tips:

- Split on whitespace: first token `values`, second token is the **key**.
- Remaining fields are comma-separated; last fields are `ts` then an integer milliseconds since boot.
- Missing sensors use the literal token `nan` (not a number).
- Lines end with `\n`. Trailing comma before `ts` is normal.

### Stream catalogue

| Key | Approx rate | Fields (before `ts`) | Units / notes |
|-----|-------------|----------------------|---------------|
| `motors` | ~10 Hz | 5 floats | Normalized position **0..1** if calibrated, else `nan`. Order M1..M5 |
| `angles` | ~10 Hz | 5 floats | Encoder angle **degrees**, 1 decimal. Order M1..M5 |
| `quat` | up to ~100 Hz | `w,x,y,z` | Unit quaternion from palm IMU (Madgwick). 6 decimals |
| `linaccel` | up to ~100 Hz | `ax,ay,az` | Linear accel m/s² (gravity removed). 3 decimals |
| `flex` | up to ~100 Hz | 5 floats | Finger flexion **degrees**, 2 decimals. Order: **thumb, index, middle, ring, pinky** |

`motors` / `angles` come from the core’s 100 ms timer.  
`quat` / `linaccel` / `flex` arrive when the glove sends RS485 frames (typically ~100 Hz each); they may be absent if the glove is unplugged.

### Example lines

```
values motors 0.000,0.500,1.000,nan,0.250,ts,1000,
values angles 12.3,-5.1,40.0,nan,8.7,ts,1000,
values quat 0.998765,0.012345,-0.001234,0.045678,ts,1001,
values linaccel 0.123,-0.456,0.789,ts,1001,
values flex 12.30,45.60,78.90,101.10,121.30,ts,1002,
```

### Special BLE/Serial lines (not `values`)

| Line | When |
|------|------|
| `version:…` | Response to `get version` (USB + BLE notify) |
| `FAULT\n` | Driver fault latched (USB + BLE notify) |
| `BLE Connected` / `BLE disconnected` | USB Serial only |
| Boot banner, `>: …`, `help`, status | Mostly USB Serial |

---

## 6. Semantics the GUI should respect

### Motor positions

- `values motors` is only meaningful after **min/max calibration** for that motor.
- `goto N p` uses the same 0..1 space (`0` = min end, `1` = max end).
- Calibration is **RAM-only** — lost on power cycle. GUI should prompt to recalibrate after reconnect.
- Soft endstops: velocity jogs won’t push further past ~5% / ~95% when calibrated.

### Finger flex

- Published in **degrees** (not raw deci-degrees).
- Not zeroed to a flat hand; expect a non-zero baseline until you add your own UI calibration.
- Unsigned: curl and hyperextension both increase the angle.
- If a finger drops out, the core holds the last good value; before the first good sample the field is `nan`.

### Quaternion / linaccel

- Palm orientation relative to gravity (Madgwick).
- `imu reset` restarts the filter if orientation looks stuck/wrong.

---

## 7. Suggested GUI architecture

```
┌─────────────┐     USB 115200      ┌──────────────────┐
│             │◄───────────────────►│                  │
│  Desktop /  │                     │  OMNIHUMAN-O1    │
│  mobile GUI │◄────── BLE NUS ────►│  (ESP32 core)    │
│             │   name: OMNIHUMAN-O1│                  │
└─────────────┘                     └────────┬─────────┘
                                             │ RS485
                                             ▼
                                       Glove (IMUs)
```

Recommended internal pipeline:

1. **Transport layer** — Serial and/or BLE, both exposing `sendLine(cmd)` and `onLine(callback)`.
2. **Line router** — if line starts with `values `, parse key + CSV; else treat as log/status.
3. **State store** — latest `motors[5]`, `angles[5]`, `flex[5]`, `quat[4]`, `linaccel[3]`, `connected`, `streaming`, `version`.
4. **Widgets** — plots/bars bound to the store; buttons emit commands ending in `\n`.

### Parsing pseudocode

```
onLine(line):
  line = strip(line)
  if line.startswith("values "):
    parts = line.split()          # ["values", key, "0.1,0.2,...,ts,123,"]
    key = parts[1]
    fields = parts[2].rstrip(",").split(",")
    # fields ends with ..., "ts", "<millis>"
    ts = int(fields[-1])
    data = fields[:-2]
    handleValues(key, data, ts)
  elif line.startswith("version:"):
    version = line[len("version:"):]
  elif line.startswith("FAULT"):
    showFault()
  else:
    appendLog(line)
```

### BLE notify caveats

- High rate (`quat`/`flex` ~100 Hz × several lines) can flood BLE. Prefer UI updates at 10–30 Hz even if you receive faster.
- If notifies stall, check CCCD subscription and that `start` was sent.
- Command replies that only `Serial.print` will **not** appear on BLE — don’t wait for them over BLE; rely on `values` feedback or use USB for debug consoles.

---

## 8. Connection checklist for the GUI agent

- [ ] Serial: open port @ 115200, send `get version\n`, expect `version:…`
- [ ] Serial: confirm lines like `values motors …` (streaming defaults on; send `start\n` if needed)
- [ ] BLE: scan for **`OMNIHUMAN-O1`**, connect, discover NUS UUIDs above
- [ ] BLE: enable TX notifications, write `get version\n` to RX, expect notify
- [ ] BLE: write `start\n`, receive `values …` notifies
- [ ] Motor UI: after user sets ends with `min`/`max`, `values motors` leaves `nan`
- [ ] Flex UI: plot `values flex` as five degree channels thumb→pinky
- [ ] Safety: always expose `idle` / `stop`; clear FAULT with `fault clear` only when hardware is OK

---

## 9. Source of truth in the repo

| Topic | File |
|-------|------|
| Commands, motor streaming | `OH1-CORE-v1.0_01092026.ino` |
| BLE NUS + RX parsing | `mBle.h` |
| Dual Serial/BLE emit + timestamps | `com_out.h` |
| Glove IMU → `quat` / `linaccel` / `flex` | `com_rx.h` |
| Glove RS485 wire format (not needed by GUI) | `examples/RS485_PROTOCOL.md` |

---

## 10. Out of scope for the GUI (unless you add it later)

- Talking to the glove over RS485 directly  
- Finger min/max calibration persistence on-device (not implemented yet)  
- Motor calibration persistence (RAM only today)  
- Binary BLE protocol — text lines only  

If the GUI needs a stable machine API later (JSON, request/response over BLE), that would be a firmware change; today the contract is this newline text protocol.
