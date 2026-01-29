"""
Parser for ESP32 flex sensor data and IMU data.
Extracts finger values and IMU orientation from ASCII serial output.
"""

import re
from typing import Optional, List, Tuple


class FlexParser:
    """Parser for flex sensor data lines and IMU data."""
    
    # Pattern: "values flex <v0>,<v1>,<v2>,<v3>,<v4>,\n"
    # New format from ESP32: comma-separated values with trailing comma
    FLEX_PATTERN = re.compile(r'values\s+flex\s+(-?\d+\.?\d*),(-?\d+\.?\d*),(-?\d+\.?\d*),(-?\d+\.?\d*),(-?\d+\.?\d*),')
    
    # Pattern: "values ypr yaw,pitch,roll,\n"
    # IMU orientation data from ESP32: yaw, pitch, roll (comma-separated with trailing comma)
    YPR_PATTERN = re.compile(r'values\s+ypr\s+(-?\d+\.?\d*),(-?\d+\.?\d*),(-?\d+\.?\d*),')
    
    @staticmethod
    def parse_flex_line(line: str) -> Optional[List[float]]:
        """
        Parse a flex sensor data line.
        
        Args:
            line: Input line (e.g., "values flex -16.20,17.34,78.09,82.23,7.31,")
            
        Returns:
            List of 5 float values [Pinky, Ring, Middle, Index, Thumb] or None if parsing fails
        """
        match = FlexParser.FLEX_PATTERN.match(line.strip())
        if match:
            try:
                values = [float(match.group(i)) for i in range(1, 6)]
                return values
            except ValueError:
                return None
        return None
    
    @staticmethod
    def is_flex_line(line: str) -> bool:
        """Check if a line appears to be a flex sensor data line."""
        return line.strip().startswith("values flex ")
    
    @staticmethod
    def parse_ypr_line(line: str) -> Optional[Tuple[float, float, float]]:
        """
        Parse an IMU orientation data line (yaw, pitch, roll).
        
        Args:
            line: Input line (e.g., "values ypr 0,45,-30,")
            
        Returns:
            Tuple of (yaw, pitch, roll) in degrees, or None if parsing fails
        """
        match = FlexParser.YPR_PATTERN.match(line.strip())
        if match:
            try:
                yaw = float(match.group(1))
                pitch = float(match.group(2))
                roll = float(match.group(3))
                return (yaw, pitch, roll)
            except ValueError:
                return None
        return None
    
    @staticmethod
    def is_ypr_line(line: str) -> bool:
        """Check if a line appears to be an IMU orientation data line."""
        return line.strip().startswith("values ypr ")


