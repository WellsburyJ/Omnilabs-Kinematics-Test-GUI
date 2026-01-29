"""
3D kinematic hand model.
Represents hand structure and computes finger segment positions from angles.
"""

import numpy as np
from typing import List, Tuple
import math


class HandModel:
    """3D kinematic model of a hand."""
    
    # Finger names in order: Pinky, Ring, Middle, Index, Thumb
    FINGER_NAMES = ["Pinky", "Ring", "Middle", "Index", "Thumb"]
    
    def __init__(self):
        """Initialize hand model with default dimensions."""
        # Palm dimensions (in arbitrary units, will be scaled for display)
        self.palm_width = 8.0
        self.palm_length = 5.0
        self.palm_thickness = 1.0
        
        # Finger segment lengths (proximal, middle, distal)
        # More realistic human hand proportions
        # Note: Thumb only has 2 segments (no DIP joint), so distal length is 0
        self.finger_segments = [
            [2.0, 1.2, 0.8],  # Pinky (shorter overall, smaller middle segment)
            [2.4, 1.6, 1.0],  # Ring
            [2.8, 2.0, 1.2],  # Middle (longest)
            [2.5, 1.7, 1.0],  # Index
            [1.8, 1.6, 0.0],  # Thumb (only 2 segments: proximal + distal, no middle/DIP joint)
        ]
        
        # Finger base positions on palm (relative to palm center)
        # Format: (x_offset, y_offset) where x is palm width direction, y is palm length direction
        # Realistic hand model with natural finger spacing and arc formation
        # Wrist is at y = -palm_length = -5.0
        import math
        wrist_y = -self.palm_length  # -5.0
        
        # Natural finger spacing angles - reduced spread for more compact hand
        # Cumulative angles from middle finger (0°):
        # Pinky: -12° (reduced from -20°)
        # Ring: -6° (reduced from -11°)
        # Middle: 0° (straight ahead)
        # Index: +6° (reduced from +9°)
        # Thumb: +18° (reduced from +27°, but still larger gap)
        
        # MCP joints form an arc (not straight line):
        # Middle finger is highest (longest), others form arc
        middle_y = 2.8  # Highest point
        middle_x = 0.0
        
        ring_y = 2.4  # Slightly lower than middle
        ring_dist = ring_y - wrist_y  # ~7.4
        ring_x = ring_dist * math.tan(math.radians(-6))  # ~-0.78
        
        pinky_y = 2.0  # Lower (shortest finger)
        pinky_dist = pinky_y - wrist_y  # ~7.0
        pinky_x = pinky_dist * math.tan(math.radians(-12))  # ~-1.49
        
        index_y = 2.4  # Similar to ring
        index_dist = index_y - wrist_y  # ~7.4
        index_x = index_dist * math.tan(math.radians(6))  # ~0.78
        
        # Thumb: lower, more forward, larger angle gap but reduced
        # Also positioned lower in Z to avoid interference with other fingers
        thumb_y = 0.5  # Lower and more forward (was 0.8)
        thumb_dist = thumb_y - wrist_y  # ~5.5
        thumb_x = thumb_dist * math.tan(math.radians(18))  # ~1.79
        
        self.finger_base_positions = [
            (pinky_x, pinky_y),   # Pinky
            (ring_x, ring_y),      # Ring
            (middle_x, middle_y), # Middle
            (index_x, index_y),    # Index
            (thumb_x, thumb_y),   # Thumb
        ]
        
        # Current finger angles (in degrees, relative to palm)
        self.finger_angles = [0.0] * 5
        
        # Smoothing factor for angle updates (EMA)
        self.smoothing_alpha = 0.3
        
        # Hand orientation: True = right hand, False = left hand (mirrored)
        self.is_right_hand = True
    
    def update_angles(self, angles: List[float], apply_smoothing: bool = True):
        """
        Update finger angles.
        
        Args:
            angles: List of 5 angles in degrees [Pinky, Ring, Middle, Index, Thumb]
            apply_smoothing: If True, apply exponential moving average smoothing
        """
        if len(angles) != 5:
            return
        
        if apply_smoothing:
            for i in range(5):
                # Exponential moving average
                self.finger_angles[i] = (
                    self.smoothing_alpha * angles[i] + 
                    (1 - self.smoothing_alpha) * self.finger_angles[i]
                )
        else:
            self.finger_angles = angles.copy()
    
    def set_smoothing(self, alpha: float):
        """
        Set smoothing factor (0.0 = no smoothing, 1.0 = maximum smoothing).
        
        Args:
            alpha: Smoothing factor (typically 0.1-0.5)
        """
        self.smoothing_alpha = max(0.0, min(1.0, alpha))
    
    def set_hand_orientation(self, is_right_hand: bool):
        """
        Set hand orientation (right or left hand).
        
        Args:
            is_right_hand: True for right hand, False for left hand (mirrored)
        """
        self.is_right_hand = is_right_hand
    
    def get_finger_segments(self, finger_index: int) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Get 3D positions of finger segments for a given finger.
        
        Args:
            finger_index: Index of finger (0=Pinky, 4=Thumb)
            
        Returns:
            List of (start_point, end_point) tuples for each segment in 3D space
        """
        if finger_index < 0 or finger_index >= 5:
            return []
        
        # Get base position on palm
        base_x, base_y = self.finger_base_positions[finger_index]
        # Mirror X coordinate if left hand
        if not self.is_right_hand:
            base_x = -base_x
        # Thumb is positioned lower in Z to avoid interference with other fingers
        if finger_index == 4:  # Thumb
            base_z = self.palm_thickness / 2 - 0.5  # Lower than other fingers
        else:
            base_z = self.palm_thickness / 2
        base_pos = np.array([base_x, base_y, base_z])
        
        # Get finger angle in radians
        angle_rad = math.radians(self.finger_angles[finger_index])
        
        # For simplicity, we'll model the finger as bending in the Y-Z plane
        # (bending forward/down from the palm)
        
        segments = []
        current_pos = base_pos.copy()
        
        # Check if angle is negative (extended backward) or positive (curled forward)
        if angle_rad < 0:
            # Negative angle: Base joint (MCP) bends, rest of finger stays in line
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)
            
            # Special case: Thumb (finger_index == 4) only has 2 segments
            # Thumb bends inwards (towards other fingers) instead of down
            if finger_index == 4:  # Thumb
                # Thumb extends backward inwards (towards other fingers) in X-Y plane
                # Negative angle = extend backward and inward
                cos_a = math.cos(angle_rad)
                sin_a = math.sin(angle_rad)
                
                # Proximal segment rotates at base joint (inwards in X-Y plane)
                # For left hand, thumb bends in opposite direction
                x_sign = -1 if self.is_right_hand else 1
                proximal_len = self.finger_segments[finger_index][0]
                proximal_end = current_pos + np.array([
                    x_sign * proximal_len * sin_a,  # Inward extension (direction depends on hand)
                    proximal_len * cos_a,   # Backward in Y
                    0  # No Z change
                ])
                segments.append((current_pos.copy(), proximal_end.copy()))
                current_pos = proximal_end
                
                # Distal segment (only segment for thumb) stays in line
                distal_len = self.finger_segments[finger_index][1]  # Use middle segment length as distal
                distal_end = current_pos + np.array([
                    x_sign * distal_len * sin_a,  # Inward extension
                    distal_len * cos_a,   # Backward in Y
                    0  # No Z change
                ])
                segments.append((current_pos.copy(), distal_end.copy()))
            else:
                # Other fingers: 3 segments
                # Proximal segment rotates at base joint
                proximal_len = self.finger_segments[finger_index][0]
                proximal_end = current_pos + np.array([
                    0,
                    proximal_len * cos_a,
                    -proximal_len * sin_a  # Negative Z for backward extension
                ])
                segments.append((current_pos.copy(), proximal_end.copy()))
                current_pos = proximal_end
                
                # Middle segment stays in line with proximal (no additional rotation)
                middle_len = self.finger_segments[finger_index][1]
                middle_end = current_pos + np.array([
                    0,
                    middle_len * cos_a,
                    -middle_len * sin_a
                ])
                segments.append((current_pos.copy(), middle_end.copy()))
                current_pos = middle_end
                
                # Distal segment stays in line (no fingertip bend for negative angles)
                distal_len = self.finger_segments[finger_index][2]
                distal_end = current_pos + np.array([
                    0,
                    distal_len * cos_a,
                    -distal_len * sin_a
                ])
                segments.append((current_pos.copy(), distal_end.copy()))
        else:
            # Positive angle: Distribute bend between base (20%) and middle (80%) joints
            # Special case: Thumb (finger_index == 4) bends inwards instead of down
            if finger_index == 4:  # Thumb
                # Thumb: Base joint (MCP) and IP joint (only 2 segments)
                # Distribute: 30% at base, 70% at IP
                # Thumb bends inwards (towards other fingers) in X-Y plane
                base_angle_rad = angle_rad * 0.3
                ip_angle_rad = angle_rad * 0.7
                
                # Thumb bends inwards (towards other fingers) in X-Y plane
                # Rotation is around Z axis (inward towards palm/fingers)
                # For right hand: positive angle = bend inwards (towards negative X)
                # For left hand: positive angle = bend inwards (towards positive X)
                x_sign = -1 if self.is_right_hand else 1
                cos_base = math.cos(base_angle_rad)
                sin_base = math.sin(base_angle_rad)
                
                # Proximal segment rotates at base joint (inwards in X-Y plane)
                proximal_len = self.finger_segments[finger_index][0]
                proximal_end = current_pos + np.array([
                    x_sign * proximal_len * sin_base,  # Inward bend (direction depends on hand)
                    proximal_len * cos_base,   # Forward in Y
                    0  # No Z change (stays in same plane)
                ])
                segments.append((current_pos.copy(), proximal_end.copy()))
                current_pos = proximal_end
                
                # Distal segment (only segment for thumb) - rotates at IP joint
                # Total angle = base + IP
                total_angle_rad = base_angle_rad + ip_angle_rad
                cos_total = math.cos(total_angle_rad)
                sin_total = math.sin(total_angle_rad)
                
                distal_len = self.finger_segments[finger_index][1]  # Use middle segment length as distal
                distal_end = current_pos + np.array([
                    x_sign * distal_len * sin_total,  # Inward bend
                    distal_len * cos_total,  # Forward in Y
                    0  # No Z change
                ])
                segments.append((current_pos.copy(), distal_end.copy()))
            else:
                # Other fingers: 3 segments, bend down in Y-Z plane
                # Base joint (MCP): 20% of total angle
                base_angle_rad = angle_rad * 0.2
                cos_base = math.cos(base_angle_rad)
                sin_base = math.sin(base_angle_rad)
                
                # Middle joint (PIP): 80% of total angle (relative to base)
                middle_angle_rad = angle_rad * 0.8
                cos_middle = math.cos(middle_angle_rad)
                sin_middle = math.sin(middle_angle_rad)
                
                # Proximal segment rotates at base joint
                proximal_len = self.finger_segments[finger_index][0]
                proximal_end = current_pos + np.array([
                    0,
                    proximal_len * cos_base,
                    -proximal_len * sin_base  # Negative Z for downward bend
                ])
                segments.append((current_pos.copy(), proximal_end.copy()))
                current_pos = proximal_end
                
                # Middle segment rotates at middle joint (relative to proximal direction)
                # Need to combine base rotation with middle rotation
                # Total angle at middle = base_angle + middle_angle
                total_middle_angle_rad = base_angle_rad + middle_angle_rad
                cos_total_middle = math.cos(total_middle_angle_rad)
                sin_total_middle = math.sin(total_middle_angle_rad)
                
                middle_len = self.finger_segments[finger_index][1]
                middle_end = current_pos + np.array([
                    0,
                    middle_len * cos_total_middle,
                    -middle_len * sin_total_middle  # Negative Z for downward bend
                ])
                segments.append((current_pos.copy(), middle_end.copy()))
                current_pos = middle_end
                
                # Distal segment (tip) - curls further when bent forward
                # DIP joint angle is approximately 0.6 times the middle joint angle (80% of total)
                dip_angle_rad = middle_angle_rad * 0.6
                # Total angle from palm = base + middle + DIP
                total_angle_rad = base_angle_rad + middle_angle_rad + dip_angle_rad
                cos_total = math.cos(total_angle_rad)
                sin_total = math.sin(total_angle_rad)
                
                distal_len = self.finger_segments[finger_index][2]
                distal_end = current_pos + np.array([
                    0,
                    distal_len * cos_total,
                    -distal_len * sin_total  # Negative Z for downward curl
                ])
                segments.append((current_pos.copy(), distal_end.copy()))
        
        return segments
    
    def get_wrist_position(self) -> np.ndarray:
        """
        Get 3D position of wrist point.
        
        Returns:
            Wrist position as numpy array
        """
        # Wrist is at the base of the palm, centered in X, at the back in Y
        z = self.palm_thickness / 2
        return np.array([0.0, -self.palm_length, z])
    
    def get_mcp_joints(self) -> List[np.ndarray]:
        """
        Get 3D positions of all MCP (metacarpophalangeal) joints.
        These are the base positions where fingers attach to the palm.
        
        Returns:
            List of 5 MCP joint positions [Pinky, Ring, Middle, Index, Thumb]
        """
        mcp_joints = []
        for i, (x_offset, y_offset) in enumerate(self.finger_base_positions):
            # Mirror X coordinate if left hand
            x = -x_offset if not self.is_right_hand else x_offset
            # Thumb is positioned lower in Z to avoid interference with other fingers
            if i == 4:  # Thumb
                z = self.palm_thickness / 2 - 0.5
            else:
                z = self.palm_thickness / 2
            mcp_joints.append(np.array([x, y_offset, z]))
        return mcp_joints
    
    def get_palm_corners(self) -> List[np.ndarray]:
        """
        Get 3D positions for palm rendering (wrist + MCP joints).
        Returns wrist position and MCP joint positions for drawing lines.
        
        Returns:
            List with wrist position first, then 5 MCP joint positions
        """
        wrist = self.get_wrist_position()
        mcp_joints = self.get_mcp_joints()
        return [wrist] + mcp_joints
    
    def get_all_segments(self) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Get all finger segments for all fingers.
        
        Returns:
            List of (start_point, end_point) tuples for all finger segments
        """
        all_segments = []
        for i in range(5):
            all_segments.extend(self.get_finger_segments(i))
        return all_segments


