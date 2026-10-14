# OMNIHUMAN-O1 Command Reference

Text commands sent by the Hand Viewer to the OH1 core over **USB Serial** or **BLE** (Nordic UART). Full protocol: `references/GUI_HANDOVER.md`.

Endpoint discovery / `goto` hardening for firmware: **`references/FIRMWARE_ENDPOINT_HANDOVER.md`**.

## Transport

- Serial: 115200 8N1, commands end with `\n`
- BLE advertise name: `OMNIHUMAN-O1`
- Same command vocabulary on both transports

## Finger / motor numbering

**Device command and stream order** (M1..M5):

| Motor | Finger |
|-------|--------|
| 1 | Thumb |
| 2 | Index |
| 3 | Middle |
| 4 | Ring |
| 5 | Pinky |

The hand was rewired so device order now matches the GUI rows (Thumb→Pinky).
The mapping lives in `ui_to_device_motor()` in `fingers.py`.

## Motion & calibration

| Command | Meaning |
|---------|---------|
| `min` / `max` | Mark current pose as min/max for **all** motors |
| `min N` / `max N` | Same for motor N only |
| `fwd N [seconds] [speed]` | Velocity jog forward (default ~2 s at 2 rad/s) |
| `rev N [seconds] [speed]` | Velocity jog reverse |
| `goto N <0..1> [speed]` | Move to calibrated fraction of travel (`0`=min, `1`=max; default 3 rad/s) |

`speed` is motor-shaft rad/s, clamped to 0.1..10; omitted/0 = firmware default. It is
positional, so a jog speed needs seconds too (`fwd 3 2 5`). `goto` still times out after
10 s, so very slow speeds over a long travel can stop short. Endpoint Lab exposes these
as **Jog rad/s** (0.1–2) and **Move rad/s** (0.1–3): slow-down only, since the firmware
defaults are full speed for this application.
| `hold N` | Hold current angle |
| `idle` / `idle N` | Stop / coast |
| `cal clear` / `cal clear N` | Clear stored min/max (all / motor N) |
| `demo` | Device smoke test: each calibrated motor goto min, then max |
| `torque N <amps>` | Torque command |
| `en N` / `dis N` | Driver enable |

Soft endstops clamp `fwd` / `rev` to roughly 5%–95% once a motor has both ends,
so a jog cannot widen an existing range. Power cycling clears calibration (RAM-only).

### Requested / pending (firmware)

| Command | Meaning |
|---------|---------|
| `cal clear` / `cal clear N` | Forget stored min/max (all / motor N). Endpoint Lab **Forget** sends `cal clear N`. |
| `get minmax` | Reply stored ends in encoder ° — preferred `minmax m1_min,m1_max,…,m5_min,m5_max` (`nan` if unset). Nice to have; the host tracks ends set this session. |

Details: `references/FIRMWARE_ENDPOINT_HANDOVER.md`.

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
| `flex` | 5 floats | Finger flexion degrees: Thumb→Pinky (same as UI) |
| `quat` | w,x,y,z | Palm IMU |
| `linaccel` | ax,ay,az | Linear accel (gravity removed) |

Missing sensors use literal `nan`. Lines include `,ts,<millis>,`.

## GUI usage

1. **Connect** → app sends `get version` then `start`
2. **Control Panel** → jog with Fwd/Rev, set `Min`/`Max`, then `Goto`; **Device Demo** sends firmware `demo`
3. **Endpoint Lab** → per-finger **Auto Cal** (find min → find max → margin inset via `goto`), or the individual Find/Set/Margin controls; **Host Demo** drives each finger to min (`goto 0`) then max (`goto 1`)
4. **Threshold / Choreography** → `goto 1.0` → hold → `goto 0.0` → `idle` per finger
5. **Debug Console** → type any command and press Enter / Send
6. **Disconnect** → app sends `idle` then `stop`

Calibration is RAM-only on the device — recalibrate after power cycle.
