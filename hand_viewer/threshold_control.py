"""
Per-finger threshold mode: when calibrated angle exceeds a threshold, run a timed
pressure (2s) → rest → vacuum+pump (0.7s) → 0.5s idle → drain (pressure only, 3s) sequence, merged with
Control Panel outputs for other fingers.
"""

from __future__ import annotations

from functools import partial
from typing import List, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSlider,
    QVBoxLayout,
)

try:
    from .control_panel import ControlPanel
except ImportError:
    from control_panel import ControlPanel

try:
    from .threshold_sequence import (
        PRESSURE_MS,
        STEP_MS,
        VACUUM_PUMP_MS,
        DRAIN_DELAY_MS,
        build_set_outputs_command,
    )
except ImportError:
    from threshold_sequence import (
        PRESSURE_MS,
        STEP_MS,
        VACUUM_PUMP_MS,
        DRAIN_DELAY_MS,
        build_set_outputs_command,
    )


class ThresholdControlDialog(QDialog):
    """Dialog to enable threshold-triggered valve/pump sequences per finger."""

    def __init__(self, parent=None, reader=None, control_panel: Optional[ControlPanel] = None):
        super().__init__(parent)
        self._reader = reader
        self._control_panel = control_panel

        self.setWindowTitle("Threshold Control")
        self.setGeometry(320, 320, 720, 420)
        self.setMinimumSize(680, 380)

        # phase[i]: None | 'pressure' | 'rest' | 'vacuum_pump' | 'drain_delay' | 'drain'
        self._phase: List[Optional[str]] = [None] * 6
        self._armed: List[bool] = [False] * 6

        self._enable_checks: List[Optional[QCheckBox]] = [None] * 6
        self._threshold_spins: List[Optional[QDoubleSpinBox]] = [None] * 6

        self._pump_level = 3
        self._pump_label: Optional[QLabel] = None
        self._choreography_suppressed = False

        layout = QVBoxLayout()
        self.setLayout(layout)

        pump_row = QHBoxLayout()
        pump_row.addWidget(QLabel("Pump level (pressure + vacuum burst, 0–3):"))
        self._pump_slider = QSlider(Qt.Horizontal)
        self._pump_slider.setMinimum(0)
        self._pump_slider.setMaximum(3)
        self._pump_slider.setValue(self._pump_level)
        self._pump_slider.setToolTip(
            "Pump speed for the pressure step and the 0.7s vacuum+pump burst"
        )
        self._pump_slider.valueChanged.connect(self._on_pump_level_changed)
        pump_row.addWidget(self._pump_slider)
        self._pump_label = QLabel(str(self._pump_level))
        self._pump_label.setMinimumWidth(24)
        pump_row.addWidget(self._pump_label)
        layout.addLayout(pump_row)

        grid_group = QGroupBox("Per-finger threshold (calibrated angle °, signed ≥ triggers)")
        grid = QGridLayout()
        grid_group.setLayout(grid)
        grid.addWidget(QLabel("Finger"), 0, 0)
        grid.addWidget(QLabel("Enable"), 0, 1)
        grid.addWidget(QLabel("Threshold °"), 0, 2)

        for col in range(5):
            finger_idx = col + 1
            name = ControlPanel.FINGER_NAMES[col]
            grid.addWidget(QLabel(name), finger_idx, 0)

            en = QCheckBox()
            en.setToolTip(
                "Run full pressure/rest/vacuum burst/idle/drain sequence when angle ≥ threshold"
            )
            en.stateChanged.connect(partial(self._on_enable_changed, finger_idx))
            self._enable_checks[finger_idx] = en
            grid.addWidget(en, finger_idx, 1)

            sp = QDoubleSpinBox()
            sp.setRange(-180.0, 180.0)
            sp.setDecimals(1)
            sp.setSingleStep(1.0)
            sp.setValue(30.0)
            sp.setToolTip("Trigger when calibrated angle is ≥ this value")
            self._threshold_spins[finger_idx] = sp
            grid.addWidget(sp, finger_idx, 2)

        layout.addWidget(grid_group)

        self._status = QLabel("Status: Not connected")
        layout.addWidget(self._status)

        self._update_connection_state()

    def _on_pump_level_changed(self, value: int):
        self._pump_level = value
        if self._pump_label:
            self._pump_label.setText(str(value))
        for i in range(1, 6):
            if self._phase[i] in ("pressure", "vacuum_pump"):
                self._send_merged()

    def _on_enable_changed(self, finger_idx: int, state):
        if not bool(state):
            self._phase[finger_idx] = None
            self._armed[finger_idx] = False
            self._send_merged()

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

    def get_pump_level(self) -> int:
        return self._pump_level

    def set_choreography_suppressed(self, suppressed: bool):
        self._choreography_suppressed = suppressed

    def clear_phases_for_choreography(self):
        """Reset all per-finger sequence state and sync outputs to Control Panel."""
        for i in range(1, 6):
            self._phase[i] = None
            self._armed[i] = False
        self._send_merged()

    def _update_connection_state(self):
        ok = self._reader is not None and self._reader.is_connected()
        for i in range(1, 6):
            if self._enable_checks[i]:
                self._enable_checks[i].setEnabled(ok)
            if self._threshold_spins[i]:
                self._threshold_spins[i].setEnabled(ok)
        self._pump_slider.setEnabled(ok)
        if not ok:
            self._status.setText("Status: Not connected")
        else:
            self._status.setText("Status: Ready")

    def _threshold_for(self, finger_idx: int) -> float:
        sp = self._threshold_spins[finger_idx]
        return float(sp.value()) if sp else 0.0

    def _is_enabled(self, finger_idx: int) -> bool:
        cb = self._enable_checks[finger_idx]
        return bool(cb) and bool(cb.isChecked())

    def _send_merged(self):
        if not self._reader or not self._reader.is_connected():
            self._status.setText("Status: Not connected")
            return
        cp = self._control_panel
        if not cp:
            return

        cmd = build_set_outputs_command(self._phase, self._pump_level, cp)
        if self._reader.write(cmd):
            short = cmd.strip()
            if len(short) > 52:
                short = short[:49] + "..."
            self._status.setText(f"Status: Sent — {short}")
        else:
            self._status.setText("Status: Failed to send")

    def on_angles_updated(self, angles: List[float]):
        """angles[0..4] match Pinky..Thumb (same order as calibration)."""
        if not self._reader or not self._reader.is_connected():
            return
        if self._choreography_suppressed:
            return

        for finger_idx in range(1, 6):
            if not self._is_enabled(finger_idx):
                continue
            angle = angles[finger_idx - 1]
            thr = self._threshold_for(finger_idx)
            ph = self._phase[finger_idx]

            if ph is None:
                if angle < thr:
                    self._armed[finger_idx] = True
                if self._armed[finger_idx] and angle >= thr:
                    self._armed[finger_idx] = False
                    self._begin_pressure(finger_idx)

    def _begin_pressure(self, finger_idx: int):
        self._phase[finger_idx] = "pressure"
        self._send_merged()
        QTimer.singleShot(PRESSURE_MS, partial(self._on_pressure_done, finger_idx))

    def _on_pressure_done(self, finger_idx: int):
        if self._phase[finger_idx] != "pressure":
            return
        if not self._is_enabled(finger_idx):
            self._phase[finger_idx] = None
            self._send_merged()
            return
        self._phase[finger_idx] = "rest"
        self._send_merged()
        QTimer.singleShot(STEP_MS, partial(self._on_rest_done, finger_idx))

    def _on_rest_done(self, finger_idx: int):
        if self._phase[finger_idx] != "rest":
            return
        if not self._is_enabled(finger_idx):
            self._phase[finger_idx] = None
            self._send_merged()
            return
        self._phase[finger_idx] = "vacuum_pump"
        self._send_merged()
        QTimer.singleShot(VACUUM_PUMP_MS, partial(self._on_vacuum_pump_done, finger_idx))

    def _on_vacuum_pump_done(self, finger_idx: int):
        if self._phase[finger_idx] != "vacuum_pump":
            return
        if not self._is_enabled(finger_idx):
            self._phase[finger_idx] = None
            self._send_merged()
            return
        self._phase[finger_idx] = "drain_delay"
        self._send_merged()
        QTimer.singleShot(DRAIN_DELAY_MS, partial(self._on_drain_delay_done, finger_idx))

    def _on_drain_delay_done(self, finger_idx: int):
        if self._phase[finger_idx] != "drain_delay":
            return
        if not self._is_enabled(finger_idx):
            self._phase[finger_idx] = None
            self._send_merged()
            return
        self._phase[finger_idx] = "drain"
        self._send_merged()
        QTimer.singleShot(STEP_MS, partial(self._on_drain_done, finger_idx))

    def _on_drain_done(self, finger_idx: int):
        if self._phase[finger_idx] != "drain":
            return
        self._phase[finger_idx] = None
        self._send_merged()
