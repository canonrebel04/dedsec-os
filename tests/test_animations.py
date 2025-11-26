"""
Unit tests for Animation System

Tests all animation classes and the animation manager.
"""

import unittest
from unittest.mock import MagicMock
from ui.animations import (
    Animator,
    ColorGradient,
    PulsingEffect,
    GlitchEffect,
    FadeTransition,
    MatrixRain,
    AnimationManager,
    create_button_press_animation,
    create_status_pulse,
    create_logo_glitch,
    create_fade_in,
    create_fade_out,
    create_matrix_background
)


class TestColorGradient(unittest.TestCase):
    """Tests for ColorGradient animation."""
    
    def test_initialization(self):
        """Test gradient initializes correctly."""
        gradient = ColorGradient("#ff0000", "#0000ff", duration_frames=10)
        
        self.assertEqual(gradient.start_rgb, (255, 0, 0))
        self.assertEqual(gradient.end_rgb, (0, 0, 255))
        self.assertEqual(gradient.duration_frames, 10)
    
    def test_gradient_start(self):
        """Test gradient at start."""
        gradient = ColorGradient("#ff0000", "#0000ff", duration_frames=10)
        gradient.start()
        
        # First frame should be start color
        color = gradient.update()
        self.assertEqual(color, "#ff0000")
    
    def test_gradient_progress(self):
        """Test gradient progresses through frames."""
        gradient = ColorGradient("#000000", "#ffffff", duration_frames=2)
        gradient.start()
        
        # Frame 0: #000000
        color1 = gradient.update()
        self.assertEqual(color1, "#000000")
        
        # Frame 1: ~#808080
        color2 = gradient.update()
        self.assertNotEqual(color2, "#000000")
        self.assertNotEqual(color2, "#ffffff")
        
        # Frame 2: #ffffff
        color3 = gradient.update()
        self.assertEqual(color3, "#ffffff")
    
    def test_gradient_completion(self):
        """Test gradient completes."""
        gradient = ColorGradient("#ff0000", "#0000ff", duration_frames=5, loop=False)
        gradient.start()
        
        # Run through all frames
        for _ in range(6):
            gradient.update()
        
        self.assertTrue(gradient.is_complete)


class TestPulsingEffect(unittest.TestCase):
    """Tests for PulsingEffect animation."""
    
    def test_initialization(self):
        """Test pulse initializes correctly."""
        pulse = PulsingEffect(min_value=0.5, max_value=1.0, duration_frames=30)
        
        self.assertEqual(pulse.min_value, 0.5)
        self.assertEqual(pulse.max_value, 1.0)
        self.assertEqual(pulse.duration_frames, 30)
    
    def test_pulse_range(self):
        """Test pulse stays in range."""
        pulse = PulsingEffect(min_value=0.5, max_value=1.0, duration_frames=20, loop=True)
        pulse.start()
        
        # Test many frames
        for _ in range(100):
            value = pulse.update()
            self.assertGreaterEqual(value, 0.5)
            self.assertLessEqual(value, 1.0)
    
    def test_pulse_cycles(self):
        """Test pulse cycles when looping."""
        pulse = PulsingEffect(min_value=0.0, max_value=1.0, duration_frames=4, loop=True)
        pulse.start()
        
        values = []
        for _ in range(12):  # 3 complete cycles
            values.append(pulse.update())
        
        # Should oscillate
        self.assertGreater(max(values), 0.9)
        self.assertLess(min(values), 0.1)


class TestGlitchEffect(unittest.TestCase):
    """Tests for GlitchEffect animation."""
    
    def test_initialization(self):
        """Test glitch initializes correctly."""
        glitch = GlitchEffect(
            glitch_texts=["ERROR", "HACK"],
            glitch_colors=["#ff0000", "#00ff00"],
            glitch_chance=0.5
        )
        
        self.assertEqual(len(glitch.glitch_texts), 2)
        self.assertEqual(len(glitch.glitch_colors), 2)
        self.assertEqual(glitch.glitch_chance, 0.5)
    
    def test_set_normal_state(self):
        """Test setting normal state."""
        glitch = GlitchEffect(
            glitch_texts=["ERR"],
            glitch_colors=["#f00"]
        )
        glitch.set_normal_state("NORMAL", "#0f0")
        
        self.assertEqual(glitch.normal_text, "NORMAL")
        self.assertEqual(glitch.normal_color, "#0f0")
    
    def test_glitch_output_structure(self):
        """Test glitch output has correct structure."""
        glitch = GlitchEffect(
            glitch_texts=["GLITCH"],
            glitch_colors=["#ff0000"],
            glitch_chance=1.0  # Always glitch for testing
        )
        glitch.set_normal_state("NORMAL", "#00ff00")
        glitch.start()
        
        result = glitch.update()
        
        self.assertIn('text', result)
        self.assertIn('color', result)
        self.assertIn('offset_x', result)
        self.assertIn('offset_y', result)
        self.assertIn('is_glitching', result)


