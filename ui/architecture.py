"""
DedSecOS UI Architecture - MVC Pattern Foundation

This module provides the base classes for implementing a clean Model-View-Controller
pattern in the DedSecOS UI. It enables separation of concerns, testability, and
scalability from 2 to 20+ security tools.

Architecture:
    Model:      Business logic (PortScanner, ARPSpoofer, etc.)
    View:       UI rendering (Canvas, components, visual effects)
    Controller: Input handling (MenuState, ButtonState, touch events)

Usage:
    from ui.architecture import Model, View, Controller

    class MySecurityTool(Model):
        def execute(self):
            # Tool business logic here
            pass

    class MyToolView(View):
        def render(self, rect):
            # Render results to canvas
            pass
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

# ============================================================================
# TYPE DEFINITIONS
# ============================================================================


@dataclass
class Rectangle:
    """Simple rectangle for positioning UI elements."""

    x: int
    y: int
    width: int
    height: int

    @property
    def center_x(self) -> int:
        return self.x + self.width // 2

    @property
    def center_y(self) -> int:
        return self.y + self.height // 2

    def contains_point(self, px: int, py: int) -> bool:
        """Check if point (px, py) is inside this rectangle."""
        return self.x <= px < self.x + self.width and self.y <= py < self.y + self.height


class UIState(Enum):
    """Enumeration of possible UI element states."""

    NORMAL = "normal"
    HOVER = "hover"
    PRESSED = "pressed"
    DISABLED = "disabled"
    ERROR = "error"
    SUCCESS = "success"
    LOADING = "loading"


# ============================================================================
# MODEL LAYER - Business Logic
# ============================================================================


class Model(ABC):
    """
    Base class for all business logic models.

    Models encapsulate the core functionality of security tools, managing
    state, execution, and data transformation independent of the UI.

    Example:
        class PortScanner(Model):
            def __init__(self):
                self.target = None
                self.results = []

            def execute(self):
                # Scan ports
                self.results = scan_target(self.target)
                self.notify_observers()
    """

    def __init__(self, name: str):
        """Initialize model with a name."""
        self.name = name
        self.observers: List["Observer"] = []
        self.is_running = False
        self.error_state = None
        self.logger = logging.getLogger(f"Model:{name}")

    @abstractmethod
    def execute(self) -> None:
        """Execute the model's primary operation. Implement in subclasses."""
        pass

    def reset(self) -> None:
        """Reset model to initial state."""
        self.is_running = False
        self.error_state = None
        self.logger.info(f"Model '{self.name}' reset")

    def set_error(self, error: Exception) -> None:
        """Set error state and notify observers."""
        self.error_state = error
        self.logger.error(f"Model error: {error}")
        self.notify_observers()

    def subscribe(self, observer: "Observer") -> None:
        """Register observer for state changes."""
        if observer not in self.observers:
            self.observers.append(observer)

    def unsubscribe(self, observer: "Observer") -> None:
        """Unregister observer."""
        if observer in self.observers:
            self.observers.remove(observer)

    def notify_observers(self) -> None:
        """Notify all observers of state change."""
        for observer in self.observers:
            observer.on_model_changed(self)


class Observer(ABC):
    """Observer pattern for model state changes."""

    @abstractmethod
    def on_model_changed(self, model: Model) -> None:
        """Called when model state changes."""
        pass


# ============================================================================
# VIEW LAYER - UI Rendering
# ============================================================================


class View(ABC):
    """
    Base class for all UI views.

    Views handle rendering to the canvas and don't contain business logic.
    They receive data from models and display it to the user.

    Example:
        class PortScannerView(View):
            def render(self, rect):
                # Draw scan results to canvas
                self.canvas.create_text(...)
    """

    def __init__(self, name: str, canvas=None):
        """Initialize view with name and canvas reference."""
        self.name = name
        self.canvas = canvas
        self.rect = None
        self.is_visible = True
        self.state = UIState.NORMAL
        self.logger = logging.getLogger(f"View:{name}")

    @abstractmethod
    def render(self, rect: Rectangle) -> None:
        """
        Render view content to canvas.

        Args:
            rect: Rectangle defining view area
        """
        pass

    def set_rect(self, rect: Rectangle) -> None:
        """Update rendering rectangle."""
        self.rect = rect

    def set_state(self, state: UIState) -> None:
        """Update view state (affects visual appearance)."""
        self.state = state
        self.logger.debug(f"View '{self.name}' state: {state.value}")

    def show(self) -> None:
        """Make view visible."""
        self.is_visible = True
        self.logger.debug(f"View '{self.name}' shown")

    def hide(self) -> None:
        """Hide view."""
        self.is_visible = False
        self.logger.debug(f"View '{self.name}' hidden")

    def get_color_for_state(self, state_colors: Dict[UIState, str]) -> str:
        """Get color based on current state."""
        return state_colors.get(self.state, state_colors.get(UIState.NORMAL, "#ffffff"))


