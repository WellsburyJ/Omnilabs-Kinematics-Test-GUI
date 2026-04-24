"""
Embedded accel bars widget for live IMU acceleration visualization.
"""

from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt


class AccelBarsWidget(QGroupBox):
    """Small embedded widget showing accel X/Y/Z bars in g."""

    MIN_G = -2.0
    MAX_G = 2.0

    def __init__(self, parent=None, reader=None):
        super().__init__("Accel (g)", parent)
        self._reader = reader
        self.setMinimumWidth(280)
        self.setMaximumWidth(320)

        layout = QVBoxLayout()
        self.setLayout(layout)

        grid = QGridLayout()
        layout.addLayout(grid)

        self._bars = {}
        self._value_labels = {}

        for row, axis in enumerate(("X", "Y", "Z")):
            name = QLabel(f"{axis}:")
            bar = QProgressBar()
            bar.setRange(0, 400)  # maps -2g..+2g to 0..400
            bar.setValue(200)     # center at 0g
            bar.setTextVisible(False)
            value = QLabel("0.000 g")
            value.setMinimumWidth(68)
            value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self._bars[axis] = bar
            self._value_labels[axis] = value

            grid.addWidget(name, row, 0)
            grid.addWidget(bar, row, 1)
            grid.addWidget(value, row, 2)

        self._status_label = QLabel("Status: Not connected")
        layout.addWidget(self._status_label)

        self.set_reader(reader)

    def set_reader(self, reader):
        """Update connection source and enable/disable bars."""
        self._reader = reader
        connected = bool(reader and reader.is_connected())
        for axis in ("X", "Y", "Z"):
            self._bars[axis].setEnabled(connected)
        self._status_label.setText("Status: Ready" if connected else "Status: Not connected")

    def _to_bar_value(self, g_value: float) -> int:
        clamped = max(self.MIN_G, min(self.MAX_G, g_value))
        normalized = (clamped - self.MIN_G) / (self.MAX_G - self.MIN_G)  # 0..1
        return int(round(normalized * 400))

    def set_accel_values(self, ax: float, ay: float, az: float):
        """Update bar positions and labels from accel values in g."""
        values = {"X": ax, "Y": ay, "Z": az}
        for axis, value in values.items():
            self._bars[axis].setValue(self._to_bar_value(value))
            self._value_labels[axis].setText(f"{value:.3f} g")
