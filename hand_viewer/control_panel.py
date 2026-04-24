"""
Control panel for pumps and valves.
Allows controlling pressure/vacuum valves and pump speeds for each finger.
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
                                QLabel, QCheckBox, QSlider, QPushButton, QGroupBox)
from PySide6.QtCore import Qt, Signal, QObject
from typing import Optional


def finger_segment(vacuum: bool, pressure: bool, speed_slider: int) -> str:
    """
    Encode one finger for a 'set outputs' command: valve letter + pump digit (0,3,6,9).
    speed_slider is 0-3 like the control panel sliders.
    """
    if not vacuum and not pressure:
        state = "O"
    elif not vacuum and pressure:
        state = "P"
    elif vacuum and not pressure:
        state = "V"
    else:
        state = "C"
    speed = speed_slider * 3
    return state + str(speed)


class ControlPanel(QDialog):
    """Control panel window for pumps and valves."""
    
    # Finger names in order: Pinky, Ring, Middle, Index, Thumb
    FINGER_NAMES = ["Pinky", "Ring", "Middle", "Index", "Thumb"]
    
    def __init__(self, parent=None, serial_reader=None):
        super().__init__(parent)
        # Accept any DataReader (SerialReader or BLEReader)
        self.serial_reader = serial_reader
        
        self.setWindowTitle("Control Panel - Pumps & Valves")
        self.setGeometry(300, 300, 900, 500)
        self.setMinimumSize(800, 400)
        
        # State tracking for each finger (1-5)
        self.vacuum_valves = [False] * 6  # Index 0 unused, 1-5 for fingers
        self.pressure_valves = [False] * 6
        self.pump_speeds = [0] * 6  # Slider values 0-3
        
        # UI components
        self.vacuum_checkboxes = [None] * 6
        self.pressure_checkboxes = [None] * 6
        self.pump_sliders = [None] * 6
        self.pump_labels = [None] * 6
        self.release_buttons = [None] * 6
        
        self._setup_ui()
        self._update_connection_state()
    
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Main grid for finger controls
        grid_group = QGroupBox("Finger Controls")
        grid_layout = QGridLayout()
        grid_group.setLayout(grid_layout)
        
        # Header row
        grid_layout.addWidget(QLabel("Finger"), 0, 0, Qt.AlignCenter)
        for col in range(5):
            finger_name = self.FINGER_NAMES[col]
            grid_layout.addWidget(QLabel(finger_name), 0, col + 1, Qt.AlignCenter)
        
        # Vacuum valve row
        grid_layout.addWidget(QLabel("Vacuum"), 1, 0)
        for col in range(5):
            finger_idx = col + 1  # 1-5
            checkbox = QCheckBox()
            checkbox.setToolTip("Enable vacuum valve for this finger")
            checkbox.stateChanged.connect(lambda state, idx=finger_idx: self._on_vacuum_changed(idx, state))
            self.vacuum_checkboxes[finger_idx] = checkbox
            grid_layout.addWidget(checkbox, 1, col + 1, Qt.AlignCenter)
        
        # Pressure valve row
        grid_layout.addWidget(QLabel("Pressure"), 2, 0)
        for col in range(5):
            finger_idx = col + 1  # 1-5
            checkbox = QCheckBox()
            checkbox.setToolTip("Enable pressure valve for this finger")
            checkbox.stateChanged.connect(lambda state, idx=finger_idx: self._on_pressure_changed(idx, state))
            self.pressure_checkboxes[finger_idx] = checkbox
            grid_layout.addWidget(checkbox, 2, col + 1, Qt.AlignCenter)
        
        # Pump speed row
        grid_layout.addWidget(QLabel("Pump Speed"), 3, 0)
        for col in range(5):
            finger_idx = col + 1  # 1-5
            # Container for slider and label
            slider_container = QHBoxLayout()
            
            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(3)
            slider.setValue(0)
            slider.setToolTip("Pump speed: 0-3 (sends 0, 3, 6, or 9 to ESP32)")
            slider.valueChanged.connect(lambda value, idx=finger_idx: self._on_pump_changed(idx, value))
            self.pump_sliders[finger_idx] = slider
            
            label = QLabel("0")
            label.setMinimumWidth(30)
            label.setAlignment(Qt.AlignCenter)
            self.pump_labels[finger_idx] = label
            
            slider_container.addWidget(slider)
            slider_container.addWidget(label)
            
            container_widget = QGroupBox()
            container_widget.setLayout(slider_container)
            grid_layout.addWidget(container_widget, 3, col + 1)
        
        # Release buttons row
        grid_layout.addWidget(QLabel("Release"), 4, 0)
        for col in range(5):
            finger_idx = col + 1  # 1-5
            button = QPushButton("Release")
            button.setToolTip(f"Release {self.FINGER_NAMES[col]} finger (sets pump to 0, valves to off)")
            button.setAutoDefault(False)  # Prevent default button styling
            button.setDefault(False)  # Prevent default button styling
            button.clicked.connect(lambda checked, idx=finger_idx: self._on_release_clicked(idx))
            self.release_buttons[finger_idx] = button
            grid_layout.addWidget(button, 4, col + 1)
        
        layout.addWidget(grid_group)
        
        # Bottom controls
        bottom_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("Reset All")
        self.reset_btn.setToolTip("Reset all pumps and valves (sends 'reset' command)")
        self.reset_btn.setAutoDefault(False)  # Prevent default button styling
        self.reset_btn.setDefault(False)  # Prevent default button styling
        self.reset_btn.clicked.connect(self._on_reset_clicked)
        bottom_layout.addWidget(self.reset_btn)
        
        bottom_layout.addStretch()
        
        self.status_label = QLabel("Status: Ready")
        bottom_layout.addWidget(self.status_label)
        
        layout.addLayout(bottom_layout)
    
    def _build_outputs_command(self) -> str:
        """
        Build the 'set outputs' command from current UI state.
        
        Returns:
            Command string in format: "set outputs <state1><speed1>...\n"
        """
        command = "set outputs "
        for finger_idx in range(1, 6):
            command += finger_segment(
                self.vacuum_valves[finger_idx],
                self.pressure_valves[finger_idx],
                self.pump_speeds[finger_idx],
            )
        return command + "\n"
    
    def _send_command(self, command: str):
        """Send command to ESP32 via serial reader."""
        if not self.serial_reader:
            self.status_label.setText("Status: No serial connection")
            return
        
        if not self.serial_reader.is_connected():
            self.status_label.setText("Status: Not connected")
            return
        
        success = self.serial_reader.write(command)
        if success:
            # Show last command sent (truncated if too long)
            display_cmd = command.strip()
            if len(display_cmd) > 50:
                display_cmd = display_cmd[:47] + "..."
            self.status_label.setText(f"Status: Sent - {display_cmd}")
        else:
            self.status_label.setText("Status: Failed to send command")
    
    def _on_vacuum_changed(self, finger_idx: int, state):
        """Handle vacuum valve checkbox change."""
        # Use bool(state) instead of state == Qt.Checked for PySide6 compatibility
        # stateChanged emits 0 (unchecked) or 2 (checked) - bool() handles both int and enum
        self.vacuum_valves[finger_idx] = bool(state)
        command = self._build_outputs_command()
        self._send_command(command)
    
    def _on_pressure_changed(self, finger_idx: int, state):
        """Handle pressure valve checkbox change."""
        # Use bool(state) instead of state == Qt.Checked for PySide6 compatibility
        self.pressure_valves[finger_idx] = bool(state)
        command = self._build_outputs_command()
        self._send_command(command)
    
    def _on_pump_changed(self, finger_idx: int, value: int):
        """Handle pump speed slider change."""
        self.pump_speeds[finger_idx] = value
        # Update label
        if self.pump_labels[finger_idx]:
            self.pump_labels[finger_idx].setText(str(value))
        command = self._build_outputs_command()
        self._send_command(command)
    
    def _on_release_clicked(self, finger_idx: int):
        """Handle release button click for a finger."""
        # Reset UI state for this finger
        self.vacuum_valves[finger_idx] = False
        self.pressure_valves[finger_idx] = False
        self.pump_speeds[finger_idx] = 0
        
        # Update UI
        if self.vacuum_checkboxes[finger_idx]:
            self.vacuum_checkboxes[finger_idx].setChecked(False)
        if self.pressure_checkboxes[finger_idx]:
            self.pressure_checkboxes[finger_idx].setChecked(False)
        if self.pump_sliders[finger_idx]:
            self.pump_sliders[finger_idx].setValue(0)
        if self.pump_labels[finger_idx]:
            self.pump_labels[finger_idx].setText("0")
        
        # Send release command
        release_cmd = f"release{finger_idx}\n"
        self._send_command(release_cmd)
        
        # Also send updated outputs command
        outputs_cmd = self._build_outputs_command()
        self._send_command(outputs_cmd)
    
    def _on_reset_clicked(self):
        """Handle reset button click."""
        # Reset all UI state
        for finger_idx in range(1, 6):
            self.vacuum_valves[finger_idx] = False
            self.pressure_valves[finger_idx] = False
            self.pump_speeds[finger_idx] = 0
            
            # Update UI
            if self.vacuum_checkboxes[finger_idx]:
                self.vacuum_checkboxes[finger_idx].setChecked(False)
            if self.pressure_checkboxes[finger_idx]:
                self.pressure_checkboxes[finger_idx].setChecked(False)
            if self.pump_sliders[finger_idx]:
                self.pump_sliders[finger_idx].setValue(0)
            if self.pump_labels[finger_idx]:
                self.pump_labels[finger_idx].setText("0")
        
        # Send reset command
        self._send_command("reset\n")
    
    def set_serial_reader(self, reader):
        """Update the data reader reference (can be SerialReader or BLEReader)."""
        self.serial_reader = reader
        self._update_connection_state()
    
    def _update_connection_state(self):
        """Enable/disable controls based on connection status."""
        is_connected = (self.serial_reader is not None and 
                       self.serial_reader.is_connected())
        
        for finger_idx in range(1, 6):
            if self.vacuum_checkboxes[finger_idx]:
                self.vacuum_checkboxes[finger_idx].setEnabled(is_connected)
            if self.pressure_checkboxes[finger_idx]:
                self.pressure_checkboxes[finger_idx].setEnabled(is_connected)
            if self.pump_sliders[finger_idx]:
                self.pump_sliders[finger_idx].setEnabled(is_connected)
            if self.release_buttons[finger_idx]:
                self.release_buttons[finger_idx].setEnabled(is_connected)
        
        if self.reset_btn:
            self.reset_btn.setEnabled(is_connected)
        
        if not is_connected:
            self.status_label.setText("Status: Not connected")
        else:
            self.status_label.setText("Status: Ready")

