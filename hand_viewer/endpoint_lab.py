"""
Endpoint Lab: host-side min/max discovery + host-driven demo for OH1 motors.

Uses device primitives (fwd/rev/idle/min/max/goto) and live encoder angles.
Firmware auto-find is not used — see references/FIRMWARE_ENDPOINT_HANDOVER.md.
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    from .fingers import (
        FINGER_NAMES,
        display_motor_order,
        is_fwd_rev_inverted,
        normalize_fwd_rev,
        set_fwd_rev_inverted,
        ui_to_device_motor,
    )
    from .parser import FlexParser
except ImportError:
    from fingers import (
        FINGER_NAMES,
        display_motor_order,
        is_fwd_rev_inverted,
        normalize_fwd_rev,
        set_fwd_rev_inverted,
        ui_to_device_motor,
    )
    from parser import FlexParser


# Give up on a Find step after this long so a chained Auto Cal run can't stall.
FIND_TIMEOUT_S = 30.0
# Host Demo: wait for encoder near the stored end before advancing (large travels
# need far more than a fixed 1–2 s dwell).
DEMO_ARRIVE_DEG = 8.0
DEMO_GOTO_TIMEOUT_S = 45.0
# Defaults for Find torque apply/restore (tune in the UI).
DEFAULT_FIND_TORQUE_A = 1.0
DEFAULT_RESTORE_TORQUE_A = 1.0
DEFAULT_MULTI_TORQUE_A = 0.35
CHORUS_TIMEOUT_S = 45.0
# Speed controls only slow things down: the firmware defaults are the fastest the
# application needs. 0 = send no speed (firmware default); firmware floor is 0.1 rad/s.
FW_JOG_SPEED_RAD_S = 2.0
FW_GOTO_SPEED_RAD_S = 3.0
# Tunables persist next to this module (same idea as calibration.json).
SETTINGS_PATH = Path(__file__).resolve().parent / "endpoint_lab_settings.json"

MODE_PUSH_PULL = "push_pull"
MODE_PULL_ONLY = "pull_only"

INFO_PUSH_PULL = (
    "Host owns endpoint discovery (jog → plateau → min/max). "
    "Find keeps jogging until |Δangle| stays below Plateau ° for Hold ms, "
    "then marks the end. Tune Find A / After A / Plateau / Hold / Jog as needed "
    "(saved between sessions). "
    "Auto Cal runs find min, find max, then the margin for one finger in a single click. "
    "Margin is applied host-side, so the device keeps the full discovered range. "
    "Once both ends are set the device clamps jogs inside that range, so re-finding "
    "needs Forget (sends cal clear N). "
    "Device Demo on the Control Panel is separate. "
    "See references/FIRMWARE_ENDPOINT_HANDOVER.md."
)

INFO_PULL_ONLY = (
    "Pull-only hardware: motors can only pull fingers open; a passive return closes them. "
    "Start Auto Cal with the finger relaxed/closed — it marks min at that pose (needed so "
    "firmware goto works), then jogs fwd until plateau and marks max = fully open. "
    "Open All drives to max (less the margin); Release All idles so the fingers close. "
    "Tune Find A / After A / Plateau / Hold / Jog as needed (saved between sessions). "
    "Once both ends are set, re-finding needs Forget (sends cal clear N)."
)


BUTTON_HEIGHT = 28
ROW_HEIGHT = BUTTON_HEIGHT + 8


def _make_button(text: str, tooltip: str = "") -> QPushButton:
    btn = QPushButton(text)
    btn.setToolTip(tooltip)
    btn.setAutoDefault(False)
    btn.setDefault(False)
    btn.setMinimumHeight(BUTTON_HEIGHT)
    btn.setMinimumWidth(56)
    btn.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
    return btn


class EndpointLabDialog(QDialog):
    """Host endpoint finding + Host Demo (goto 0 → 1 per finger)."""

    invert_changed = Signal()

    def __init__(self, parent=None, reader=None):
        super().__init__(parent)
        self._reader = reader
        self._is_right_hand = True

        self.setWindowTitle("Endpoint Lab")
        self.setGeometry(260, 160, 1100, 700)
        self.setMinimumSize(900, 560)

        # Device-order angles from stream (len 5); remapped for display.
        self._device_angles: List[float] = [float("nan")] * 5
        self._has_min = [False] * 6  # index by UI motor 1..5
        self._has_max = [False] * 6
        # Encoder ° captured when min/max were marked (for Host Demo arrival checks).
        self._end_angle_min: List[float] = [float("nan")] * 6
        self._end_angle_max: List[float] = [float("nan")] * 6
        # Margin is applied host-side when issuing goto. Re-marking min/max at an
        # inset pose would shrink the device range on every run, and the firmware
        # then clamps jogs inside it (GUI_HANDOVER: soft endstops at ~5%/~95%).
        self._margin_frac = [0.0] * 6

        self._pull_only = False
        # Widgets that only make sense on push-pull hardware (hidden in pull-only).
        self._push_only_widgets: List[QWidget] = []
        self._auto_buttons: List[QPushButton] = []

        self._busy = False
        self._stop_requested = False
        self._find_state: Optional[dict] = None
        self._demo_state: Optional[dict] = None
        self._margin_state: Optional[dict] = None
        self._chorus_state: Optional[dict] = None
        # UI motor that currently has Find torque applied (for restore on stop/timeout).
        self._find_torque_motor: Optional[int] = None
        # Motors given multi-finger torque for Open/Close All.
        self._multi_torque_motors: List[int] = []
        # Remaining steps of a chained Auto Cal run (find min → find max → margin).
        self._sequence: Optional[List[str]] = None
        self._sequence_motor: Optional[int] = None
        # Extra fingers waiting for sequential Auto Cal Selected.
        self._auto_cal_queue: List[int] = []

        self._angle_labels: Dict[int, QLabel] = {}
        self._name_labels: Dict[int, QLabel] = {}
        self._demo_checks: Dict[int, QCheckBox] = {}
        self._invert_checks: Dict[int, QCheckBox] = {}
        self._row_widgets: Dict[int, List[QWidget]] = {m: [] for m in range(1, 6)}
        self._finger_buttons: List[QPushButton] = []
        self._grid: Optional[QGridLayout] = None

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(50)
        self._poll_timer.timeout.connect(self._on_poll)

        self._settings_save_timer = QTimer(self)
        self._settings_save_timer.setSingleShot(True)
        self._settings_save_timer.setInterval(300)
        self._settings_save_timer.timeout.connect(self._save_settings)
        self._settings_loading = False

        self._setup_ui()
        self._load_settings()
        self._apply_mode_ui()
        self._wire_settings_persistence()
        self.set_hand_orientation(True)
        self._update_connection_state()

    def _setup_ui(self):
        # Scroll rather than squeeze: word-wrapped labels make Qt under-count the
        # height, which otherwise compresses and clips the finger rows.
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        scroll.setWidget(content)
        outer.addWidget(scroll)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Hardware"))
        self._mode_combo = QComboBox()
        self._mode_combo.addItem("Push-pull", MODE_PUSH_PULL)
        self._mode_combo.addItem("Pull only", MODE_PULL_ONLY)
        self._mode_combo.setToolTip(
            "Pull only: motors can only open the fingers; closing is a release (idle)"
        )
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_row.addWidget(self._mode_combo)
        mode_row.addStretch()
        layout.addLayout(mode_row)

        self._info_label = QLabel(INFO_PUSH_PULL)
        self._info_label.setWordWrap(True)
        layout.addWidget(self._info_label)

        # --- Tunables ---
        tune = QGroupBox("Tunables")
        tune_layout = QVBoxLayout()
        tune.setLayout(tune_layout)
        tune_row = QHBoxLayout()
        speed_row_top = QHBoxLayout()
        tune_layout.addLayout(tune_row)
        tune_layout.addLayout(speed_row_top)

        tune_row.addWidget(QLabel("Plateau °"))
        self._plateau_spin = QDoubleSpinBox()
        self._plateau_spin.setRange(0.05, 5.0)
        self._plateau_spin.setDecimals(2)
        self._plateau_spin.setSingleStep(0.05)
        self._plateau_spin.setValue(0.3)
        self._plateau_spin.setToolTip("|Δangle| below this for hold time ⇒ plateau")
        tune_row.addWidget(self._plateau_spin)

        tune_row.addWidget(QLabel("Hold ms"))
        self._hold_spin = QSpinBox()
        self._hold_spin.setRange(100, 5000)
        self._hold_spin.setSingleStep(50)
        self._hold_spin.setValue(400)
        self._hold_spin.setToolTip("How long the plateau must hold")
        tune_row.addWidget(self._hold_spin)

        tune_row.addWidget(QLabel("Jog s"))
        self._jog_spin = QDoubleSpinBox()
        self._jog_spin.setRange(0.5, 10.0)
        self._jog_spin.setDecimals(1)
        self._jog_spin.setSingleStep(0.5)
        self._jog_spin.setValue(2.0)
        self._jog_spin.setToolTip("fwd/rev duration argument (seconds)")
        tune_row.addWidget(self._jog_spin)

        tune_row.addWidget(QLabel("Find A"))
        self._find_torque_spin = QDoubleSpinBox()
        self._find_torque_spin.setRange(0.05, 5.0)
        self._find_torque_spin.setDecimals(2)
        self._find_torque_spin.setSingleStep(0.05)
        self._find_torque_spin.setValue(DEFAULT_FIND_TORQUE_A)
        self._find_torque_spin.setToolTip(
            "torque N applied at the start of Find (raise if the finger stalls early)"
        )
        tune_row.addWidget(self._find_torque_spin)

        tune_row.addWidget(QLabel("After A"))
        self._restore_torque_spin = QDoubleSpinBox()
        self._restore_torque_spin.setRange(0.05, 10.0)
        self._restore_torque_spin.setDecimals(2)
        self._restore_torque_spin.setSingleStep(0.1)
        self._restore_torque_spin.setValue(DEFAULT_RESTORE_TORQUE_A)
        self._restore_torque_spin.setToolTip(
            "torque N restored when Find finishes, times out, or is stopped"
        )
        tune_row.addWidget(self._restore_torque_spin)

        tune_row.addWidget(QLabel("Margin %"))
        self._margin_spin = QDoubleSpinBox()
        self._margin_spin.setRange(0.0, 25.0)
        self._margin_spin.setDecimals(1)
        self._margin_spin.setSingleStep(1.0)
        self._margin_spin.setValue(5.0)
        self._margin_spin.setToolTip(
            "Host-side inset. Device keeps the full range; goto is limited to "
            "margin..1-margin so the motor never drives into the hard stops."
        )
        tune_row.addWidget(self._margin_spin)

        tune_row.addStretch()

        speed_row_top.addWidget(QLabel("Jog rad/s"))
        self._jog_speed_spin = QDoubleSpinBox()
        self._jog_speed_spin.setRange(0.0, FW_JOG_SPEED_RAD_S)
        self._jog_speed_spin.setDecimals(1)
        self._jog_speed_spin.setSingleStep(0.1)
        self._jog_speed_spin.setValue(0.0)
        self._jog_speed_spin.setSpecialValueText(f"full ({FW_JOG_SPEED_RAD_S:g})")
        self._jog_speed_spin.setToolTip(
            "Slow down Fwd/Rev jogs and Find (fwd/rev N secs speed), 0.1–2 rad/s. "
            "full = firmware default 2 rad/s. Slower makes Find gentler on the stops."
        )
        speed_row_top.addWidget(self._jog_speed_spin)

        speed_row_top.addWidget(QLabel("Move rad/s"))
        self._move_speed_spin = QDoubleSpinBox()
        self._move_speed_spin.setRange(0.0, FW_GOTO_SPEED_RAD_S)
        self._move_speed_spin.setDecimals(1)
        self._move_speed_spin.setSingleStep(0.1)
        self._move_speed_spin.setValue(0.0)
        self._move_speed_spin.setSpecialValueText(f"full ({FW_GOTO_SPEED_RAD_S:g})")
        self._move_speed_spin.setToolTip(
            "Slow down every goto (Open / Open All / Close All / Host Demo / margin park), "
            "0.1–3 rad/s. full = firmware default 3 rad/s. Firmware goto gives up after "
            "10 s, so very slow speeds over a long travel can stop short."
        )
        speed_row_top.addWidget(self._move_speed_spin)
        speed_row_top.addWidget(
            QLabel("(slow-down only — full speed is the firmware default)")
        )
        speed_row_top.addStretch()
        layout.addWidget(tune)

        # --- Finger grid ---
        grid_group = QGroupBox("Fingers (live encoder °)")
        grid_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)
        grid_group.setLayout(grid)
        self._grid = grid

        headers = [
            "Finger",
            "Angle °",
            "Auto Cal",
            "Open",
            "Jog",
            "Set",
            "Find",
            "Margin",
            "Inv",
            "Incl.",
        ]
        for col, text in enumerate(headers):
            hdr = QLabel(text)
            hdr.setAlignment(Qt.AlignCenter)
            grid.addWidget(hdr, 0, col)
            if text == "Margin":
                self._push_only_widgets.append(hdr)

        for ui_motor in range(1, 6):
            name = FINGER_NAMES[ui_motor - 1]
            dev = ui_to_device_motor(ui_motor)

            name_lbl = QLabel(f"{name} (M{dev})")
            self._name_labels[ui_motor] = name_lbl

            ang_lbl = QLabel("—")
            ang_lbl.setAlignment(Qt.AlignCenter)
            ang_lbl.setMinimumWidth(64)
            self._angle_labels[ui_motor] = ang_lbl

            fwd = _make_button("Fwd")
            fwd.clicked.connect(lambda _=False, m=ui_motor: self._jog(m, "fwd"))
            rev = _make_button("Rev")
            rev.clicked.connect(lambda _=False, m=ui_motor: self._jog(m, "rev"))
            idle = _make_button("Idle")
            idle.clicked.connect(lambda _=False, m=ui_motor: self._send_motor("idle", m))
            jog_wrap = self._hwrap(fwd, rev, idle)

            set_min = _make_button("Min", f"min {dev}")
            set_min.clicked.connect(lambda _=False, m=ui_motor: self._set_end(m, "min"))
            set_max = _make_button("Max", f"max {dev}")
            set_max.clicked.connect(lambda _=False, m=ui_motor: self._set_end(m, "max"))
            forget = _make_button(
                "Forget",
                f"cal clear {dev} — clear device min/max so Find can search full travel again",
            )
            forget.clicked.connect(lambda _=False, m=ui_motor: self._forget_ends(m))
            set_wrap = self._hwrap(set_min, set_max, forget)

            find_min = _make_button(
                "Find Min",
                "Jog rev until plateau, then min N",
            )
            find_min.clicked.connect(lambda _=False, m=ui_motor: self._start_find(m, "min"))
            find_max = _make_button(
                "Find Max",
                "Jog fwd until plateau, then max N",
            )
            find_max.clicked.connect(lambda _=False, m=ui_motor: self._start_find(m, "max"))
            find_wrap = self._hwrap(find_min, find_max)

            auto_btn = _make_button(
                "Auto Cal",
                "One click: find min, find max, then apply the margin for this finger",
            )
            auto_btn.setMinimumWidth(84)
            auto_btn.clicked.connect(
                lambda _=False, m=ui_motor: self._start_auto_calibrate(m)
            )

            demo_chk = QCheckBox("Incl.")
            demo_chk.setChecked(True)
            demo_chk.setToolTip(
                "Include in Auto Cal Selected and Host Demo"
            )
            self._demo_checks[ui_motor] = demo_chk

            inv_chk = QCheckBox("Inv")
            inv_chk.setChecked(is_fwd_rev_inverted(ui_motor))
            inv_chk.setToolTip(
                f"Swap Fwd/Rev for {name} everywhere (saved). "
                "Clears this finger's ends if set — re-run Auto Cal after."
            )
            inv_chk.toggled.connect(
                lambda checked, m=ui_motor: self._on_invert_toggled(m, checked)
            )
            self._invert_checks[ui_motor] = inv_chk

            margin_btn = _make_button(
                "Apply", "Record the margin for this finger and park at the inset min"
            )
            margin_btn.clicked.connect(lambda _=False, m=ui_motor: self._start_margin(m))

            self._push_only_widgets.extend([set_min, find_min, margin_btn])
            self._auto_buttons.append(auto_btn)

            open_btn = _make_button(
                "Open",
                f"Open {name} only (needs min+max this session; uses Multi A)",
            )
            open_btn.clicked.connect(lambda _=False, m=ui_motor: self._on_open_finger(m))

            self._row_widgets[ui_motor] = [
                name_lbl,
                ang_lbl,
                auto_btn,
                open_btn,
                jog_wrap,
                set_wrap,
                find_wrap,
                margin_btn,
                inv_chk,
                demo_chk,
            ]
            self._finger_buttons.extend(
                [
                    fwd,
                    rev,
                    idle,
                    set_min,
                    set_max,
                    forget,
                    find_min,
                    find_max,
                    margin_btn,
                    auto_btn,
                    open_btn,
                ]
            )

        layout.addWidget(grid_group)

        # --- Global ---
        actions = QHBoxLayout()
        self.stop_btn = _make_button("Stop", "idle all — abort find/demo/margin/batch")
        self.stop_btn.clicked.connect(self._on_stop)
        self.idle_all_btn = _make_button("Idle All", "idle")
        self.idle_all_btn.clicked.connect(lambda: self._send("idle"))
        actions.addWidget(self.stop_btn)
        actions.addWidget(self.idle_all_btn)
        actions.addStretch()
        layout.addLayout(actions)

        batch_group = QGroupBox("Batch modes")
        batch_layout = QVBoxLayout()
        batch_group.setLayout(batch_layout)
        self._batch_label = QLabel()
        self._batch_label.setWordWrap(True)
        batch_layout.addWidget(self._batch_label)

        multi_row = QHBoxLayout()
        multi_row.addWidget(QLabel("Multi A"))
        self._multi_torque_spin = QDoubleSpinBox()
        self._multi_torque_spin.setRange(0.05, 5.0)
        self._multi_torque_spin.setDecimals(2)
        self._multi_torque_spin.setSingleStep(0.05)
        self._multi_torque_spin.setValue(DEFAULT_MULTI_TORQUE_A)
        self._multi_torque_spin.setToolTip(
            "torque N applied to each finger during Open/Close All (keep low for peak current)"
        )
        multi_row.addWidget(self._multi_torque_spin)
        multi_row.addStretch()
        batch_layout.addLayout(multi_row)

        batch_btns = QHBoxLayout()
        self.auto_cal_sel_btn = _make_button(
            "Auto Cal Selected",
            "Run Auto Cal on each Incl. finger that does not already have ends",
        )
        self.auto_cal_sel_btn.clicked.connect(self._start_auto_cal_selected)
        self.open_all_btn = _make_button(
            "Open All",
            "goto inset-min on all calibrated fingers at once (Multi A)",
        )
        self.open_all_btn.clicked.connect(self._on_open_all)
        self.close_all_btn = _make_button(
            "Close All",
            "goto inset-max on all calibrated fingers at once (Multi A)",
        )
        self.close_all_btn.clicked.connect(lambda: self._start_chorus(1.0))
        self.release_all_btn = _make_button(
            "Release All",
            "idle all motors and restore After A — the passive return closes the fingers",
        )
        self.release_all_btn.clicked.connect(self._release_all)
        batch_btns.addWidget(self.auto_cal_sel_btn)
        batch_btns.addWidget(self.open_all_btn)
        batch_btns.addWidget(self.close_all_btn)
        batch_btns.addWidget(self.release_all_btn)
        batch_btns.addStretch()
        batch_layout.addLayout(batch_btns)
        layout.addWidget(batch_group)

        demo_group = QGroupBox("Host Demo (not device `demo`)")
        demo_layout = QVBoxLayout()
        demo_group.setLayout(demo_layout)
        self._demo_label = QLabel()
        self._demo_label.setWordWrap(True)
        demo_layout.addWidget(self._demo_label)

        speed_row = QHBoxLayout()
        speed_row.addWidget(QLabel("Settle ms"))
        self._dwell_spin = QSpinBox()
        self._dwell_spin.setRange(100, 8000)
        self._dwell_spin.setSingleStep(100)
        self._dwell_spin.setValue(400)
        self._dwell_spin.setToolTip(
            "Extra hold after the motor arrives at min/max before the next move "
            "(demo waits for the encoder, not a fixed travel time)"
        )
        speed_row.addWidget(self._dwell_spin)
        speed_row.addWidget(QLabel("Speed %"))
        self._speed_slider = QSlider(Qt.Horizontal)
        self._speed_slider.setMinimum(50)
        self._speed_slider.setMaximum(200)
        self._speed_slider.setValue(100)
        self._speed_label = QLabel("100%")
        self._speed_slider.valueChanged.connect(
            lambda v: self._speed_label.setText(f"{v}%")
        )
        speed_row.addWidget(self._speed_slider)
        speed_row.addWidget(self._speed_label)
        demo_layout.addLayout(speed_row)

        demo_btns = QHBoxLayout()
        self.host_demo_btn = _make_button("Run Host Demo")
        self.host_demo_btn.clicked.connect(self._start_host_demo)
        demo_btns.addWidget(self.host_demo_btn)
        demo_btns.addStretch()
        demo_layout.addLayout(demo_btns)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumHeight(140)
        demo_layout.addWidget(self._log)
        layout.addWidget(demo_group)

        self.status_label = QLabel("Status: Ready")
        layout.addWidget(self.status_label)

        self._global_buttons = [
            self.stop_btn,
            self.idle_all_btn,
            self.auto_cal_sel_btn,
            self.open_all_btn,
            self.close_all_btn,
            self.release_all_btn,
            self.host_demo_btn,
        ]

    # --- Hardware mode ---

    def _on_mode_changed(self, _index: int = 0):
        if self._busy:
            return
        self._pull_only = self._mode_combo.currentData() == MODE_PULL_ONLY
        self._apply_mode_ui()
        if not self._settings_loading:
            label = "Pull only" if self._pull_only else "Push-pull"
            self._append_log(f"Hardware mode: {label}")
            self._schedule_save_settings()

    def _apply_mode_ui(self):
        pull = self._pull_only
        self._info_label.setText(INFO_PULL_ONLY if pull else INFO_PUSH_PULL)
        for w in self._push_only_widgets:
            w.setVisible(not pull)
        self.close_all_btn.setVisible(not pull)
        self.release_all_btn.setVisible(pull)
        auto_tip = (
            "One click (finger relaxed/closed): mark min here, find max (open), record margin"
            if pull
            else "One click: find min, find max, then apply the margin for this finger"
        )
        for btn in self._auto_buttons:
            btn.setToolTip(auto_tip)
        if pull:
            self.open_all_btn.setToolTip(
                "goto inset-max (fully open) on all calibrated fingers at once (Multi A)"
            )
            self._batch_label.setText(
                "Auto Cal Selected: one included finger at a time (mark min → find max → margin).\n"
                "Open All: simultaneous goto to max (open) on every finger with both ends set "
                "this session. Release All idles every motor so the fingers close. Peak current "
                "scales with motor count — keep Multi A low and Stop if the bus browns out."
            )
            self._demo_label.setText(
                "One finger at a time, for each included finger with both ends set this "
                "session: open to max → wait until arrived → release (idle) → wait Settle ms."
            )
        else:
            self.open_all_btn.setToolTip(
                "goto inset-min on all calibrated fingers at once (Multi A)"
            )
            self._batch_label.setText(
                "Auto Cal Selected: one included finger at a time (find min → max → margin).\n"
                "Open/Close All: simultaneous goto on every finger that has both ends set this "
                "session. Peak current scales with motor count — Multi A is kept lower than "
                "normal; use a stout supply and Stop if the bus browns out."
            )
            self._demo_label.setText(
                "One finger at a time, for each included finger with both ends set "
                "this session: back to min → wait until arrived → out to max → "
                "wait until arrived → idle. Settle ms is a short pause after arrival."
            )

    def closeEvent(self, event):
        self._settings_save_timer.stop()
        self._save_settings()
        super().closeEvent(event)

    def _wire_settings_persistence(self):
        for spin in (
            self._plateau_spin,
            self._hold_spin,
            self._jog_spin,
            self._find_torque_spin,
            self._jog_speed_spin,
            self._move_speed_spin,
            self._restore_torque_spin,
            self._margin_spin,
            self._multi_torque_spin,
            self._dwell_spin,
        ):
            spin.valueChanged.connect(self._schedule_save_settings)
        self._speed_slider.valueChanged.connect(self._schedule_save_settings)
        for chk in self._demo_checks.values():
            chk.toggled.connect(self._schedule_save_settings)

    def _schedule_save_settings(self, *_args):
        if self._settings_loading:
            return
        self._settings_save_timer.start()

    def _settings_dict(self) -> dict:
        return {
            "plateau_deg": float(self._plateau_spin.value()),
            "hold_ms": int(self._hold_spin.value()),
            "jog_s": float(self._jog_spin.value()),
            "find_a": float(self._find_torque_spin.value()),
            "jog_speed": float(self._jog_speed_spin.value()),
            "move_speed": float(self._move_speed_spin.value()),
            "after_a": float(self._restore_torque_spin.value()),
            "margin_pct": float(self._margin_spin.value()),
            "multi_a": float(self._multi_torque_spin.value()),
            "settle_ms": int(self._dwell_spin.value()),
            "speed_pct": int(self._speed_slider.value()),
            "hardware_mode": MODE_PULL_ONLY if self._pull_only else MODE_PUSH_PULL,
            "include": [
                bool(self._demo_checks[m].isChecked()) for m in range(1, 6)
            ],
        }

    def _save_settings(self):
        try:
            SETTINGS_PATH.write_text(
                json.dumps(self._settings_dict(), indent=2) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            self._append_log(f"settings save failed: {exc}")

    def _load_settings(self):
        if not SETTINGS_PATH.exists():
            return
        try:
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            self._append_log(f"settings load failed: {exc}")
            return
        if not isinstance(data, dict):
            return

        self._settings_loading = True
        try:
            if "plateau_deg" in data:
                self._plateau_spin.setValue(float(data["plateau_deg"]))
            if "hold_ms" in data:
                self._hold_spin.setValue(int(data["hold_ms"]))
            if "jog_s" in data:
                self._jog_spin.setValue(float(data["jog_s"]))
            if "jog_speed" in data:
                self._jog_speed_spin.setValue(float(data["jog_speed"]))
            if "move_speed" in data:
                self._move_speed_spin.setValue(float(data["move_speed"]))
            if "find_a" in data:
                self._find_torque_spin.setValue(float(data["find_a"]))
            if "after_a" in data:
                self._restore_torque_spin.setValue(float(data["after_a"]))
            if "margin_pct" in data:
                self._margin_spin.setValue(float(data["margin_pct"]))
            if "multi_a" in data:
                self._multi_torque_spin.setValue(float(data["multi_a"]))
            if "settle_ms" in data:
                self._dwell_spin.setValue(int(data["settle_ms"]))
            if "speed_pct" in data:
                self._speed_slider.setValue(int(data["speed_pct"]))
            mode = data.get("hardware_mode")
            if mode in (MODE_PUSH_PULL, MODE_PULL_ONLY):
                idx = self._mode_combo.findData(mode)
                if idx >= 0:
                    self._mode_combo.setCurrentIndex(idx)
                self._pull_only = mode == MODE_PULL_ONLY
            include = data.get("include")
            if isinstance(include, list):
                for i, checked in enumerate(include[:5]):
                    chk = self._demo_checks.get(i + 1)
                    if chk is not None:
                        chk.setChecked(bool(checked))
        finally:
            self._settings_loading = False

    @staticmethod
    def _hwrap(*widgets) -> QWidget:
        wrap = QWidget()
        wrap.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        wrap.setMinimumHeight(ROW_HEIGHT)
        row = QHBoxLayout(wrap)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(4)
        for w in widgets:
            row.addWidget(w, 0, Qt.AlignVCenter)
        return wrap

    def set_hand_orientation(self, is_right_hand: bool):
        self._is_right_hand = bool(is_right_hand)
        if self._grid is None:
            return
        for ui_motor in range(1, 6):
            for w in self._row_widgets[ui_motor]:
                self._grid.removeWidget(w)
        for display_row, (ui_motor, name) in enumerate(
            display_motor_order(self._is_right_hand), start=1
        ):
            dev = ui_to_device_motor(ui_motor)
            lbl = self._name_labels.get(ui_motor)
            if lbl:
                lbl.setText(f"{name} (M{dev})")
            self._grid.setRowMinimumHeight(display_row, ROW_HEIGHT)
            for col, w in enumerate(self._row_widgets[ui_motor]):
                self._grid.addWidget(w, display_row, col, Qt.AlignVCenter)

    def set_reader(self, reader):
        self._reader = reader
        self._update_connection_state()

    def _update_connection_state(self):
        ok = self._reader is not None and self._reader.is_connected()
        for btn in self._finger_buttons:
            btn.setEnabled(ok and not self._busy)
        for btn in self._global_buttons:
            # Stop always enabled when connected so user can abort.
            if btn is self.stop_btn:
                btn.setEnabled(ok)
            else:
                btn.setEnabled(ok and not self._busy)
        self._mode_combo.setEnabled(not self._busy)
        for chk in self._invert_checks.values():
            chk.setEnabled(not self._busy)
        if not self._busy:
            self.status_label.setText(
                "Status: Ready" if ok else "Status: Not connected"
            )

    def update_angles(self, device_angles: List[float]):
        """device_angles: M1..M5 (Thumb..Pinky) from values angles."""
        if not device_angles or len(device_angles) < 5:
            return
        self._device_angles = list(device_angles[:5])
        for ui_motor in range(1, 6):
            lbl = self._angle_labels.get(ui_motor)
            if not lbl:
                continue
            dev_i = ui_to_device_motor(ui_motor) - 1
            lbl.setText(FlexParser.format_float(self._device_angles[dev_i], 1))

    def _ui_angle(self, ui_motor: int) -> float:
        dev_i = ui_to_device_motor(ui_motor) - 1
        return self._device_angles[dev_i]

    def _pos(self, ui_motor: int, frac: float) -> float:
        """Map 0..1 of usable travel into the device's 0..1, honouring the margin."""
        margin = self._margin_frac[ui_motor]
        lo, hi = margin, 1.0 - margin
        if hi <= lo:
            return 0.5
        frac = max(0.0, min(1.0, frac))
        return lo + (hi - lo) * frac

    def _open_close_frac(self, ui_motor: int, usable_frac: float) -> float:
        """
        Map UI open(0)/close(1) to a device goto fraction (with margin).

        Inverted motors (Inv checkbox) have their mechanical sense reversed
        relative to the other fingers: Find Min (jog rev) still matches the Rev
        button, but that end is the opposite open/close pose from Thumb/etc.
        Flip here so Open/Close All and Host Demo match the hand.
        """
        return self._pos(ui_motor, self._axis_frac(ui_motor, usable_frac))

    def _axis_frac(self, ui_motor: int, usable_frac: float) -> float:
        # Pull-only defines max as fully open for every finger, so no per-motor flip.
        frac = max(0.0, min(1.0, float(usable_frac)))
        if not self._pull_only and is_fwd_rev_inverted(ui_motor):
            frac = 1.0 - frac
        return frac

    def _record_end_angle(self, ui_motor: int, which: str, angle: float):
        if which == "min":
            self._has_min[ui_motor] = True
            self._end_angle_min[ui_motor] = float(angle)
        else:
            self._has_max[ui_motor] = True
            self._end_angle_max[ui_motor] = float(angle)

    def _target_angle(self, ui_motor: int, usable_frac: float) -> Optional[float]:
        """Expected encoder ° for open(0)/close(1) after margin (and axis flip)."""
        a0 = self._end_angle_min[ui_motor]
        a1 = self._end_angle_max[ui_motor]
        if math.isnan(a0) or math.isnan(a1):
            return None
        frac = self._axis_frac(ui_motor, usable_frac)
        # Device fraction after margin, then interpolate host-captured end angles.
        return a0 + (a1 - a0) * self._pos(ui_motor, frac)

    def _ends_locked(self, ui_motor: int) -> bool:
        """
        Both ends known on the device, so its soft endstops clamp velocity jogs
        inside the current range and a Find pass cannot widen it.
        """
        return self._has_min[ui_motor] and self._has_max[ui_motor]

    def _reject_locked(self, ui_motor: int) -> bool:
        if not self._ends_locked(ui_motor):
            return False
        name = FINGER_NAMES[ui_motor - 1]
        self._append_log(
            f"{name}: ends already set — the device clamps jogs to the current "
            "range, so Find cannot widen it. Press Forget (cal clear) on this row."
        )
        self.status_label.setText(
            "Status: Ends already set — press Forget to clear"
        )
        return True

    def _on_invert_toggled(self, ui_motor: int, inverted: bool):
        if inverted == is_fwd_rev_inverted(ui_motor):
            return
        set_fwd_rev_inverted(ui_motor, inverted)
        name = FINGER_NAMES[ui_motor - 1]
        state = "inverted" if inverted else "normal"
        self._append_log(f"{name}: Fwd/Rev {state}")
        if self._has_min[ui_motor] or self._has_max[ui_motor]:
            # Ends were found in the old direction; they'd be backwards now.
            self._append_log(f"{name}: clearing ends — re-run Auto Cal")
            self._forget_ends(ui_motor)
        self.invert_changed.emit()

    def _forget_ends(self, ui_motor: int):
        """Clear device min/max via cal clear N, then host-side tracking."""
        name = FINGER_NAMES[ui_motor - 1]
        dev = ui_to_device_motor(ui_motor)
        if not self._send(f"cal clear {dev}"):
            return
        self._has_min[ui_motor] = False
        self._has_max[ui_motor] = False
        self._end_angle_min[ui_motor] = float("nan")
        self._end_angle_max[ui_motor] = float("nan")
        self._margin_frac[ui_motor] = 0.0
        self._append_log(f"{name}: cal clear {dev} — ends forgotten")
        self.status_label.setText(f"Status: {name} ends cleared")

    def _send(self, command: str) -> bool:
        if not self._reader or not self._reader.is_connected():
            self.status_label.setText("Status: Not connected")
            return False
        cmd = command if command.endswith("\n") else command + "\n"
        ok = bool(self._reader.write(cmd))
        if ok:
            display = cmd.strip()
            if len(display) > 60:
                display = display[:57] + "..."
            self.status_label.setText(f"Status: Sent — {display}")
        else:
            self.status_label.setText("Status: Failed to send command")
        return ok

    def _send_motor(self, verb: str, ui_motor: int, extra: str = "") -> bool:
        verb = normalize_fwd_rev(verb, ui_motor)
        dev = ui_to_device_motor(ui_motor)
        if extra:
            return self._send(f"{verb} {dev} {extra}")
        return self._send(f"{verb} {dev}")

    def _idle_all(self) -> bool:
        """Coast every motor — use whenever nothing should be holding/moving."""
        return self._send("idle")

    def _jog_args(self) -> str:
        """`seconds [speed]` for fwd/rev; speed is positional so seconds always goes first."""
        secs = float(self._jog_spin.value())
        speed = float(self._jog_speed_spin.value())
        if 0 < speed < FW_JOG_SPEED_RAD_S:
            return f"{secs:.1f} {speed:.2f}"
        return f"{secs:.1f}"

    def _send_goto(self, ui_motor: int, pos: float) -> bool:
        cmd = f"goto {ui_to_device_motor(ui_motor)} {pos:.3f}"
        speed = float(self._move_speed_spin.value())
        if 0 < speed < FW_GOTO_SPEED_RAD_S:
            cmd += f" {speed:.2f}"
        return self._send(cmd)

    def _jog(self, ui_motor: int, direction: str):
        self._send_motor(direction, ui_motor, self._jog_args())

    def _set_end(self, ui_motor: int, which: str):
        self._send_motor(which, ui_motor)
        angle = self._ui_angle(ui_motor)
        self._record_end_angle(ui_motor, which, angle)
        name = FINGER_NAMES[ui_motor - 1]
        angle_s = FlexParser.format_float(angle, 1)
        self._append_log(f"{name}: set {which} @ {angle_s}°")

    def _append_log(self, line: str):
        self._log.append(line)

    def _set_busy(self, busy: bool):
        self._busy = busy
        self._update_connection_state()
        if busy:
            if not self._poll_timer.isActive():
                self._poll_timer.start()
        elif (
            not self._find_state
            and not self._demo_state
            and not self._margin_state
            and not self._chorus_state
        ):
            self._poll_timer.stop()

    def _on_stop(self):
        self._stop_requested = True
        self._restore_find_torque()
        self._restore_multi_torque()
        self._send("idle")
        self._find_state = None
        self._demo_state = None
        self._margin_state = None
        self._chorus_state = None
        self._sequence = None
        self._sequence_motor = None
        self._auto_cal_queue = []
        self._set_busy(False)
        self._stop_requested = False
        self.status_label.setText("Status: Stopped — idle")
        self._append_log("Stopped")

    # --- Step chaining ---

    def _finish_step(self, status: str):
        """
        End the current step. If an Auto Cal run has steps left, continue it;
        otherwise start the next finger in Auto Cal Selected, or release the panel.
        """
        if self._sequence:
            self._run_next_sequence_step()
            return
        if self._sequence is not None and self._sequence_motor is not None:
            name = FINGER_NAMES[self._sequence_motor - 1]
            self._append_log(f"{name}: auto cal done")
            status = f"{name} auto cal done"
        self._sequence = None
        self._sequence_motor = None
        self._idle_all()

        if self._auto_cal_queue:
            self.status_label.setText(f"Status: {status}")
            next_m = self._auto_cal_queue.pop(0)
            self._begin_auto_calibrate(next_m)
            return

        self._set_busy(False)
        self.status_label.setText(f"Status: {status}")

    def _start_auto_calibrate(self, ui_motor: int):
        """One click per finger: find min, find max, then apply the margin."""
        if self._busy:
            self.status_label.setText("Status: Busy — Stop first")
            return
        if self._reject_locked(ui_motor):
            return
        self._auto_cal_queue = []
        self._stop_requested = False
        self._idle_all()
        self._set_busy(True)
        self._begin_auto_calibrate(ui_motor)

    def _begin_auto_calibrate(self, ui_motor: int):
        """Start (or continue) Auto Cal for one finger while already busy."""
        name = FINGER_NAMES[ui_motor - 1]
        if self._pull_only:
            self._sequence = ["mark_min", "find_max", "margin"]
            self._append_log(
                f"{name}: auto cal (pull only) — mark min at relaxed pose, find max, margin"
            )
        else:
            self._sequence = ["find_min", "find_max", "margin"]
            self._append_log(f"{name}: auto cal — find min, find max, margin")
        self._sequence_motor = ui_motor
        self._run_next_sequence_step()

    def _start_auto_cal_selected(self):
        """Sequential Auto Cal for every Incl. finger that still needs ends."""
        if self._busy:
            self.status_label.setText("Status: Busy — Stop first")
            return
        queue: List[int] = []
        for ui_motor in range(1, 6):
            chk = self._demo_checks.get(ui_motor)
            if not chk or not chk.isChecked():
                continue
            if self._ends_locked(ui_motor):
                name = FINGER_NAMES[ui_motor - 1]
                self._append_log(
                    f"{name}: skipped (ends already set — Forget to re-find)"
                )
                continue
            queue.append(ui_motor)
        if not queue:
            self.status_label.setText(
                "Status: No Incl. fingers need Auto Cal (or all already have ends)"
            )
            return
        self._stop_requested = False
        self._auto_cal_queue = queue[1:]
        self._idle_all()
        self._set_busy(True)
        names = ", ".join(FINGER_NAMES[m - 1] for m in queue)
        self._append_log(f"Auto Cal Selected: {names}")
        self._begin_auto_calibrate(queue[0])

    def _run_next_sequence_step(self):
        if not self._sequence:
            self._finish_step("done")
            return
        step = self._sequence.pop(0)
        ui_motor = self._sequence_motor
        # Coast everything between steps so only the next jog/goto is active.
        self._idle_all()
        if step == "mark_min":
            self._mark_min_here(ui_motor)
        elif step == "find_min":
            self._begin_find(ui_motor, "min")
        elif step == "find_max":
            self._begin_find(ui_motor, "max")
        elif step == "margin":
            self._begin_margin(ui_motor)

    def _mark_min_here(self, ui_motor: int):
        """Pull-only: the relaxed pose is the closed end; mark it so goto can work."""
        name = FINGER_NAMES[ui_motor - 1]
        angle = self._ui_angle(ui_motor)
        self._send_motor("min", ui_motor)
        self._record_end_angle(ui_motor, "min", angle)
        angle_s = FlexParser.format_float(angle, 1)
        self._append_log(f"{name}: min (relaxed/closed) @ {angle_s}°")
        if math.isnan(angle):
            self._append_log(
                f"{name}: no encoder angle yet — Open All arrival checks will time out"
            )
        self._finish_step(f"{name} min set")

    # --- Find Min / Max (plateau) ---

    def _apply_find_torque(self, ui_motor: int):
        amps = float(self._find_torque_spin.value())
        dev = ui_to_device_motor(ui_motor)
        self._send(f"torque {dev} {amps:.3f}")
        self._find_torque_motor = ui_motor
        name = FINGER_NAMES[ui_motor - 1]
        self._append_log(f"{name}: find torque {amps:.2f} A")

    def _restore_find_torque(self, ui_motor: Optional[int] = None):
        m = ui_motor if ui_motor is not None else self._find_torque_motor
        if m is None:
            return
        amps = float(self._restore_torque_spin.value())
        dev = ui_to_device_motor(m)
        self._send(f"torque {dev} {amps:.3f}")
        name = FINGER_NAMES[m - 1]
        self._append_log(f"{name}: restore torque {amps:.2f} A")
        if self._find_torque_motor == m:
            self._find_torque_motor = None

    def _start_find(self, ui_motor: int, which: str):
        if self._busy:
            self.status_label.setText("Status: Busy — Stop first")
            return
        if self._reject_locked(ui_motor):
            return
        self._stop_requested = False
        self._sequence = None
        self._sequence_motor = None
        self._idle_all()
        self._set_busy(True)
        self._begin_find(ui_motor, which)

    def _begin_find(self, ui_motor: int, which: str):
        direction = "fwd" if which == "max" else "rev"
        self._find_state = {
            "ui_motor": ui_motor,
            "which": which,
            "direction": direction,
            "last_angle": None,
            "plateau_since": None,
            "last_jog_at": 0.0,
            "started": time.monotonic(),
        }
        name = FINGER_NAMES[ui_motor - 1]
        self.status_label.setText(f"Status: Finding {which} — {name}")
        self._append_log(f"{name}: find {which} (jog {direction})")
        self._apply_find_torque(ui_motor)
        self._find_jog_burst()

    def _find_jog_burst(self):
        st = self._find_state
        if not st:
            return
        self._send_motor(st["direction"], st["ui_motor"], self._jog_args())
        st["last_jog_at"] = time.monotonic()

    def _on_poll(self):
        if self._stop_requested:
            return
        if self._find_state:
            self._poll_find()
        elif self._margin_state:
            self._poll_margin()
        elif self._chorus_state:
            self._poll_chorus()
        elif self._demo_state:
            self._poll_demo()

    def _poll_find(self):
        st = self._find_state
        if not st:
            return
        ui_motor = st["ui_motor"]
        name = FINGER_NAMES[ui_motor - 1]
        now = time.monotonic()

        # Without this, a motor that never reports an angle would stall the run.
        if now - st["started"] >= FIND_TIMEOUT_S:
            self._idle_all()
            self._restore_find_torque(ui_motor)
            self._append_log(
                f"{name}: find {st['which']} timed out after {FIND_TIMEOUT_S:.0f}s "
                "— no plateau (check encoder / angles stream)"
            )
            self._find_state = None
            self._sequence = None
            self._sequence_motor = None
            self._auto_cal_queue = []
            self._set_busy(False)
            self.status_label.setText(f"Status: {name} find {st['which']} timed out")
            return

        angle = self._ui_angle(ui_motor)
        if math.isnan(angle):
            return

        thresh = float(self._plateau_spin.value())
        hold_s = float(self._hold_spin.value()) / 1000.0
        jog_s = float(self._jog_spin.value())

        last = st["last_angle"]
        if last is None:
            st["last_angle"] = angle
            st["plateau_since"] = None
            return

        delta = abs(angle - last)
        st["last_angle"] = angle

        if delta < thresh:
            if st["plateau_since"] is None:
                st["plateau_since"] = now
            elif now - st["plateau_since"] >= hold_s:
                which = st["which"]
                self._send_motor("idle", ui_motor)
                self._send_motor(which, ui_motor)
                self._record_end_angle(ui_motor, which, angle)
                self._append_log(
                    f"{name}: plateau → {which} @ {angle:.1f}° (Δ={delta:.2f})"
                )
                self._restore_find_torque(ui_motor)
                self._find_state = None
                self._finish_step(f"{name} {which} set")
                return
        else:
            st["plateau_since"] = None

        if now - st["last_jog_at"] >= max(0.4, jog_s * 0.75):
            self._find_jog_burst()

    # --- Margin ---

    def _start_margin(self, ui_motor: int):
        if self._busy:
            self.status_label.setText("Status: Busy — Stop first")
            return
        if not (self._has_min[ui_motor] and self._has_max[ui_motor]):
            self.status_label.setText("Status: Set both min and max first")
            return
        self._stop_requested = False
        self._sequence = None
        self._sequence_motor = None
        self._idle_all()
        self._set_busy(True)
        self._begin_margin(ui_motor)

    def _begin_margin(self, ui_motor: int):
        """
        Record the margin and park at the inset open pose. The device keeps the
        full discovered range; the host just stops commanding the last few percent.
        """
        name = FINGER_NAMES[ui_motor - 1]
        margin = float(self._margin_spin.value()) / 100.0
        self._margin_frac[ui_motor] = margin
        if self._pull_only:
            # Relaxed pose is already the closed end; nothing to park.
            self._append_log(
                f"{name}: margin {margin * 100:.1f}% — Open All stops at {1.0 - margin:.2f}"
            )
            self._finish_step(f"{name} margin set")
            return
        if margin <= 0:
            self._append_log(f"{name}: margin 0% — using full travel")
            self._finish_step(f"{name} margin 0%")
            return
        self._margin_state = {
            "ui_motor": ui_motor,
            "started": time.monotonic(),
            "dwell_s": 1.5,
        }
        self.status_label.setText(f"Status: Applying margin — {name}")
        self._append_log(
            f"{name}: margin {margin * 100:.1f}% — goto limited to "
            f"{margin:.2f}–{1.0 - margin:.2f}"
        )
        self._send_goto(ui_motor, self._open_close_frac(ui_motor, 0.0))

    def _poll_margin(self):
        st = self._margin_state
        if not st:
            return
        if time.monotonic() - st["started"] < st["dwell_s"]:
            return
        ui_motor = st["ui_motor"]
        self._send_motor("idle", ui_motor)
        name = FINGER_NAMES[ui_motor - 1]
        self._append_log(f"{name}: parked at inset open")
        self._margin_state = None
        self._finish_step(f"{name} margin set")

    # --- Host Demo ---

    def _demo_settle_s(self) -> float:
        base = float(self._dwell_spin.value())
        speed = max(50, int(self._speed_slider.value()))
        return (base * 100.0 / speed) / 1000.0

    def _start_host_demo(self):
        if self._busy:
            self.status_label.setText("Status: Busy — Stop first")
            return
        queue: List[int] = []
        for ui_motor in range(1, 6):
            chk = self._demo_checks.get(ui_motor)
            if chk and chk.isChecked():
                if self._has_min[ui_motor] and self._has_max[ui_motor]:
                    queue.append(ui_motor)
                else:
                    name = FINGER_NAMES[ui_motor - 1]
                    self._append_log(f"{name}: skipped (need min+max this session)")
        if not queue:
            self.status_label.setText("Status: No fingers ready for Host Demo")
            return
        self._stop_requested = False
        self._demo_state = {
            "queue": queue,
            "ui_motor": None,
            "phase": "next",
            "phase_started": time.monotonic(),
            "target_angle": None,
            "arrived_at": None,
            "usable_frac": None,
            "idled_on_arrive": False,
        }
        self._idle_all()
        self._set_busy(True)
        self._append_log("Host Demo start")
        self._advance_demo(force=True)

    def _demo_phase_ready(self, st: dict, force: bool) -> bool:
        """True when we may leave the current to_min / to_max move."""
        if force:
            return True
        now = time.monotonic()
        elapsed = now - st["phase_started"]
        settle = self._demo_settle_s()
        target = st.get("target_angle")
        ui_motor = st["ui_motor"]
        angle = self._ui_angle(ui_motor) if ui_motor else float("nan")

        if target is not None and not math.isnan(angle):
            if abs(angle - target) <= DEMO_ARRIVE_DEG:
                if st.get("arrived_at") is None:
                    st["arrived_at"] = now
                    # Drop FOC hold while parked so the motor coasts at the end.
                    # Pull-only holds open through settle; the release phase idles.
                    if not st.get("idled_on_arrive") and not self._pull_only:
                        self._idle_all()
                        st["idled_on_arrive"] = True
                if now - st["arrived_at"] >= settle:
                    return True
            else:
                st["arrived_at"] = None
                st["idled_on_arrive"] = False
            if elapsed >= DEMO_GOTO_TIMEOUT_S:
                name = FINGER_NAMES[ui_motor - 1]
                self._append_log(
                    f"{name}: goto timeout after {DEMO_GOTO_TIMEOUT_S:.0f}s "
                    f"(at {angle:.1f}°, target {target:.1f}°) — continuing"
                )
                self._idle_all()
                return True
            return False

        # No stored end angles — fall back to settle-as-dwell only.
        return elapsed >= max(settle, 2.0)

    def _advance_demo(self, force: bool = False):
        st = self._demo_state
        if not st:
            return

        phase = st["phase"]
        ui_motor = st["ui_motor"]

        if phase in ("to_min", "to_max") and not self._demo_phase_ready(st, force):
            return

        now = time.monotonic()

        if phase == "release":
            # Pull-only: give the passive return time to close the finger.
            if now - st["phase_started"] < max(self._demo_settle_s(), 1.0):
                return
            st["phase"] = "next"
            st["ui_motor"] = None
            return

        if phase == "next":
            if not st["queue"]:
                self._demo_state = None
                self._idle_all()
                self._set_busy(False)
                self.status_label.setText("Status: Host Demo done")
                self._append_log("Host Demo done")
                return
            ui_motor = st["queue"].pop(0)
            st["ui_motor"] = ui_motor
            if self._pull_only:
                st["phase"] = "to_max"
                st["phase_started"] = now
                st["arrived_at"] = None
                st["idled_on_arrive"] = False
                st["usable_frac"] = 1.0
                st["target_angle"] = self._target_angle(ui_motor, 1.0)
                name = FINGER_NAMES[ui_motor - 1]
                pos = self._open_close_frac(ui_motor, 1.0)
                tgt = st["target_angle"]
                tgt_s = FlexParser.format_float(tgt, 1) if tgt is not None else "?"
                self._append_log(f"{name}: open — goto {pos:.3f} (target {tgt_s}°)")
                self._send_goto(ui_motor, pos)
                return
            st["phase"] = "to_min"
            st["phase_started"] = now
            st["arrived_at"] = None
            st["idled_on_arrive"] = False
            st["usable_frac"] = 0.0
            st["target_angle"] = self._target_angle(ui_motor, 0.0)
            name = FINGER_NAMES[ui_motor - 1]
            ang_s = FlexParser.format_float(self._ui_angle(ui_motor), 1)
            pos = self._open_close_frac(ui_motor, 0.0)
            tgt = st["target_angle"]
            tgt_s = FlexParser.format_float(tgt, 1) if tgt is not None else "?"
            self._append_log(
                f"{name}: back to min — goto {pos:.3f} "
                f"(now {ang_s}°, target {tgt_s}°)"
            )
            self._send_goto(ui_motor, pos)
            return

        if phase == "to_min":
            name = FINGER_NAMES[ui_motor - 1]
            ang_s = FlexParser.format_float(self._ui_angle(ui_motor), 1)
            self._append_log(f"{name}: at min ({ang_s}°) — going to max")
            st["phase"] = "to_max"
            st["phase_started"] = now
            st["arrived_at"] = None
            st["idled_on_arrive"] = False
            st["usable_frac"] = 1.0
            st["target_angle"] = self._target_angle(ui_motor, 1.0)
            pos = self._open_close_frac(ui_motor, 1.0)
            tgt = st["target_angle"]
            tgt_s = FlexParser.format_float(tgt, 1) if tgt is not None else "?"
            self._append_log(
                f"{name}: out to max — goto {pos:.3f} (target {tgt_s}°)"
            )
            self._send_goto(ui_motor, pos)
            return

        if phase == "to_max" and self._pull_only:
            self._idle_all()
            name = FINGER_NAMES[ui_motor - 1]
            ang_s = FlexParser.format_float(self._ui_angle(ui_motor), 1)
            self._append_log(f"{name}: open ({ang_s}°) — release")
            st["phase"] = "release"
            st["phase_started"] = now
            st["target_angle"] = None
            st["arrived_at"] = None
            st["idled_on_arrive"] = False
            return

        if phase == "to_max":
            self._idle_all()
            name = FINGER_NAMES[ui_motor - 1]
            ang_s = FlexParser.format_float(self._ui_angle(ui_motor), 1)
            self._append_log(f"{name}: at max ({ang_s}°) — idle")
            st["phase"] = "next"
            st["phase_started"] = now
            st["ui_motor"] = None
            st["target_angle"] = None
            st["arrived_at"] = None
            st["idled_on_arrive"] = False
            return

    def _poll_demo(self):
        self._advance_demo(force=False)

    # --- Open / Close All (simultaneous goto) ---

    def _apply_multi_torque(self, motors: List[int]):
        amps = float(self._multi_torque_spin.value())
        self._multi_torque_motors = list(motors)
        for ui_motor in motors:
            dev = ui_to_device_motor(ui_motor)
            self._send(f"torque {dev} {amps:.3f}")
        self._append_log(
            f"multi torque {amps:.2f} A on "
            + ", ".join(FINGER_NAMES[m - 1] for m in motors)
        )

    def _restore_multi_torque(self):
        if not self._multi_torque_motors:
            return
        amps = float(self._restore_torque_spin.value())
        for ui_motor in self._multi_torque_motors:
            dev = ui_to_device_motor(ui_motor)
            self._send(f"torque {dev} {amps:.3f}")
        self._append_log(f"restore torque {amps:.2f} A after Open/Close All")
        self._multi_torque_motors = []

    def _on_open_all(self):
        # Push-pull open is the min end; pull-only defines max as fully open.
        self._start_chorus(1.0 if self._pull_only else 0.0)

    def _release_all(self):
        """Pull-only close: drop drive so the passive return closes the fingers."""
        if self._busy:
            self.status_label.setText("Status: Busy — Stop first")
            return
        self._idle_all()
        self._restore_multi_torque()
        self._append_log("Release All — idle (passive return closes fingers)")
        self.status_label.setText("Status: Released — idle")

    def _on_open_finger(self, ui_motor: int):
        self._start_chorus(1.0 if self._pull_only else 0.0, only=[ui_motor])

    def _start_chorus(self, usable_frac: float, only: Optional[List[int]] = None):
        """
        Move every finger (or just `only`) that has both ends this session to
        inset-min (0.0) or inset-max (1.0) at once. Uses Multi A to limit peak current.
        """
        if self._busy:
            self.status_label.setText("Status: Busy — Stop first")
            return
        candidates = only if only is not None else list(range(1, 6))
        motors: List[int] = []
        for ui_motor in candidates:
            if self._has_min[ui_motor] and self._has_max[ui_motor]:
                motors.append(ui_motor)
            else:
                name = FINGER_NAMES[ui_motor - 1]
                hint = " — run Auto Cal" if self._pull_only else ""
                self._append_log(f"{name}: skipped (need min+max this session{hint})")
        if not motors:
            self.status_label.setText("Status: No fingers ready to move")
            return

        if self._pull_only:
            opening = usable_frac >= 1.0
        else:
            opening = usable_frac <= 0.0
        verb = "Open" if opening else "Close"
        if only is not None and len(motors) == 1:
            label = f"{verb} {FINGER_NAMES[motors[0] - 1]}"
        else:
            label = f"{verb} All"
        targets: Dict[int, Optional[float]] = {}
        for ui_motor in motors:
            targets[ui_motor] = self._target_angle(ui_motor, usable_frac)

        self._stop_requested = False
        self._auto_cal_queue = []
        self._idle_all()
        self._apply_multi_torque(motors)
        for ui_motor in motors:
            pos = self._open_close_frac(ui_motor, usable_frac)
            self._send_goto(ui_motor, pos)

        self._chorus_state = {
            "label": label,
            "motors": motors,
            "usable_frac": usable_frac,
            "targets": targets,
            "started": time.monotonic(),
            "arrived_at": None,
            "idled": False,
        }
        self._set_busy(True)
        names = ", ".join(FINGER_NAMES[m - 1] for m in motors)
        multi_a = float(self._multi_torque_spin.value())
        self._append_log(
            f"{label}: {names} @ Multi A={multi_a:.2f} "
            f"(peak current ≈ N×A — watch the supply)"
        )
        self.status_label.setText(f"Status: {label} — {len(motors)} fingers")

    def _poll_chorus(self):
        st = self._chorus_state
        if not st:
            return
        now = time.monotonic()
        motors = st["motors"]
        targets = st["targets"]
        settle = self._demo_settle_s()

        all_arrived = True
        for ui_motor in motors:
            target = targets.get(ui_motor)
            angle = self._ui_angle(ui_motor)
            if target is None or math.isnan(angle):
                all_arrived = False
                continue
            if abs(angle - target) > DEMO_ARRIVE_DEG:
                all_arrived = False

        if all_arrived:
            if self._pull_only:
                # Idling would let the passive return close the hand; keep holding
                # open at Multi A until Release All / Stop.
                self._chorus_state = None
                self._set_busy(False)
                self.status_label.setText(f"Status: {st['label']} — holding open")
                how = "Release All" if len(st["motors"]) > 1 else "Idle or Release All"
                self._append_log(f"{st['label']} done — holding; {how} to close")
                return
            if st["arrived_at"] is None:
                st["arrived_at"] = now
                if not st["idled"]:
                    self._idle_all()
                    st["idled"] = True
            elif now - st["arrived_at"] >= settle:
                self._restore_multi_torque()
                self._chorus_state = None
                self._set_busy(False)
                self.status_label.setText(f"Status: {st['label']} done")
                self._append_log(f"{st['label']} done")
            return

        st["arrived_at"] = None
        if now - st["started"] >= CHORUS_TIMEOUT_S:
            self._idle_all()
            self._restore_multi_torque()
            self._append_log(
                f"{st['label']}: timed out after {CHORUS_TIMEOUT_S:.0f}s — idle"
            )
            self._chorus_state = None
            self._set_busy(False)
            self.status_label.setText(f"Status: {st['label']} timed out")
