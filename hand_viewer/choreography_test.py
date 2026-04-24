"""
Choreography Test: run the full threshold sequence once per finger, Thumb → Pinky.
"""

from __future__ import annotations

from functools import partial
from typing import List, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
)

try:
    from .control_panel import ControlPanel
    from .threshold_control import ThresholdControlDialog
    from .threshold_sequence import (
        DRAIN_DELAY_MS,
        PRESSURE_MS,
        STEP_MS,
        VACUUM_PUMP_MS,
        build_set_outputs_command,
        scaled_duration_ms,
    )
except ImportError:
    from control_panel import ControlPanel
    from threshold_control import ThresholdControlDialog
    from threshold_sequence import (
        DRAIN_DELAY_MS,
        PRESSURE_MS,
        STEP_MS,
        VACUUM_PUMP_MS,
        build_set_outputs_command,
        scaled_duration_ms,
    )

# Finger indices 5..1: Thumb, Index, Middle, Ring, Pinky
CHOREOGRAPHY_FINGER_ORDER = [5, 4, 3, 2, 1]

_SPEED_MIN = 50
_SPEED_MAX = 200
_SPEED_DEFAULT = 100


class ChoreographyTestDialog(QDialog):
    def __init__(
        self,
        parent=None,
        reader=None,
        control_panel: Optional[ControlPanel] = None,
        threshold_control: Optional[ThresholdControlDialog] = None,
    ):
        super().__init__(parent)
        self._reader = reader
        self._control_panel = control_panel
        self._threshold_control = threshold_control

        self.setWindowTitle("Choreography Test")
        self.setGeometry(340, 340, 520, 280)
        self.setMinimumSize(480, 240)

        self._phases: List[Optional[str]] = [None] * 6
        self._running = False
        self._finger_queue: List[int] = []
        self._speed_percent = _SPEED_DEFAULT

        layout = QVBoxLayout()
        self.setLayout(layout)

        info = QGroupBox("Threshold sequence — one finger at a time (Thumb → Pinky)")
        info_layout = QVBoxLayout()
        info_layout.addWidget(
            QLabel(
                "Pump level follows the Threshold Control dialog. "
                "Run is ignored while a choreography is already in progress."
            )
        )
        info.setLayout(info_layout)
        layout.addWidget(info)

        speed_row = QHBoxLayout()
        speed_row.addWidget(QLabel("Speed (% of nominal):"))
        self._speed_slider = QSlider(Qt.Horizontal)
        self._speed_slider.setMinimum(_SPEED_MIN)
        self._speed_slider.setMaximum(_SPEED_MAX)
        self._speed_slider.setValue(_SPEED_DEFAULT)
        self._speed_slider.setToolTip(
            "100% = same timings as Threshold Control; higher = faster; lower = slower"
        )
        self._speed_slider.valueChanged.connect(self._on_speed_changed)
        speed_row.addWidget(self._speed_slider)
        self._speed_value_label = QLabel(str(_SPEED_DEFAULT))
        self._speed_value_label.setMinimumWidth(36)
        speed_row.addWidget(self._speed_value_label)
        layout.addLayout(speed_row)

        self._run_btn = QPushButton("Run choreography")
        self._run_btn.setAutoDefault(False)
        self._run_btn.setDefault(False)
        self._run_btn.clicked.connect(self._on_run_clicked)
        layout.addWidget(self._run_btn)

        self._status = QLabel("Status: Not connected")
        layout.addWidget(self._status)

        self._update_connection_state()

    def _on_speed_changed(self, value: int):
        self._speed_percent = value
        self._speed_value_label.setText(str(value))

    def set_reader(self, reader):
        self._reader = reader
        if reader is None and self._running:
            self._abort_choreography()
        self._update_connection_state()

    def set_control_panel(self, control_panel: Optional[ControlPanel]):
        self._control_panel = control_panel

    def set_threshold_control(self, threshold_control: Optional[ThresholdControlDialog]):
        self._threshold_control = threshold_control

    def _update_connection_state(self):
        ok = self._reader is not None and self._reader.is_connected()
        self._run_btn.setEnabled(ok and not self._running)
        self._speed_slider.setEnabled(ok)
        if not ok:
            self._status.setText("Status: Not connected")
        elif self._running:
            pass
        else:
            self._status.setText("Status: Ready")

    def _scale(self, base_ms: int) -> int:
        return scaled_duration_ms(base_ms, self._speed_percent)

    def _emit(self):
        if not self._reader or not self._reader.is_connected():
            self._status.setText("Status: Not connected")
            return
        cp = self._control_panel
        tc = self._threshold_control
        if not cp or not tc:
            return
        pump = tc.get_pump_level()
        cmd = build_set_outputs_command(self._phases, pump, cp)
        if self._reader.write(cmd):
            short = cmd.strip()
            if len(short) > 52:
                short = short[:49] + "..."
            self._status.setText(f"Status: Sent — {short}")
        else:
            self._status.setText("Status: Failed to send")

    def _on_run_clicked(self):
        if self._running:
            self._status.setText("Status: Already running")
            return
        if not self._reader or not self._reader.is_connected():
            return
        tc = self._threshold_control
        if not tc or not self._control_panel:
            return

        tc.clear_phases_for_choreography()
        tc.set_choreography_suppressed(True)

        self._running = True
        self._run_btn.setEnabled(False)
        self._finger_queue = list(CHOREOGRAPHY_FINGER_ORDER)
        for i in range(1, 6):
            self._phases[i] = None
        self._start_next_finger()

    def _start_next_finger(self):
        if not self._finger_queue:
            self._finish_choreography()
            return
        finger = self._finger_queue.pop(0)
        self._phases[finger] = "pressure"
        self._emit()
        QTimer.singleShot(self._scale(PRESSURE_MS), partial(self._on_pressure_done, finger))

    def _finish_choreography(self):
        for i in range(1, 6):
            self._phases[i] = None
        self._running = False
        if self._threshold_control:
            self._threshold_control.set_choreography_suppressed(False)
        self._emit()
        self._update_connection_state()
        self._status.setText("Status: Choreography finished")

    def _abort_choreography(self):
        self._finger_queue = []
        for i in range(1, 6):
            self._phases[i] = None
        self._running = False
        if self._threshold_control:
            self._threshold_control.set_choreography_suppressed(False)
        self._update_connection_state()
        self._status.setText("Status: Aborted (disconnected)")

    def _on_pressure_done(self, finger_idx: int):
        if not self._running or self._phases[finger_idx] != "pressure":
            return
        self._phases[finger_idx] = "rest"
        self._emit()
        QTimer.singleShot(self._scale(STEP_MS), partial(self._on_rest_done, finger_idx))

    def _on_rest_done(self, finger_idx: int):
        if not self._running or self._phases[finger_idx] != "rest":
            return
        self._phases[finger_idx] = "vacuum_pump"
        self._emit()
        QTimer.singleShot(self._scale(VACUUM_PUMP_MS), partial(self._on_vacuum_pump_done, finger_idx))

    def _on_vacuum_pump_done(self, finger_idx: int):
        if not self._running or self._phases[finger_idx] != "vacuum_pump":
            return
        self._phases[finger_idx] = "drain_delay"
        self._emit()
        QTimer.singleShot(self._scale(DRAIN_DELAY_MS), partial(self._on_drain_delay_done, finger_idx))

    def _on_drain_delay_done(self, finger_idx: int):
        if not self._running or self._phases[finger_idx] != "drain_delay":
            return
        self._phases[finger_idx] = "drain"
        self._emit()
        QTimer.singleShot(self._scale(STEP_MS), partial(self._on_drain_done, finger_idx))

    def _on_drain_done(self, finger_idx: int):
        if not self._running or self._phases[finger_idx] != "drain":
            return
        self._phases[finger_idx] = None
        self._emit()
        self._start_next_finger()
