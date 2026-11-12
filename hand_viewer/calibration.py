"""
Calibration management for finger sensors.
Handles zero-point calibration and angle conversion.
"""

import json
import math
import os
from typing import List, Optional
from pathlib import Path


class Calibration:
    """Manages calibration offsets and angle conversion."""
    
    # Finger names in OH1 order: Thumb, Index, Middle, Ring, Pinky
    FINGER_NAMES = ["Thumb", "Index", "Middle", "Ring", "Pinky"]

    # Hand model / GUI convention: positive angle = finger curling closed.
    # The thumb flex channel on this glove increases the opposite way, so flip it
    # after subtracting the zero point. Raw flex in the values panel stays as-is.
    FLEX_SIGN = (-1.0, 1.0, 1.0, 1.0, 1.0)
    
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
            raw_values: List of 5 raw sensor values [Thumb, Index, Middle, Ring, Pinky]
        """
        if len(raw_values) != 5:
            raise ValueError("Expected 5 sensor values")
        # Keep the previous zero when this finger is missing (nan).
        updated: List[Optional[float]] = []
        for i, value in enumerate(raw_values):
            v = float(value)
            if math.isnan(v):
                updated.append(self.zero_points[i])
            else:
                updated.append(v)
        self.zero_points = updated
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
            raw = float(raw_values[i])
            if math.isnan(raw):
                angles.append(float("nan"))
                continue
            zero = self.zero_points[i]
            if zero is not None and not (isinstance(zero, float) and math.isnan(zero)):
                angles.append(self.FLEX_SIGN[i] * (raw - float(zero)))
            else:
                angles.append(0.0)
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