# ============================================================================
# CONTROLLER LAYER - Input & State Management
# ============================================================================


class Controller(ABC):
    """
    Base class for input controllers.

    Controllers handle user input (touch, gestures, commands) and coordinate
    between models and views.

    Example:
        class PortScannerController(Controller):
            def on_touch(self, x, y):
                if self.start_button_rect.contains_point(x, y):
                    self.model.execute()
    """

    def __init__(self, name: str):
        """Initialize controller."""
        self.name = name
        self.model: Optional[Model] = None
        self.view: Optional[View] = None
        self.logger = logging.getLogger(f"Controller:{name}")

    def set_model(self, model: Model) -> None:
        """Bind model to this controller."""
        self.model = model
        self.logger.info(f"Model bound: {model.name}")

    def set_view(self, view: View) -> None:
        """Bind view to this controller."""
        self.view = view
        self.logger.info(f"View bound: {view.name}")

    @abstractmethod
    def on_touch(self, x: int, y: int) -> None:
        """Handle touch input. Implement in subclasses."""
        pass

    def on_command(self, command: str, args: Optional[Dict[str, Any]] = None) -> None:
        """
        Handle command from UI or external source.

        Args:
            command: Command name (e.g., "start", "stop")
            args: Optional arguments dictionary
        """
        self.logger.debug(f"Command: {command} {args or ''}")

    def on_back(self) -> None:
        """Handle back/cancel action."""
        self.logger.debug("Back action")

    def update(self, dt: float) -> None:
        """
        Update controller state each frame.

        Args:
            dt: Delta time since last frame (seconds)
        """
        pass


# ============================================================================
# COMPOSITE PATTERN - Hierarchical UI Components
# ============================================================================


class UIComponent(ABC):
    """
    Base class for reusable UI components.

    Components can be nested hierarchically and can contain other components.
    This enables building complex UIs from simple, testable pieces.

    Example:
        panel = Panel(Rectangle(10, 10, 300, 200))
        button = Button(Rectangle(10, 10, 50, 20), "Click Me")
        panel.add_child(button)
    """

    def __init__(self, name: str, rect: Rectangle):
        """Initialize component."""
        self.name = name
        self.rect = rect
        self.children: List["UIComponent"] = []
        self.parent: Optional["UIComponent"] = None
        self.state: UIState = UIState.NORMAL
        self.is_visible = True
        self.is_enabled = True
        self.state = UIState.NORMAL
        self.logger = logging.getLogger(f"Component:{name}")

    def add_child(self, component: "UIComponent") -> None:
        """Add child component."""
        if component.parent:
            component.parent.remove_child(component)
        component.parent = self
        self.children.append(component)
        self.logger.debug(f"Added child: {component.name}")

    def remove_child(self, component: "UIComponent") -> None:
        """Remove child component."""
        if component in self.children:
            self.children.remove(component)
            component.parent = None
            self.logger.debug(f"Removed child: {component.name}")

    @abstractmethod
    def render(self, canvas) -> None:
        """Render this component and all children."""
        pass

    def handle_touch(self, x: int, y: int) -> bool:
        """
        Handle touch event.

        Returns True if event was handled (consumed), False otherwise.
        """
        if not self.is_visible or not self.is_enabled:
            return False

        # Check children first (they're rendered on top)
        for child in reversed(self.children):
            if child.handle_touch(x, y):
                return True

        # Check self
        if self.rect.contains_point(x, y):
            return self.on_touch(x, y)

        return False

    @abstractmethod
    def on_touch(self, x: int, y: int) -> bool:
        """Handle touch on this component. Implement in subclasses."""
        pass

    def on_model_changed(self, model: Model) -> None:
        """Observer pattern: called when bound model changes."""
        self.logger.debug(f"Model changed: {model.name}")

    def set_state(self, state: UIState) -> None:
        """Set component state."""
        self.state = state
        for child in self.children:
            child.set_state(state)

    def show(self) -> None:
        """Show component and children."""
        self.is_visible = True
        for child in self.children:
            child.show()

    def hide(self) -> None:
        """Hide component and children."""
        self.is_visible = False
        for child in self.children:
            child.hide()

    def enable(self) -> None:
        """Enable component and children."""
        self.is_enabled = True
        for child in self.children:
            child.enable()

    def disable(self) -> None:
        """Disable component and children."""
        self.is_enabled = False
        for child in self.children:
            child.disable()


