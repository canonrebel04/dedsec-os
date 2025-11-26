"""DedSecOS Configuration Module

Centralized configuration for all constants, colors, dimensions, and timings.

This module provides:
- Layout dimensions (optimized for 320×240 Pi screen)
- Color definitions (defaults + theme integration)
- Animation timings
- Debug/feature flags
- Tool configuration

Design: All colors default to Neon Green theme but can be overridden by ThemeManager.

Example:
    from config import LAYOUT, COLORS, TIMINGS

    # Get layout dimensions
    canvas_width = LAYOUT.CANVAS_WIDTH  # 320
    header_height = LAYOUT.HEADER_HEIGHT  # 30

    # Get colors (defaults or from ThemeManager)
    bg_color = COLORS.get("background")  # "#000000"
    text_color = COLORS.get("text")  # "#00FF00"

    # Get timing values
    animation_speed = TIMINGS.BUTTON_PRESS_DURATION  # 100 ms
"""

from dataclasses import dataclass

# ============================================================================
# LAYOUT CONFIGURATION (Optimized for Raspberry Pi 2 - 320×240)
# ============================================================================


@dataclass
class LayoutConfig:
    """Display and component layout dimensions.

    Phase 3.2.2: Spacious Grid Layout
    - Maximizes negative space for readability on 320x240 TFT
    - 30px header/footer with vertical centering
    - 70px sidebar + 10px gutter for visual separation
    - 5px terminal padding to prevent edge touching
    - 240x180 main content area, 230x170 usable terminal space
    """

    # Screen dimensions (Adafruit 320×240 touchscreen)
    CANVAS_WIDTH: int = 320
    CANVAS_HEIGHT: int = 240

    # Primary zones (spacious grid)
    HEADER_HEIGHT: int = 30  # Top bar (vertically centered title/time)
    FOOTER_HEIGHT: int = 30  # Bottom bar (spaced system stats)
    SIDEBAR_WIDTH: int = 70  # Left navigation panel
    GUTTER_WIDTH: int = 10  # Blank separator (negative space)

    # Header/Footer padding
    HEADER_PADDING: int = 5
    STATUS_BAR_PADDING: int = 5

    # Sidebar configuration
    SIDEBAR_ITEM_HEIGHT: int = 40
    SIDEBAR_PADDING: int = 5

    # Main content area (calculated from grid)
    CONTENT_X: int = SIDEBAR_WIDTH + GUTTER_WIDTH  # 80px (70 + 10)
    CONTENT_Y: int = HEADER_HEIGHT  # 30px
    CONTENT_WIDTH: int = 240  # 320 - 70 - 10
    CONTENT_HEIGHT: int = 180  # 240 - 30 - 30

    # Terminal internal padding (5px safety margin all sides)
    TERMINAL_PADDING_TOP: int = 5
    TERMINAL_PADDING_BOTTOM: int = 5
    TERMINAL_PADDING_LEFT: int = 5
    TERMINAL_PADDING_RIGHT: int = 5

    # Usable terminal space (with padding applied)
    TERMINAL_USABLE_WIDTH: int = 230  # 240 - 5 - 5
    TERMINAL_USABLE_HEIGHT: int = 170  # 180 - 5 - 5
    TERMINAL_WRAP_CHARS: int = 41  # ~230px ÷ 5.5px/char @ 9pt mono
    TERMINAL_MAX_VISIBLE_LINES: int = 14  # 170px ÷ 12px line height

    # Legacy status bar (footer)
    STATUS_BAR_HEIGHT: int = FOOTER_HEIGHT  # 30
    STATUS_BAR_Y: int = CANVAS_HEIGHT - STATUS_BAR_HEIGHT  # 210

    # Modal (centered dialog)
    MODAL_WIDTH: int = 280
    MODAL_HEIGHT: int = 160
    MODAL_X: int = (CANVAS_WIDTH - MODAL_WIDTH) // 2
    MODAL_Y: int = (CANVAS_HEIGHT - MODAL_HEIGHT) // 2
    MODAL_PADDING: int = 10
    MODAL_BORDER_WIDTH: int = 2

    # Button dimensions
    BUTTON_WIDTH: int = 60
    BUTTON_HEIGHT: int = 25
    BUTTON_PADDING: int = 5
    BUTTON_BORDER_WIDTH: int = 2

    # Text rendering
    FONT_FAMILY: str = "Courier"
    FONT_SIZE_HEADER: int = 12
    FONT_SIZE_BODY: int = 10
    FONT_SIZE_SMALL: int = 8

    # Selection highlight
    SELECTION_BORDER_WIDTH: int = 2
    SELECTION_PADDING: int = 2


