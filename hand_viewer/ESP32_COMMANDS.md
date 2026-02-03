# ESP32 Command Reference

This document explains the commands that the Hand Viewer application sends to the ESP32 controller to control the pneumatic glove system. These commands control pumps, pressure valves, and vacuum valves for each of the five fingers.

## Overview

The ESP32 receives text-based commands over serial (or BLE) communication. Each command is a single line of text ending with a newline character (`\n`). The commands control the state of pneumatic actuators for each finger.

## Finger Numbering

The system uses five fingers, numbered 1 through 5:

- **Finger 1**: Pinky
- **Finger 2**: Ring
- **Finger 3**: Middle
- **Finger 4**: Index
- **Finger 5**: Thumb

## Commands

### 1. `set outputs` Command

This is the main command used to control all fingers simultaneously. It sets the valve state and pump speed for each of the five fingers.

#### Syntax

```
set outputs <finger1_state><finger1_speed><finger2_state><finger2_speed><finger3_state><finger3_speed><finger4_state><finger4_speed><finger5_state><finger5_speed>
```

#### Valve States

Each finger has a valve state represented by a single letter:

- **O** (Open): Both pressure and vacuum valves are OFF. The finger is in a neutral/open state.
- **P** (Pressure): Only the pressure valve is ON. This applies positive pressure to inflate/extend the finger.
- **V** (Vacuum): Only the vacuum valve is ON. This applies negative pressure to deflate/contract the finger.
- **C** (Closed): Both pressure and vacuum valves are ON. This creates a closed/blocked state.

#### Pump Speeds

Each finger has a pump speed represented by a single digit:

- **0**: Pump is OFF (no flow)
- **3**: Pump speed level 1 (low flow)
- **6**: Pump speed level 2 (medium flow)
- **9**: Pump speed level 3 (high flow)

Note: The pump speed values are always multiples of 3 (0, 3, 6, or 9), even though the control panel slider shows 0-3. The application automatically multiplies the slider value by 3 when sending the command.

#### Command Format

The command always contains exactly 10 characters after "set outputs " (2 characters per finger: 1 state + 1 speed), for a total of 5 fingers.

#### Examples

**Example 1: All fingers neutral, pumps off**
```
set outputs O0O0O0O0O0
```
- All fingers: Open state (O), pump speed 0
- Result: All fingers in neutral position with no pump activity

**Example 2: Thumb pressure, medium speed**
```
set outputs O0O0O0O0P6
```
- Fingers 1-4: Open (O), pump off (0)
- Finger 5 (Thumb): Pressure (P), pump speed 6
- Result: Thumb finger applies pressure at medium speed

**Example 3: Multiple fingers with different states**
```
set outputs V3P6O0C9O0
```
- Finger 1 (Pinky): Vacuum (V), speed 3
- Finger 2 (Ring): Pressure (P), speed 6
- Finger 3 (Middle): Open (O), speed 0
- Finger 4 (Index): Closed (C), speed 9
- Finger 5 (Thumb): Open (O), speed 0

**Example 4: All fingers in pressure mode, varying speeds**
```
set outputs P0P3P6P9P0
```
- All fingers: Pressure state (P)
- Speeds: 0, 3, 6, 9, 0 (increasing then back to 0)

### 2. `release` Command

This command releases a specific finger, turning off its pump and setting both valves to the open (neutral) state.

#### Syntax

```
release<finger_number>
```

Where `<finger_number>` is a single digit from 1 to 5.

#### Examples

**Release the thumb (finger 5):**
```
release5
```

**Release the index finger (finger 4):**
```
release4
```

#### What It Does

When a release command is sent, the ESP32:
1. Sets the pump speed to 0 for that finger
2. Sets both valves to OFF (Open state)
3. This effectively returns the finger to a neutral, unpressurized state

Note: The control panel also sends an updated `set outputs` command after releasing a finger to ensure all states are synchronized.

### 3. `reset` Command

This command resets the entire system, turning off all pumps and setting all valves to the open (neutral) state for all fingers.

#### Syntax

```
reset
```

#### What It Does

The reset command:
1. Sets all pump speeds to 0 for all fingers
2. Sets all valves to OFF (Open state) for all fingers
3. Returns the entire glove system to a neutral, unpressurized state

#### Example

```
reset
```

This is equivalent to sending:
```
set outputs O0O0O0O0O0
```

## Command Transmission

- All commands are sent as ASCII text strings
- Each command must end with a newline character (`\n` or `\r\n`)
- Commands are sent immediately when controls are changed in the Control Panel
- The status label in the Control Panel shows the last command that was sent

## How the Control Panel Uses These Commands

### Automatic Command Generation

The Control Panel automatically generates and sends `set outputs` commands whenever you:

1. **Check or uncheck a valve checkbox** (Vacuum or Pressure)
   - The command is rebuilt with the new valve state
   - Pump speeds remain unchanged

2. **Adjust a pump speed slider**
   - The slider value (0-3) is multiplied by 3 to get the speed value (0, 3, 6, or 9)
   - The command is rebuilt with the new pump speed
   - Valve states remain unchanged

### Manual Commands

The Control Panel also sends commands when you:

1. **Click a "Release" button** for a specific finger
   - Sends `release<number>` command
   - Then sends an updated `set outputs` command

2. **Click "Reset All" button**
   - Sends `reset` command
   - Resets all UI controls to their default state

## Understanding the Status Display

In the Control Panel, the status label at the bottom shows:
- **"Status: Sent - <command>"**: The last command that was successfully sent
- **"Status: Not connected"**: No connection to ESP32
- **"Status: Ready"**: Connected and ready to send commands

The displayed command is truncated if it's longer than 50 characters, but the full command is always sent to the ESP32.

## Common Usage Patterns

### Pattern 1: Gradual Pressure Application
```
set outputs P0P0P0P0P0  (Start: all pressure, pumps off)
set outputs P3P3P3P3P3  (Low speed)
set outputs P6P6P6P6P6  (Medium speed)
set outputs P9P9P9P9P9  (High speed)
```

### Pattern 2: Finger Sequence
```
set outputs P9O0O0O0O0  (Thumb only)
set outputs O0P9O0O0O0  (Ring only)
set outputs O0O0P9O0O0  (Middle only)
set outputs O0O0O0P9O0  (Index only)
set outputs O0O0O0O0P9  (Pinky only)
```

### Pattern 3: Release Sequence
```
release1
release2
release3
release4
release5
```

Or simply:
```
reset
```

## Troubleshooting

### Command Not Working?

1. **Check connection**: Ensure the ESP32 is connected (serial or BLE)
2. **Check status label**: Look for error messages in the Control Panel status
3. **Verify command format**: The `set outputs` command must have exactly 10 characters after "set outputs " (2 per finger)
4. **Check finger numbering**: Remember fingers are numbered 1-5 (Pinky=1, Thumb=5)

### Understanding Valve States

- **O (Open)**: Both valves off - finger is neutral/unpressurized
- **P (Pressure)**: Pressure valve on - finger inflates/extends
- **V (Vacuum)**: Vacuum valve on - finger deflates/contracts
- **C (Closed)**: Both valves on - finger is blocked/closed

If a finger isn't responding as expected, check that the valve state matches your intended action.

## Technical Notes

- Commands are case-sensitive: use lowercase for `set outputs`, `release`, and `reset`
- The ESP32 processes commands as they are received
- Multiple rapid commands may be queued by the ESP32
- The system does not send acknowledgment messages back to the application
- Pump speed values are always 0, 3, 6, or 9 (multiples of 3)