# ============================================================================
# EVENT SYSTEM - Decoupled Communication
# ============================================================================


@dataclass
class Event:
    """Base event class for decoupled communication."""

    type: str
    timestamp: float
    data: Dict[str, Any] = field(default_factory=dict)


class EventBus:
    """
    Central event bus for decoupled communication between components.

    Components can publish events without knowing who listens, and can
    subscribe to events without knowing who publishes.

    Example:
        bus = EventBus()

        # Subscribe to events
        bus.subscribe("scan_complete", on_scan_complete)

        # Publish events
        bus.publish(Event("scan_complete", time.time(), {"results": data}))
    """

    def __init__(self):
        """Initialize event bus."""
        self.subscribers: Dict[str, List[Callable]] = {}
        self.logger = logging.getLogger("EventBus")

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        self.logger.debug(f"Subscribed to '{event_type}'")

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """Unsubscribe from event type."""
        if event_type in self.subscribers:
            if callback in self.subscribers[event_type]:
                self.subscribers[event_type].remove(callback)
                self.logger.debug(f"Unsubscribed from '{event_type}'")

    def publish(self, event: Event) -> None:
        """Publish event to all subscribers."""
        if event.type in self.subscribers:
            for callback in self.subscribers[event.type]:
                try:
                    callback(event)
                except Exception as e:
                    self.logger.error(f"Error in event handler: {e}")
        else:
            self.logger.debug(f"No subscribers for event: {event.type}")


# ============================================================================
# APPLICATION FRAMEWORK - Tying It All Together
# ============================================================================


class Application:
    """
    Base application class that coordinates MVC components.

    This class manages the lifecycle of models, views, and controllers,
    and provides a framework for building complex applications.

    Example:
        app = Application("DedSecOS")
        app.register_tool("port_scanner", PortScannerModel, PortScannerView, PortScannerController)
        app.run()
    """

    def __init__(self, name: str, canvas=None):
        """Initialize application."""
        self.name = name
        self.canvas = canvas
        self.models: Dict[str, Model] = {}
        self.views: Dict[str, View] = {}
        self.controllers: Dict[str, Controller] = {}
        self.event_bus = EventBus()
        self.logger = logging.getLogger(f"App:{name}")
        self.is_running = False

    def register_tool(self, tool_name: str, model_class, view_class, controller_class) -> None:
        """
        Register a new tool with Model, View, Controller classes.

        Args:
            tool_name: Unique name for the tool
            model_class: Model class (will be instantiated)
            view_class: View class
            controller_class: Controller class
        """
        try:
            # Instantiate components
            model = model_class(tool_name)
            view = view_class(tool_name, self.canvas)
            controller = controller_class(tool_name)

            # Wire them together
            controller.set_model(model)
            controller.set_view(view)
            model.subscribe(view)

            # Register
            self.models[tool_name] = model
            self.views[tool_name] = view
            self.controllers[tool_name] = controller

            self.logger.info(f"Tool registered: {tool_name}")
        except Exception as e:
            self.logger.error(f"Error registering tool: {e}")

    def get_tool(
        self, tool_name: str
    ) -> Tuple[Optional[Model], Optional[View], Optional[Controller]]:
        """Get MVC components for a tool."""
        return (
            self.models.get(tool_name),
            self.views.get(tool_name),
            self.controllers.get(tool_name),
        )

    def shutdown(self) -> None:
        """Shutdown application and clean up resources."""
        self.is_running = False
        for model in self.models.values():
            model.reset()
        self.logger.info(f"Application '{self.name}' shutdown complete")


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "Rectangle",
    "UIState",
    "Model",
    "Observer",
    "View",
    "Controller",
    "UIComponent",
    "Event",
    "EventBus",
    "Application",
]
