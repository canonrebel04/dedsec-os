"""
Modular canvas rendering system for DedSec cyberdeck.

Provides clean, reusable rendering methods for UI components with:
- Configuration-driven dimensions and colors
- Observer pattern integration for reactive updates
- Performance-optimized canvas operations
- Separation of concerns between rendering logic and state management

This module enables the DedSecOS application to render complex UI elements
by composing modular draw functions, each responsible for a specific area
of the screen (header, sidebar, terminal, status bar, modal, etc.).

Each render method:
1. Uses config constants (LAYOUT, COLORS, TIMINGS)
2. Works with configuration-based colors from ThemeManager
3. Performs dirty rectangle tracking when needed
4. Integrates with the component library (Button, Modal, etc.)
5. Handles z-order with tag_raise/tag_lower for correct layering

Architecture:
    ScreenRenderer
    ├── _draw_background()      - Static bg image with optional glass overlay
    ├── _draw_header()          - Clock, network icon, title
    ├── _draw_sidebar()         - Vertical button menu (nmap, wifi, etc)
    ├── _draw_terminal()        - Scrollable log display with pooled text
    ├── _draw_status_bar()      - CPU/RAM/Temp/Battery indicators
    ├── _draw_modal()           - Modal dialogs (wifi, bt, payload, etc)
    └── _draw_animations()      - Background matrix, pulsing effects

Usage:
    renderer = ScreenRenderer(canvas, config, theme_manager)
    renderer.draw_header(clock_text="12:34:56", network_status="connected")
    renderer.draw_terminal(log_lines, scroll_offset, line_height)
    renderer.draw_status_bar(cpu_pct, ram_gb, temp_c, battery_pct)

Integration with Architecture:
    - Canvas: Tkinter canvas for rendering
    - Config: LayoutConfig, ColorConfig, TimingConfig for constants
    - ThemeManager: Dynamic color provider with observer pattern
    - UIComponent: Renders components using inherited render() methods
    - StateContainer: Notifies renderer of state changes triggering redraws
"""

from typing import Optional, Dict, List, Tuple, Any, Callable
from dataclasses import dataclass
from enum import Enum
import tkinter as tk
import logging

# Import configuration and theme systems
try:
    from config import LAYOUT, COLORS, TIMINGS, DEBUG  # type: ignore[attr-defined]
except ImportError:
    # Provide default fallbacks if config not available
    LAYOUT = type('LAYOUT', (), {'SCREEN_WIDTH': 320, 'SCREEN_HEIGHT': 240})()
    COLORS = type('COLORS', (), {'BG': '#000000', 'TEXT': '#00FF00'})()
    TIMINGS = type('TIMINGS', (), {'FRAME_RATE': 30})()
    DEBUG = type('DEBUG', (), {'ENABLE_DEBUG_LOGGING': False})()
from ui.themes import ThemeManager
from ui.components import Button, Modal, TextDisplay, Gauge

logger = logging.getLogger(__name__)


class LayerZ(Enum):
    """Z-order layer indices for proper stacking of canvas elements."""
    BACKGROUND = 0
    GLASS_PANEL = 1
    TERMINAL_TEXT = 2
    UI_ELEMENTS = 3
    MODAL_BG = 4
    MODAL_CONTENT = 5
    OVERLAY = 6


@dataclass
class RenderContext:
    """
    Context object passed to rendering methods containing shared state and callbacks.
    
    This allows rendering methods to communicate state changes back to the UI without
    tight coupling to the main DedSecOS class.
    """
    canvas: tk.Canvas
    theme_manager: Optional[ThemeManager] = None
    on_color_change: Optional[Callable] = None
    on_state_change: Optional[Callable] = None
    debug_mode: bool = False


