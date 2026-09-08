"""
Parser for OMNIHUMAN-O1 telemetry lines (`values …`) and legacy IMU formats.
"""

import math
import re
from typing import Optional, List, Tuple


class FlexParser:
    """Parser for flex / motors / angles / IMU data lines."""

    # Optional serial counter prefix: "[10376] values ..."
    LINE_PREFIX = re.compile(r"^\[\d+\]\s*")

    # values <key> <csv>,ts,<millis>,
    VALUES_LINE = re.compile(
        r"^values\s+(\w+)\s+(.+)$"
    )

    # Legacy patterns kept for older firmware
    GYRO_PATTERN = re.compile(
        r"values\s+gyro\s+(-?\d+\.?\d*),(-?\d+\.?\d*),(-?\d+\.?\d*)(?:,|,ts,.*)$"
    )
    YPR_PATTERN = re.compile(r"values\s+ypr\s+(-?\d+\.?\d*),(-?\d+\.?\d*),(-?\d+\.?\d*),")

    @staticmethod
    def normalize_line(line: str) -> str:
        """Strip optional [n] counter prefix and whitespace."""
        return FlexParser.LINE_PREFIX.sub("", line.strip())

    @staticmethod
    def parse_float_token(token: str) -> float:
        """Parse a CSV field; literal 'nan' → float('nan')."""
        t = token.strip()
        if not t or t.lower() == "nan":
            return float("nan")
        return float(t)

    @staticmethod
    def parse_values_fields(line: str) -> Optional[Tuple[str, List[str], Optional[int]]]:
        """
        Split a `values <key> <csv>` line.

        Returns:
            (key, data_fields_before_ts, timestamp_ms) or None
        """
        normalized = FlexParser.normalize_line(line)
        match = FlexParser.VALUES_LINE.match(normalized)
        if not match:
            return None
        key = match.group(1).lower()
        csv = match.group(2).rstrip(",").strip()
        parts = [p.strip() for p in csv.split(",")]
        ts_ms: Optional[int] = None
        data = parts
        if len(parts) >= 2 and parts[-2].lower() == "ts":
            try:
                ts_ms = int(float(parts[-1]))
            except ValueError:
                ts_ms = None
            data = parts[:-2]
        return key, data, ts_ms

    @staticmethod
    def parse_n_floats(line: str, key: str, n: int) -> Optional[List[float]]:
        """Parse `values <key>` with exactly n float fields (nan allowed)."""
        parsed = FlexParser.parse_values_fields(line)
        if not parsed:
            return None
        found_key, data, _ts = parsed
        if found_key != key.lower() or len(data) < n:
            return None
        try:
            return [FlexParser.parse_float_token(data[i]) for i in range(n)]
        except ValueError:
            return None

    @staticmethod
    def parse_flex_line(line: str) -> Optional[List[float]]:
        """
        Parse flex degrees into UI order: Thumb, Index, Middle, Ring, Pinky.

        Wire order from the glove/core is:
          Index, Middle, Ring, Pinky, Thumb
        (thumb last; other fingers index→pinky). Remap here for the UI.
        """
        values = FlexParser.parse_n_floats(line, "flex", 5)
        if values is None:
            return None
        # wire: [Index, Middle, Ring, Pinky, Thumb] → UI Thumb..Pinky
        index, middle, ring, pinky, thumb = values
        return [thumb, index, middle, ring, pinky]

    @staticmethod
    def parse_motors_line(line: str) -> Optional[List[float]]:
        """Parse normalized motor positions 0..1 (or nan). Order M1..M5."""
        return FlexParser.parse_n_floats(line, "motors", 5)

    @staticmethod
    def parse_angles_line(line: str) -> Optional[List[float]]:
        """Parse encoder angles in degrees. Order M1..M5."""
        return FlexParser.parse_n_floats(line, "angles", 5)

    @staticmethod
    def is_flex_line(line: str) -> bool:
        return FlexParser.normalize_line(line).startswith("values flex ")

    @staticmethod
    def is_motors_line(line: str) -> bool:
        return FlexParser.normalize_line(line).startswith("values motors ")

    @staticmethod
    def is_angles_line(line: str) -> bool:
        return FlexParser.normalize_line(line).startswith("values angles ")

    @staticmethod
    def _parse_triplet(pattern: re.Pattern, line: str) -> Optional[Tuple[float, float, float]]:
        match = pattern.match(FlexParser.normalize_line(line))
        if match:
            try:
                return (
                    float(match.group(1)),
                    float(match.group(2)),
                    float(match.group(3)),
                )
            except ValueError:
                return None
        return None

    @staticmethod
    def parse_accel_line(line: str) -> Optional[Tuple[float, float, float]]:
        """Parse linaccel (or legacy accel) as (ax, ay, az)."""
        vals = FlexParser.parse_n_floats(line, "linaccel", 3)
        if vals is not None:
            return (vals[0], vals[1], vals[2])
        vals = FlexParser.parse_n_floats(line, "accel", 3)
        if vals is not None:
            return (vals[0], vals[1], vals[2])
        return None

    @staticmethod
    def parse_quat_line(line: str) -> Optional[Tuple[float, float, float, float]]:
        """Parse quaternion as (w, x, y, z)."""
        vals = FlexParser.parse_n_floats(line, "quat", 4)
        if vals is None:
            return None
        return (vals[0], vals[1], vals[2], vals[3])

    @staticmethod
    def parse_gyro_line(line: str) -> Optional[Tuple[float, float, float]]:
        return FlexParser._parse_triplet(FlexParser.GYRO_PATTERN, line)

    @staticmethod
    def parse_ypr_line(line: str) -> Optional[Tuple[float, float, float]]:
        return FlexParser._parse_triplet(FlexParser.YPR_PATTERN, line)

    @staticmethod
    def is_ypr_line(line: str) -> bool:
        return FlexParser.normalize_line(line).startswith("values ypr ")

    @staticmethod
    def is_accel_line(line: str) -> bool:
        normalized = FlexParser.normalize_line(line)
        return normalized.startswith("values linaccel ") or normalized.startswith("values accel ")

    @staticmethod
    def is_quat_line(line: str) -> bool:
        return FlexParser.normalize_line(line).startswith("values quat ")

    @staticmethod
    def is_gyro_line(line: str) -> bool:
        return FlexParser.normalize_line(line).startswith("values gyro ")

    @staticmethod
    def is_fault_line(line: str) -> bool:
        return FlexParser.normalize_line(line).upper().startswith("FAULT")

    @staticmethod
    def parse_version_line(line: str) -> Optional[str]:
        normalized = FlexParser.normalize_line(line)
        if normalized.lower().startswith("version:"):
            return normalized.split(":", 1)[1].strip()
        return None

    @staticmethod
    def format_float(value: float, decimals: int = 3) -> str:
        if isinstance(value, float) and math.isnan(value):
            return "nan"
        return f"{value:.{decimals}f}"
