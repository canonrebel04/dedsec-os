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

from .architecture import (
    Model,
    View,
    Controller,
    UIComponent,
    UIState,
    Rectangle,
    Event,
    EventBus,
    Application,
    Observer,
)

from .components import (
    Button,
    Modal,
    TextDisplay,
    SelectionMenu,
    Gauge,
    Panel,
    List,
)

from .state import (
    MenuState,
    MenuMode,
    ToolState,
    ToolStatus,
    StateContainer,
    PreferenceManager,
)

from .themes import (
    Theme,
    ThemeManager,
    ThemeType,
)

from .rendering import (
    ScreenRenderer,
    RenderContext,
    LayerZ,
    create_default_renderer,
)

from .tool_manager import (
    ToolManager,
    ToolMetadata,
    ToolCategory,
    ToolStatus as ToolExecutionStatus,
    ToolExecutionContext,
    get_tool_manager,
)

from .animations import (
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
    create_matrix_background,
)

from .diagnostics import (
    DiagnosticsOverlay,
    FPSCounter,
    MemoryTracker,
    CPUMonitor,
    TouchLogger,
    FrameTimer,
    create_diagnostics_overlay,
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
