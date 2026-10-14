"""
Per-finger threshold mode: when calibrated flex angle ≥ threshold, run
goto 1.0 → short hold → goto 0.0 → idle for that motor.
"""

from __future__ import annotations

from functools import partial
from typing import List, Optional

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
)

try:
    from .control_panel import ControlPanel
    from .fingers import display_motor_order, ui_to_device_motor
    from .threshold_sequence import FLEX_MS, HOLD_MS, OPEN_MS, cmd_goto, cmd_hold, cmd_idle
except ImportError:
    from control_panel import ControlPanel
    from fingers import display_motor_order, ui_to_device_motor
    from threshold_sequence import FLEX_MS, HOLD_MS, OPEN_MS, cmd_goto, cmd_hold, cmd_idle


class ThresholdControlDialog(QDialog):
    """Dialog to enable threshold-triggered motor sequences per finger."""

    def __init__(self, parent=None, reader=None, control_panel: Optional[ControlPanel] = None):
        super().__init__(parent)
        self._reader = reader
        self._control_panel = control_panel

        self.setWindowTitle("Threshold Control")
        self.setGeometry(320, 320, 520, 360)
        self.setMinimumSize(480, 320)

        # phase[i]: None | 'flex' | 'hold' | 'open'
        self._phase: List[Optional[str]] = [None] * 6
        self._armed: List[bool] = [False] * 6

        self._enable_checks: List[Optional[QCheckBox]] = [None] * 6
        self._threshold_spins: List[Optional[QDoubleSpinBox]] = [None] * 6
        self._name_labels: List[Optional[QLabel]] = [None] * 6
        self._row_widgets: List[List] = [[] for _ in range(6)]
        self._grid: Optional[QGridLayout] = None
        self._is_right_hand = True
        self._choreography_suppressed = False

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(
            QLabel(
                "When calibrated flex angle ≥ threshold: goto 1.0 → hold → goto 0.0 → idle.\n"
                "Requires motor min/max calibration on the Control Panel."
            )
        )

        grid_group = QGroupBox("Per-finger threshold (calibrated flex °)")
        grid = QGridLayout()
        grid_group.setLayout(grid)
        self._grid = grid
        grid.addWidget(QLabel("Finger"), 0, 0)
        grid.addWidget(QLabel("Enable"), 0, 1)
        grid.addWidget(QLabel("Threshold °"), 0, 2)

        for motor in range(1, 6):
            name = ControlPanel.FINGER_NAMES[motor - 1]
            dev = ui_to_device_motor(motor)
            name_lbl = QLabel(f"{name} (M{dev})")
            self._name_labels[motor] = name_lbl

            en = QCheckBox()
            en.setToolTip("Run goto flex/open sequence when angle ≥ threshold")
            en.stateChanged.connect(partial(self._on_enable_changed, motor))
            self._enable_checks[motor] = en

            sp = QDoubleSpinBox()
            sp.setRange(-180.0, 360.0)
            sp.setDecimals(1)
            sp.setSingleStep(1.0)
            sp.setValue(40.0)
            sp.setToolTip("Trigger when calibrated flex angle is ≥ this value")
            self._threshold_spins[motor] = sp

            self._row_widgets[motor] = [name_lbl, en, sp]

        layout.addWidget(grid_group)

        self._status = QLabel("Status: Not connected")
        layout.addWidget(self._status)
        self.set_hand_orientation(True)
        self._update_connection_state()

    def set_hand_orientation(self, is_right_hand: bool):
        """Reorder finger rows to match control panel / 3D hand layout."""
        self._is_right_hand = bool(is_right_hand)
        if self._grid is None:
            return
        for motor in range(1, 6):
            for w in self._row_widgets[motor]:
                self._grid.removeWidget(w)
        for display_row, (motor, name) in enumerate(display_motor_order(self._is_right_hand), start=1):
            lbl = self._name_labels[motor]
            if lbl:
                lbl.setText(f"{name} (M{ui_to_device_motor(motor)})")
            for col, w in enumerate(self._row_widgets[motor]):
                self._grid.addWidget(w, display_row, col)

    def _on_enable_changed(self, finger_idx: int, state):
        if not bool(state):
            self._phase[finger_idx] = None
            self._armed[finger_idx] = False
            self._send(cmd_idle(ui_to_device_motor(finger_idx)))

    def set_reader(self, reader):
        self._reader = reader
        if reader is None:
            self._choreography_suppressed = False
            for i in range(1, 6):
                self._phase[i] = None
                self._armed[i] = False
        self._update_connection_state()

    def set_control_panel(self, control_panel: Optional[ControlPanel]):
        self._control_panel = control_panel

    def set_choreography_suppressed(self, suppressed: bool):
        self._choreography_suppressed = suppressed

    def clear_phases_for_choreography(self):
        for i in range(1, 6):
            self._phase[i] = None
            self._armed[i] = False

    def _update_connection_state(self):
        ok = self._reader is not None and self._reader.is_connected()
        for i in range(1, 6):
            if self._enable_checks[i]:
                self._enable_checks[i].setEnabled(ok)
            if self._threshold_spins[i]:
                self._threshold_spins[i].setEnabled(ok)
        self._status.setText("Status: Ready" if ok else "Status: Not connected")

    def _threshold_for(self, finger_idx: int) -> float:
        sp = self._threshold_spins[finger_idx]
        return float(sp.value()) if sp else 0.0

    def _is_enabled(self, finger_idx: int) -> bool:
        cb = self._enable_checks[finger_idx]
        return bool(cb) and bool(cb.isChecked())

    def _send(self, cmd: str):
        if not self._reader or not self._reader.is_connected():
            self._status.setText("Status: Not connected")
            return
        if self._reader.write(cmd):
            short = cmd.strip()
            if len(short) > 52:
                short = short[:49] + "..."
            self._status.setText(f"Status: Sent — {short}")
        else:
            self._status.setText("Status: Failed to send")

    def on_angles_updated(self, angles: List[float]):
        """angles[0..4] = Thumb..Pinky (same order as calibration / flex)."""
        if not self._reader or not self._reader.is_connected():
            return
        if self._choreography_suppressed:
            return

        for finger_idx in range(1, 6):
            if not self._is_enabled(finger_idx):
                continue
            if self._phase[finger_idx] is not None:
                continue
            angle = angles[finger_idx - 1]
            thr = self._threshold_for(finger_idx)
            if angle < thr:
                self._armed[finger_idx] = True
            if self._armed[finger_idx] and angle >= thr:
                self._armed[finger_idx] = False
                self._begin_flex(finger_idx)

    def _begin_flex(self, finger_idx: int):
        self._phase[finger_idx] = "flex"
        self._send(cmd_goto(ui_to_device_motor(finger_idx), 1.0))
        QTimer.singleShot(FLEX_MS, partial(self._on_flex_done, finger_idx))

    def _on_flex_done(self, finger_idx: int):
        if self._phase[finger_idx] != "flex":
            return
        if not self._is_enabled(finger_idx):
            self._phase[finger_idx] = None
            self._send(cmd_idle(ui_to_device_motor(finger_idx)))
            return
        self._phase[finger_idx] = "hold"
        self._send(cmd_hold(ui_to_device_motor(finger_idx)))
        QTimer.singleShot(HOLD_MS, partial(self._on_hold_done, finger_idx))

    def _on_hold_done(self, finger_idx: int):
        if self._phase[finger_idx] != "hold":
            return
        if not self._is_enabled(finger_idx):
            self._phase[finger_idx] = None
            self._send(cmd_idle(ui_to_device_motor(finger_idx)))
            return
        self._phase[finger_idx] = "open"
        self._send(cmd_goto(ui_to_device_motor(finger_idx), 0.0))
        QTimer.singleShot(OPEN_MS, partial(self._on_open_done, finger_idx))

    def _on_open_done(self, finger_idx: int):
        if self._phase[finger_idx] != "open":
            return
        self._phase[finger_idx] = None
        self._send(cmd_idle(ui_to_device_motor(finger_idx)))
