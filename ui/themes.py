"""Theme System for DedSec UI Framework

Provides cyberpunk-themed color schemes and dynamic theme switching.

Features:
    - 5 pre-built cyberpunk themes
    - Themeable component colors
    - Runtime theme switching
    - Custom theme support
    - Color interpolation for gradients

Themes:
    1. NEON_GREEN: Classic hacker aesthetic (lime green on black)
    2. SYNTHWAVE: Retrowave pink/blue/purple
    3. MONOCHROME: Greyscale for accessibility
    4. ACID_TRIP: Psychedelic rainbow cycling
    5. STEALTH_MODE: Minimal dark theme

Example:
    >>> from ui.themes import ThemeManager
    >>> tm = ThemeManager()
    >>> tm.set_theme("neon_green")
    >>> color = tm.get_color("text")
    >>> tm.get_all_colors()
    {
        'background': '#000000',
        'text': '#00FF00',
        ...
    }
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Callable, List, Optional, Tuple
import logging


# ============================================================================
# LOGGING SETUP
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class ThemeType(Enum):
    """Available theme presets."""
    NEON_GREEN = "neon_green"
    SYNTHWAVE = "synthwave"
    MONOCHROME = "monochrome"
    ACID_TRIP = "acid_trip"
    STEALTH_MODE = "stealth_mode"


# ============================================================================
# COLOR UTILITIES
# ============================================================================

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple.
    
    Args:
        hex_color: Color in hex format '#RRGGBB'
        
    Returns:
        Tuple of (R, G, B) values 0-255
        
    Example:
        >>> hex_to_rgb("#FF0000")
        (255, 0, 0)
    """
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return (rgb[0], rgb[1], rgb[2])  # type: Tuple[int, int, int]


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB values to hex color.
    
    Args:
        r: Red value 0-255
        g: Green value 0-255
        b: Blue value 0-255
        
    Returns:
        Color in hex format '#RRGGBB'
        
    Example:
        >>> rgb_to_hex(255, 0, 0)
        '#FF0000'
    """
    return f"#{r:02X}{g:02X}{b:02X}"


def interpolate_color(color1: str, color2: str, factor: float) -> str:
    """Interpolate between two colors.
    
    Args:
        color1: Starting color (hex)
        color2: Ending color (hex)
        factor: Interpolation factor 0.0-1.0
        
    Returns:
        Interpolated color (hex)
        
    Example:
        >>> interpolate_color("#FF0000", "#0000FF", 0.5)
        '#7F007F'  # Purple (halfway between red and blue)
    """
    r1, g1, b1 = hex_to_rgb(color1)
    r2, g2, b2 = hex_to_rgb(color2)
    
    r = int(r1 + (r2 - r1) * factor)
    g = int(g1 + (g2 - g1) * factor)
    b = int(b1 + (b2 - b1) * factor)
    
    return rgb_to_hex(r, g, b)


# ============================================================================
# THEME DEFINITIONS
# ============================================================================

@dataclass
class Theme:
    """Theme definition with all colors.
    
    Attributes:
        name: Theme identifier
        label: Human-readable theme name
        background: Main background color
        text: Primary text color
        text_secondary: Secondary text color
        header_bg: Header background
        header_text: Header text
        button_bg: Button background
        button_text: Button text
        button_hover: Button hover state
        button_active: Button pressed state
        button_disabled: Button disabled state
        modal_bg: Modal background
        modal_text: Modal text
        modal_border: Modal border
        input_bg: Input field background
        input_text: Input field text
        input_border: Input field border
        error_bg: Error state background
        error_text: Error state text
        success_bg: Success state background
        success_text: Success state text
        warning_bg: Warning state background
        warning_text: Warning state text
        border: Standard border color
        highlight: Highlight/focus color
        accent: Accent color
        muted: Muted/disabled text
        progress_bg: Progress bar background
        progress_fill: Progress bar fill
        panel_bg: Panel background
        panel_border: Panel border
    """
    
    name: str
    label: str
    background: str
    text: str
    text_secondary: str
    header_bg: str
    header_text: str
    button_bg: str
    button_text: str
    button_hover: str
    button_active: str
    button_disabled: str
    modal_bg: str
    modal_text: str
    modal_border: str
    input_bg: str
    input_text: str
    input_border: str
    error_bg: str
    error_text: str
    success_bg: str
    success_text: str
    warning_bg: str
    warning_text: str
    border: str
    highlight: str
    accent: str
    muted: str
    progress_bg: str
    progress_fill: str
    panel_bg: str
    panel_border: str
    
    def get_color(self, key: str) -> Optional[str]:
        """Get color by name.
        
        Args:
            key: Color attribute name
            
        Returns:
            Hex color or None if not found
        """
        return getattr(self, key, None)
    
    def to_dict(self) -> Dict[str, str]:
        """Convert theme to dictionary.
        
        Returns:
            Dictionary of all colors
        """
        colors = {}
        for key in dir(self):
            if not key.startswith('_'):
                value = getattr(self, key)
                if isinstance(value, str) and value.startswith('#'):
                    colors[key] = value
        return colors


# ============================================================================
# THEME PRESETS
# ============================================================================

def get_theme_neon_green() -> Theme:
    """Neon Green theme - classic hacker aesthetic.
    
    Colors:
        - Lime green on pure black
        - High contrast
        - Traditional terminal feel
    """
    return Theme(
        name="neon_green",
        label="Neon Green",
        background="#000000",
        text="#00FF00",
        text_secondary="#00CC00",
        header_bg="#001A00",
        header_text="#00FF00",
        button_bg="#003300",
        button_text="#00FF00",
        button_hover="#00FF00",
        button_active="#FFFFFF",
        button_disabled="#333333",
        modal_bg="#001A00",
        modal_text="#00FF00",
        modal_border="#00FF00",
        input_bg="#000000",
        input_text="#00FF00",
        input_border="#00FF00",
        error_bg="#330000",
        error_text="#FF0000",
        success_bg="#003300",
        success_text="#00FF00",
        warning_bg="#333300",
        warning_text="#FFFF00",
        border="#00FF00",
        highlight="#00FF00",
        accent="#00FF00",
        muted="#666666",
        progress_bg="#003300",
        progress_fill="#00FF00",
        panel_bg="#000000",
        panel_border="#00FF00",
    )


def get_theme_synthwave() -> Theme:
    """Synthwave theme - retrowave pink/blue/purple.
    
    Colors:
        - Vibrant pinks and cyans
        - Cyberpunk aesthetic
        - 1980s retrowave vibes
    """
    return Theme(
        name="synthwave",
        label="Synthwave",
        background="#0A0E27",
        text="#FF006E",
        text_secondary="#FB5607",
        header_bg="#1B1B3F",
        header_text="#FF006E",
        button_bg="#1B1B3F",
        button_text="#FF006E",
        button_hover="#00D9FF",
        button_active="#FFB703",
        button_disabled="#444444",
        modal_bg="#1B1B3F",
        modal_text="#FF006E",
        modal_border="#00D9FF",
        input_bg="#0A0E27",
        input_text="#FF006E",
        input_border="#00D9FF",
        error_bg="#3D0000",
        error_text="#FF0000",
        success_bg="#003D00",
        success_text="#00FF00",
        warning_bg="#3D3D00",
        warning_text="#FFFF00",
        border="#00D9FF",
        highlight="#FF006E",
        accent="#00D9FF",
        muted="#666666",
        progress_bg="#1B1B3F",
        progress_fill="#FF006E",
        panel_bg="#0A0E27",
        panel_border="#00D9FF",
    )


def get_theme_monochrome() -> Theme:
    """Monochrome theme - greyscale for accessibility.
    
    Colors:
        - Pure black and white
        - High contrast
        - Accessibility-friendly
    """
    return Theme(
        name="monochrome",
        label="Monochrome",
        background="#000000",
        text="#FFFFFF",
        text_secondary="#CCCCCC",
        header_bg="#222222",
        header_text="#FFFFFF",
        button_bg="#333333",
        button_text="#FFFFFF",
        button_hover="#FFFFFF",
        button_active="#000000",
        button_disabled="#666666",
        modal_bg="#222222",
        modal_text="#FFFFFF",
        modal_border="#FFFFFF",
        input_bg="#000000",
        input_text="#FFFFFF",
        input_border="#FFFFFF",
        error_bg="#333333",
        error_text="#FFFFFF",
        success_bg="#333333",
        success_text="#FFFFFF",
        warning_bg="#333333",
        warning_text="#FFFFFF",
        border="#FFFFFF",
        highlight="#FFFFFF",
        accent="#FFFFFF",
        muted="#999999",
        progress_bg="#333333",
        progress_fill="#FFFFFF",
        panel_bg="#000000",
        panel_border="#FFFFFF",
    )


def get_theme_acid_trip() -> Theme:
    """Acid Trip theme - psychedelic rainbow cycling.
    
    Colors:
        - Rainbow spectrum
        - Vibrant and energetic
        - Suitable for special effects
    """
    return Theme(
        name="acid_trip",
        label="Acid Trip",
        background="#1A0033",
        text="#FF00FF",
        text_secondary="#00FFFF",
        header_bg="#330066",
        header_text="#FF00FF",
        button_bg="#330033",
        button_text="#FF00FF",
        button_hover="#00FFFF",
        button_active="#FFFF00",
        button_disabled="#666666",
        modal_bg="#330066",
        modal_text="#FF00FF",
        modal_border="#00FFFF",
        input_bg="#1A0033",
        input_text="#FF00FF",
        input_border="#00FFFF",
        error_bg="#330000",
        error_text="#FF0000",
        success_bg="#003300",
        success_text="#00FF00",
        warning_bg="#333300",
        warning_text="#FFFF00",
        border="#00FFFF",
        highlight="#FF00FF",
        accent="#FFFF00",
        muted="#666666",
        progress_bg="#330033",
        progress_fill="#FF00FF",
        panel_bg="#1A0033",
        panel_border="#00FFFF",
    )


def get_theme_stealth_mode() -> Theme:
    """Stealth Mode theme - minimal dark theme.
    
    Colors:
        - Dark greys and blacks
        - Minimal contrast
        - Low power consumption
    """
    return Theme(
        name="stealth_mode",
        label="Stealth Mode",
        background="#0F0F0F",
        text="#1A1A1A",
        text_secondary="#333333",
        header_bg="#1A1A1A",
        header_text="#1A1A1A",
        button_bg="#1A1A1A",
        button_text="#1A1A1A",
        button_hover="#333333",
        button_active="#555555",
        button_disabled="#222222",
        modal_bg="#1A1A1A",
        modal_text="#1A1A1A",
        modal_border="#333333",
        input_bg="#0F0F0F",
        input_text="#1A1A1A",
        input_border="#333333",
        error_bg="#1A0000",
        error_text="#330000",
        success_bg="#001A00",
        success_text="#003300",
        warning_bg="#1A1A00",
        warning_text="#333300",
        border="#333333",
        highlight="#1A1A1A",
        accent="#333333",
        muted="#1A1A1A",
        progress_bg="#1A1A1A",
        progress_fill="#333333",
        panel_bg="#0F0F0F",
        panel_border="#1A1A1A",
    )


# ============================================================================
# THEME MANAGER
# ============================================================================

class ThemeManager:
    """Manages themes and provides color lookups.
    
    Features:
        - Switch between themes at runtime
        - Get colors by name
        - Color interpolation
        - Custom theme support
        - Subscribe to theme changes
        
    Example:
        >>> tm = ThemeManager()
        >>> tm.set_theme("neon_green")
        >>> color = tm.get_color("text")
        >>> tm.subscribe(lambda t: print(f"Theme changed to {t.label}"))
        >>> tm.set_theme("synthwave")  # Triggers subscriber
        Theme changed to Synthwave
    """
    
    def __init__(self, default_theme: str = "neon_green"):
        """Initialize theme manager.
        
        Args:
            default_theme: Default theme to use
        """
        self.themes: Dict[str, Theme] = {
            "neon_green": get_theme_neon_green(),
            "synthwave": get_theme_synthwave(),
            "monochrome": get_theme_monochrome(),
            "acid_trip": get_theme_acid_trip(),
            "stealth_mode": get_theme_stealth_mode(),
        }
        
        self.current_theme: Theme = self.themes.get(
            default_theme,
            self.themes["neon_green"]
        )
        
        self._subscribers: List[Callable[[Theme], None]] = []
        logger.info(f"ThemeManager initialized with theme: {self.current_theme.label}")
    
    def set_theme(self, theme_name: str) -> bool:
        """Switch to a theme.
        
        Args:
            theme_name: Theme identifier
            
        Returns:
            True if theme was changed, False if not found
            
        Example:
            >>> tm = ThemeManager()
            >>> tm.set_theme("synthwave")
            True
            >>> tm.set_theme("invalid")
            False
        """
        if theme_name not in self.themes:
            logger.warning(f"Theme not found: {theme_name}")
            return False
        
        old_theme = self.current_theme
        self.current_theme = self.themes[theme_name]
        
        logger.info(f"Theme changed: {old_theme.name} → {theme_name}")
        self._notify_subscribers()
        return True
    
    def get_theme(self, theme_name: Optional[str] = None) -> Optional[Theme]:
        """Get a theme by name.
        
        Args:
            theme_name: Theme identifier (uses current if None)
            
        Returns:
            Theme instance or None if not found
        """
        if theme_name is None:
            return self.current_theme
        return self.themes.get(theme_name)
    
    def get_color(self, key: str) -> str:
        """Get color from current theme.
        
        Args:
            key: Color attribute name
            
        Returns:
            Hex color string
            
        Example:
            >>> tm = ThemeManager()
            >>> tm.get_color("text")
            '#00FF00'
            >>> tm.get_color("button_hover")
            '#00FF00'
        """
        color = self.current_theme.get_color(key)
        if color is None:
            logger.warning(f"Color not found: {key}")
            return "#000000"  # Fallback
        return color
    
    def get_all_colors(self) -> Dict[str, str]:
        """Get all colors from current theme.
        
        Returns:
            Dictionary of color name → hex value
            
        Example:
            >>> tm = ThemeManager()
            >>> colors = tm.get_all_colors()
            >>> colors['text']
            '#00FF00'
        """
        return self.current_theme.to_dict()
    
    def get_available_themes(self) -> List[str]:
        """Get list of available theme names.
        
        Returns:
            List of theme identifiers
        """
        return list(self.themes.keys())
    
    def get_theme_labels(self) -> Dict[str, str]:
        """Get mapping of theme name to label.
        
        Returns:
            Dictionary of name → human-readable label
            
        Example:
            >>> tm = ThemeManager()
            >>> labels = tm.get_theme_labels()
            >>> labels['neon_green']
            'Neon Green'
        """
        return {name: theme.label for name, theme in self.themes.items()}
    
    def register_theme(self, theme: Theme) -> None:
        """Register a custom theme.
        
        Args:
            theme: Theme instance to register
            
        Example:
            >>> custom = Theme("custom", "Custom Theme", ...)
            >>> tm = ThemeManager()
            >>> tm.register_theme(custom)
            >>> tm.set_theme("custom")
            True
        """
        self.themes[theme.name] = theme
        logger.info(f"Custom theme registered: {theme.name}")
    
    def interpolate(self, key: str, factor: float) -> str:
        """Interpolate color between two themes.
        
        Interpolates between current theme and next theme by factor.
        
        Args:
            key: Color attribute name
            factor: Interpolation 0.0-1.0 (0=current, 1=next)
            
        Returns:
            Interpolated hex color
        """
        color1 = self.get_color(key)
        themes = list(self.themes.values())
        
        # Find next theme (for cycling)
        current_index = themes.index(self.current_theme)
        next_index = (current_index + 1) % len(themes)
        next_theme = themes[next_index]
        
        color2 = next_theme.get_color(key)
        if color2 is None:
            color2 = color1
        
        return interpolate_color(color1, color2, factor)
    
    def subscribe(self, callback: Callable[[Theme], None]) -> None:
        """Subscribe to theme changes.
        
        Args:
            callback: Function to call with new theme when changed
            
        Example:
            >>> tm = ThemeManager()
            >>> tm.subscribe(lambda t: print(f"New theme: {t.label}"))
            >>> tm.set_theme("synthwave")
            New theme: Synthwave
        """
        self._subscribers.append(callback)
    
    def _notify_subscribers(self) -> None:
        """Internal: Notify all subscribers of theme change."""
        for callback in self._subscribers:
            try:
                callback(self.current_theme)
            except Exception as e:
                logger.error(f"Error in theme subscriber: {e}")


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "ThemeType",
    "Theme",
    "ThemeManager",
    "hex_to_rgb",
    "rgb_to_hex",
    "interpolate_color",
    "get_theme_neon_green",
    "get_theme_synthwave",
    "get_theme_monochrome",
    "get_theme_acid_trip",
    "get_theme_stealth_mode",
]
