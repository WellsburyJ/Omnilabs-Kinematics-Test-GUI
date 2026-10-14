"""
OH1 finger / motor ordering for the GUI.

UI anatomical order (labels / panel rows):
  Thumb, Index, Middle, Ring, Pinky   (UI motors 1..5)

Device `values motors` / `values angles` and motion commands use the same
order (Thumb=1 .. Pinky=5) since the hand was rewired. Still go through
ui_to_device_motor() so a future rewire only needs changing here.

Flex telemetry on the wire is the same as the UI:
  Thumb, Index, Middle, Ring, Pinky

For left/right hand display, panel rows match the 3D view (screen-left → right):
right hand Thumb→Pinky, left hand Pinky→Thumb.
"""

import json
from pathlib import Path
from typing import List, Set, Tuple

FINGER_NAMES = ["Thumb", "Index", "Middle", "Ring", "Pinky"]

# UI motor index (1..5) for each name — Thumb=1 … Pinky=5
FINGER_TO_MOTOR = {name: i + 1 for i, name in enumerate(FINGER_NAMES)}

# UI motors whose fwd/rev should be swapped before sending to the device.
# Editable at runtime (Endpoint Lab "Inv") and saved here; shared by all panels.
MOTOR_INVERT_PATH = Path(__file__).resolve().parent / "motor_invert.json"
DEFAULT_INVERTED_UI_MOTORS = frozenset({3})


def _load_inverted() -> Set[int]:
    try:
        data = json.loads(MOTOR_INVERT_PATH.read_text(encoding="utf-8"))
        motors = data.get("inverted_ui_motors") if isinstance(data, dict) else None
        if isinstance(motors, list):
            return {int(m) for m in motors if 1 <= int(m) <= 5}
    except (OSError, ValueError, TypeError):
        pass
    return set(DEFAULT_INVERTED_UI_MOTORS)


FWD_REV_INVERTED_UI_MOTORS: Set[int] = _load_inverted()


def _save_inverted():
    try:
        MOTOR_INVERT_PATH.write_text(
            json.dumps(
                {"inverted_ui_motors": sorted(FWD_REV_INVERTED_UI_MOTORS)}, indent=2
            )
            + "\n",
            encoding="utf-8",
        )
    except OSError:
        pass


def is_fwd_rev_inverted(ui_motor: int) -> bool:
    return int(ui_motor) in FWD_REV_INVERTED_UI_MOTORS


def set_fwd_rev_inverted(ui_motor: int, inverted: bool):
    m = int(ui_motor)
    if inverted:
        FWD_REV_INVERTED_UI_MOTORS.add(m)
    else:
        FWD_REV_INVERTED_UI_MOTORS.discard(m)
    _save_inverted()


def inverted_ui_motors() -> List[int]:
    return sorted(FWD_REV_INVERTED_UI_MOTORS)


def ui_to_device_motor(ui_motor: int) -> int:
    """
    Map UI motor (1=Thumb .. 5=Pinky) to device motor (1=Thumb .. 5=Pinky).
    """
    return int(ui_motor)


def device_to_ui_motor(device_motor: int) -> int:
    """Inverse of ui_to_device_motor."""
    return int(device_motor)


def normalize_fwd_rev(verb: str, ui_motor: int) -> str:
    """
    Swap fwd/rev for motors marked inverted (see set_fwd_rev_inverted).
    """
    v = verb.strip().lower()
    if v not in ("fwd", "rev"):
        return verb
    if not is_fwd_rev_inverted(ui_motor):
        return verb
    return "rev" if v == "fwd" else "fwd"


def display_motor_order(is_right_hand: bool) -> List[Tuple[int, str]]:
    """
    Return (ui_motor_index, finger_name) pairs in panel display order.

    Right hand (thumb on screen-left): Thumb→Pinky.
    Left hand (pinky on screen-left): Pinky→Thumb.
    """
    pairs = [(i + 1, name) for i, name in enumerate(FINGER_NAMES)]
    if is_right_hand:
        return pairs
    return list(reversed(pairs))
