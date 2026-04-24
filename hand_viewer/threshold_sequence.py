"""
Shared threshold sequence: base timings and merged `set outputs` command builder.
Used by Threshold Control (angle-triggered) and Choreography Test (sequential).
"""

from __future__ import annotations

from typing import List, Optional

try:
    from .control_panel import ControlPanel, finger_segment
except ImportError:
    from control_panel import ControlPanel, finger_segment

PRESSURE_MS = 2000
STEP_MS = 3000
VACUUM_PUMP_MS = 700
DRAIN_DELAY_MS = 500


def scaled_duration_ms(base_ms: int, speed_percent: int) -> int:
    """
    Uniform speed scaling for choreography. `speed_percent` in 50–200; 100 = nominal.
    Higher percent = faster (shorter duration): duration = base * 100 / percent.
    """
    if speed_percent <= 0:
        speed_percent = 100
    return max(0, round(base_ms * 100 / speed_percent))


def build_set_outputs_command(
    phases: List[Optional[str]],
    pump_level: int,
    control_panel: ControlPanel,
) -> str:
    """
    Build full `set outputs ...\\n`. `phases` length >= 6; index 0 unused; 1–5 = finger phases.
    None = use control_panel state for that finger.
    """
    parts = []
    for finger_idx in range(1, 6):
        ph = phases[finger_idx]
        if ph == "pressure":
            parts.append(finger_segment(False, True, pump_level))
        elif ph == "rest":
            parts.append(finger_segment(False, False, 0))
        elif ph == "vacuum_pump":
            parts.append(finger_segment(True, False, pump_level))
        elif ph == "drain_delay":
            parts.append(finger_segment(False, False, 0))
        elif ph == "drain":
            parts.append(finger_segment(False, True, 0))
        else:
            parts.append(
                finger_segment(
                    control_panel.vacuum_valves[finger_idx],
                    control_panel.pressure_valves[finger_idx],
                    control_panel.pump_speeds[finger_idx],
                )
            )
    return "set outputs " + "".join(parts) + "\n"
