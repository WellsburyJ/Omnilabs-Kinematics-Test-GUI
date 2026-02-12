"""
Abstract base class for data readers (Serial, BLE, etc.)
Defines the common interface that all data readers must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Callable, Optional


class DataReader(ABC):
    """Abstract base class for data readers."""
    
    def __init__(self, on_line_received: Callable[[str], None]):
        """
        Args:
            on_line_received: Callback function called with each received line
        """
        self.on_line_received = on_line_received
    
    @staticmethod
    @abstractmethod
    def list_available_devices() -> List[str]:
        """List all available devices (ports, BLE devices, etc.)."""
        pass
    
    @abstractmethod
    def connect(self, device: str, **kwargs) -> bool:
        """
        Connect to the specified device.
        
        Args:
            device: Device identifier (port name, BLE address, etc.)
            **kwargs: Additional connection parameters
            
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from the device."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if currently connected."""
        pass
    
    @abstractmethod
    def write(self, command: str) -> bool:
        """
        Send a command string to the device.
        
        Args:
            command: Command string to send (should include newline if needed)
            
        Returns:
            True if command sent successfully, False otherwise
        """
        pass
    
    @property
    @abstractmethod
    def device_name(self) -> Optional[str]:
        """Get the name/identifier of the currently connected device."""
        pass


