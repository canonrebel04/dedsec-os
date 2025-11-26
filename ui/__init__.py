"""
DedSecOS UI Package

This package contains the user interface framework for DedSecOS, including:
- Architecture: MVC pattern base classes
- Components: Reusable UI widgets
- Themes: Visual theme system
- State: Application state management
- Tool Manager: Dynamic tool loading

Usage:
    from ui.architecture import Model, View, Controller
    from ui.components import Button, Modal, TextDisplay
    from ui.themes import Theme, ThemeManager
    from ui.state import MenuState, ToolState, StateContainer
"""

from .animations import (
    AnimationManager,
    Animator,
    ColorGradient,
    FadeTransition,
    GlitchEffect,
    MatrixRain,
    PulsingEffect,
    create_button_press_animation,
    create_fade_in,
    create_fade_out,
    create_logo_glitch,
    create_matrix_background,
    create_status_pulse,
)
from .architecture import (
    Application,
    Controller,
    Event,
    EventBus,
    Model,
    Observer,
    Rectangle,
    UIComponent,
    UIState,
    View,
)
from .components import (
    Button,
    Gauge,
    List,
    Modal,
    Panel,
    SelectionMenu,
    TextDisplay,
)
from .diagnostics import (
    CPUMonitor,
    DiagnosticsOverlay,
    FPSCounter,
    FrameTimer,
    MemoryTracker,
    TouchLogger,
    create_diagnostics_overlay,
)
from .rendering import (
    LayerZ,
    RenderContext,
    ScreenRenderer,
    create_default_renderer,
)
from .state import (
    MenuMode,
    MenuState,
    PreferenceManager,
    StateContainer,
    ToolState,
    ToolStatus,
)
from .themes import (
    Theme,
    ThemeManager,
    ThemeType,
)
from .tool_manager import (
    ToolCategory,
    ToolExecutionContext,
    ToolManager,
    ToolMetadata,
    get_tool_manager,
)
from .tool_manager import (
    ToolStatus as ToolExecutionStatus,
)

__all__ = [
    # Architecture
    "Model",
    "View",
    "Controller",
    "UIComponent",
    "UIState",
    "Rectangle",
    "Event",
    "EventBus",
    "Application",
    "Observer",
    # Components
    "Button",
    "Modal",
    "TextDisplay",
    "SelectionMenu",
    "Gauge",
    "Panel",
    "List",
    # State
    "MenuState",
    "MenuMode",
    "ToolState",
    "ToolStatus",
    "StateContainer",
    "PreferenceManager",
    # Themes
    "Theme",
    "ThemeManager",
    "ThemeType",
    # Rendering
    "ScreenRenderer",
    "RenderContext",
    "LayerZ",
    "create_default_renderer",
    # Tool Manager
    "ToolManager",
    "ToolMetadata",
    "ToolCategory",
    "ToolExecutionStatus",
    "ToolExecutionContext",
    "get_tool_manager",
    # Animations
    "Animator",
    "ColorGradient",
    "PulsingEffect",
    "GlitchEffect",
    "FadeTransition",
    "MatrixRain",
    "AnimationManager",
    "create_button_press_animation",
    "create_status_pulse",
    "create_logo_glitch",
    "create_fade_in",
    "create_fade_out",
    "create_matrix_background",
    # Diagnostics
    "DiagnosticsOverlay",
    "FPSCounter",
    "MemoryTracker",
    "CPUMonitor",
    "TouchLogger",
    "FrameTimer",
    "create_diagnostics_overlay",
]

__version__ = "3.2.1"
