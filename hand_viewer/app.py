"""
Main application entry point for Hand Viewer.
"""

import sys
import time
import os

# Set environment variables to speed up Qt initialization
os.environ.setdefault('QT_LOGGING_RULES', '*.debug=false')
os.environ.setdefault('QT_ENABLE_HIGHDPI_SCALING', '0')
os.environ.setdefault('QT_AUTO_SCREEN_SCALE_FACTOR', '0')

# Optimize Python import system
# Force Python to use .pyc files and optimize imports
if not hasattr(sys, 'dont_write_bytecode'):
    # Ensure bytecode is written (helps with caching)
    sys.dont_write_bytecode = False

# Check if warmup was run (helps user know if they should run it)
_warmup_marker = os.path.join(os.path.dirname(__file__), '.warmup_complete')
if os.path.exists(_warmup_marker):
    # Warmup was run - imports should be faster
    pass  # Silent - warmup is working
else:
    # Only warn in verbose mode to avoid cluttering output
    if '--verbose' in sys.argv or '-v' in sys.argv:
        print("[APP] NOTE: Warmup not detected. For faster startup, run:")
        print("[APP]        python hand_viewer/warmup.py --remove-quarantine")

_start_time = time.time()
_last_time = _start_time

def _print_timed(message):
    """Print message with elapsed time since last call."""
    global _last_time
    current_time = time.time()
    elapsed = current_time - _last_time
    total_elapsed = current_time - _start_time
    print(f"{message} [took {elapsed:.3f}s, total: {total_elapsed:.3f}s]")
    _last_time = current_time

print("[APP] Starting imports...")

_print_timed("[APP] Importing PySide6.QtWidgets...")
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                QHBoxLayout, QPushButton, QComboBox, QLabel,
                                QGroupBox, QSlider, QTextEdit, QMessageBox,
                                QDialog, QCheckBox)
_print_timed("[APP] PySide6.QtWidgets imported")

_print_timed("[APP] Importing PySide6.QtCore...")
from PySide6.QtCore import Qt, QTimer, Signal, QObject
_print_timed("[APP] PySide6.QtCore imported")

_print_timed("[APP] Importing PySide6.QtGui...")
from PySide6.QtGui import QFont, QTextCursor
_print_timed("[APP] PySide6.QtGui imported")

_print_timed("[APP] Importing local modules individually...")
try:
    _print_timed("[APP] Importing serial_reader...")
    from .serial_reader import SerialReader
    _print_timed("[APP] serial_reader imported")
    
    _print_timed("[APP] Importing parser...")
    from .parser import FlexParser
    _print_timed("[APP] parser imported")
    
    _print_timed("[APP] Importing calibration...")
    from .calibration import Calibration
    _print_timed("[APP] calibration imported")
    
    _print_timed("[APP] Importing hand_model...")
    from .hand_model import HandModel
    _print_timed("[APP] hand_model imported")
    
    _print_timed("[APP] Importing render_widget...")
    from .render_widget import HandRenderWidget
    _print_timed("[APP] render_widget imported")
    
    _print_timed("[APP] Importing control_panel...")
    from .control_panel import ControlPanel
    _print_timed("[APP] control_panel imported")
except ImportError:
    _print_timed("[APP] Trying absolute imports...")
    
    _print_timed("[APP] Importing serial_reader...")
    from serial_reader import SerialReader
    _print_timed("[APP] serial_reader imported")
    
    _print_timed("[APP] Importing parser...")
    from parser import FlexParser
    _print_timed("[APP] parser imported")
    
    _print_timed("[APP] Importing calibration...")
    from calibration import Calibration
    _print_timed("[APP] calibration imported")
    
    _print_timed("[APP] Importing hand_model...")
    from hand_model import HandModel
    _print_timed("[APP] hand_model imported")
    
    _print_timed("[APP] Importing render_widget...")
    from render_widget import HandRenderWidget
    _print_timed("[APP] render_widget imported")
    
    _print_timed("[APP] Importing control_panel...")
    from control_panel import ControlPanel
    _print_timed("[APP] control_panel imported")
    
_print_timed("[APP] All local modules imported")


class DebugSignals(QObject):
    """Signals for thread-safe debug log updates."""
    new_line = Signal(str)


class DataUpdateSignals(QObject):
    """Signals for thread-safe data updates."""
    values_updated = Signal(list)  # raw values
    model_updated = Signal()  # trigger hand model update


