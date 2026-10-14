"""
Control panel for OMNIHUMAN-O1 FOC motors (M1–M5).
Sends text commands identical on USB Serial and BLE.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QDoubleSpinBox,
    QPushButton,
    QGroupBox,
    QWidget,
    QSizePolicy,
)
from PySide6.QtCore import Qt
from typing import Dict, List, Optional

try:
    from .fingers import (
        FINGER_NAMES,
        display_motor_order,
        normalize_fwd_rev,
        ui_to_device_motor,
    )
except ImportError:
    from fingers import (
        FINGER_NAMES,
        display_motor_order,
        normalize_fwd_rev,
        ui_to_device_motor,
    )


def _make_button(text: str, tooltip: str = "") -> QPushButton:
    btn = QPushButton(text)
    btn.setToolTip(tooltip)
    btn.setAutoDefault(False)
    btn.setDefault(False)
    btn.setMinimumHeight(32)
    btn.setMinimumWidth(64)
    btn.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
    return btn


def _wrap_row(*widgets) -> QWidget:
    """Horizontal row without GroupBox chrome (avoids crushing button text)."""
    wrap = QWidget()
    row = QHBoxLayout(wrap)
    row.setContentsMargins(2, 2, 2, 2)
    row.setSpacing(6)
    for w in widgets:
        row.addWidget(w)
    return wrap


class ControlPanel(QDialog):
    """Per-motor motion / calibration controls for OH1 core."""

    FINGER_NAMES = FINGER_NAMES  # Thumb → Pinky (motors 1–5)

    def __init__(self, parent=None, serial_reader=None):
        super().__init__(parent)
        self.serial_reader = serial_reader
        self._is_right_hand = True

        self.setWindowTitle("Control Panel — Motors")
        self.setGeometry(280, 200, 1100, 520)
        self.setMinimumSize(980, 460)

        self._goto_spins: List[Optional[QDoubleSpinBox]] = [None] * 6
        self._pos_labels: List[Optional[QLabel]] = [None] * 6
        self._angle_labels: List[Optional[QLabel]] = [None] * 6
        self._name_labels: List[Optional[QLabel]] = [None] * 6
        self._motor_buttons: List[List] = [[] for _ in range(6)]
        # (fwd, rev) buttons per UI motor, so tooltips can follow the invert setting.
        self._jog_buttons: Dict[int, tuple] = {}
        # Widgets in each motor row (for reordering in the grid)
        self._row_widgets: Dict[int, List[QWidget]] = {m: [] for m in range(1, 6)}
        self._grid: Optional[QGridLayout] = None

        self._setup_ui()
        self.refresh_direction_tooltips()
        self.set_hand_orientation(True)
        self._update_connection_state()

    def refresh_direction_tooltips(self):
        for ui_motor, (fwd, rev) in self._jog_buttons.items():
            dev = ui_to_device_motor(ui_motor)
            fwd.setToolTip(f"{normalize_fwd_rev('fwd', ui_motor)} {dev}")
            rev.setToolTip(f"{normalize_fwd_rev('rev', ui_motor)} {dev}")

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        self.setLayout(layout)

        grid_group = QGroupBox("Finger motors (M1–M5)")
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        grid.setContentsMargins(12, 16, 12, 12)
        grid_group.setLayout(grid)
        self._grid = grid

        headers = [
            "Finger",
            "Pos (0–1)",
            "Angle °",
            "Goto",
            "Jog",
            "Hold / Idle",
            "Calibrate",
        ]
        for col, text in enumerate(headers):
            hdr = QLabel(text)
            hdr.setAlignment(Qt.AlignCenter)
            grid.addWidget(hdr, 0, col)

        for col in (3, 4, 5, 6):
            grid.setColumnStretch(col, 1)

        # Build one row per UI finger (1=Thumb … 5=Pinky); device motor is reversed.
        for ui_motor in range(1, 6):
            name = self.FINGER_NAMES[ui_motor - 1]
            dev = ui_to_device_motor(ui_motor)
            name_lbl = QLabel(f"{name} (M{dev})")
            name_lbl.setMinimumWidth(100)
            self._name_labels[ui_motor] = name_lbl

            pos_lbl = QLabel("nan")
            pos_lbl.setAlignment(Qt.AlignCenter)
            pos_lbl.setMinimumWidth(64)
            self._pos_labels[ui_motor] = pos_lbl

            ang_lbl = QLabel("nan")
            ang_lbl.setAlignment(Qt.AlignCenter)
            ang_lbl.setMinimumWidth(64)
            self._angle_labels[ui_motor] = ang_lbl

            spin = QDoubleSpinBox()
            spin.setRange(0.0, 1.0)
            spin.setDecimals(2)
            spin.setSingleStep(0.05)
            spin.setValue(0.5)
            spin.setMinimumHeight(32)
            spin.setMinimumWidth(72)
            spin.setToolTip("Calibrated fraction of travel (needs min+max)")
            self._goto_spins[ui_motor] = spin
            goto_btn = _make_button("Go", f"goto {dev} <pos>")
            goto_btn.clicked.connect(lambda _=False, m=ui_motor: self._on_goto(m))
            goto_wrap = _wrap_row(spin, goto_btn)
            self._motor_buttons[ui_motor].extend([goto_btn, spin])

            fwd = _make_button("Fwd")
            fwd.clicked.connect(lambda _=False, m=ui_motor: self._send_motor("fwd", m))
            rev = _make_button("Rev")
            rev.clicked.connect(lambda _=False, m=ui_motor: self._send_motor("rev", m))
            self._jog_buttons[ui_motor] = (fwd, rev)
            jog_wrap = _wrap_row(fwd, rev)
            self._motor_buttons[ui_motor].extend([fwd, rev])

            hold = _make_button("Hold", f"hold {dev}")
            hold.clicked.connect(lambda _=False, m=ui_motor: self._send_motor("hold", m))
            idle = _make_button("Idle", f"idle {dev}")
            idle.clicked.connect(lambda _=False, m=ui_motor: self._send_motor("idle", m))
            hi_wrap = _wrap_row(hold, idle)
            self._motor_buttons[ui_motor].extend([hold, idle])

            min_btn = _make_button("Min", f"min {dev}")
            min_btn.clicked.connect(lambda _=False, m=ui_motor: self._send_motor("min", m))
            max_btn = _make_button("Max", f"max {dev}")
            max_btn.clicked.connect(lambda _=False, m=ui_motor: self._send_motor("max", m))
            cal_wrap = _wrap_row(min_btn, max_btn)
            self._motor_buttons[ui_motor].extend([min_btn, max_btn])

            self._row_widgets[ui_motor] = [
                name_lbl, pos_lbl, ang_lbl, goto_wrap, jog_wrap, hi_wrap, cal_wrap
            ]

        layout.addWidget(grid_group)

        global_row = QHBoxLayout()
        global_row.setSpacing(8)
        self.min_all_btn = _make_button("Min All", "min — mark current pose as min for all motors")
        self.min_all_btn.setMinimumWidth(88)
        self.min_all_btn.clicked.connect(lambda: self._send("min"))
        self.max_all_btn = _make_button("Max All", "max — mark current pose as max for all motors")
        self.max_all_btn.setMinimumWidth(88)
        self.max_all_btn.clicked.connect(lambda: self._send("max"))
        self.idle_all_btn = _make_button("Idle All", "idle — coast all motors")
        self.idle_all_btn.setMinimumWidth(88)
        self.idle_all_btn.clicked.connect(lambda: self._send("idle"))
        self.demo_btn = _make_button(
            "Device Demo",
            "demo — firmware: each calibrated motor goto min then max "
            "(Host Demo is in Endpoint Lab)",
        )
        self.demo_btn.clicked.connect(lambda: self._send("demo"))
        self.fault_clear_btn = _make_button("Fault Clear", "fault clear")
        self.fault_clear_btn.setMinimumWidth(100)
        self.fault_clear_btn.clicked.connect(lambda: self._send("fault clear"))
        self.imu_reset_btn = _make_button("IMU Reset", "imu reset")
        self.imu_reset_btn.setMinimumWidth(100)
        self.imu_reset_btn.clicked.connect(lambda: self._send("imu reset"))

        for btn in (
            self.min_all_btn,
            self.max_all_btn,
            self.idle_all_btn,
            self.demo_btn,
            self.fault_clear_btn,
            self.imu_reset_btn,
        ):
            global_row.addWidget(btn)
        global_row.addStretch()
        layout.addLayout(global_row)

        self.status_label = QLabel("Status: Ready")
        layout.addWidget(self.status_label)

        self._global_buttons = [
            self.min_all_btn,
            self.max_all_btn,
            self.idle_all_btn,
            self.demo_btn,
            self.fault_clear_btn,
            self.imu_reset_btn,
        ]

    def set_hand_orientation(self, is_right_hand: bool):
        """Reorder finger rows to match 3D left→right layout for this hand."""
        self._is_right_hand = bool(is_right_hand)
        if self._grid is None:
            return

        # Detach current motor rows (keep header row 0).
        for ui_motor in range(1, 6):
            for w in self._row_widgets[ui_motor]:
                self._grid.removeWidget(w)

        for display_row, (ui_motor, name) in enumerate(
            display_motor_order(self._is_right_hand), start=1
        ):
            dev = ui_to_device_motor(ui_motor)
            lbl = self._name_labels[ui_motor]
            if lbl:
                lbl.setText(f"{name} (M{dev})")
            for col, w in enumerate(self._row_widgets[ui_motor]):
                self._grid.addWidget(w, display_row, col)

    def _send(self, command: str):
        if not self.serial_reader or not self.serial_reader.is_connected():
            self.status_label.setText("Status: Not connected")
            return
        cmd = command if command.endswith("\n") else command + "\n"
        if self.serial_reader.write(cmd):
            display = cmd.strip()
            if len(display) > 50:
                display = display[:47] + "..."
            self.status_label.setText(f"Status: Sent — {display}")
        else:
            self.status_label.setText("Status: Failed to send command")

    def _send_motor(self, verb: str, ui_motor: int):
        """Send a per-finger command using the device motor index."""
        verb = normalize_fwd_rev(verb, ui_motor)
        self._send(f"{verb} {ui_to_device_motor(ui_motor)}")

    def _on_goto(self, ui_motor: int):
        spin = self._goto_spins[ui_motor]
        pos = float(spin.value()) if spin else 0.0
        self._send(f"goto {ui_to_device_motor(ui_motor)} {pos:.3f}")

    def update_motor_telemetry(
        self,
        positions: Optional[List[float]] = None,
        angles: Optional[List[float]] = None,
    ):
        """Update live pos/angle labels from device motor streams."""
        try:
            from .parser import FlexParser
        except ImportError:
            from parser import FlexParser

        if positions and len(positions) >= 5:
            for ui_motor in range(1, 6):
                lbl = self._pos_labels[ui_motor]
                if lbl:
                    dev_i = ui_to_device_motor(ui_motor) - 1
                    lbl.setText(FlexParser.format_float(positions[dev_i], 3))
        if angles and len(angles) >= 5:
            for ui_motor in range(1, 6):
                lbl = self._angle_labels[ui_motor]
                if lbl:
                    dev_i = ui_to_device_motor(ui_motor) - 1
                    lbl.setText(FlexParser.format_float(angles[dev_i], 1))

    def set_serial_reader(self, reader):
        self.serial_reader = reader
        self._update_connection_state()

    def _update_connection_state(self):
        ok = self.serial_reader is not None and self.serial_reader.is_connected()
        for motor in range(1, 6):
            for w in self._motor_buttons[motor]:
                w.setEnabled(ok)
        for btn in self._global_buttons:
            btn.setEnabled(ok)
        self.status_label.setText("Status: Ready" if ok else "Status: Not connected")
