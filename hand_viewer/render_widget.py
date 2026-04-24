"""
3D rendering widget for hand model using Matplotlib.
"""

import time
import os

# Set matplotlib environment variables to speed up initialization
os.environ.setdefault('MPLBACKEND', 'Qt5Agg')  # Pre-set backend
os.environ.setdefault('MATPLOTLIBDATA', '')  # Skip data path search

_render_start = time.time()
_render_last = _render_start

def _render_print(msg):
    """Print message with elapsed time since last call."""
    global _render_last
    current = time.time()
    elapsed = current - _render_last
    total = current - _render_start
    print(f"{msg} [took {elapsed:.3f}s, total: {total:.3f}s]")
    _render_last = current

_render_print("[RENDER_WIDGET] Starting lightweight imports...")

_render_print("[RENDER_WIDGET] Importing numpy...")
import numpy as np
import math
_render_print("[RENDER_WIDGET] numpy imported")

_render_print("[RENDER_WIDGET] Importing PySide6.QtCore...")
from PySide6.QtCore import QTimer
_render_print("[RENDER_WIDGET] PySide6.QtCore imported")

from typing import List, Tuple

_render_print("[RENDER_WIDGET] Importing HandModel...")
try:
    from .hand_model import HandModel
except ImportError:
    from hand_model import HandModel
_render_print("[RENDER_WIDGET] HandModel imported")

_render_print("[RENDER_WIDGET] Lightweight imports complete - QtWidgets and matplotlib will be lazy loaded")


