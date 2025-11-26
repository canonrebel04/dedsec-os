"""State Management System for DedSec UI Framework

This module provides comprehensive state management for the DedSec application,
including menu navigation, tool state tracking, and preference persistence.

Key Classes:
    MenuState: Tracks current menu position and navigation history
    ToolState: Base class for tool-specific state management
    StateContainer: Holds all state across the application
    PreferenceManager: Persists user preferences to disk (JSON)

Architecture:
    - Observer pattern: State changes notify listeners
    - Immutable state snapshots: Each state change creates new object
    - Preference persistence: Auto-save/load from disk
    - Tool isolation: Each tool manages its own state

Example:
    >>> state = StateContainer()
    >>> state.menu.push("main")
    >>> state.menu.push("network_tools")
    >>> state.menu.current_menu
    'network_tools'
    >>> state.menu.back()
    True
    >>> state.menu.current_menu
    'main'

"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
import json
import logging
import os
from datetime import datetime


# ============================================================================
# LOGGING SETUP
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class ToolStatus(Enum):
    """Tool execution status states."""
    IDLE = "idle"              # Not running
    RUNNING = "running"        # Actively executing
    PAUSED = "paused"          # Temporarily suspended
    COMPLETED = "completed"    # Finished successfully
    ERROR = "error"            # Failed with error
    CANCELLED = "cancelled"    # User cancelled
    WAITING = "waiting"        # Waiting for user input


class MenuMode(Enum):
    """Navigation modes for menu system."""
    NORMAL = "normal"          # Standard menu navigation
    SELECTION = "selection"    # Selecting from list
    CONFIRMATION = "confirmation"  # Yes/no confirmation
    INPUT = "input"            # Text input mode


# ============================================================================
# MENU STATE
# ============================================================================

@dataclass
class MenuState:
    """Tracks menu navigation state with history stack.
    
    Attributes:
        stack: Navigation history (breadcrumb trail)
        current_menu: Currently visible menu
        mode: Current interaction mode (normal, selection, etc.)
        selection_index: Currently selected item (0-based)
        max_selections: Max items visible at once (for scrolling)
        selected_items: Set of selected items (multi-select)
        
    Methods:
        push: Navigate to new menu
        back: Go back in history
        pop: Remove from stack without switching
        clear: Reset to root menu
        get_breadcrumb: Get navigation path
        set_selection: Update selected item
        add_selection: Add to multi-select
        remove_selection: Remove from multi-select
        toggle_selection: Toggle item in multi-select
        
    Example:
        >>> menu = MenuState(root_menu="main")
        >>> menu.push("tools")
        >>> menu.push("network")
        >>> menu.get_breadcrumb()
        ['main', 'tools', 'network']
        >>> menu.back()
        True
        >>> menu.current_menu
        'tools'
    """
    
    stack: List[str] = field(default_factory=lambda: ["main"])
    current_menu: str = "main"
    mode: MenuMode = MenuMode.NORMAL
    selection_index: int = 0
    max_selections: int = 6  # Pi 2 screen shows ~6 items
    selected_items: Set[str] = field(default_factory=set)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Callbacks for state changes
    _on_menu_change: List[Callable[["MenuState"], None]] = field(default_factory=list)
    _on_selection_change: List[Callable[[int], None]] = field(default_factory=list)
    
    def push(self, menu: str) -> None:
        """Navigate to new menu, adding to stack.
        
        Args:
            menu: Menu identifier to navigate to
            
        Example:
            >>> menu = MenuState()
            >>> menu.push("tools")
            >>> menu.current_menu
            'tools'
        """
        if menu != self.current_menu:
            self.stack.append(menu)
            self.current_menu = menu
            self.selection_index = 0
            self.selected_items.clear()
            self.timestamp = datetime.now().isoformat()
            self._notify_menu_change()
            logger.debug(f"Navigated to menu: {menu}")
    
    def back(self) -> bool:
        """Go back to previous menu in history.
        
        Returns:
            True if back was possible, False if already at root
            
        Example:
            >>> menu = MenuState()
            >>> menu.push("tools")
            >>> menu.back()
            True
            >>> menu.current_menu
            'main'
            >>> menu.back()
            False
        """
        if len(self.stack) > 1:
            self.stack.pop()
            self.current_menu = self.stack[-1]
            self.selection_index = 0
            self.selected_items.clear()
            self.timestamp = datetime.now().isoformat()
            self._notify_menu_change()
            logger.debug(f"Navigated back to: {self.current_menu}")
            return True
        return False
    
    def pop(self) -> Optional[str]:
        """Remove from stack without switching menu.
        
        Returns:
            Popped menu name, or None if stack would be empty
        """
        if len(self.stack) > 1:
            popped = self.stack.pop()
            logger.debug(f"Popped menu: {popped}")
            return popped
        return None
    
    def clear(self) -> None:
        """Reset to root menu."""
        self.stack = ["main"]
        self.current_menu = "main"
        self.selection_index = 0
        self.selected_items.clear()
        self.timestamp = datetime.now().isoformat()
        self._notify_menu_change()
        logger.debug("Menu state cleared to root")
    
    def get_breadcrumb(self) -> List[str]:
        """Get navigation breadcrumb trail.
        
        Returns:
            List of menu names from root to current
            
        Example:
            >>> menu = MenuState()
            >>> menu.push("tools")
            >>> menu.push("network")
            >>> menu.get_breadcrumb()
            ['main', 'tools', 'network']
        """
        return self.stack.copy()
    
    def set_selection(self, index: int) -> None:
        """Set selected item index.
        
        Args:
            index: 0-based item index
            
        Example:
            >>> menu = MenuState()
            >>> menu.set_selection(3)
            >>> menu.selection_index
            3
        """
        self.selection_index = max(0, index)
        self.timestamp = datetime.now().isoformat()
        self._notify_selection_change()
        logger.debug(f"Selection changed to: {index}")
    
    def add_selection(self, item: str) -> None:
        """Add item to multi-select set.
        
        Args:
            item: Item identifier to add
        """
        self.selected_items.add(item)
        self.timestamp = datetime.now().isoformat()
        logger.debug(f"Added to selection: {item}")
    
    def remove_selection(self, item: str) -> None:
        """Remove item from multi-select set.
        
        Args:
            item: Item identifier to remove
        """
        self.selected_items.discard(item)
        self.timestamp = datetime.now().isoformat()
        logger.debug(f"Removed from selection: {item}")
    
    def toggle_selection(self, item: str) -> bool:
        """Toggle item in multi-select set.
        
        Args:
            item: Item identifier to toggle
            
        Returns:
            True if now selected, False if now deselected
        """
        if item in self.selected_items:
            self.remove_selection(item)
            return False
        else:
            self.add_selection(item)
            return True
    
    def subscribe_menu_change(self, callback: Callable[["MenuState"], None]) -> None:
        """Subscribe to menu changes.
        
        Args:
            callback: Function to call when menu changes
        """
        self._on_menu_change.append(callback)
    
    def subscribe_selection_change(self, callback: Callable[[int], None]) -> None:
        """Subscribe to selection changes.
        
        Args:
            callback: Function to call with new selection index
        """
        self._on_selection_change.append(callback)
    
    def _notify_menu_change(self) -> None:
        """Internal: Notify menu change subscribers."""
        for callback in self._on_menu_change:
            try:
                callback(self)
            except Exception as e:
                logger.error(f"Error in menu change callback: {e}")
    
    def _notify_selection_change(self) -> None:
        """Internal: Notify selection change subscribers."""
        for callback in self._on_selection_change:
            try:
                callback(self.selection_index)
            except Exception as e:
                logger.error(f"Error in selection change callback: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization.
        
        Returns:
            Dictionary representation of state
        """
        return {
            "stack": self.stack,
            "current_menu": self.current_menu,
            "mode": self.mode.value,
            "selection_index": self.selection_index,
            "selected_items": list(self.selected_items),
            "timestamp": self.timestamp,
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "MenuState":
        """Create MenuState from dictionary.
        
        Args:
            data: Dictionary with state data
            
        Returns:
            MenuState instance
        """
        return MenuState(
            stack=data.get("stack", ["main"]),
            current_menu=data.get("current_menu", "main"),
            mode=MenuMode(data.get("mode", "normal")),
            selection_index=data.get("selection_index", 0),
            selected_items=set(data.get("selected_items", [])),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
        )


# ============================================================================
# TOOL STATE
# ============================================================================

@dataclass
class ToolState(ABC):
    """Base class for tool-specific state management.
    
    Subclass this for each tool to track tool-specific data.
    
    Attributes:
        tool_id: Unique tool identifier
        status: Current tool execution status
        progress: Progress 0.0-1.0 (for long operations)
        error: Error message if status is ERROR
        result: Result data from last execution
        created_at: Timestamp of state creation
        updated_at: Timestamp of last update
        
    Methods:
        reset: Clear all state
        set_result: Update result with timestamp
        set_error: Set error status
        mark_complete: Mark as completed
        to_dict: Serialize state
        from_dict: Deserialize state
        
    Example:
        >>> class PortScannerState(ToolState):
        ...     def __init__(self, tool_id):
        ...         super().__init__(tool_id)
        ...         self.ports_found = []
        ...         self.target_ip = ""
        
        >>> state = PortScannerState("port_scanner")
        >>> state.status = ToolStatus.RUNNING
        >>> state.progress = 0.5
    """
    
    tool_id: str
    status: ToolStatus = ToolStatus.IDLE
    progress: float = 0.0
    error: Optional[str] = None
    result: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def reset(self) -> None:
        """Clear all state data."""
        self.status = ToolStatus.IDLE
        self.progress = 0.0
        self.error = None
        self.result = {}
        self.updated_at = datetime.now().isoformat()
        logger.debug(f"Tool state reset: {self.tool_id}")
    
    def set_result(self, result: Dict[str, Any]) -> None:
        """Update result data with timestamp.
        
        Args:
            result: Result dictionary
        """
        self.result = result
        self.updated_at = datetime.now().isoformat()
    
    def set_error(self, error: str) -> None:
        """Set error status and message.
        
        Args:
            error: Error message
        """
        self.status = ToolStatus.ERROR
        self.error = error
        self.updated_at = datetime.now().isoformat()
        logger.error(f"Tool error [{self.tool_id}]: {error}")
    
    def mark_complete(self) -> None:
        """Mark tool as successfully completed."""
        self.status = ToolStatus.COMPLETED
        self.progress = 1.0
        self.updated_at = datetime.now().isoformat()
    
    def mark_running(self) -> None:
        """Mark tool as running."""
        self.status = ToolStatus.RUNNING
        self.progress = 0.0
        self.error = None
        self.updated_at = datetime.now().isoformat()
    
    def set_progress(self, progress: float) -> None:
        """Update progress (0.0-1.0).
        
        Args:
            progress: Progress value
        """
        self.progress = max(0.0, min(1.0, progress))
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize tool state to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "tool_id": self.tool_id,
            "status": self.status.value,
            "progress": self.progress,
            "error": self.error,
            "result": self.result,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @staticmethod
    @abstractmethod
    def from_dict(data: Dict[str, Any]) -> "ToolState":
        """Deserialize tool state from dictionary.
        
        Args:
            data: Dictionary with state data
            
        Returns:
            ToolState instance
            
        Note:
            Subclasses must override to restore tool-specific fields
        """
        raise NotImplementedError


# ============================================================================
# STATE CONTAINER
# ============================================================================

@dataclass
class StateContainer:
    """Central container for all application state.
    
    Manages:
        - Menu navigation (MenuState)
        - Tool states (Dict[tool_id, ToolState])
        - Global settings
        - Undo/redo history
        
    Example:
        >>> state = StateContainer()
        >>> state.menu.push("tools")
        >>> state.get_tool_state("port_scanner").mark_running()
        >>> state.has_changes()
        True
    """
    
    menu: MenuState = field(default_factory=MenuState)
    tool_states: Dict[str, ToolState] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    _change_listeners: List[Callable[[], None]] = field(default_factory=list)
    _history: List[Dict[str, Any]] = field(default_factory=list)
    _history_index: int = 0
    
    def register_tool_state(self, tool_id: str, state: ToolState) -> None:
        """Register a tool's state.
        
        Args:
            tool_id: Unique tool identifier
            state: ToolState instance for this tool
        """
        self.tool_states[tool_id] = state
        logger.debug(f"Registered tool state: {tool_id}")
    
    def get_tool_state(self, tool_id: str) -> Optional[ToolState]:
        """Get tool state by ID.
        
        Args:
            tool_id: Tool identifier
            
        Returns:
            ToolState instance or None if not found
        """
        return self.tool_states.get(tool_id)
    
    def reset_tool_state(self, tool_id: str) -> None:
        """Reset a tool's state to initial values.
        
        Args:
            tool_id: Tool identifier
        """
        state = self.get_tool_state(tool_id)
        if state:
            state.reset()
            logger.debug(f"Reset tool state: {tool_id}")
    
    def set_setting(self, key: str, value: Any) -> None:
        """Set a global setting.
        
        Args:
            key: Setting name
            value: Setting value
        """
        self.settings[key] = value
        logger.debug(f"Setting changed: {key} = {value}")
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a global setting.
        
        Args:
            key: Setting name
            default: Default value if not found
            
        Returns:
            Setting value or default
        """
        return self.settings.get(key, default)
    
    def subscribe_changes(self, callback: Callable[[], None]) -> None:
        """Subscribe to any state change.
        
        Args:
            callback: Function to call on state change
        """
        self._change_listeners.append(callback)
    
    def has_changes(self) -> bool:
        """Check if unsaved changes exist.
        
        Returns:
            True if state differs from saved version
        """
        return len(self._history) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize all state to dictionary.
        
        Returns:
            Dictionary representation of entire state
        """
        return {
            "menu": self.menu.to_dict(),
            "tool_states": {
                tid: state.to_dict()
                for tid, state in self.tool_states.items()
            },
            "settings": self.settings,
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "StateContainer":
        """Deserialize state from dictionary.
        
        Args:
            data: Dictionary with state data
            
        Returns:
            StateContainer instance
        """
        container = StateContainer()
        
        if "menu" in data:
            container.menu = MenuState.from_dict(data["menu"])
        
        if "settings" in data:
            container.settings = data["settings"]
        
        return container


# ============================================================================
# PREFERENCE MANAGER
# ============================================================================

class PreferenceManager:
    """Persists user preferences to disk (JSON format).
    
    Handles:
        - Auto-save preferences on changes
        - Load preferences on startup
        - Default values
        - File locking for multi-process safety
        
    Attributes:
        preferences_file: Path to JSON preferences file
        auto_save: Whether to auto-save on changes
        
    Methods:
        save: Write preferences to disk
        load: Read preferences from disk
        get: Get preference value
        set: Set preference and optionally auto-save
        
    Example:
        >>> prefs = PreferenceManager("/home/pi/.dedsec/prefs.json")
        >>> prefs.load()
        >>> prefs.set("theme", "neon_green", auto_save=True)
        >>> prefs.get("theme")
        'neon_green'
    """
    
    def __init__(
        self,
        preferences_file: Optional[str] = None,
        auto_save: bool = True
    ):
        """Initialize preference manager.
        
        Args:
            preferences_file: Path to JSON preferences file
                If None, defaults to ~/.dedsec/prefs.json
            auto_save: Automatically save on changes
        """
        if preferences_file is None:
            home = os.path.expanduser("~")
            preferences_file = os.path.join(home, ".dedsec", "prefs.json")
        
        self.preferences_file = preferences_file
        self.auto_save = auto_save
        self.preferences: Dict[str, Any] = {}
        self.defaults: Dict[str, Any] = self._get_defaults()
        
        logger.info(f"PreferenceManager initialized: {preferences_file}")
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Get default preferences.
        
        Returns:
            Dictionary of default values
        """
        return {
            "theme": "neon_green",
            "brightness": 100,
            "volume": 50,
            "last_tool": None,
            "last_menu": "main",
            "auto_scan": False,
            "animations_enabled": True,
            "fps_counter": False,
            "language": "en",
        }
    
    def load(self) -> bool:
        """Load preferences from disk.
        
        Returns:
            True if loaded successfully, False if file doesn't exist
        """
        try:
            if os.path.exists(self.preferences_file):
                with open(self.preferences_file, 'r') as f:
                    data = json.load(f)
                    self.preferences = data
                    logger.info(f"Preferences loaded: {len(data)} items")
                    return True
            else:
                logger.info("Preferences file not found, using defaults")
                self.preferences = self.defaults.copy()
                return False
        except Exception as e:
            logger.error(f"Failed to load preferences: {e}")
            self.preferences = self.defaults.copy()
            return False
    
    def save(self) -> bool:
        """Save preferences to disk.
        
        Returns:
            True if saved successfully
        """
        try:
            os.makedirs(os.path.dirname(self.preferences_file), exist_ok=True)
            
            # Write to temp file first (atomic write)
            temp_file = f"{self.preferences_file}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(self.preferences, f, indent=2)
            
            # Atomic rename
            os.replace(temp_file, self.preferences_file)
            logger.debug(f"Preferences saved: {self.preferences_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save preferences: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get preference value.
        
        Args:
            key: Preference name
            default: Default value if not found
            
        Returns:
            Preference value or default
        """
        if default is None:
            default = self.defaults.get(key)
        return self.preferences.get(key, default)
    
    def set(self, key: str, value: Any, auto_save: Optional[bool] = None) -> None:
        """Set preference value.
        
        Args:
            key: Preference name
            value: Preference value
            auto_save: Override instance auto_save setting
        """
        old_value = self.preferences.get(key)
        self.preferences[key] = value
        
        if old_value != value:
            logger.debug(f"Preference changed: {key} = {value}")
        
        # Use auto_save parameter if provided, else use instance setting
        should_save = auto_save if auto_save is not None else self.auto_save
        if should_save:
            self.save()
    
    def reset_to_defaults(self) -> None:
        """Reset all preferences to defaults."""
        self.preferences = self.defaults.copy()
        if self.auto_save:
            self.save()
        logger.info("Preferences reset to defaults")
    
    def to_dict(self) -> Dict[str, Any]:
        """Get all preferences as dictionary.
        
        Returns:
            Dictionary of all preferences
        """
        return self.preferences.copy()


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "ToolStatus",
    "MenuMode",
    "MenuState",
    "ToolState",
    "StateContainer",
    "PreferenceManager",
]