class DebugConsole(QDialog):
    """Debug console window showing raw serial data."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Debug Console - Serial Data")
        self.setGeometry(200, 200, 600, 400)
        self.setMinimumSize(400, 300)
        
        # Setup UI
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Controls row
        controls_layout = QHBoxLayout()
        
        self.auto_scroll_cb = QCheckBox("Auto-scroll")
        self.auto_scroll_cb.setChecked(True)
        
        self.show_flex_only_cb = QCheckBox("Show Flex lines only")
        self.show_flex_only_cb.setChecked(False)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_log)
        
        controls_layout.addWidget(self.auto_scroll_cb)
        controls_layout.addWidget(self.show_flex_only_cb)
        controls_layout.addStretch()
        controls_layout.addWidget(clear_btn)
        
        layout.addLayout(controls_layout)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier New", 10))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                border: 1px solid #333;
            }
        """)
        layout.addWidget(self.log_text)
        
        # Line counter
        self.line_count = 0
        self.counter_label = QLabel("Lines received: 0")
        layout.addWidget(self.counter_label)
        
        # Setup signal for thread-safe updates
        self.signals = DebugSignals()
        self.signals.new_line.connect(self._append_line)
    
    def add_line(self, line: str):
        """Add a line to the debug console (thread-safe)."""
        self.signals.new_line.emit(line)
    
    def _append_line(self, line: str):
        """Internal method to append line (called from main thread)."""
        # Filter if needed
        if self.show_flex_only_cb.isChecked():
            if not line.strip().startswith("Flex #"):
                return
        
        self.line_count += 1
        self.counter_label.setText(f"Lines received: {self.line_count}")
        
        # Append line with timestamp-like line number
        self.log_text.append(f"[{self.line_count:05d}] {line}")
        
        # Auto-scroll if enabled
        if self.auto_scroll_cb.isChecked():
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.log_text.setTextCursor(cursor)
    
    def clear_log(self):
        """Clear the log."""
        self.log_text.clear()
        self.line_count = 0
        self.counter_label.setText("Lines received: 0")