class TestFadeTransition(unittest.TestCase):
    """Tests for FadeTransition animation."""
    
    def test_fade_in(self):
        """Test fade in from 0 to 1."""
        fade = FadeTransition(fade_in=True, duration_frames=10, loop=False)
        fade.start()
        
        # First frame should be near 0
        opacity1 = fade.update()
        self.assertLess(opacity1, 0.2)
        
        # Run to completion
        for _ in range(10):
            opacity = fade.update()
        
        # Last frame should be near 1
        self.assertGreater(opacity, 0.8)
    
    def test_fade_out(self):
        """Test fade out from 1 to 0."""
        fade = FadeTransition(fade_in=False, duration_frames=10, loop=False)
        fade.start()
        
        # First frame should be near 1
        opacity1 = fade.update()
        self.assertGreater(opacity1, 0.8)
        
        # Run to completion
        for _ in range(10):
            opacity = fade.update()
        
        # Last frame should be near 0
        self.assertLess(opacity, 0.2)
    
    def test_fade_range(self):
        """Test fade stays in 0-1 range."""
        fade = FadeTransition(fade_in=True, duration_frames=5)
        fade.start()
        
        for _ in range(10):
            opacity = fade.update()
            self.assertGreaterEqual(opacity, 0.0)
            self.assertLessEqual(opacity, 1.0)


class TestMatrixRain(unittest.TestCase):
    """Tests for MatrixRain animation."""
    
    def test_initialization(self):
        """Test matrix rain initializes correctly."""
        matrix = MatrixRain(max_chars=5)
        
        self.assertEqual(matrix.max_chars, 5)
        self.assertGreaterEqual(len(matrix.active_chars), 0)
    
    def test_output_structure(self):
        """Test matrix rain output structure."""
        matrix = MatrixRain(max_chars=3)
        matrix.start()
        
        result = matrix.update()
        
        self.assertIsInstance(result, list)
        
        for char_data in result:
            self.assertIn('char', char_data)
            self.assertIn('x', char_data)
            self.assertIn('y', char_data)
            self.assertIn('color', char_data)
            self.assertIn('brightness_step', char_data)
    
    def test_characters_fall(self):
        """Test characters move downward."""
        matrix = MatrixRain(max_chars=1)
        matrix.start()
        
        # Get initial state
        result1 = matrix.update()
        if len(result1) > 0:
            initial_y = result1[0]['y']
            
            # Update several times
            for _ in range(5):
                matrix.update()
            
            result2 = matrix.update()
            if len(result2) > 0:
                # Y should increase (falling down)
                self.assertGreaterEqual(result2[0]['y'], initial_y)


class TestAnimationManager(unittest.TestCase):
    """Tests for AnimationManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = AnimationManager()
    
    def test_initialization(self):
        """Test manager initializes empty."""
        self.assertEqual(len(self.manager.animations), 0)
    
    def test_register_animation(self):
        """Test registering animations."""
        anim = ColorGradient("#000", "#fff", duration_frames=10)
        
        self.manager.register("test", anim)
        
        self.assertEqual(len(self.manager.animations), 1)
        self.assertIn("test", self.manager.animations)
    
    def test_unregister_animation(self):
        """Test unregistering animations."""
        anim = ColorGradient("#000", "#fff", duration_frames=10)
        
        self.manager.register("test", anim)
        self.manager.unregister("test")
        
        self.assertEqual(len(self.manager.animations), 0)
    
    def test_get_animation(self):
        """Test retrieving registered animation."""
        anim = ColorGradient("#000", "#fff", duration_frames=10)
        
        self.manager.register("test", anim)
        retrieved = self.manager.get("test")
        
        self.assertEqual(retrieved, anim)
    
    def test_start_animation(self):
        """Test starting animation."""
        anim = ColorGradient("#000", "#fff", duration_frames=10)
        
        self.manager.register("test", anim)
        self.manager.start("test")
        
        self.assertTrue(anim.is_running)
    
    def test_stop_animation(self):
        """Test stopping animation."""
        anim = ColorGradient("#000", "#fff", duration_frames=10)
        
        self.manager.register("test", anim)
        self.manager.start("test")
        self.manager.stop("test")
        
        self.assertFalse(anim.is_running)
    
    def test_update_all(self):
        """Test updating all animations."""
        anim1 = ColorGradient("#000", "#fff", duration_frames=5)
        anim2 = PulsingEffect(loop=True)
        
        self.manager.register("grad", anim1)
        self.manager.register("pulse", anim2)
        
        self.manager.start_all()
        results = self.manager.update_all()
        
        self.assertIn("grad", results)
        self.assertIn("pulse", results)


class TestFactoryFunctions(unittest.TestCase):
    """Tests for animation factory functions."""
    
    def test_create_button_press_animation(self):
        """Test button press animation creation."""
        anim = create_button_press_animation()
        
        self.assertIsInstance(anim, ColorGradient)
        self.assertEqual(anim.duration_frames, 5)
    
    def test_create_status_pulse(self):
        """Test status pulse creation."""
        anim = create_status_pulse()
        
        self.assertIsInstance(anim, PulsingEffect)
        self.assertTrue(anim.loop)
    
    def test_create_logo_glitch(self):
        """Test logo glitch creation."""
        anim = create_logo_glitch()
        
        self.assertIsInstance(anim, GlitchEffect)
    
    def test_create_fade_in(self):
        """Test fade in creation."""
        anim = create_fade_in(duration_frames=20)
        
        self.assertIsInstance(anim, FadeTransition)
        self.assertEqual(anim.duration_frames, 20)
    
    def test_create_fade_out(self):
        """Test fade out creation."""
        anim = create_fade_out(duration_frames=15)
        
        self.assertIsInstance(anim, FadeTransition)
        self.assertEqual(anim.duration_frames, 15)
    
    def test_create_matrix_background(self):
        """Test matrix background creation."""
        anim = create_matrix_background()
        
        self.assertIsInstance(anim, MatrixRain)


if __name__ == '__main__':
    unittest.main()
