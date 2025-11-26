"""
Animation System for DedSec OS UI (Phase 3.2 - Task #14)

Provides reusable animation classes for UI effects including gradients,
pulsing, glitch effects, fades, and matrix rain. Integrates with ThemeManager
for color consistency and uses centralized TIMINGS config.

Classes:
    - Animator: Base class for all animations
    - ColorGradient: Smooth color transitions
    - PulsingEffect: Rhythmic opacity/scale changes
    - GlitchEffect: Cyberpunk-style screen distortions
    - FadeTransition: Opacity fade in/out
    - MatrixRain: Falling matrix characters
    
Architecture:
    - Frame-based updates (not time-based for Pi 2 performance)
    - Reusable animation instances
    - Canvas item manipulation
    - Theme-aware colors
"""

import random
import math
from typing import Callable, Optional, Tuple, List, Dict, Any
from abc import ABC, abstractmethod


class Animator(ABC):
    """
    Base class for all animations.
    
    Provides common functionality for frame-based animations with
    start/stop/reset controls and completion callbacks.
    """
    
    def __init__(self, duration_frames: int = 30, loop: bool = False):
        """
        Initialize animator.
        
        Args:
            duration_frames: Number of frames for one animation cycle
            loop: Whether to loop the animation continuously
        """
        self.duration_frames = duration_frames
        self.loop = loop
        self.current_frame = 0
        self.is_running = False
        self.is_complete = False
        self.on_complete: Optional[Callable] = None
    
    def start(self):
        """Start the animation from current frame."""
        self.is_running = True
        self.is_complete = False
    
    def stop(self):
        """Pause the animation."""
        self.is_running = False
    
    def reset(self):
        """Reset animation to beginning."""
        self.current_frame = 0
        self.is_complete = False
    
    def set_on_complete(self, callback: Callable):
        """Set callback to execute when animation completes."""
        self.on_complete = callback
    
    @abstractmethod
    def update(self) -> Any:
        """
        Update animation by one frame.
        
        Returns:
            Animation state/value for this frame
        """
        pass
    
    def _advance_frame(self):
        """Advance to next frame, handling loop/completion."""
        if not self.is_running:
            return
        
        self.current_frame += 1
        
        if self.current_frame >= self.duration_frames:
            if self.loop:
                self.current_frame = 0
            else:
                self.is_complete = True
                self.is_running = False
                if self.on_complete:
                    self.on_complete()
    
    def get_progress(self) -> float:
        """Get animation progress as 0.0 to 1.0."""
        if self.duration_frames == 0:
            return 1.0
        return min(1.0, self.current_frame / self.duration_frames)


