"""
Shared threshold / choreography sequence for OH1 motor gotos.
Sequence per finger: goto 1.0 → hold → goto 0.0 → idle.
"""

from typing import Optional


FLEX_MS = 2500
HOLD_MS = 500
OPEN_MS = 2500


def scaled_duration_ms(base_ms: int, speed_percent: int) -> int:
    """Uniform speed scaling. speed_percent in 50–200; 100 = nominal."""
    if speed_percent <= 0:
        speed_percent = 100
    return max(0, round(base_ms * 100 / speed_percent))


def cmd_goto(motor: int, pos: float) -> str:
    return f"goto {motor} {pos:.3f}\n"


def cmd_idle(motor: Optional[int] = None) -> str:
    if motor is None:
        return "idle\n"
    return f"idle {motor}\n"


def cmd_hold(motor: int) -> str:
    return f"hold {motor}\n"
