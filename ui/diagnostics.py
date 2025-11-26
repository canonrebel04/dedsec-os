"""
Diagnostics Overlay for DedSec OS (Phase 3.2 - Task #18)

Provides real-time performance monitoring and debugging information
displayed as an overlay on the UI. Includes FPS counter, memory tracking,
CPU usage, touch event logging, and frame timing graphs.

Classes:
    - DiagnosticsOverlay: Main overlay manager
    - FPSCounter: Frames-per-second measurement
    - MemoryTracker: Memory usage monitoring
    - CPUMonitor: CPU usage tracking
    - TouchLogger: Touch/click event logger
    - FrameTimer: Frame timing analysis

Usage:
    overlay = DiagnosticsOverlay(canvas, enabled=DEBUG_MODE)
    # In main loop:
    overlay.update()
    overlay.draw()
"""

import time
import psutil
import os
from typing import List, Dict, Optional, Tuple
from collections import deque


class FPSCounter:
    """
    Tracks frames per second for performance monitoring.

    Uses a rolling window to smooth out FPS measurements.
    """

    def __init__(self, window_size: int = 60):
        """
        Initialize FPS counter.

        Args:
            window_size: Number of frames to average over
        """
        self.frame_times: deque = deque(maxlen=window_size)
        self.last_frame_time = time.time()
        self.current_fps = 0.0

    def tick(self):
        """Record a frame and update FPS calculation."""
        current_time = time.time()
        frame_duration = current_time - self.last_frame_time
        self.last_frame_time = current_time

        if frame_duration > 0:
            self.frame_times.append(frame_duration)

        # Calculate FPS from average frame time
        if len(self.frame_times) > 0:
            avg_frame_time = sum(self.frame_times) / len(self.frame_times)
            if avg_frame_time > 0:
                self.current_fps = 1.0 / avg_frame_time

    def get_fps(self) -> float:
        """Get current FPS."""
        return self.current_fps

    def get_avg_frame_time(self) -> float:
        """Get average frame time in milliseconds."""
        if len(self.frame_times) > 0:
            return (sum(self.frame_times) / len(self.frame_times)) * 1000
        return 0.0


class MemoryTracker:
    """
    Tracks memory usage of the current process.

    Monitors RAM consumption and provides percentage and MB values.
    """

    def __init__(self):
        """Initialize memory tracker."""
        self.process = psutil.Process(os.getpid())
        self.current_mb = 0.0
        self.current_percent = 0.0

    def update(self):
        """Update memory statistics."""
        try:
            mem_info = self.process.memory_info()
            self.current_mb = mem_info.rss / 1024 / 1024  # Convert to MB
            self.current_percent = self.process.memory_percent()
        except Exception:
            pass  # Ignore errors if process info unavailable

    def get_mb(self) -> float:
        """Get current memory usage in MB."""
        return self.current_mb

    def get_percent(self) -> float:
        """Get current memory usage as percentage."""
        return self.current_percent


class CPUMonitor:
    """
    Tracks CPU usage of the current process.

    Provides both process-specific and system-wide CPU metrics.
    """

    def __init__(self, interval: float = 1.0):
        """
        Initialize CPU monitor.

        Args:
            interval: Measurement interval in seconds
        """
        self.process = psutil.Process(os.getpid())
        self.interval = interval
        self.last_update = time.time()
        self.current_percent = 0.0
        self.system_percent = 0.0

    def update(self):
        """Update CPU statistics."""
        current_time = time.time()

        # Only update at specified interval
        if current_time - self.last_update >= self.interval:
            try:
                self.current_percent = self.process.cpu_percent()
                self.system_percent = psutil.cpu_percent()
                self.last_update = current_time
            except Exception:
                pass  # Ignore errors

    def get_process_percent(self) -> float:
        """Get current process CPU usage percentage."""
        return self.current_percent

    def get_system_percent(self) -> float:
        """Get system-wide CPU usage percentage."""
        return self.system_percent


