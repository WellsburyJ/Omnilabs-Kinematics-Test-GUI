# OMNIHUMAN-O1 Command Reference

Text commands sent by the Hand Viewer to the OH1 core over **USB Serial** or **BLE** (Nordic UART). Full protocol: `references/GUI_HANDOVER.md`.

## Transport

- Serial: 115200 8N1, commands end with `\n`
- BLE advertise name: `OMNIHUMAN-O1`
- Same command vocabulary on both transports

## Finger / motor numbering

| Motor | Finger |
|-------|--------|
| 1 | Thumb |
| 2 | Index |
| 3 | Middle |
| 4 | Ring |
| 5 | Pinky |

## Motion & calibration

| Command | Meaning |
|---------|---------|
| `min` / `max` | Mark current pose as min/max for **all** motors |
| `min N` / `max N` | Same for motor N only |
| `fwd N [seconds]` | Velocity jog forward (default ~2 s) |
| `rev N [seconds]` | Velocity jog reverse |
| `goto N <0..1>` | Move to calibrated fraction of travel |
| `hold N` | Hold current angle |
| `idle` / `idle N` | Stop / coast |
| `demo` | Each calibrated motor: goto min, then max |
| `torque N <amps>` | Torque command |
| `en N` / `dis N` | Driver enable |

## System

| Command | Meaning |
|---------|---------|
| `start` | Enable `values …` telemetry (sent automatically on Connect) |
| `stop` | Disable telemetry (sent on Disconnect) |
| `get version` | Reply `version:…` |
| `fault` / `fault clear` | Read / clear driver fault |
| `imu reset` | Reset Madgwick filter |
| `help` | Command list (Serial) |

## Telemetry (`values …`)

| Key | Fields | Notes |
|-----|--------|-------|
| `motors` | 5 floats | Normalized 0..1 if calibrated, else `nan`. M1..M5 |
| `angles` | 5 floats | Encoder degrees. M1..M5 |
| `flex` | 5 floats | Finger flexion degrees: Thumb→Pinky |
| `quat` | w,x,y,z | Palm IMU |
| `linaccel` | ax,ay,az | Linear accel (gravity removed) |

Missing sensors use literal `nan`. Lines include `,ts,<millis>,`.

## GUI usage

1. **Connect** → app sends `get version` then `start`
2. **Control Panel** → jog with Fwd/Rev, set `Min`/`Max`, then `Goto`
3. **Threshold / Choreography** → `goto 1.0` → hold → `goto 0.0` → `idle` per finger
4. **Debug Console** → type any command and press Enter / Send
5. **Disconnect** → app sends `idle` then `stop`

Calibration is RAM-only on the device — recalibrate after power cycle.
