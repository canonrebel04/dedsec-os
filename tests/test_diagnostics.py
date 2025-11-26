"""
Unit tests for Diagnostics Overlay

Tests FPS counter, memory tracking, CPU monitoring, and touch logging.
"""

import unittest
from unittest.mock import MagicMock, patch
from ui.diagnostics import (
    DiagnosticsOverlay,
    FPSCounter,
    MemoryTracker,
    CPUMonitor,
    TouchLogger,
    FrameTimer,
    create_diagnostics_overlay,
)
import time


class TestFPSCounter(unittest.TestCase):
    """Tests for FPS counter."""

    def test_initialization(self):
        """Test FPS counter initializes correctly."""
        fps = FPSCounter(window_size=30)

        self.assertEqual(fps.current_fps, 0.0)
        self.assertEqual(len(fps.frame_times), 0)

    def test_tick_updates_fps(self):
        """Test ticking updates FPS."""
        fps = FPSCounter()

        fps.tick()
        time.sleep(0.01)
        fps.tick()

        self.assertGreater(fps.get_fps(), 0)

    def test_avg_frame_time(self):
        """Test average frame time calculation."""
        fps = FPSCounter()

        fps.tick()
        time.sleep(0.01)
        fps.tick()

        avg = fps.get_avg_frame_time()
        self.assertGreater(avg, 0)


class TestMemoryTracker(unittest.TestCase):
    """Tests for memory tracker."""

    @patch("psutil.Process")
    def test_initialization(self, mock_process):
        """Test memory tracker initializes."""
        tracker = MemoryTracker()

        self.assertEqual(tracker.current_mb, 0.0)
        self.assertEqual(tracker.current_percent, 0.0)

    @patch("psutil.Process")
    def test_update(self, mock_process):
        """Test memory update."""
        mock_instance = mock_process.return_value
        mock_instance.memory_info.return_value = MagicMock(rss=10485760)  # 10 MB
        mock_instance.memory_percent.return_value = 5.0

        tracker = MemoryTracker()
        tracker.update()

        self.assertEqual(tracker.get_mb(), 10.0)
        self.assertEqual(tracker.get_percent(), 5.0)


class TestCPUMonitor(unittest.TestCase):
    """Tests for CPU monitor."""

    @patch("psutil.Process")
    @patch("psutil.cpu_percent")
    def test_initialization(self, mock_cpu_percent, mock_process):
        """Test CPU monitor initializes."""
        monitor = CPUMonitor(interval=1.0)

        self.assertEqual(monitor.current_percent, 0.0)
        self.assertEqual(monitor.system_percent, 0.0)

    @patch("psutil.Process")
    @patch("psutil.cpu_percent")
    def test_update(self, mock_cpu_percent, mock_process):
        """Test CPU update."""
        mock_instance = mock_process.return_value
        mock_instance.cpu_percent.return_value = 15.0
        mock_cpu_percent.return_value = 50.0

        monitor = CPUMonitor(interval=0.1)
        time.sleep(0.2)
        monitor.update()

        self.assertEqual(monitor.get_process_percent(), 15.0)
        self.assertEqual(monitor.get_system_percent(), 50.0)


class TestTouchLogger(unittest.TestCase):
    """Tests for touch logger."""

    def test_initialization(self):
        """Test touch logger initializes."""
        logger = TouchLogger(max_events=5)

        self.assertEqual(logger.get_event_count(), 0)
        self.assertEqual(len(logger.get_recent_events()), 0)

    def test_log_event(self):
        """Test logging touch events."""
        logger = TouchLogger()

        logger.log_event(100, 150, "click")
        logger.log_event(200, 250, "press")

        self.assertEqual(logger.get_event_count(), 2)

        events = logger.get_recent_events(2)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["x"], 100)
        self.assertEqual(events[0]["y"], 150)
        self.assertEqual(events[0]["type"], "click")

    def test_max_events_limit(self):
        """Test max events limit."""
        logger = TouchLogger(max_events=3)

        for i in range(10):
            logger.log_event(i, i, "click")

        events = logger.get_recent_events(10)
        self.assertEqual(len(events), 3)  # Should only keep last 3