class HandViewerApp(QMainWindow):
    """Main application window."""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self._init_start = time.time()
        self._init_last = self._init_start
        
        def _init_print(msg):
            if self.verbose:
                current = time.time()
                elapsed = current - self._init_last
                total = current - self._init_start
                print(f"{msg} [took {elapsed:.3f}s, total: {total:.3f}s]")
                self._init_last = current
            else:
                print(msg)
        
        _init_print("[INIT] Starting HandViewerApp initialization...")
        super().__init__()
        _init_print("[INIT] QMainWindow created")
        
        _init_print("[INIT] Setting window properties...")
        self.setWindowTitle("Hand Viewer - 3D Kinematic Model")
        self.setGeometry(100, 100, 1200, 800)
        _init_print("[INIT] Window properties set")
        
        # Initialize components
        _init_print("[INIT] Creating SerialReader...")
        self.serial_reader = SerialReader(self.on_serial_line)
        _init_print("[INIT] SerialReader created")
        
        _init_print("[INIT] Creating FlexParser...")
        self.parser = FlexParser()
        _init_print("[INIT] FlexParser created")
        
        _init_print("[INIT] Creating Calibration...")
        self.calibration = Calibration()
        _init_print("[INIT] Calibration created")
        
        _init_print("[INIT] Creating HandModel...")
        self.hand_model = HandModel()
        _init_print("[INIT] HandModel created")
        
        # Current raw values (as floats for decimal support)
        self.current_raw_values = [0.0] * 5
        # Current IMU values (yaw, pitch, roll)
        self.current_imu_values = (0.0, 0.0, 0.0)
        
        # FPS tracking
        _init_print("[INIT] Setting up FPS tracking...")
        self.frame_count = 0
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self.update_fps)
        self.fps_timer.start(1000)  # Update every second
        self.fps = 0
        _init_print("[INIT] FPS tracking setup complete")
        
        # Debug console
        _init_print("[INIT] Creating DebugConsole...")
        self.debug_console = DebugConsole(self)
        _init_print("[INIT] DebugConsole created")
        
        # Control panel
        _init_print("[INIT] Creating ControlPanel...")
        self.control_panel = ControlPanel(self, self.serial_reader)
        _init_print("[INIT] ControlPanel created")
        
        # Signals for thread-safe updates
        self.data_signals = DataUpdateSignals()
        self.data_signals.values_updated.connect(self._handle_values_update)
        self.data_signals.model_updated.connect(self._handle_model_update)
        
        # Throttling for GUI updates - limit to 30 FPS max
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._process_pending_update)
        self.update_timer.setSingleShot(False)
        self.update_timer.start(33)  # ~30 FPS (1000ms / 30 = 33ms)
        self.pending_raw_values = None
        self.update_pending = False
        
        # Setup UI
        _init_print("[INIT] Setting up UI...")
        self.setup_ui()
        _init_print("[INIT] UI setup complete")
        
        # Refresh port list
        _init_print("[INIT] Refreshing port list...")
        self.refresh_ports()
        _init_print("[INIT] Port list refreshed")
        _init_print("[INIT] Initialization complete!")
    
    def setup_ui(self):
        """Setup the user interface."""
        if self.verbose:
            print("[UI] Creating central widget...")
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Left panel - Controls
        if self.verbose:
            print("[UI] Creating left control panel...")
        left_panel = QWidget()
        left_panel.setMaximumWidth(300)
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        # Serial connection group
        serial_group = QGroupBox("Serial Connection")
        serial_layout = QVBoxLayout()
        
        self.port_combo = QComboBox()
        refresh_btn = QPushButton("Refresh Ports")
        refresh_btn.clicked.connect(self.refresh_ports)
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        
        self.status_label = QLabel("Status: Disconnected")
        
        self.debug_btn = QPushButton("Open Debug Console")
        self.debug_btn.clicked.connect(self.open_debug_console)
        
        self.control_panel_btn = QPushButton("Open Control Panel")
        self.control_panel_btn.clicked.connect(self.open_control_panel)
        
        serial_layout.addWidget(QLabel("Port:"))
        serial_layout.addWidget(self.port_combo)
        serial_layout.addWidget(refresh_btn)
        serial_layout.addWidget(self.connect_btn)
        serial_layout.addWidget(self.status_label)
        serial_layout.addWidget(self.debug_btn)
        serial_layout.addWidget(self.control_panel_btn)
        serial_group.setLayout(serial_layout)
        
        # Calibration group
        calib_group = QGroupBox("Calibration")
        calib_layout = QVBoxLayout()
        
        self.zero_btn = QPushButton("Set Zero Point")
        self.zero_btn.clicked.connect(self.set_zero_point)
        self.zero_btn.setEnabled(False)
        
        self.reset_calib_btn = QPushButton("Reset Calibration")
        self.reset_calib_btn.clicked.connect(self.reset_calibration)
        
        self.calib_status_label = QLabel("Calibration: Not set")
        if self.calibration.is_calibrated():
            self.calib_status_label.setText("Calibration: Loaded from file")
        
        calib_layout.addWidget(self.zero_btn)
        calib_layout.addWidget(self.reset_calib_btn)
        calib_layout.addWidget(self.calib_status_label)
        calib_group.setLayout(calib_layout)
        
        # Display group
        display_group = QGroupBox("Display")
        display_layout = QVBoxLayout()
        
        self.fps_label = QLabel("FPS: 0")
        
        smoothing_label = QLabel("Smoothing:")
        self.smoothing_slider = QSlider(Qt.Horizontal)
        self.smoothing_slider.setMinimum(0)
        self.smoothing_slider.setMaximum(100)
        self.smoothing_slider.setValue(30)  # Default 0.3
        self.smoothing_slider.valueChanged.connect(self.on_smoothing_changed)
        
        self.reset_camera_btn = QPushButton("Reset Camera")
        self.reset_camera_btn.clicked.connect(self.reset_camera)
        
        # Hand orientation toggle button
        # Initialize state: hand model starts as right hand (is_right_hand = True in HandModel)
        self._is_right_hand = True  # Track current state
        self.hand_orientation_btn = QPushButton("Switch to Right Hand")  # Text is inverted to match actual behavior
        self.hand_orientation_btn.clicked.connect(self.toggle_hand_orientation)
        # Set hand model initial state (right hand = True)
        self.hand_model.set_hand_orientation(True)
        
        display_layout.addWidget(self.fps_label)
        display_layout.addWidget(smoothing_label)
        display_layout.addWidget(self.smoothing_slider)
        display_layout.addWidget(self.reset_camera_btn)
        display_layout.addWidget(self.hand_orientation_btn)
        display_group.setLayout(display_layout)
        
        # Raw values display
        values_group = QGroupBox("Raw Values")
        values_layout = QVBoxLayout()
        
        self.values_text = QTextEdit()
        self.values_text.setMaximumHeight(150)
        self.values_text.setReadOnly(True)
        self.update_values_display()
        
        values_layout.addWidget(self.values_text)
        values_group.setLayout(values_layout)
        
        # Assemble left panel
        left_layout.addWidget(serial_group)
        left_layout.addWidget(calib_group)
        left_layout.addWidget(display_group)
        left_layout.addWidget(values_group)
        left_layout.addStretch()
        
        # Right panel - 3D view
        if self.verbose:
            print("[UI] Creating 3D render widget...")
        self.render_widget = HandRenderWidget()
        if self.verbose:
            print("[UI] 3D render widget created, updating hand model...")
        self.render_widget.update_hand_model(self.hand_model)
        if self.verbose:
            print("[UI] Hand model updated")
        
        # Add to main layout
        if self.verbose:
            print("[UI] Adding widgets to layout...")
        main_layout.addWidget(left_panel)
        main_layout.addWidget(self.render_widget._widget, stretch=1)
        if self.verbose:
            print("[UI] Layout complete")
    
    def refresh_ports(self):
        """Refresh the list of available serial ports."""
        self.port_combo.clear()
        ports = SerialReader.list_available_ports()
        if ports:
            self.port_combo.addItems(ports)
        else:
            self.port_combo.addItem("No ports available")
    
    def toggle_connection(self):
        """Toggle serial connection."""
        if self.serial_reader.is_connected():
            self.serial_reader.disconnect()
            self.connect_btn.setText("Connect")
            self.status_label.setText("Status: Disconnected")
            self.zero_btn.setEnabled(False)
            # Update control panel connection state
            self.control_panel._update_connection_state()
        else:
            port = self.port_combo.currentText()
            if port and port != "No ports available":
                if self.serial_reader.connect(port):
                    self.connect_btn.setText("Disconnect")
                    self.status_label.setText(f"Status: Connected to {port}")
                    self.zero_btn.setEnabled(True)
                    # Update control panel connection state
                    self.control_panel.set_serial_reader(self.serial_reader)
                    self.control_panel._update_connection_state()
                else:
                    QMessageBox.warning(self, "Connection Failed", 
                                       f"Failed to connect to {port}")
    
    def open_debug_console(self):
        """Open the debug console window."""
        self.debug_console.show()
        self.debug_console.raise_()
        self.debug_console.activateWindow()
    
    def open_control_panel(self):
        """Open the control panel window."""
        self.control_panel.show()
        self.control_panel.raise_()
        self.control_panel.activateWindow()
    
    def on_serial_line(self, line: str):
        """Callback for received serial line (called from background thread)."""
        # Send all lines to debug console
        self.debug_console.add_line(line)
        
        if self.parser.is_flex_line(line):
            raw_values = self.parser.parse_flex_line(line)
            if raw_values:
                # Emit signal for thread-safe update
                self.data_signals.values_updated.emit(raw_values)
                self.frame_count += 1
        elif self.parser.is_ypr_line(line):
            ypr_values = self.parser.parse_ypr_line(line)
            if ypr_values:
                # Update IMU values directly (no signal needed, just for display)
                self.current_imu_values = ypr_values
                # Update display in main thread
                QTimer.singleShot(0, self.update_values_display)
    
    def _handle_values_update(self, raw_values):
        """Handle values update in main thread (called from signal)."""
        # Store the latest values for throttled processing
        self.pending_raw_values = raw_values
        self.update_pending = True
        # Don't update immediately - let the timer handle it
    
    def _process_pending_update(self):
        """Process pending update at throttled rate (~30 FPS)."""
        if not self.update_pending or self.pending_raw_values is None:
            return
        
        raw_values = self.pending_raw_values
        self.update_pending = False
        
        self.current_raw_values = raw_values
        if self.verbose:
            print(f"[SERIAL] Processing values: {raw_values}")
        
        # Update display
        self.update_values_display()
        
        # Convert to angles
        angles = self.calibration.get_angles(raw_values)
        if self.verbose:
            print(f"[SERIAL] Calculated angles: {angles}")
        
        # Update hand model
        self.hand_model.update_angles(angles)
        
        # Trigger rendering update
        self.render_widget.update_hand_model(self.hand_model)
    
    def _handle_model_update(self):
        """Handle model update in main thread."""
        # This is now handled in _process_pending_update
        pass
    
    def update_values_display(self):
        """Update the raw values display."""
        # Save scroll position before updating
        scroll_bar = self.values_text.verticalScrollBar()
        scroll_position = scroll_bar.value()
        is_at_top = scroll_position == 0
        
        finger_names = ["Pinky", "Ring", "Middle", "Index", "Thumb"]
        text = "Raw Values:\n"
        for i, name in enumerate(finger_names):
            text += f"{name}: {self.current_raw_values[i]}\n"
        
        if self.calibration.is_calibrated():
            angles = self.calibration.get_angles(self.current_raw_values)
            text += "\nAngles (degrees):\n"
            for i, name in enumerate(finger_names):
                text += f"{name}: {angles[i]:.1f}°\n"
        
        # Add IMU data
        yaw, pitch, roll = self.current_imu_values
        text += "\nIMU Orientation (degrees):\n"
        text += f"Yaw: {yaw:.1f}°\n"
        text += f"Pitch: {pitch:.1f}°\n"
        text += f"Roll: {roll:.1f}°\n"
        
        self.values_text.setText(text)
        
        # Restore scroll position if user was scrolled down
        # Only auto-scroll to top if user hasn't manually scrolled
        if is_at_top:
            # User was at top, keep at top
            scroll_bar.setValue(0)
        else:
            # User was scrolled down, restore their position
            # If content is shorter now, scroll to bottom instead
            max_scroll = scroll_bar.maximum()
            if scroll_position > max_scroll:
                scroll_bar.setValue(max_scroll)
            else:
                scroll_bar.setValue(scroll_position)
    
    def set_zero_point(self):
        """Set zero point calibration."""
        if not self.serial_reader.is_connected():
            QMessageBox.warning(self, "Not Connected", 
                               "Please connect to serial port first")
            return
        
        self.calibration.set_zero_point(self.current_raw_values)
        self.calib_status_label.setText("Calibration: Set")
        self.update_values_display()
        QMessageBox.information(self, "Calibration Set", 
                               "Zero point has been set. Place the glove flat on a table and press this button.")
    
    def reset_calibration(self):
        """Reset calibration."""
        reply = QMessageBox.question(self, "Reset Calibration", 
                                    "Are you sure you want to reset calibration?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.calibration.reset()
            self.calib_status_label.setText("Calibration: Not set")
            self.update_values_display()
    
    def on_smoothing_changed(self, value: int):
        """Handle smoothing slider change."""
        alpha = value / 100.0
        self.hand_model.set_smoothing(alpha)
        self.render_widget.set_smoothing(alpha)
    
    def reset_camera(self):
        """Reset 3D camera view."""
        self.render_widget.reset_camera()
    
    def toggle_hand_orientation(self):
        """Toggle between left and right hand orientation."""
        # Toggle the state
        self._is_right_hand = not self._is_right_hand
        # Update hand model (pass the state directly, no inversion)
        self.hand_model.set_hand_orientation(self._is_right_hand)
        # Update button text (inverted text to match actual behavior)
        # If right hand is shown, button says "Switch to Right Hand" (but clicking switches to left)
        # If left hand is shown, button says "Switch to Left Hand" (but clicking switches to right)
        self.hand_orientation_btn.setText("Switch to Right Hand" if self._is_right_hand else "Switch to Left Hand")
        # Update the render to show the new orientation
        self.render_widget.update_hand_model(self.hand_model)
    
    def update_fps(self):
        """Update FPS display."""
        self.fps = self.frame_count
        self.frame_count = 0
        self.fps_label.setText(f"FPS: {self.fps}")
    
    def closeEvent(self, event):
        """Handle window close event."""
        self.serial_reader.disconnect()
        event.accept()


def main():
    """Main entry point."""
    import sys
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    
    if verbose:
        print("=" * 50)
        print("HAND VIEWER - VERBOSE MODE")
        print("=" * 50)
    
    print("[MAIN] Creating QApplication...")
    app = QApplication(sys.argv)
    print("[MAIN] QApplication created")
    
    print("[MAIN] Creating HandViewerApp window...")
    window = HandViewerApp(verbose=verbose)
    print("[MAIN] Window created")
    
    print("[MAIN] Showing window...")
    window.show()
    print("[MAIN] Window shown, starting event loop...")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

