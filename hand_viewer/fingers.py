"""
OH1 finger / motor ordering for the GUI.

UI / Control Panel / hand model order (and motor indices M1–M5):
  Thumb, Index, Middle, Ring, Pinky

Flex telemetry on the wire is:
  Index, Middle, Ring, Pinky, Thumb
The parser remaps that into the UI order above.
"""

FINGER_NAMES = ["Thumb", "Index", "Middle", "Ring", "Pinky"]

# Motor index (1..5) for each name
FINGER_TO_MOTOR = {name: i + 1 for i, name in enumerate(FINGER_NAMES)}