class TestFrameTimer(unittest.TestCase):
    """Tests for frame timer."""

    def test_initialization(self):
        """Test frame timer initializes."""
        timer = FrameTimer()

        stats = timer.get_stats()
        self.assertEqual(stats["min"], 0.0)
        self.assertEqual(stats["max"], 0.0)
        self.assertEqual(stats["avg"], 0.0)

    def test_tick_records_timing(self):
        """Test tick records frame timing."""
        timer = FrameTimer()

        timer.tick()
        time.sleep(0.01)
        timer.tick()

        stats = timer.get_stats()
        self.assertGreater(stats["avg"], 0)

    def test_get_history(self):
        """Test getting frame time history."""
        timer = FrameTimer(history_size=5)

        for _ in range(10):
            timer.tick()
            time.sleep(0.01)

        history = timer.get_history()
        self.assertEqual(len(history), 5)  # Limited by history_size


class TestDiagnosticsOverlay(unittest.TestCase):
    """Tests for diagnostics overlay."""

    def setUp(self):
        """Set up test fixtures."""
        self.canvas = MagicMock()

    def test_initialization(self):
        """Test overlay initializes correctly."""
        overlay = DiagnosticsOverlay(self.canvas, enabled=True)

        self.assertTrue(overlay.enabled)
        self.assertIsNotNone(overlay.fps_counter)
        self.assertIsNotNone(overlay.memory_tracker)
        self.assertIsNotNone(overlay.cpu_monitor)

    def test_enable_disable(self):
        """Test enabling/disabling overlay."""
        overlay = DiagnosticsOverlay(self.canvas, enabled=False)

        self.assertFalse(overlay.enabled)

        overlay.enable()
        self.assertTrue(overlay.enabled)

        overlay.disable()
        self.assertFalse(overlay.enabled)

    def test_toggle(self):
        """Test toggling overlay."""
        overlay = DiagnosticsOverlay(self.canvas, enabled=False)

        overlay.toggle()
        self.assertTrue(overlay.enabled)

        overlay.toggle()
        self.assertFalse(overlay.enabled)

    def test_update(self):
        """Test update calls component updates."""
        overlay = DiagnosticsOverlay(self.canvas, enabled=True)

        # Should not raise errors
        overlay.update()

    def test_log_touch(self):
        """Test logging touch events."""
        overlay = DiagnosticsOverlay(self.canvas)

        overlay.log_touch(100, 200, "click")

        events = overlay.touch_logger.get_recent_events(1)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["x"], 100)
        self.assertEqual(events[0]["y"], 200)

    def test_draw_when_enabled(self):
        """Test draw creates canvas items when enabled."""
        overlay = DiagnosticsOverlay(self.canvas, enabled=True)
        overlay.draw()

        # Should have created canvas items
        self.assertGreater(len(overlay.canvas_items), 0)

        # Canvas methods should have been called
        self.canvas.create_rectangle.assert_called()
        self.canvas.create_text.assert_called()

    def test_draw_when_disabled(self):
        """Test draw does nothing when disabled."""
        overlay = DiagnosticsOverlay(self.canvas, enabled=False)
        overlay.draw()

        # Should not create any items
        self.assertEqual(len(overlay.canvas_items), 0)
        self.canvas.create_rectangle.assert_not_called()

    def test_clear(self):
        """Test clearing overlay."""
        overlay = DiagnosticsOverlay(self.canvas, enabled=True)

        # Draw to create items
        overlay.draw()
        initial_count = len(overlay.canvas_items)
        self.assertGreater(initial_count, 0)

        # Clear
        overlay.clear()
        self.assertEqual(len(overlay.canvas_items), 0)
        self.canvas.delete.assert_called()

    def test_position_variants(self):
        """Test different overlay positions."""
        positions = ["top-left", "top-right", "bottom-left", "bottom-right"]

        for pos in positions:
            overlay = DiagnosticsOverlay(self.canvas, enabled=True, position=pos)
            x, y = overlay._get_position_coords()

            self.assertIsInstance(x, int)
            self.assertIsInstance(y, int)


class TestFactoryFunction(unittest.TestCase):
    """Tests for factory function."""

    def test_create_diagnostics_overlay(self):
        """Test factory function creates overlay."""
        canvas = MagicMock()
        overlay = create_diagnostics_overlay(canvas, enabled=True)

        self.assertIsInstance(overlay, DiagnosticsOverlay)
        self.assertTrue(overlay.enabled)
        self.assertEqual(overlay.canvas, canvas)


if __name__ == "__main__":
    unittest.main()
