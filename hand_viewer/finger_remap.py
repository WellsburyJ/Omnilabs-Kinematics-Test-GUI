"""
Finger sensor remapping for alternate glove wiring (Test mode).
OH1 flex order: [Thumb, Index, Middle, Ring, Pinky].
"""

from typing import List


def apply_test_finger_remap(raw_values: List[float]) -> List[float]:
    """
    Remap OH1 flex order for test wiring.

    - Display Thumb  unchanged
    - Display Index  <- Pinky sensor (sign flipped)
    - Display Middle <- Ring sensor
    - Display Ring   <- Middle sensor
    - Display Pinky  <- Index sensor
    """
    if len(raw_values) != 5:
        return raw_values
    thumb, index, middle, ring, pinky = raw_values
    return [thumb, -pinky, ring, middle, index]