class TouchLogger:
    """
    Logs touch/click events for debugging touch responsiveness.

    Maintains a rolling log of recent events with timestamps and coordinates.
    """

    def __init__(self, max_events: int = 10):
        """
        Initialize touch logger.

        Args:
            max_events: Maximum events to keep in history
        """
        self.events: deque = deque(maxlen=max_events)
        self.event_count = 0

    def log_event(self, x: int, y: int, event_type: str = "click"):
        """
        Log a touch/click event.

        Args:
            x: X coordinate
            y: Y coordinate
            event_type: Type of event (click, press, release, etc.)
        """
        timestamp = time.time()
        self.events.append(
            {"timestamp": timestamp, "x": x, "y": y, "type": event_type, "count": self.event_count}
        )
        self.event_count += 1

    def get_recent_events(self, count: int = 5) -> List[Dict]:
        """
        Get most recent events.

        Args:
            count: Number of events to return

        Returns:
            List of event dictionaries
        """
        return list(self.events)[-count:]

    def get_event_count(self) -> int:
        """Get total event count since start."""
        return self.event_count


class FrameTimer:
    """
    Analyzes frame timing for performance debugging.

    Tracks minimum, maximum, and average frame times with history.
    """

    def __init__(self, history_size: int = 120):
        """
        Initialize frame timer.

        Args:
            history_size: Number of frames to keep in history
        """
        self.history: deque = deque(maxlen=history_size)
        self.min_frame_time = float("inf")
        self.max_frame_time = 0.0
        self.last_frame_time = time.time()

    def tick(self):
        """Record a frame timing."""
        current_time = time.time()
        frame_duration = current_time - self.last_frame_time
        self.last_frame_time = current_time

        if frame_duration > 0:
            self.history.append(frame_duration)
            self.min_frame_time = min(self.min_frame_time, frame_duration)
            self.max_frame_time = max(self.max_frame_time, frame_duration)

    def get_stats(self) -> Dict[str, float]:
        """
        Get frame timing statistics.

        Returns:
            Dict with 'min', 'max', 'avg' in milliseconds
        """
        if len(self.history) == 0:
            return {"min": 0.0, "max": 0.0, "avg": 0.0}

        avg = sum(self.history) / len(self.history)
        return {
            "min": self.min_frame_time * 1000,  # Convert to ms
            "max": self.max_frame_time * 1000,
            "avg": avg * 1000,
        }

    def get_history(self) -> List[float]:
        """Get frame time history in milliseconds."""
        return [t * 1000 for t in self.history]