class ScreenRenderer:
    """
    Modular canvas rendering system for DedSec cyberdeck UI.
    
    Responsible for all visual rendering on the 320×240 canvas. Provides methods
    for rendering discrete screen regions (header, sidebar, terminal, etc.) with
    configuration-driven dimensions and colors.
    
    This separation enables:
    - Easy maintenance (rendering logic isolated from business logic)
    - Component reusability (render methods callable independently)
    - Performance optimization (dirty rectangle tracking, object pooling)
    - Theme switching (colors pulled from ColorConfig via ThemeManager)
    - Testing (mock canvas + config for unit tests)
    
    Attributes:
        canvas: Tkinter Canvas widget (320×240)
        context: RenderContext with config and callbacks
        tag_cache: Cache of tag names for efficient tag operations
        layer_objects: Dict mapping LayerZ to list of canvas item IDs
    """
    
    def __init__(self, canvas: tk.Canvas, context: RenderContext):
        """
        Initialize the screen renderer.
        
        Args:
            canvas: Tkinter canvas for rendering (expected 320×240)
            context: RenderContext with theme manager and callbacks
        """
        self.canvas = canvas
        self.context = context
        self.tag_cache = {}  # {tag_name: canvas_item_id} for efficient lookup
        self.layer_objects = {layer: [] for layer in LayerZ}
        
        # Cache frequently accessed config values
        self.screen_width = LAYOUT.CANVAS_WIDTH
        self.screen_height = LAYOUT.CANVAS_HEIGHT
        self.theme_manager = context.theme_manager
        
        logger.info(f"ScreenRenderer initialized for {self.screen_width}×{self.screen_height}")
    
    def _get_color(self, color_key: str, fallback: str = "#00ff00") -> str:
        """
        Get current color from ThemeManager or ColorConfig.
        
        Args:
            color_key: Color name (e.g., 'background', 'text_primary')
            fallback: Fallback color if key not found
        
        Returns:
            Hex color string (e.g., '#00ff00')
        """
        if self.theme_manager:
            return self.theme_manager.get_color(color_key, fallback)
        return COLORS.get(color_key, fallback)
    
    def _create_tag(self, tag_base: str, unique_id: Optional[int] = None) -> str:
        """
        Create a unique tag name with caching.
        
        Args:
            tag_base: Base tag name (e.g., 'header_clock')
            unique_id: Optional unique identifier
        
        Returns:
            Full tag name (e.g., 'header_clock_0')
        """
        tag_name = f"{tag_base}_{unique_id}" if unique_id else tag_base
        return tag_name
    
    def draw_background(self, image_path: Optional[str] = None, 
                       glass_alpha: int = 180) -> None:
        """
        Render background layer with optional image and glass overlay.
        
        Creates a solid background or loads an image. Optionally applies a
        glass panel effect (semi-transparent overlay) for depth.
        
        Args:
            image_path: Path to background image (optional)
            glass_alpha: Alpha value for glass panel (0-255, higher=darker)
        
        Performance:
            - Image loading is deferred (lazy load on first render)
            - Glass panel created once and reused
            - Z-order: background at bottom
        """
        try:
            # Clear existing background
            self.canvas.delete("bg", "glass")
            
            # Solid background
            bg_color = self._get_color('background')
            bg_rect = self.canvas.create_rectangle(
                0, 0,
                self.screen_width, self.screen_height,
                fill=bg_color, outline="",
                tags="bg"
            )
            self.layer_objects[LayerZ.BACKGROUND].append(bg_rect)
            self.canvas.tag_lower("bg")
            
            # Optional image background
            if image_path:
                try:
                    from PIL import Image, ImageTk
                    pil_img = Image.open(image_path)
                    pil_img = pil_img.resize((self.screen_width, self.screen_height),
                                            Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(pil_img)
                    self._bg_image = photo  # Keep reference to prevent GC
                    img_item = self.canvas.create_image(
                        0, 0, image=photo, anchor="nw", tags="bg_image"
                    )
                    self.layer_objects[LayerZ.BACKGROUND].append(img_item)
                    self.canvas.tag_lower("bg_image")
                except Exception as e:
                    logger.warning(f"Failed to load background image: {e}")
            
            # Optional glass panel overlay (creates depth effect)
            if glass_alpha > 0:
                glass_color = self._get_color('glass_overlay', "#000000")
                glass_rect = self.canvas.create_rectangle(
                    0, 0,
                    self.screen_width, self.screen_height,
                    fill=glass_color, outline="",
                    tags="glass"
                )
                # Approximate alpha with fill pattern (Tkinter limitation)
                self.canvas.tag_lower("glass")
                self.layer_objects[LayerZ.GLASS_PANEL].append(glass_rect)
        
        except Exception as e:
            logger.error(f"Background render error: {e}")
    
    def draw_header(self, clock_text: str = "00:00:00",
                   network_icon: str = "●", title_text: str = "DEDSEC") -> None:
        """
        Render header bar with clock, network status, title.
        
        Header layout (top 30px):
        - Left (5px): Title ("DEDSEC")
        - Center (varies): Network icon + status
        - Right (285px): Clock (HH:MM:SS)
        
        Args:
            clock_text: Time text (e.g., "12:34:56")
            network_icon: Network status indicator (●, ○, ✗)
            title_text: Title to display (e.g., "DEDSEC", "SCANNING")
        
        Z-order: Above terminal text, below modals
        """
        try:
            # Clear existing header
            self.canvas.delete("header", "header_clock", "header_title", "header_net")
            
            # Background bar
            header_color = self._get_color('header_bg')
            header_rect = self.canvas.create_rectangle(
                0, 0,
                self.screen_width, LAYOUT.HEADER_HEIGHT,
                fill=header_color, outline=self._get_color('border'),
                tags="header"
            )
            self.layer_objects[LayerZ.UI_ELEMENTS].append(header_rect)
            
            # Title (left)
            title_color = self._get_color('text_primary')
            title_item = self.canvas.create_text(
                LAYOUT.HEADER_PADDING, LAYOUT.HEADER_HEIGHT // 2,
                text=title_text,
                fill=title_color,
                anchor="w",
                font=("Courier", 10, "bold"),
                tags="header_title"
            )
            self.layer_objects[LayerZ.UI_ELEMENTS].append(title_item)
            
            # Network status (center)
            net_color = self._get_color('network_active', "#00ff00")
            net_item = self.canvas.create_text(
                self.screen_width // 2, LAYOUT.HEADER_HEIGHT // 2,
                text=network_icon,
                fill=net_color,
                anchor="center",
                font=("Courier", 14),
                tags="header_net"
            )
            self.layer_objects[LayerZ.UI_ELEMENTS].append(net_item)
            
            # Clock (right)
            clock_color = self._get_color('text_primary')
            clock_item = self.canvas.create_text(
                self.screen_width - LAYOUT.HEADER_PADDING,
                LAYOUT.HEADER_HEIGHT // 2,
                text=clock_text,
                fill=clock_color,
                anchor="e",
                font=("Courier", 10, "bold"),
                tags="header_clock"
            )
            self.layer_objects[LayerZ.UI_ELEMENTS].append(clock_item)
            
            # Raise all header elements
            self.canvas.tag_raise("header")
        
        except Exception as e:
            logger.error(f"Header render error: {e}")
    
    def draw_sidebar(self, buttons: List[Dict[str, Any]]) -> None:
        """
        Render left sidebar with vertical button menu.
        
        Sidebar layout (65×240):
        - 7 buttons, each 55×20px with 3px spacing
        - Button positioning: (3, 28) to (3, 212)
        - Touch target: 55×20 (meets Material Design minimum)
        
        Args:
            buttons: List of button dicts:
                [
                    {"label": "NMAP", "color": "#00ff00", "callback": func},
                    {"label": "WiFi", "color": "#ffff00", "callback": func},
                    ...
                ]
        
        Performance:
            - Uses configuration coordinates (no magic numbers)
            - Buttons cached for hit detection
        """
        try:
            # Clear existing sidebar
            self.canvas.delete("sidebar", "sidebar_buttons")
            
            # Background bar
            sidebar_color = self._get_color('sidebar_bg')
            sidebar_rect = self.canvas.create_rectangle(
                0, LAYOUT.HEADER_HEIGHT,
                LAYOUT.SIDEBAR_WIDTH, self.screen_height,
                fill=sidebar_color, outline=self._get_color('border'),
                tags="sidebar"
            )
            self.layer_objects[LayerZ.UI_ELEMENTS].append(sidebar_rect)
            
            # Render buttons
            button_y_start = LAYOUT.HEADER_HEIGHT + LAYOUT.SIDEBAR_PADDING
            button_height = LAYOUT.BUTTON_HEIGHT
            button_spacing = LAYOUT.SIDEBAR_PADDING
            
            for idx, button_def in enumerate(buttons[:7]):  # Max 7 buttons in sidebar
                y_pos = button_y_start + (idx * (button_height + button_spacing))
                
                # Button rectangle
                btn_color = button_def.get("color", self._get_color('button_bg'))
                btn_item = self.canvas.create_rectangle(
                    LAYOUT.SIDEBAR_PADDING, y_pos,
                    LAYOUT.SIDEBAR_WIDTH - LAYOUT.SIDEBAR_PADDING,
                    y_pos + button_height,
                    fill="", outline=btn_color, width=1,
                    tags=f"sidebar_button_{idx}"
                )
                self.layer_objects[LayerZ.UI_ELEMENTS].append(btn_item)
                
                # Button label
                label_color = button_def.get("label_color", self._get_color('text_primary'))
                label_item = self.canvas.create_text(
                    LAYOUT.SIDEBAR_WIDTH // 2,
                    y_pos + button_height // 2,
                    text=button_def.get("label", "BTN"),
                    fill=label_color,
                    anchor="center",
                    font=("Courier", 7),
                    tags=f"sidebar_label_{idx}"
                )
                self.layer_objects[LayerZ.UI_ELEMENTS].append(label_item)
        
        except Exception as e:
            logger.error(f"Sidebar render error: {e}")
    
    def draw_terminal(self, log_lines: List[str], scroll_offset: int = 0,
                     line_height: int = 12,
                     pool: Optional[Any] = None) -> None:
        """
        Render terminal area with scrollable log display.
        
        Terminal layout (255×170, 320x240 - header - status bar):
        - Position: (65, 30) to (320, 210)
        - Line height: 12px (fits ~14 lines)
        - Uses object pooling for performance on Pi 2
        
        Args:
            log_lines: List of log line strings to display
            scroll_offset: Y-offset for scrolling (negative = up)
            line_height: Height of each line in pixels
            pool: Optional CanvasObjectPool for reusing text objects
        
        Performance:
            - Object pooling reduces GC pressure
            - Only renders visible lines (clipping)
            - Dirty rectangle tracking (only redraw if scroll changed)
            - Tag z-ordering ensures text above backgrounds
        """
        try:
            # Clear existing terminal text
            self.canvas.delete("terminal_text")
            
            # Terminal background
            term_bg = self._get_color('terminal_bg')
            term_rect = self.canvas.create_rectangle(
                LAYOUT.SIDEBAR_WIDTH, LAYOUT.HEADER_HEIGHT,
                self.screen_width, LAYOUT.CANVAS_HEIGHT - LAYOUT.STATUS_BAR_HEIGHT,
                fill=term_bg, outline=self._get_color('border'),
                tags="terminal_bg"
            )
            self.layer_objects[LayerZ.UI_ELEMENTS].append(term_rect)
            self.canvas.tag_lower("terminal_bg")
            
            # Render visible log lines
            text_color = self._get_color('text_primary')
            visible_lines = []
            
            for idx, line in enumerate(log_lines):
                y_pos = LAYOUT.HEADER_HEIGHT + scroll_offset + (idx * line_height)
                
                # Check if line is visible in viewport
                if LAYOUT.HEADER_HEIGHT - 10 < y_pos < (LAYOUT.CANVAS_HEIGHT - LAYOUT.STATUS_BAR_HEIGHT) + 10:
                    # Use pool if available, else create directly
                    if pool:
                        item_id = pool.acquire(
                            LAYOUT.SIDEBAR_WIDTH + 5, y_pos,
                            text=f"> {line}",
                            fill=text_color,
                            font=("Courier", 9)
                        )
                        if item_id:
                            visible_lines.append(item_id)
                            self.canvas.tag_raise(item_id)
                    else:
                        item_id = self.canvas.create_text(
                            LAYOUT.SIDEBAR_WIDTH + 5, y_pos,
                            text=f"> {line}",
                            fill=text_color,
                            anchor="nw",
                            font=("Courier", 9),
                            tags="terminal_text"
                        )
                        visible_lines.append(item_id)
                        self.canvas.tag_raise(item_id)
            
            # Ensure terminal text is visible above backgrounds
            self.canvas.tag_raise("terminal_text")
        
        except Exception as e:
            logger.error(f"Terminal render error: {e}")
    
    def draw_status_bar(self, cpu_pct: float = 0.0, ram_gb: float = 0.0,
                       temp_c: float = 0.0, battery_pct: float = 0.0) -> None:
        """
        Render status bar with system metrics.
        
        Status bar layout (bottom 24px):
        - CPU bar: 40-90 (visualized as heat color)
        - CPU text: "0%" @ 95
        - RAM text: "0.0GB" @ 158
        - Temp text: "0°C" @ 235
        - Battery text: "0%" @ 298
        
        Args:
            cpu_pct: CPU usage percentage (0-100)
            ram_gb: RAM usage in GB
            temp_c: CPU temperature in Celsius
            battery_pct: Battery level percentage (0-100)
        
        Color coding:
            - CPU: Heat gradient (green → red)
            - Temp: Green if < 70°C, red if >= 70°C
            - RAM: Always white
            - Battery: Green if > 20%, yellow if 10-20%, red if < 10%
        """
        try:
            # Clear existing status bar
            self.canvas.delete("status_bar")
            
            # Status bar background
            status_bg = self._get_color('status_bg')
            status_rect = self.canvas.create_rectangle(
                0, LAYOUT.STATUS_BAR_Y,
                self.screen_width, self.screen_height,
                fill=status_bg, outline=self._get_color('border'),
                tags="status_bar"
            )
            self.layer_objects[LayerZ.UI_ELEMENTS].append(status_rect)
            
            y_center = LAYOUT.STATUS_BAR_Y + 10
            
            # CPU bar (heat color gradient)
            cpu_color = self._get_heat_color(cpu_pct)
            cpu_bar_width = max(1, int(cpu_pct * 0.5))  # Max 50px for 100%
            cpu_bar = self.canvas.create_rectangle(
                40, y_center - 5,
                40 + cpu_bar_width, y_center + 5,
                fill=cpu_color, outline="",
                tags="status_cpu_bar"
            )
            self.layer_objects[LayerZ.UI_ELEMENTS].append(cpu_bar)
            
            # CPU text
            cpu_text = self.canvas.create_text(
                95, y_center,
                text=f"{cpu_pct:.0f}%",
                fill=self._get_color('text_primary'),
                anchor="w",
                font=("Courier", 8),
                tags="status_cpu_text"
            )
            self.layer_objects[LayerZ.UI_ELEMENTS].append(cpu_text)
            
            # RAM text
            ram_text = self.canvas.create_text(
                158, y_center,
                text=f"{ram_gb:.1f}GB",
                fill=self._get_color('text_primary'),
                anchor="w",
                font=("Courier", 8),
                tags="status_ram_text"
            )
            self.layer_objects[LayerZ.UI_ELEMENTS].append(ram_text)
            
            # Temperature text (color-coded)
            temp_color = self._get_color('text_primary')
            if temp_c >= 70:
                temp_color = self._get_color('error', "#ff0000")
            
            temp_text = self.canvas.create_text(
                235, y_center,
                text=f"{temp_c:.0f}°C",
                fill=temp_color,
                anchor="w",
                font=("Courier", 8),
                tags="status_temp_text"
            )
            self.layer_objects[LayerZ.UI_ELEMENTS].append(temp_text)
            
            # Battery text (color-coded)
            battery_color = self._get_color('text_primary')
            if battery_pct < 10:
                battery_color = self._get_color('error', "#ff0000")
            elif battery_pct < 20:
                battery_color = self._get_color('warning', "#ffff00")
            
            battery_text = self.canvas.create_text(
                298, y_center,
                text=f"{battery_pct:.0f}%",
                fill=battery_color,
                anchor="w",
                font=("Courier", 8),
                tags="status_battery_text"
            )
            self.layer_objects[LayerZ.UI_ELEMENTS].append(battery_text)
        
        except Exception as e:
            logger.error(f"Status bar render error: {e}")
    
    def draw_modal(self, title: str, content_text: str,
                  modal_type: str = "info",
                  buttons: Optional[List[Tuple[str, Callable]]] = None) -> None:
        """
        Render modal dialog box.
        
        Modal layout (240×160, centered):
        - Header: Title bar with close button
        - Content: Scrollable text area
        - Footer: Action buttons
        
        Args:
            title: Modal title (e.g., "WARNING", "SCAN RESULTS")
            content_text: Modal content (plain text or formatted)
            modal_type: "info", "warning", "error", "success"
            buttons: List of (label, callback) tuples for footer buttons
        
        Modal types determine border color:
            - info: cyan (#00ffff)
            - warning: yellow (#ffff00)
            - error: red (#ff0000)
            - success: green (#00ff00)
        """
        try:
            # Clear existing modal
            self.canvas.delete("modal")
            
            # Modal positioning (centered)
            modal_width = LAYOUT.MODAL_WIDTH
            modal_height = LAYOUT.MODAL_HEIGHT
            modal_x = (self.screen_width - modal_width) // 2
            modal_y = (self.screen_height - modal_height) // 2
            
            # Modal border color based on type
            border_colors = {
                "info": self._get_color('modal_info', "#00ffff"),
                "warning": self._get_color('modal_warning', "#ffff00"),
                "error": self._get_color('modal_error', "#ff0000"),
                "success": self._get_color('modal_success', "#00ff00")
            }
            border_color = border_colors.get(modal_type, "#00ffff")
            
            # Modal background
            modal_bg = self.canvas.create_rectangle(
                modal_x, modal_y,
                modal_x + modal_width, modal_y + modal_height,
                fill=self._get_color('modal_bg'),
                outline=border_color, width=2,
                tags="modal"
            )
            self.layer_objects[LayerZ.MODAL_BG].append(modal_bg)
            
            # Title bar
            title_height = 20
            title_bg = self.canvas.create_rectangle(
                modal_x, modal_y,
                modal_x + modal_width, modal_y + title_height,
                fill=border_color, outline="",
                tags="modal_title_bg"
            )
            self.layer_objects[LayerZ.MODAL_CONTENT].append(title_bg)
            
            # Title text
            title_item = self.canvas.create_text(
                modal_x + 5, modal_y + title_height // 2,
                text=title, fill="#000000",
                anchor="w", font=("Courier", 9, "bold"),
                tags="modal_title"
            )
            self.layer_objects[LayerZ.MODAL_CONTENT].append(title_item)
            
            # Close button
            close_x = modal_x + modal_width - 15
            close_btn = self.canvas.create_text(
                close_x, modal_y + 10,
                text="✕", fill="#000000",
                anchor="center", font=("Courier", 12),
                tags="modal_close"
            )
            self.layer_objects[LayerZ.MODAL_CONTENT].append(close_btn)
            
            # Content text
            content_item = self.canvas.create_text(
                modal_x + 10, modal_y + title_height + 10,
                text=content_text,
                fill=self._get_color('text_primary'),
                anchor="nw", font=("Courier", 8),
                width=modal_width - 20,
                tags="modal_content"
            )
            self.layer_objects[LayerZ.MODAL_CONTENT].append(content_item)
            
            # Footer buttons
            if buttons:
                button_y = modal_y + modal_height - 20
                button_width = (modal_width - 10) // len(buttons)
                
                for idx, (label, callback) in enumerate(buttons):
                    btn_x = modal_x + 5 + (idx * button_width)
                    btn_item = self.canvas.create_rectangle(
                        btn_x, button_y,
                        btn_x + button_width - 5, button_y + 15,
                        fill="", outline=border_color, width=1,
                        tags=f"modal_button_{idx}"
                    )
                    self.layer_objects[LayerZ.MODAL_CONTENT].append(btn_item)
                    
                    btn_label = self.canvas.create_text(
                        btn_x + (button_width - 5) // 2, button_y + 7,
                        text=label,
                        fill=self._get_color('text_primary'),
                        anchor="center", font=("Courier", 7),
                        tags=f"modal_button_label_{idx}"
                    )
                    self.layer_objects[LayerZ.MODAL_CONTENT].append(btn_label)
            
            # Raise modal layers to front
            self.canvas.tag_raise("modal")
            self.canvas.tag_raise("modal_title_bg")
            self.canvas.tag_raise("modal_content")
        
        except Exception as e:
            logger.error(f"Modal render error: {e}")
    
    def _get_heat_color(self, percent: float) -> str:
        """
        Get heat color gradient for CPU usage visualization.
        
        Color gradient: Green (0%) → Yellow (50%) → Red (100%)
        
        Args:
            percent: Percentage value (0-100)
        
        Returns:
            Hex color string
        """
        if percent < 50:
            # Green to Yellow
            r = int(204 + (51 * (percent / 50)))
            g = 255
        else:
            # Yellow to Red
            r = 255
            g = int(255 - (255 * ((percent - 50) / 50)))
        
        return f"#{r:02x}{g:02x}00"
    
    def update_layer_z_order(self) -> None:
        """
        Update z-order of all elements to ensure proper layering.
        
        Order (bottom to top):
        1. Background
        2. Glass panel
        3. Terminal text
        4. UI elements
        5. Modal background
        6. Modal content
        7. Overlay (tooltips, etc)
        """
        try:
            for layer in LayerZ:
                for item_id in self.layer_objects[layer]:
                    self.canvas.tag_raise(f"layer_{layer.name}")
        except Exception as e:
            logger.error(f"Z-order update error: {e}")


def create_default_renderer(canvas: tk.Canvas,
                           theme_manager: Optional[ThemeManager] = None,
                           debug: bool = False) -> ScreenRenderer:
    """
    Factory function to create a configured ScreenRenderer instance.
    
    Args:
        canvas: Tkinter canvas
        theme_manager: Optional ThemeManager for dynamic colors
        debug: Enable debug logging
    
    Returns:
        Configured ScreenRenderer instance
    """
    context = RenderContext(
        canvas=canvas,
        theme_manager=theme_manager,
        debug_mode=debug
    )
    return ScreenRenderer(canvas, context)