class HandRenderWidget:
    """Widget for rendering 3D hand model using Matplotlib."""
    
    def __init__(self, parent=None):
        init_start = time.time()
        init_last = init_start
        
        def _init_print(msg):
            current = time.time()
            elapsed = current - init_last
            total = current - init_start
            print(f"{msg} [took {elapsed:.3f}s, total: {total:.3f}s]")
            return current
        
        init_last = _init_print("[RENDER] Initializing HandRenderWidget...")
        
        # Import QtWidgets
        init_last = _init_print("[RENDER] Importing PySide6.QtWidgets...")
        from PySide6.QtWidgets import QWidget, QVBoxLayout
        from PySide6.QtCore import Qt
        init_last = _init_print("[RENDER] PySide6.QtWidgets imported")
        
        # Store for later use
        self._QWidget = QWidget
        self._QVBoxLayout = QVBoxLayout
        
        # Create the actual QWidget instance
        self._widget = QWidget(parent)
        init_last = _init_print("[RENDER] Base widget created")
        
        # Make this object behave like the widget for duck typing
        self.setLayout = self._widget.setLayout
        self.layout = lambda: self._widget.layout()
        self.show = self._widget.show
        self.hide = self._widget.hide
        self.setParent = self._widget.setParent
        self.parent = lambda: self._widget.parent()
        self.setVisible = self._widget.setVisible
        self.isVisible = lambda: self._widget.isVisible()
        
        # Hand model
        init_last = _init_print("[RENDER] Creating HandModel...")
        self.hand_model = HandModel()
        init_last = _init_print("[RENDER] HandModel created")
        
        # Import matplotlib (normal import, not lazy)
        init_last = _init_print("[RENDER] Importing matplotlib...")
        import matplotlib
        init_last = _init_print("[RENDER] matplotlib base imported")
        
        init_last = _init_print("[RENDER] Importing matplotlib.backends.backend_qt5agg...")
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
        init_last = _init_print("[RENDER] matplotlib backend imported")
        
        init_last = _init_print("[RENDER] Importing matplotlib.figure...")
        from matplotlib.figure import Figure
        init_last = _init_print("[RENDER] matplotlib.figure imported")
        
        init_last = _init_print("[RENDER] Importing mpl_toolkits.mplot3d...")
        from mpl_toolkits.mplot3d import Axes3D
        init_last = _init_print("[RENDER] matplotlib 3D imported")
        
        # Store references
        self.FigureCanvas = FigureCanvas
        self.Figure = Figure
        
        # Create matplotlib figure
        init_last = _init_print("[RENDER] Creating matplotlib figure...")
        self.fig = self.Figure(figsize=(8, 6))
        init_last = _init_print("[RENDER] Figure created")
        
        init_last = _init_print("[RENDER] Creating FigureCanvas...")
        self.canvas = self.FigureCanvas(self.fig)
        init_last = _init_print("[RENDER] FigureCanvas created")
        
        init_last = _init_print("[RENDER] Creating 3D axes...")
        self.ax = self.fig.add_subplot(111, projection='3d')
        init_last = _init_print("[RENDER] 3D axes created")
        
        # Setup layout
        init_last = _init_print("[RENDER] Setting up layout...")
        layout = self._QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self._widget.setLayout(layout)
        init_last = _init_print("[RENDER] Layout set")
        
        # Set up the plot
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        self.ax.set_title('Hand Model')
        
        # Set fixed aspect ratio to prevent distortion
        # Hand spans roughly: X: -2 to 3, Y: -5 to 3, Z: -5 to 1
        # Use equal scaling to preserve proportions
        self.ax.set_box_aspect([1, 1, 0.5])
        
        # Set fixed axis limits to prevent auto-scaling distortion
        # Adjusted Y limits to accommodate full hand with bent fingers
        # Hand: wrist at y=-5, MCP joints at y=0.8-2.8, fingers extend forward when bent
        self.ax.set_xlim(-3, 3)
        self.ax.set_ylim(-6, 10)  # Extended to fit bent fingers (was -6 to 4)
        self.ax.set_zlim(-6, 2)
        
        # Hide axis tick labels (numbers) but keep grid
        self.ax.set_xticklabels([])
        self.ax.set_yticklabels([])
        self.ax.set_zticklabels([])
        
        # Keep grid visible
        self.ax.grid(True)
        
        # Throttling - don't update if one is in progress
        self._updating = False
        self._update_pending = False
        self._initialized = True
        
        # Base plane tilt state (degrees); mapped from IMU integration in app.py
        self._base_tilt_z_deg = 0.0
        self._base_tilt_y_deg = 0.0
        
        # Initial render
        init_last = _init_print("[RENDER] Performing initial render...")
        self.update_hand()
        _init_print("[RENDER] HandRenderWidget initialization complete!")
    
    
    def update_hand_model(self, hand_model: HandModel):
        """Update the hand model and refresh rendering."""
        self.hand_model = hand_model
        self.update_hand()
    
    def set_base_tilt(self, z_tilt_deg: float, y_tilt_deg: float):
        """Set glove-base plane tilt (degrees). Rendering is driven by caller."""
        self._base_tilt_z_deg = float(z_tilt_deg)
        self._base_tilt_y_deg = float(y_tilt_deg)
    
    def update_hand(self):
        """Update the 3D rendering of the hand."""
        # Skip if already updating (prevent queue buildup)
        if self._updating:
            self._update_pending = True
            return
        
        self._updating = True
        
        try:
            # Save current view angles before clearing (preserve user's rotation)
            elev = self.ax.elev
            azim = self.ax.azim
            
            # Clear the axes
            self.ax.clear()
            self.ax.set_xlabel('X')
            self.ax.set_ylabel('Y')
            self.ax.set_zlabel('Z')
            self.ax.set_title('Hand Model')
            
            # Hide axis tick labels (numbers) but keep grid
            self.ax.set_xticklabels([])
            self.ax.set_yticklabels([])
            self.ax.set_zticklabels([])
            self.ax.grid(True)
            
            # Finger colors and names
            finger_colors = [
                '#ff0000',  # Pinky - Red
                '#00ff00',  # Ring - Green
                '#0000ff',  # Middle - Blue
                '#ffff00',  # Index - Yellow
                '#ff00ff',  # Thumb - Magenta
            ]
            finger_names = self.hand_model.FINGER_NAMES
            
            # Draw fingers
            for finger_idx in range(5):
                segments = self.hand_model.get_finger_segments(finger_idx)
                color = finger_colors[finger_idx]
                
                for start, end in segments:
                    # Draw line segment
                    self.ax.plot3D(
                        [start[0], end[0]],
                        [start[1], end[1]],
                        [start[2], end[2]],
                        color=color,
                        linewidth=3,
                        marker='o',
                        markersize=4
                    )
            
            # Create legend using proxy artists (lines)
            from matplotlib.lines import Line2D
            legend_handles = [
                Line2D([0], [0], color=finger_colors[i], linewidth=3, marker='o', markersize=4, label=finger_names[i])
                for i in range(5)
            ]
            self.ax.legend(handles=legend_handles, loc='upper left', bbox_to_anchor=(0, 1))
            
            # Draw palm as wrist point connected to MCP joints
            palm_points = self.hand_model.get_palm_corners()
            wrist = palm_points[0]  # First point is wrist
            mcp_joints = palm_points[1:]  # Rest are MCP joints
            
            # Draw wrist point
            self.ax.scatter3D([wrist[0]], [wrist[1]], [wrist[2]], 
                            color='gray', s=50, marker='o')
            
            # Draw lines from wrist to each MCP joint
            for mcp in mcp_joints:
                self.ax.plot3D(
                    [wrist[0], mcp[0]],
                    [wrist[1], mcp[1]],
                    [wrist[2], mcp[2]],
                    color='gray', linewidth=2
                )
            
            # Draw a plane over the hand to visualize integrated glove-base tilt.
            # Mapping comes from app integration: gyro Z and Y channels drive tilt.
            palm_center = np.mean(np.array(mcp_joints), axis=0)
            plane_center = palm_center + np.array([0.0, 0.0, 1.4])
            half_side = 2.9
            local_corners = np.array([
                [-half_side, -half_side, 0.0],
                [ half_side, -half_side, 0.0],
                [ half_side,  half_side, 0.0],
                [-half_side,  half_side, 0.0],
            ])
            # Visual gain helps make subtle integrated-angle changes easier to see.
            visual_gain = 1.0
            z_rad = math.radians(self._base_tilt_z_deg * visual_gain)
            y_rad = math.radians(self._base_tilt_y_deg * visual_gain)
            # Pure tilt model (no in-plane spin): set plane height from two axis slopes.
            x = local_corners[:, 0]
            y = local_corners[:, 1]
            local_corners[:, 2] = np.tan(y_rad) * x + np.tan(z_rad) * y
            world_corners = local_corners + plane_center
            self.ax.plot_trisurf(
                world_corners[:, 0],
                world_corners[:, 1],
                world_corners[:, 2],
                triangles=[[0, 1, 2], [0, 2, 3]],
                color='#ff9aa2',
                alpha=0.45,
                edgecolor='none',
                linewidth=0.0,
            )
            
            # Set equal aspect ratio
            self.ax.set_box_aspect([1, 1, 0.5])
            
            # Restore the view angles (preserves user's rotation)
            self.ax.view_init(elev=elev, azim=azim)
            
            # Keep fixed axis limits to prevent auto-scaling distortion
            # Adjusted Y limits to accommodate full hand with bent fingers
            self.ax.set_xlim(-3, 3)
            self.ax.set_ylim(-6, 10)  # Extended to fit bent fingers
            self.ax.set_zlim(-6, 2)
            
            # Update canvas (this can be slow, so we throttle)
            self.canvas.draw()
            
        finally:
            self._updating = False
            # If another update was requested while we were updating, do it now
            if self._update_pending:
                self._update_pending = False
                QTimer.singleShot(0, self.update_hand)
    
    def set_smoothing(self, alpha: float):
        """Set smoothing factor for hand model."""
        self.hand_model.set_smoothing(alpha)
    
    def reset_camera(self):
        """Reset camera to default position."""
        self.ax.view_init(elev=20, azim=45)
        self.canvas.draw()