# ============================================================================
# COLOR CONFIGURATION (Neon Green Theme - Default)
# ============================================================================


class ColorConfig:
    """Color definitions for UI components.

    Design: These are default colors (Neon Green theme).
    Override with ThemeManager.get_all_colors() for dynamic theming.

    Attributes:
        DEFAULTS: Default color palette (Neon Green)
    """

    # Default color palette (Neon Green theme - classic hacker)
    DEFAULTS = {
        # Layout colors
        "background": "#000000",
        "text": "#00FF00",
        "text_secondary": "#00CC00",
        "border": "#00FF00",
        # Header
        "header_bg": "#001A00",
        "header_text": "#00FF00",
        # Sidebar
        "sidebar_bg": "#000000",
        "sidebar_item_bg": "#003300",
        "sidebar_item_hover": "#00FF00",
        "sidebar_item_active": "#FFFFFF",
        "sidebar_text": "#00FF00",
        # Buttons
        "button_bg": "#003300",
        "button_text": "#00FF00",
        "button_hover": "#00FF00",
        "button_active": "#FFFFFF",
        "button_disabled": "#333333",
        # Modals
        "modal_bg": "#001A00",
        "modal_text": "#00FF00",
        "modal_border": "#00FF00",
        # Input fields
        "input_bg": "#000000",
        "input_text": "#00FF00",
        "input_border": "#00FF00",
        "input_cursor": "#00FF00",
        # Status indicators
        "error_bg": "#330000",
        "error_text": "#FF0000",
        "success_bg": "#003300",
        "success_text": "#00FF00",
        "warning_bg": "#333300",
        "warning_text": "#FFFF00",
        # UI elements
        "highlight": "#00FF00",
        "accent": "#00FF00",
        "muted": "#666666",
        # Progress and status
        "progress_bg": "#003300",
        "progress_fill": "#00FF00",
        "status_ok": "#00FF00",
        "status_warning": "#FFFF00",
        "status_error": "#FF0000",
        # Panels
        "panel_bg": "#000000",
        "panel_border": "#00FF00",
        # Terminal
        "terminal_bg": "#000000",
        "terminal_text": "#00FF00",
        "terminal_border": "#00FF00",
    }

    def __init__(self, theme_manager=None):
        """Initialize color config with optional theme manager.

        Args:
            theme_manager: ThemeManager instance for dynamic colors (optional)
        """
        self.theme_manager = theme_manager
        self._colors = self.DEFAULTS.copy()

    def get(self, key: str, default: str = "#000000") -> str:
        """Get color by name.

        If theme_manager is set, gets color from current theme.
        Otherwise returns default palette.

        Args:
            key: Color name
            default: Fallback color if not found

        Returns:
            Hex color string
        """
        if self.theme_manager:
            try:
                return self.theme_manager.get_color(key)
            except Exception:
                pass  # Fall through to defaults

        return self._colors.get(key, default)

    def set_theme_manager(self, theme_manager) -> None:
        """Set theme manager for dynamic colors.

        Args:
            theme_manager: ThemeManager instance
        """
        self.theme_manager = theme_manager

    def get_all(self) -> dict[str, str]:
        """Get all colors as dictionary.

        Returns:
            Dictionary of color name → hex value
        """
        if self.theme_manager:
            return self.theme_manager.get_all_colors()
        return self._colors.copy()


# ============================================================================
# ANIMATION TIMING CONFIGURATION
# ============================================================================


@dataclass
class TimingConfig:
    """Animation and timing constants (in milliseconds)."""

    # Button interactions
    BUTTON_PRESS_DURATION: int = 100  # Flash duration on click
    BUTTON_HOVER_DELAY: int = 50  # Delay before hover effect

    # Clock and updates
    CLOCK_UPDATE_INTERVAL: int = 1000  # Update clock every 1 second
    STATUS_UPDATE_INTERVAL: int = 500  # Update status every 500ms

    # Tool execution
    TOOL_PROGRESS_UPDATE_INTERVAL: int = 100  # Update progress every 100ms
    TOOL_TIMEOUT_WARNING: int = 30000  # Warn if tool takes >30 seconds

    # Animations
    FADE_DURATION: int = 300  # Fade in/out duration
    SLIDE_DURATION: int = 200  # Slide animation duration
    PULSING_DURATION: int = 600  # Pulse effect duration
    GLITCH_DURATION: int = 200  # Glitch effect duration

    # Menu
    MENU_TRANSITION_DURATION: int = 150  # Menu change animation
    SELECTION_CHANGE_DELAY: int = 50  # Delay on selection change

    # Rendering
    FRAME_RATE: int = 30  # Target FPS
    FRAME_DELAY: int = 33  # Milliseconds per frame (1000/30)

    # Debug/monitoring
    FPS_COUNTER_UPDATE: int = 1000  # Update FPS counter every 1 second
    MEMORY_CHECK_INTERVAL: int = 5000  # Check memory every 5 seconds