class DiagnosticsOverlay:
    """
    Main diagnostics overlay manager.

    Coordinates all diagnostic components and handles rendering.
    """

    def __init__(
        self,
        canvas,
        enabled: bool = False,
        position: str = "top-right",
        bg_color: str = "#000000",
        fg_color: str = "#00ff00",
        opacity: float = 0.8,
    ):
        """
        Initialize diagnostics overlay.

        Args:
            canvas: Tkinter canvas to draw on
            enabled: Whether overlay is initially enabled
            position: Overlay position ('top-left', 'top-right', 'bottom-left', 'bottom-right')
            bg_color: Background color
            fg_color: Foreground (text) color
            opacity: Background opacity (0.0 to 1.0)
        """
        self.canvas = canvas
        self.enabled = enabled
        self.position = position
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.opacity = opacity

        # Initialize components
        self.fps_counter = FPSCounter()
        self.memory_tracker = MemoryTracker()
        self.cpu_monitor = CPUMonitor()
        self.touch_logger = TouchLogger()
        self.frame_timer = FrameTimer()

        # Canvas items for rendering
        self.canvas_items: List[int] = []

        # Display options
        self.show_fps = True
        self.show_memory = True
        self.show_cpu = True
        self.show_frame_times = True
        self.show_touch_log = False  # Off by default (takes space)

    def enable(self):
        """Enable the overlay."""
        self.enabled = True

    def disable(self):
        """Disable the overlay and clear from canvas."""
        self.enabled = False
        self.clear()

    def toggle(self):
        """Toggle overlay on/off."""
        if self.enabled:
            self.disable()
        else:
            self.enable()

    def update(self):
        """Update all diagnostic components."""
        if not self.enabled:
            return

        self.fps_counter.tick()
        self.memory_tracker.update()
        self.cpu_monitor.update()
        self.frame_timer.tick()

    def log_touch(self, x: int, y: int, event_type: str = "click"):
        """Log a touch event."""
        self.touch_logger.log_event(x, y, event_type)

    def clear(self):
        """Remove overlay from canvas."""
        for item_id in self.canvas_items:
            try:
                self.canvas.delete(item_id)
            except:
                pass
        self.canvas_items.clear()

    def _get_position_coords(self) -> Tuple[int, int]:
        """Get x, y coordinates based on position setting."""
        if self.position == "top-left":
            return (5, 5)
        elif self.position == "top-right":
            return (220, 5)
        elif self.position == "bottom-left":
            return (5, 180)
        else:  # bottom-right
            return (220, 180)

    def draw(self):
        """Draw the diagnostics overlay."""
        if not self.enabled:
            return

        # Clear previous frame
        self.clear()

        # Get position
        x, y = self._get_position_coords()

        # Build text content
        lines = []

        if self.show_fps:
            fps = self.fps_counter.get_fps()
            lines.append(f"FPS: {fps:.1f}")

        if self.show_memory:
            mem_mb = self.memory_tracker.get_mb()
            mem_pct = self.memory_tracker.get_percent()
            lines.append(f"RAM: {mem_mb:.1f}MB ({mem_pct:.1f}%)")

        if self.show_cpu:
            cpu_proc = self.cpu_monitor.get_process_percent()
            cpu_sys = self.cpu_monitor.get_system_percent()
            lines.append(f"CPU: {cpu_proc:.1f}% / {cpu_sys:.1f}%")

        if self.show_frame_times:
            stats = self.frame_timer.get_stats()
            lines.append(f"Frame: {stats['avg']:.1f}ms")
            lines.append(f"Min/Max: {stats['min']:.1f}/{stats['max']:.1f}ms")

        if self.show_touch_log:
            events = self.touch_logger.get_recent_events(3)
            if events:
                lines.append("--- Touches ---")
                for event in events:
                    lines.append(f"{event['type']}: ({event['x']},{event['y']})")

        # Calculate dimensions
        line_height = 12
        padding = 5
        width = 95
        height = len(lines) * line_height + padding * 2

        # Draw background
        bg_id = self.canvas.create_rectangle(
            x,
            y,
            x + width,
            y + height,
            fill=self.bg_color,
            outline=self.fg_color,
            width=1,
            tags="diagnostics",
        )
        self.canvas_items.append(bg_id)

        # Draw text lines
        text_y = y + padding + 6
        for line in lines:
            text_id = self.canvas.create_text(
                x + padding,
                text_y,
                text=line,
                fill=self.fg_color,
                font=("monospace", 8),
                anchor="w",
                tags="diagnostics",
            )
            self.canvas_items.append(text_id)
            text_y += line_height

        # Ensure overlay is on top
        self.canvas.tag_raise("diagnostics")


# Convenience function for easy integration
def create_diagnostics_overlay(canvas, enabled: bool = False) -> DiagnosticsOverlay:
    """
    Create a diagnostics overlay with default settings.

    Args:
        canvas: Tkinter canvas to draw on
        enabled: Whether to enable immediately

    Returns:
        Configured DiagnosticsOverlay instance
    """
    return DiagnosticsOverlay(
        canvas=canvas,
        enabled=enabled,
        position="top-right",
        bg_color="#000000",
        fg_color="#00ff00",
        opacity=0.8,
    )
