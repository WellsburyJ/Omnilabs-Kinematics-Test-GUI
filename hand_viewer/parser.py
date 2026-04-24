"""
Parser for ESP32 flex sensor and IMU data.
Extracts finger values and IMU values from ASCII output lines.
"""

import re
from typing import Optional, List, Tuple


class FlexParser:
    """Parser for flex sensor data lines and IMU data."""
    
    # Pattern: "values flex <v0>,<v1>,<v2>,<v3>,<v4>,\n"
    # New format from ESP32: comma-separated values with trailing comma
    FLEX_PATTERN = re.compile(r'values\s+flex\s+(-?\d+\.?\d*),(-?\d+\.?\d*),(-?\d+\.?\d*),(-?\d+\.?\d*),(-?\d+\.?\d*),')
    
    # Pattern: "values accel x,y,z,ts,1234," (ts suffix is ignored)
    ACCEL_PATTERN = re.compile(
        r"values\s+accel\s+(-?\d+\.?\d*),(-?\d+\.?\d*),(-?\d+\.?\d*)(?:,|,ts,.*)$"
    )
    # Pattern: "values gyro x,y,z,ts,1234," (ts suffix is ignored)
    GYRO_PATTERN = re.compile(
        r"values\s+gyro\s+(-?\d+\.?\d*),(-?\d+\.?\d*),(-?\d+\.?\d*)(?:,|,ts,.*)$"
    )
    # Legacy pattern: "values ypr yaw,pitch,roll,\n"
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
    def _parse_triplet(pattern: re.Pattern, line: str) -> Optional[Tuple[float, float, float]]:
        """Parse three comma-separated floats using pattern."""
        match = pattern.match(line.strip())
        if match:
            try:
                x = float(match.group(1))
                y = float(match.group(2))
                z = float(match.group(3))
                return (x, y, z)
            except ValueError:
                return None
        return None

    @staticmethod
    def parse_accel_line(line: str) -> Optional[Tuple[float, float, float]]:
        """
        Parse acceleration line in g units.
        Example: "values accel 0.791,0.337,0.544,ts,35734,"
        """
        return FlexParser._parse_triplet(FlexParser.ACCEL_PATTERN, line)

    @staticmethod
    def parse_gyro_line(line: str) -> Optional[Tuple[float, float, float]]:
        """
        Parse gyro line in deg/s units.
        Example: "values gyro -0.756,3.000,-0.221,ts,35719,"
        """
        return FlexParser._parse_triplet(FlexParser.GYRO_PATTERN, line)

    @staticmethod
    def parse_ypr_line(line: str) -> Optional[Tuple[float, float, float]]:
        """
        Parse an IMU orientation data line (yaw, pitch, roll).
        
        Args:
            line: Input line (e.g., "values ypr 0,45,-30,")
            
        Returns:
            Tuple of (yaw, pitch, roll) in degrees, or None if parsing fails
        """
        return FlexParser._parse_triplet(FlexParser.YPR_PATTERN, line)
    
    @staticmethod
    def is_ypr_line(line: str) -> bool:
        """Check if a line appears to be an IMU orientation data line."""
        return line.strip().startswith("values ypr ")

    @staticmethod
    def is_accel_line(line: str) -> bool:
        """Check if a line appears to be an acceleration data line."""
        return line.strip().startswith("values accel ")

    @staticmethod
    def is_gyro_line(line: str) -> bool:
        """Check if a line appears to be a gyro data line."""
        return line.strip().startswith("values gyro ")