class ColorGradient(Animator):
    """
    Smooth color transition between two colors.
    
    Interpolates RGB values linearly over the animation duration.
    """
    
    def __init__(self, start_color: str, end_color: str, 
                 duration_frames: int = 30, loop: bool = False):
        """
        Initialize color gradient.
        
        Args:
            start_color: Starting color in hex format (e.g., '#00FF00')
            end_color: Ending color in hex format
            duration_frames: Frames for full transition
            loop: Whether to loop continuously
        """
        super().__init__(duration_frames, loop)
        self.start_rgb = self._hex_to_rgb(start_color)
        self.end_rgb = self._hex_to_rgb(end_color)
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b)
    
    def _rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex color."""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    
    def update(self) -> str:
        """
        Get current color in gradient.
        
        Returns:
            Hex color string for current frame
        """
        progress = self.get_progress()
        
        # Interpolate each RGB component
        r = int(self.start_rgb[0] + (self.end_rgb[0] - self.start_rgb[0]) * progress)
        g = int(self.start_rgb[1] + (self.end_rgb[1] - self.start_rgb[1]) * progress)
        b = int(self.start_rgb[2] + (self.end_rgb[2] - self.start_rgb[2]) * progress)
        
        self._advance_frame()
        return self._rgb_to_hex((r, g, b))


class PulsingEffect(Animator):
    """
    Rhythmic pulsing effect using sine wave.
    
    Creates smooth expansion/contraction or brightness changes.
    """
    
    def __init__(self, min_value: float = 0.5, max_value: float = 1.0,
                 duration_frames: int = 30, loop: bool = True):
        """
        Initialize pulsing effect.
        
        Args:
            min_value: Minimum value (e.g., 0.5 for 50% opacity)
            max_value: Maximum value (e.g., 1.0 for 100% opacity)
            duration_frames: Frames for one complete pulse cycle
            loop: Whether to loop (typically True for pulsing)
        """
        super().__init__(duration_frames, loop)
        self.min_value = min_value
        self.max_value = max_value
        self.value_range = max_value - min_value
    
    def update(self) -> float:
        """
        Get current pulse value.
        
        Returns:
            Value between min_value and max_value following sine wave
        """
        # Use sine wave for smooth pulsing
        progress = self.get_progress()
        sine_value = math.sin(progress * 2 * math.pi)
        
        # Map sine (-1 to 1) to our value range
        normalized = (sine_value + 1) / 2  # 0 to 1
        value = self.min_value + (normalized * self.value_range)
        
        self._advance_frame()
        return value


class GlitchEffect(Animator):
    """
    Cyberpunk-style glitch effect with random distortions.
    
    Provides random text, color, and position changes for glitch aesthetic.
    """
    
    def __init__(self, glitch_texts: List[str], glitch_colors: List[str],
                 glitch_chance: float = 0.3, duration_frames: int = 60, loop: bool = True):
        """
        Initialize glitch effect.
        
        Args:
            glitch_texts: List of possible glitch text variations
            glitch_colors: List of possible glitch colors
            glitch_chance: Probability of glitch on each frame (0.0 to 1.0)
            duration_frames: Frames per cycle
            loop: Whether to loop continuously
        """
        super().__init__(duration_frames, loop)
        self.glitch_texts = glitch_texts
        self.glitch_colors = glitch_colors
        self.glitch_chance = glitch_chance
        self.normal_text: Optional[str] = None
        self.normal_color: Optional[str] = None
    
    def set_normal_state(self, text: str, color: str):
        """Set the normal (non-glitched) state."""
        self.normal_text = text
        self.normal_color = color
    
    def update(self) -> Dict[str, Any]:
        """
        Get current glitch state.
        
        Returns:
            Dict with 'text', 'color', 'offset_x', 'offset_y', 'is_glitching'
        """
        is_glitching = random.random() < self.glitch_chance
        
        if is_glitching:
            result = {
                'text': random.choice(self.glitch_texts),
                'color': random.choice(self.glitch_colors),
                'offset_x': random.randint(-2, 2),
                'offset_y': random.randint(-2, 2),
                'is_glitching': True
            }
        else:
            result = {
                'text': self.normal_text,
                'color': self.normal_color,
                'offset_x': 0,
                'offset_y': 0,
                'is_glitching': False
            }
        
        self._advance_frame()
        return result


class FadeTransition(Animator):
    """
    Opacity fade in or fade out effect.
    
    Smoothly transitions opacity from 0 to 1 (fade in) or 1 to 0 (fade out).
    """
    
    def __init__(self, fade_in: bool = True, duration_frames: int = 30, 
                 loop: bool = False):
        """
        Initialize fade transition.
        
        Args:
            fade_in: True for fade in (0→1), False for fade out (1→0)
            duration_frames: Frames for complete fade
            loop: Whether to loop
        """
        super().__init__(duration_frames, loop)
        self.fade_in = fade_in
    
    def update(self) -> float:
        """
        Get current opacity value.
        
        Returns:
            Opacity value from 0.0 (transparent) to 1.0 (opaque)
        """
        progress = self.get_progress()
        
        if self.fade_in:
            opacity = progress
        else:
            opacity = 1.0 - progress
        
        self._advance_frame()
        return opacity


class MatrixRain(Animator):
    """
    Matrix-style falling character animation.
    
    Manages multiple falling character streams with brightness fading.
    """
    
    def __init__(self, max_chars: int = 8, 
                 chars: Optional[List[str]] = None,
                 brightness_levels: Optional[List[str]] = None,
                 duration_frames: int = 150, loop: bool = True):
        """
        Initialize matrix rain.
        
        Args:
            max_chars: Maximum simultaneous characters
            chars: List of possible characters (defaults to matrix symbols)
            brightness_levels: List of colors for brightness fade
            duration_frames: Frames per cycle (not used in continuous mode)
            loop: Always True for matrix rain
        """
        super().__init__(duration_frames, True)  # Always loop
        self.max_chars = max_chars
        self.chars = chars or ["0", "1", "X", "Ø", "µ", "¶", "§"]
        self.brightness_levels = brightness_levels or [
            "#00ff00",  # Bright
            "#00cc00",  # Medium
            "#009900",  # Dim
            "#006600"   # Very dim
        ]
        self.active_chars: List[Dict[str, Any]] = []
    
    def update(self) -> List[Dict[str, Any]]:
        """
        Update matrix rain state.
        
        Returns:
            List of dicts with 'char', 'x', 'y', 'brightness_level' for each active character
        """
        # Add new characters if under max
        if len(self.active_chars) < self.max_chars and random.random() > 0.5:
            self.active_chars.append({
                'char': random.choice(self.chars),
                'x': random.randint(60, 320),
                'y': random.randint(25, 200),
                'brightness_step': 0
            })
        
        # Update existing characters (fade through brightness levels)
        for char_data in self.active_chars[:]:
            char_data['brightness_step'] += 1
            
            # Remove if fully faded
            if char_data['brightness_step'] >= len(self.brightness_levels):
                self.active_chars.remove(char_data)
        
        # Build return data with current brightness colors
        result = []
        for char_data in self.active_chars:
            step = min(char_data['brightness_step'], len(self.brightness_levels) - 1)
            result.append({
                'char': char_data['char'],
                'x': char_data['x'],
                'y': char_data['y'],
                'color': self.brightness_levels[step],
                'brightness_step': step
            })
        
        self._advance_frame()
        return result


class AnimationManager:
    """
    Central manager for all active animations.
    
    Coordinates multiple animations and provides batch update functionality.
    """
    
    def __init__(self):
        """Initialize animation manager."""
        self.animations: Dict[str, Animator] = {}
    
    def register(self, name: str, animator: Animator):
        """
        Register an animation with a name.
        
        Args:
            name: Unique identifier for this animation
            animator: Animator instance to register
        """
        self.animations[name] = animator
    
    def unregister(self, name: str):
        """Remove an animation by name."""
        if name in self.animations:
            del self.animations[name]
    
    def get(self, name: str) -> Optional[Animator]:
        """Get animator by name."""
        return self.animations.get(name)
    
    def start(self, name: str):
        """Start a specific animation."""
        if name in self.animations:
            self.animations[name].start()
    
    def stop(self, name: str):
        """Stop a specific animation."""
        if name in self.animations:
            self.animations[name].stop()
    
    def start_all(self):
        """Start all registered animations."""
        for animator in self.animations.values():
            animator.start()
    
    def stop_all(self):
        """Stop all registered animations."""
        for animator in self.animations.values():
            animator.stop()
    
    def update_all(self) -> Dict[str, Any]:
        """
        Update all running animations.
        
        Returns:
            Dict mapping animation names to their current states
        """
        results = {}
        for name, animator in self.animations.items():
            if animator.is_running:
                results[name] = animator.update()
        return results
    
    def clear(self):
        """Remove all animations."""
        self.animations.clear()


# Convenience factory functions for common animation patterns

def create_button_press_animation() -> ColorGradient:
    """Create animation for button press feedback."""
    return ColorGradient(
        start_color="#ccff00",
        end_color="#ffffff",
        duration_frames=5,
        loop=False
    )


def create_status_pulse() -> PulsingEffect:
    """Create pulsing effect for status indicators."""
    return PulsingEffect(
        min_value=0.6,
        max_value=1.0,
        duration_frames=40,
        loop=True
    )


def create_logo_glitch() -> GlitchEffect:
    """Create glitch effect for logo/header."""
    glitch = GlitchEffect(
        glitch_texts=["DEDSEC_OS", "D3DSEC_0S", "DEADSEC", "ERR_0x90", "SYSTEM_FAIL"],
        glitch_colors=["#ccff00", "#ffffff", "#ff0000", "#00ffff"],
        glitch_chance=0.3,
        duration_frames=60,
        loop=True
    )
    glitch.set_normal_state("DEDSEC_OS", "#ccff00")
    return glitch


def create_fade_in(duration_frames: int = 30) -> FadeTransition:
    """Create fade-in transition."""
    return FadeTransition(fade_in=True, duration_frames=duration_frames, loop=False)


def create_fade_out(duration_frames: int = 30) -> FadeTransition:
    """Create fade-out transition."""
    return FadeTransition(fade_in=False, duration_frames=duration_frames, loop=False)


def create_matrix_background() -> MatrixRain:
    """Create matrix rain background effect."""
    return MatrixRain(
        max_chars=8,
        duration_frames=150,
        loop=True
    )