# ============================================================================
# DEBUG AND FEATURE FLAGS
# ============================================================================


@dataclass
class DebugConfig:
    """Debug flags and feature toggles."""

    # Logging
    ENABLE_LOGGING: bool = True
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FILE: str = "/tmp/dedsec.log"

    # Performance monitoring
    SHOW_FPS_COUNTER: bool = False
    SHOW_MEMORY_USAGE: bool = False
    SHOW_CPU_USAGE: bool = False
    PROFILE_RENDERING: bool = False

    # Touch and input
    LOG_TOUCH_EVENTS: bool = False
    SHOW_TOUCH_COORDINATES: bool = False

    # Rendering
    DEBUG_RECTANGLES: bool = False  # Draw debug outlines
    DEBUG_GRID: bool = False  # Draw grid overlay
    DEBUG_REGIONS: bool = False  # Highlight regions

    # Tools
    LOG_TOOL_EXECUTION: bool = True
    TOOL_SIMULATION_MODE: bool = False  # Simulate tool results without running

    # Canvas
    CANVAS_CLEAR_PREVIOUS: bool = True  # Clear canvas each frame
    CANVAS_DOUBLE_BUFFER: bool = True  # Use double buffering


# ============================================================================
# TOOL CONFIGURATION
# ============================================================================


@dataclass
class ToolConfig:
    """Configuration for security tools."""

    # Network scanning
    PORT_SCAN_TIMEOUT: int = 5000  # milliseconds per port
    PORT_SCAN_DEFAULT_PORTS: str = "1-1024"  # Default port range
    PING_TIMEOUT: int = 2000  # milliseconds

    # Wireless
    WIFI_SCAN_TIMEOUT: int = 10000  # milliseconds
    WIFI_CONNECT_TIMEOUT: int = 15000  # milliseconds

    # General
    DEFAULT_TOOL_TIMEOUT: int = 30000  # 30 seconds
    MAX_OUTPUT_LINES: int = 500  # Max lines in text display
    MAX_RESULT_SIZE: int = 10 * 1024 * 1024  # 10 MB


# ============================================================================
# GLOBAL CONFIGURATION INSTANCES
# ============================================================================

# Create singleton instances
LAYOUT = LayoutConfig()
COLORS = ColorConfig()
TIMINGS = TimingConfig()
DEBUG = DebugConfig()
TOOLS = ToolConfig()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def set_theme_manager(theme_manager) -> None:
    """Set theme manager for dynamic color switching.

    Call this after initializing ThemeManager to enable dynamic colors.

    Args:
        theme_manager: ThemeManager instance

    Example:
        from ui.themes import ThemeManager
        from config import set_theme_manager

        tm = ThemeManager()
        set_theme_manager(tm)

        # Now colors will use current theme
        from config import COLORS
        bg = COLORS.get("background")  # Gets from current theme
    """
    COLORS.set_theme_manager(theme_manager)


def reset_colors() -> None:
    """Reset colors to defaults (Neon Green theme)."""
    COLORS._colors = ColorConfig.DEFAULTS.copy()
    COLORS.theme_manager = None


def enable_debug_mode() -> None:
    """Enable all debug flags for development."""
    DEBUG.SHOW_FPS_COUNTER = True
    DEBUG.SHOW_MEMORY_USAGE = True
    DEBUG.SHOW_CPU_USAGE = True
    DEBUG.LOG_TOUCH_EVENTS = True
    DEBUG.SHOW_TOUCH_COORDINATES = True
    DEBUG.DEBUG_RECTANGLES = True
    DEBUG.PROFILE_RENDERING = True


def disable_debug_mode() -> None:
    """Disable all debug flags for production."""
    DEBUG.SHOW_FPS_COUNTER = False
    DEBUG.SHOW_MEMORY_USAGE = False
    DEBUG.SHOW_CPU_USAGE = False
    DEBUG.LOG_TOUCH_EVENTS = False
    DEBUG.SHOW_TOUCH_COORDINATES = False
    DEBUG.DEBUG_RECTANGLES = False
    DEBUG.PROFILE_RENDERING = False


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "LAYOUT",
    "COLORS",
    "TIMINGS",
    "DEBUG",
    "TOOLS",
    "LayoutConfig",
    "ColorConfig",
    "TimingConfig",
    "DebugConfig",
    "ToolConfig",
    "set_theme_manager",
    "reset_colors",
    "enable_debug_mode",
    "disable_debug_mode",
]
