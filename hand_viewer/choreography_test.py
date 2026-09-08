"""
Choreography Test: run motor flex sequence once per finger, Thumb → Pinky.
"""

from __future__ import annotations

from functools import partial
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
)
from PySide6.QtCore import QTimer

try:
    from .control_panel import ControlPanel
    from .threshold_control import ThresholdControlDialog
    from .threshold_sequence import (
        FLEX_MS,
        HOLD_MS,
        OPEN_MS,
        cmd_goto,
        cmd_hold,
        cmd_idle,
        scaled_duration_ms,
    )
except ImportError:
    from control_panel import ControlPanel
    from threshold_control import ThresholdControlDialog
    from threshold_sequence import (
        FLEX_MS,
        HOLD_MS,
        OPEN_MS,
        cmd_goto,
        cmd_hold,
        cmd_idle,
        scaled_duration_ms,
    )

# Motor indices 1..5: Thumb → Pinky
CHOREOGRAPHY_FINGER_ORDER = [1, 2, 3, 4, 5]

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
        self.setGeometry(340, 340, 520, 260)
        self.setMinimumSize(480, 220)

        self._phase: Optional[str] = None
        self._active_finger: Optional[int] = None
        self._running = False
        self._finger_queue: List[int] = []
        self._speed_percent = _SPEED_DEFAULT

        layout = QVBoxLayout()
        self.setLayout(layout)

        info = QGroupBox("Motor sequence — one finger at a time (Thumb → Pinky)")
        info_layout = QVBoxLayout()
        info_layout.addWidget(
            QLabel(
                "Each finger: goto 1.0 → hold → goto 0.0 → idle. "
                "Requires min/max calibration."
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
        elif not self._running:
            self._status.setText("Status: Ready")

    def _scale(self, base_ms: int) -> int:
        return scaled_duration_ms(base_ms, self._speed_percent)

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

    def _on_run_clicked(self):
        if self._running:
            self._status.setText("Status: Already running")
            return
        if not self._reader or not self._reader.is_connected():
            return
        tc = self._threshold_control
        if tc:
            tc.clear_phases_for_choreography()
            tc.set_choreography_suppressed(True)

        self._running = True
        self._run_btn.setEnabled(False)
        self._finger_queue = list(CHOREOGRAPHY_FINGER_ORDER)
        self._start_next_finger()

    def _start_next_finger(self):
        if not self._finger_queue:
            self._finish_choreography()
            return
        finger = self._finger_queue.pop(0)
        self._active_finger = finger
        self._phase = "flex"
        name = ControlPanel.FINGER_NAMES[finger - 1]
        self._status.setText(f"Status: {name} — flex")
        self._send(cmd_goto(finger, 1.0))
        QTimer.singleShot(self._scale(FLEX_MS), partial(self._on_flex_done, finger))

    def _finish_choreography(self):
        self._phase = None
        self._active_finger = None
        self._running = False
        if self._threshold_control:
            self._threshold_control.set_choreography_suppressed(False)
        self._send(cmd_idle())
        self._update_connection_state()
        self._status.setText("Status: Choreography finished")

    def _abort_choreography(self):
        self._finger_queue = []
        self._phase = None
        self._active_finger = None
        self._running = False
        if self._threshold_control:
            self._threshold_control.set_choreography_suppressed(False)
        self._update_connection_state()
        self._status.setText("Status: Aborted (disconnected)")

    def _on_flex_done(self, finger_idx: int):
        if not self._running or self._phase != "flex" or self._active_finger != finger_idx:
            return
        self._phase = "hold"
        self._send(cmd_hold(finger_idx))
        QTimer.singleShot(self._scale(HOLD_MS), partial(self._on_hold_done, finger_idx))

    def _on_hold_done(self, finger_idx: int):
        if not self._running or self._phase != "hold" or self._active_finger != finger_idx:
            return
        self._phase = "open"
        self._send(cmd_goto(finger_idx, 0.0))
        QTimer.singleShot(self._scale(OPEN_MS), partial(self._on_open_done, finger_idx))

    def _on_open_done(self, finger_idx: int):
        if not self._running or self._phase != "open" or self._active_finger != finger_idx:
            return
        self._send(cmd_idle(finger_idx))
        self._phase = None
        self._active_finger = None
        self._start_next_finger()
