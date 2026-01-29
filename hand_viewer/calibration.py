"""
Calibration management for finger sensors.
Handles zero-point calibration and angle conversion.
"""

import json
import os
from typing import List, Optional
from pathlib import Path


class Calibration:
    """Manages calibration offsets and angle conversion."""
    
    # Finger names in order: Pinky, Ring, Middle, Index, Thumb
    FINGER_NAMES = ["Pinky", "Ring", "Middle", "Index", "Thumb"]
    
    def __init__(self, config_file: str = "calibration.json"):
        """
        Args:
            config_file: Path to JSON file storing calibration data
        """
        self.config_file = Path(config_file)
        self.zero_points: List[Optional[float]] = [None] * 5
        self.load()
    
    def set_zero_point(self, raw_values: List[float]):
        """
        Set zero point from current raw sensor values.
        
        Args:
            raw_values: List of 5 raw sensor values [Pinky, Ring, Middle, Index, Thumb]
        """
        if len(raw_values) != 5:
            raise ValueError("Expected 5 sensor values")
        self.zero_points = raw_values.copy()
        self.save()
    
    def get_angles(self, raw_values: List[float]) -> List[float]:
        """
        Convert raw sensor values to angles relative to zero point.
        
        Args:
            raw_values: List of 5 raw sensor values
            
        Returns:
            List of 5 angles in degrees (relative to zero point)
        """
        if len(raw_values) != 5:
            raise ValueError("Expected 5 sensor values")
        
        angles = []
        for i in range(5):
            if self.zero_points[i] is not None:
                # Angle is simply the difference from zero point
                # Sensors provide relative angles, so this is straightforward
                angle = float(raw_values[i] - self.zero_points[i])
            else:
                # No calibration yet, return 0
                angle = 0.0
            angles.append(angle)
        
        return angles
    
    def is_calibrated(self) -> bool:
        """Check if calibration has been set."""
        return all(zp is not None for zp in self.zero_points)
    
    def reset(self):
        """Reset calibration to uncalibrated state."""
        self.zero_points = [None] * 5
        self.save()
    
    def save(self):
        """Save calibration to JSON file."""
        data = {
            "zero_points": self.zero_points,
            "finger_names": self.FINGER_NAMES
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to save calibration: {e}")
    
    def load(self):
        """Load calibration from JSON file."""
        if not self.config_file.exists():
            return
        
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                zero_points = data.get("zero_points", [None] * 5)
                if len(zero_points) == 5:
                    self.zero_points = zero_points
        except Exception as e:
            print(f"Failed to load calibration: {e}")


