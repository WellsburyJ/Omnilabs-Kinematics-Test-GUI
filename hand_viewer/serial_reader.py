"""
Serial port reader for ESP32 communication.
Handles port discovery, connection, and line-by-line reading.
"""

import serial
import serial.tools.list_ports
from threading import Thread
from queue import Queue
from typing import Optional, Callable

try:
    from .data_reader import DataReader
except ImportError:
    from data_reader import DataReader


class SerialReader(DataReader):
    """Thread-safe serial port reader."""
    
    def __init__(self, on_line_received: Callable[[str], None]):
        """
        Args:
            on_line_received: Callback function called with each received line
        """
        self.on_line_received = on_line_received
        self.serial_connection: Optional[serial.Serial] = None
        self.read_thread: Optional[Thread] = None
        self.running = False
        self.port_name: Optional[str] = None
        self._last_error: Optional[str] = None
        
    @staticmethod
    def list_available_ports():
        """List all available serial ports."""
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
    
    @staticmethod
    def list_available_devices():
        """List all available serial ports (alias for compatibility)."""
        return SerialReader.list_available_ports()
    
    def connect(self, port: str, baud_rate: int = 115200) -> bool:
        """
        Connect to the specified serial port.
        
        Args:
            port: Serial port name (e.g., 'COM3' on Windows, '/dev/ttyUSB0' on Linux)
            baud_rate: Baud rate (default 115200)
            
        Returns:
            True if connection successful, False otherwise
        """
        if self.serial_connection and self.serial_connection.is_open:
            self.disconnect()
            
        try:
            self.serial_connection = serial.Serial(
                port=port,
                baudrate=baud_rate,
                timeout=1.0,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            self.port_name = port
            self.running = True
            self.read_thread = Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()
            return True
        except Exception as e:
            error_msg = f"Failed to connect to {port}: {type(e).__name__}: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            self._last_error = error_msg
            return False
    
    def disconnect(self):
        """Disconnect from serial port."""
        self.running = False
        if self.read_thread:
            self.read_thread.join(timeout=2.0)
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        self.serial_connection = None
        self.port_name = None
    
    def is_connected(self) -> bool:
        """Check if currently connected."""
        return (self.serial_connection is not None and 
                self.serial_connection.is_open and 
                self.running)
    
    def write(self, command: str) -> bool:
        """
        Send a command string to the ESP32 via serial port.
        
        Args:
            command: Command string to send (should include newline if needed)
            
        Returns:
            True if command sent successfully, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            # Ensure command ends with newline
            if not command.endswith('\n'):
                command += '\n'
            
            # Encode and write to serial port
            data = command.encode('utf-8')
            self.serial_connection.write(data)
            return True
        except Exception as e:
            print(f"Failed to write command: {e}")
            return False
    
    def _read_loop(self):
        """Internal thread loop for reading serial data."""
        if not self.serial_connection:
            return
            
        buffer = ""
        while self.running and self.serial_connection and self.serial_connection.is_open:
            try:
                # Read available bytes
                if self.serial_connection.in_waiting > 0:
                    data = self.serial_connection.read(self.serial_connection.in_waiting)
                    buffer += data.decode('utf-8', errors='ignore')
                    
                    # Process complete lines
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        if line:
                            self.on_line_received(line)
                else:
                    # Small sleep to avoid busy-waiting
                    import time
                    time.sleep(0.01)
            except Exception as e:
                print(f"Serial read error: {e}")
                break
        
        self.running = False
    
    @property
    def device_name(self) -> Optional[str]:
        """Get the name/identifier of the currently connected device."""
        return self.port_name



