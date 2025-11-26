# ARCHITECTURE BLUEPRINT: Phase 3.2 - Professional UI Refactoring
**Date:** November 22, 2025  
**Status:** 📋 SPECIFICATION READY  
**Target Version:** v3.2

---

## Part 1: MVC/MVP Architecture Foundation

### Current State Analysis
```
BEFORE (Monolithic):
┌─────────────────────────────────────┐
│       DedSecOS (667 lines)          │
├─────────────────────────────────────┤
│ • UI rendering (canvas operations)  │
│ • State management (menu_state)     │
│ • Tool execution (tools.py imports) │
│ • Network operations (subprocess)   │
│ • Event handling (mouse/keyboard)   │
│ • Logging + error handling          │
└─────────────────────────────────────┘

Issues:
- Hard to test components in isolation
- State mutations scattered across methods
- Tool integration not standardized
- Rendering logic tightly coupled to data
- Difficult to add new tools (copy-paste code)
```

### Target Architecture
```
AFTER (Modular MVC):

┌──────────────────────────────────────────────────┐
│  app.py (Entry point, 15 lines)                  │
├──────────────────────────────────────────────────┤
│  from ui.main import DedSecOS                    │
│  if __name__ == "__main__": ...                  │
└──────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
    ┌────────┐   ┌──────────┐    ┌──────────┐
    │ MODEL  │   │   VIEW   │    │CONTROLLER│
    ├────────┤   ├──────────┤    ├──────────┤
    │Security│   │Components│    │  Input   │
    │ Tools  │   │ Rendering│    │ Handlers │
    │ State  │   │  Themes  │    │  Events  │
    └────────┘   └──────────┘    └──────────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
            ┌───────────┴───────────┐
            ▼                       ▼
        ┌─────────────┐    ┌────────────────┐
        │  core/      │    │  ui/           │
        ├─────────────┤    ├────────────────┤
        │ security/   │    │ architecture.py│
        │ tools/      │    │ components.py  │
        │ logging.py  │    │ themes.py      │
        │             │    │ state.py       │
        │             │    │ tool_manager.py│
        │             │    │ animations.py  │
        │             │    │ diagnostics.py │
        └─────────────┘    └────────────────┘
```

### File Structure (Proposed)
```
dedsec/
├── app.py                           # Entry point (15 lines)
├── config.py                        # Global config (colors, dimensions)
├── PLAN.md                          # Current master plan
├── IMPLEMENTATION_3_2_BUGFIXES.md   # This file
│
├── core/
│   ├── __init__.py
│   ├── logging.py                   # Structured logging + performance
│   ├── security/                    # Phase 2 tools
│   │   └── __init__.py
│   └── tools/                       # Phase 3 tools
│       ├── __init__.py
│       ├── base.py                  # ToolBase class
│       ├── port_scanner.py
│       ├── arp_spoofer.py
│       └── ...
│
├── ui/
│   ├── __init__.py
│   ├── main.py                      # DedSecOS refactored (clean)
│   ├── architecture.py              # MVC base classes
│   ├── components.py                # UIComponent, Button, Modal, etc.
│   ├── themes.py                    # Theme system + 5 variations
│   ├── state.py                     # MenuState, ToolState
│   ├── tool_manager.py              # ToolManager, dynamic loading
│   ├── animations.py                # Animation utilities
│   ├── diagnostics.py               # FPS, memory, CPU monitoring
│   └── design_system.py             # (existing, keep as-is)
│
└── tests/
    ├── __init__.py
    ├── test_architecture.py
    ├── test_components.py
    ├── test_themes.py
    └── test_tools.py
```

---

## Part 2: MVC Layer Definitions

### Model Layer (`core/`)

#### Purpose
- Encapsulate business logic
- Manage data state (secure)
- Provide tool interfaces
- Handle networking operations

#### Key Classes

**ToolBase (core/tools/base.py)**
```python
from abc import ABC, abstractmethod

class ToolBase(ABC):
    """Base class for all security tools."""
    
    def __init__(self, name: str, version: str = "1.0"):
        self.name = name
        self.version = version
        self.is_running = False
        self.last_result = None
        self.error_log = []
    
    @abstractmethod
    def execute(self, *args, **kwargs):
        """Run the tool. Override in subclass."""
        pass
    
    @abstractmethod
    def get_status(self) -> dict:
        """Return current status: {running, progress, error}."""
        pass
    
    @abstractmethod
    def cancel(self):
        """Stop execution gracefully."""
        pass
    
    @abstractmethod
    def reset(self):
        """Clear state and results."""
        pass
```

**SecurityModel (core/security_model.py)**
```python
class SecurityModel:
    """Manages all active security tools and their state."""
    
    def __init__(self):
        self.tools: Dict[str, ToolBase] = {}
        self.results: Dict[str, Any] = {}
        self.state_history: List[Dict] = []
    
    def register_tool(self, name: str, tool: ToolBase) -> bool:
        """Register a new tool."""
        if name in self.tools:
            raise ValueError(f"Tool {name} already registered")
        self.tools[name] = tool
        return True
    
    def run_tool(self, name: str, *args, **kwargs) -> Future:
        """Execute tool asynchronously."""
        if name not in self.tools:
            raise KeyError(f"Unknown tool: {name}")
        tool = self.tools[name]
        # Return Future for async execution
        return executor.submit(tool.execute, *args, **kwargs)
    
    def get_tool_result(self, name: str) -> Any:
        """Get last tool result."""
        return self.results.get(name)
```

### View Layer (`ui/components.py`)

#### Purpose
- Render UI elements (canvas operations)
- Apply themes/styles
- Display data (no logic)
- Provide visual feedback

#### Key Classes

**UIComponent (base class)**
```python
class UIComponent(ABC):
    """Base class for all UI components."""
    
    def __init__(self, name: str, rect: Rect, theme: Theme):
        self.name = name
        self.rect = rect  # Bounding box
        self.theme = theme
        self.canvas_ids = []  # Track created items for cleanup
        self.is_visible = True
        self.state = "NORMAL"
    
    @abstractmethod
    def render(self, canvas: tk.Canvas):
        """Draw component on canvas."""
        pass
    
    @abstractmethod
    def on_touch(self, event) -> bool:
        """Handle touch event. Return True if handled."""
        pass
    
    def cleanup(self):
        """Remove all canvas items."""
        for item_id in self.canvas_ids:
            self.canvas.delete(item_id)
        self.canvas_ids.clear()
    
    def set_state(self, state: str):
        """Update component state: NORMAL, HOVER, PRESSED, DISABLED."""
        self.state = state
        self.render(self.canvas)
```

**Button Component**
```python
class Button(UIComponent):
    """Clickable button with visual feedback."""
    
    def __init__(self, name: str, rect: Rect, text: str, 
                 command: Callable, theme: Theme):
        super().__init__(name, rect, theme)
        self.text = text
        self.command = command
    
    def render(self, canvas: tk.Canvas):
        """Render button with state-appropriate colors."""
        colors = {
            "NORMAL": self.theme.button_bg,
            "HOVER": self.theme.button_hover,
            "PRESSED": self.theme.button_pressed,
            "DISABLED": self.theme.button_disabled,
        }
        
        # Draw button rectangle
        rect_id = canvas.create_rectangle(
            self.rect.x, self.rect.y,
            self.rect.x + self.rect.width, self.rect.y + self.rect.height,
            fill=colors[self.state],
            outline=self.theme.button_border
        )
        self.canvas_ids.append(rect_id)
        
        # Draw text
        text_id = canvas.create_text(
            self.rect.center_x(), self.rect.center_y(),
            text=self.text,
            fill=self.theme.text_primary,
            font=self.theme.font_body
        )
        self.canvas_ids.append(text_id)
    
    def on_touch(self, event) -> bool:
        """Execute command on click."""
        if self._point_in_rect(event.x, event.y):
            self.set_state("PRESSED")
            self.root.after(100, lambda: self.set_state("NORMAL"))
            self.command()
            return True
        return False
```

**Modal Component**
```python
class Modal(UIComponent):
    """Reusable modal dialog."""
    
    def __init__(self, name: str, title: str, content: UIComponent,
                 width: int = 240, height: int = 160, theme: Theme = None):
        rect = Rect(
            x=(320-width)//2,
            y=(240-height)//2,
            width=width,
            height=height
        )
        super().__init__(name, rect, theme)
        self.title = title
        self.content = content
    
    def render(self, canvas: tk.Canvas):
        """Draw modal with header, content, close button."""
        # Background
        bg_id = canvas.create_rectangle(
            self.rect.x, self.rect.y,
            self.rect.x + self.rect.width, self.rect.y + self.rect.height,
            fill=self.theme.modal_bg,
            outline=self.theme.modal_border
        )
        self.canvas_ids.append(bg_id)
        
        # Header
        header_height = 24
        header_id = canvas.create_rectangle(
            self.rect.x, self.rect.y,
            self.rect.x + self.rect.width, self.rect.y + header_height,
            fill=self.theme.modal_header_bg,
            outline=""
        )
        self.canvas_ids.append(header_id)
        
        # Title
        title_id = canvas.create_text(
            self.rect.x + 10, self.rect.y + 12,
            text=self.title,
            fill=self.theme.text_primary,
            font=self.theme.font_title,
            anchor="w"
        )
        self.canvas_ids.append(title_id)
        
        # Close button (X)
        close_x = self.rect.x + self.rect.width - 20
        close_y = self.rect.y + 12
        close_id = canvas.create_text(
            close_x, close_y,
            text="✕",
            fill=self.theme.error_color,
            font=("Courier", 12, "bold")
        )
        self.canvas_ids.append(close_id)
        
        # Content
        content_rect = Rect(
            self.rect.x + 5,
            self.rect.y + header_height + 5,
            self.rect.width - 10,
            self.rect.height - header_height - 10
        )
        self.content.rect = content_rect
        self.content.render(canvas)
```

### Controller Layer (`ui/state.py`)

#### Purpose
- Handle user input
- Update model based on UI interactions
- Trigger view updates
- Manage application state flow

#### Key Classes

**AppController**
```python
class AppController:
    """Central controller for app state and input handling."""
    
    def __init__(self, model: SecurityModel, view_manager: ViewManager):
        self.model = model
        self.views = view_manager
        self.current_tool = None
        self.state_stack = []  # For back navigation
    
    def on_button_click(self, button_name: str):
        """Handle button press from UI."""
        handler = self._get_handler(button_name)
        if handler:
            handler()
    
    def on_tool_selected(self, tool_name: str):
        """Switch to selected tool."""
        self.current_tool = tool_name
        self.state_stack.append(tool_name)
        # Update view with tool UI
        self.views.show_tool(tool_name)
    
    def on_tool_executed(self, tool_name: str, params: dict) -> Future:
        """Execute tool with parameters."""
        future = self.model.run_tool(tool_name, **params)
        future.add_done_callback(
            lambda f: self._on_tool_complete(tool_name, f)
        )
        return future
    
    def _on_tool_complete(self, tool_name: str, future: Future):
        """Update view when tool completes."""
        try:
            result = future.result()
            self.views.show_tool_result(tool_name, result)
        except Exception as e:
            self.views.show_error(f"Tool error: {e}")
```

---

## Part 3: Component Library Specification

### Core Components (ui/components.py - 400 lines)

| Component | Purpose | States | Canvas Items |
|-----------|---------|--------|--------------|
| Button | Clickable action | NORMAL, HOVER, PRESSED, DISABLED | Rectangle + Text |
| TextDisplay | Read-only text (logs) | NORMAL, SELECTED | Text (pooled) |
| SelectionMenu | Grid of options | NORMAL, SELECTED | Rectangles + Text |
| Modal | Dialog container | HIDDEN, VISIBLE | Rectangle + Widgets |
| Gauge | Progress/status bar | NORMAL, WARNING, ERROR | Rectangle (filled) |
| Status | System info widget | NORMAL, ANIMATED | Text |
| Terminal | Multi-line scrollable text | NORMAL, SCROLLING | Text (pooled) |

### Each Component Implements
```python
class UIComponent(ABC):
    # Initialization
    def __init__(self, name: str, rect: Rect, theme: Theme)
    
    # Rendering
    def render(self, canvas: tk.Canvas)  # Draw on canvas
    def cleanup(self)                     # Remove from canvas
    def set_state(self, state: str)       # Update visual state
    
    # Interaction
    def on_touch(self, event) -> bool     # Handle click
    def on_hover(self, event)             # Handle mouse enter/leave
```

---

## Part 4: Theme System Specification

### Theme Class Structure (ui/themes.py - 200 lines)

```python
class Theme:
    """Color and style definitions for UI rendering."""
    
    # Color palette
    background: str
    foreground: str
    accent: str
    error: str
    warning: str
    success: str
    
    # Component colors
    button_bg: str
    button_hover: str
    button_pressed: str
    button_disabled: str
    button_border: str
    button_text: str
    
    modal_bg: str
    modal_border: str
    modal_header_bg: str
    
    # Typography
    font_title: tuple      # (name, size, weight)
    font_body: tuple
    font_small: tuple
    font_code: tuple
    
    # Spacing
    padding: int
    border_width: int
    
    # Animations
    transition_ms: int
    animation_frames: int
```

### 5 Cyberpunk Theme Variations

#### Theme 1: Neon Green (Classic Matrix)
```python
NEON_GREEN = Theme(
    name="Neon Green",
    background="#000000",
    foreground="#00ff00",
    accent="#00ff00",
    error="#ff0000",
    warning="#ffff00",
    success="#00ff00",
    # ...
)
```

#### Theme 2: Cyberpunk Pink/Blue (Synthwave)
```python
CYBERPUNK = Theme(
    name="Cyberpunk",
    background="#0a0e27",
    foreground="#ff006e",    # Hot pink
    accent="#00f5ff",        # Cyan
    error="#ff0a16",
    warning="#ffa502",
    success="#00ff88",
    # ...
)
```

#### Theme 3: Monochrome Matrix
```python
MONOCHROME = Theme(
    name="Monochrome",
    background="#000000",
    foreground="#00aa00",    # Muted green
    accent="#00aa00",
    error="#aa0000",
    warning="#aa8800",
    success="#00aa00",
    # ...
)
```

#### Theme 4: Acid Trip (RGB Cycling - Warnings Only)
```python
ACID_TRIP = Theme(
    name="Acid Trip",
    background="#000000",
    foreground="#ff00ff",
    accent="#00ffff",
    error="#ff0000",
    warning="#ffff00",      # Rapid cycle
    success="#00ff00",
    # Special: animations cycle through RGB
)
```

#### Theme 5: Stealth Mode (Dark Gray)
```python
STEALTH = Theme(
    name="Stealth",
    background="#0a0a0a",
    foreground="#666666",
    accent="#999999",
    error="#cc0000",
    warning="#ccaa00",
    success="#00cc00",
    # Minimal visual feedback - for stealth ops
)
```

### Theme Application
```python
# In config.py or ui/themes.py
ACTIVE_THEME = NEON_GREEN  # Switchable at runtime

# Usage in components
class Button(UIComponent):
    def render(self, canvas):
        canvas.create_rectangle(
            fill=self.theme.button_bg,
            outline=self.theme.button_border
        )
```

---

## Part 5: State Management Specification

### MenuState Expansion (ui/state.py)

**Current:**
```python
class MenuState:
    def __init__(self):
        self.current_menu = "main"
        self.wifi_list = []
        self.selected_wifi = None
```

**Enhanced:**
```python
class MenuState:
    """Centralized menu/UI state."""
    
    def __init__(self):
        # Navigation
        self.current_view = "main"  # main, tools, modal, settings
        self.modal_stack = []        # For nested modals
        self.history = []            # Back navigation
        
        # Tool selection
        self.selected_tool = None
        self.tool_params = {}        # Current tool parameters
        
        # WiFi state
        self.wifi_list: List[AP] = []
        self.selected_bssid = None
        self.target_channel = None
        
        # General
        self.last_update = time.time()
        self.is_busy = False         # Tool running
```

### ToolState Base Class

```python
class ToolState(ABC):
    """Manage state for individual tools."""
    
    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.is_running = False
        self.result = None
        self.error = None
        self.last_run = None
    
    @abstractmethod
    def serialize(self) -> dict:
        """Convert state to dict for saving."""
        pass
    
    @abstractmethod
    def deserialize(self, data: dict):
        """Restore state from dict."""
        pass
    
    def save_to_file(self, path: str):
        """Persist state to disk."""
        import json
        with open(path, 'w') as f:
            json.dump(self.serialize(), f)
    
    def load_from_file(self, path: str):
        """Load state from disk."""
        import json
        with open(path, 'r') as f:
            self.deserialize(json.load(f))
```

### State Persistence
```python
# Save user preferences
class PreferenceManager:
    def __init__(self, config_dir: str = "~/.dedsec"):
        self.config_dir = Path(config_dir).expanduser()
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def save_theme(self, theme_name: str):
        """Save user's theme preference."""
        config = {"theme": theme_name, "timestamp": time.time()}
        with open(self.config_dir / "theme.json", 'w') as f:
            json.dump(config, f)
    
    def load_theme(self) -> str:
        """Load saved theme or default."""
        theme_file = self.config_dir / "theme.json"
        if theme_file.exists():
            with open(theme_file) as f:
                return json.load(f).get("theme", "NEON_GREEN")
        return "NEON_GREEN"
```

---

## Part 6: Tool Registration System

### ToolManager (ui/tool_manager.py - 150 lines)

```python
class ToolManager:
    """Dynamically load and manage security tools."""
    
    def __init__(self, model: SecurityModel):
        self.model = model
        self.tools_dir = Path(__file__).parent.parent / "core" / "tools"
        self.loaded_tools = {}
    
    def discover_tools(self) -> List[str]:
        """Find all .py files in tools/ directory."""
        tools = []
        for tool_file in self.tools_dir.glob("*.py"):
            if tool_file.name != "__init__.py" and not tool_file.name.startswith("_"):
                tools.append(tool_file.stem)
        return sorted(tools)
    
    def load_tool(self, tool_name: str) -> ToolBase:
        """Dynamically import and instantiate tool."""
        # Import module: core.tools.{tool_name}
        module = importlib.import_module(f"core.tools.{tool_name}")
        
        # Find ToolBase subclass in module
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, ToolBase) and 
                obj != ToolBase):
                tool = obj()
                self.model.register_tool(tool_name, tool)
                self.loaded_tools[tool_name] = tool
                return tool
        
        raise ValueError(f"No ToolBase subclass found in {tool_name}")
    
    def get_all_tools(self) -> Dict[str, ToolBase]:
        """Get all loaded tools."""
        return self.loaded_tools.copy()
    
    def unload_tool(self, tool_name: str):
        """Stop and remove tool."""
        tool = self.loaded_tools.pop(tool_name)
        if tool.is_running:
            tool.cancel()
```

### Tool Lifecycle

```
DISCOVERY (on startup):
  ToolManager.discover_tools() → ["port_scanner", "arp_spoofer", ...]

LOADING (when needed):
  ToolManager.load_tool("port_scanner")
  → Imports core.tools.port_scanner module
  → Finds PortScanner class (extends ToolBase)
  → Instantiates and registers with model

EXECUTION (on user action):
  controller.on_tool_executed("port_scanner", {"target": "192.168.1.1"})
  → model.run_tool("port_scanner", target="192.168.1.1")
  → Runs in thread pool, returns Future

COMPLETION (when done):
  Future callbacks update view with results
  → views.show_tool_result("port_scanner", results)

UNLOADING (on exit or deselect):
  ToolManager.unload_tool("port_scanner")
  → Tool.cancel() if running
  → Remove from loaded_tools
```

---

## Part 7: Rendering Refactor

### Current Structure (Monolithic)
```python
class DedSecOS:
    def setup_ui_layers(self):
        # 300+ lines: buttons, modals, stats, scrollbar, etc.
        # All mixed together, no separation of concerns
```

### Target Structure (Modular)
```python
class DedSecOS:
    def _draw_header(self):
        """Render status bar (clock, network, icons)."""
    
    def _draw_sidebar(self):
        """Render left button panel."""
    
    def _draw_terminal(self):
        """Render log output area."""
    
    def _draw_status_bar(self):
        """Render system stats (CPU, RAM, Temp, Power)."""
    
    def _draw_modal(self):
        """Render active modal if any."""
    
    def _draw_overlays(self):
        """Render floating elements (tooltips, notifications)."""
    
    def render(self):
        """Master render - called every frame."""
        self.canvas.delete("all")  # Clear
        self._draw_header()
        self._draw_sidebar()
        self._draw_terminal()
        self._draw_status_bar()
        self._draw_modal()
        self._draw_overlays()
        self.root.after(33, self.render)  # ~30 FPS
```

### Benefits
- **Testability**: Each method can be tested independently
- **Maintenance**: Easy to locate and fix rendering bugs
- **Scalability**: Add new sections without touching existing code
- **Performance**: Optimize individual sections
- **Reusability**: Extract sections to components

---

## Part 8: Implementation Roadmap

### Phase 3.2.1: Core Architecture (4 hours)
- [ ] Create `ui/architecture.py` with MVC base classes
- [ ] Create `ui/components.py` with 7 core components
- [ ] Create `ui/state.py` with MenuState + ToolState
- [ ] Create `core/logging.py` for structured logging

### Phase 3.2.2: Themes & Config (3 hours)
- [ ] Create `ui/themes.py` with 5 theme variations
- [ ] Create `config.py` with centralized constants
- [ ] Implement theme switching (runtime + persisted)
- [ ] Update component colors to use theme

### Phase 3.2.3: Tool System (3 hours)
- [ ] Create `core/tools/base.py` with ToolBase class
- [ ] Create `ui/tool_manager.py` with dynamic loading
- [ ] Refactor PortScanner to inherit ToolBase
- [ ] Refactor ARPSpoofer to inherit ToolBase

### Phase 3.2.4: UI Refactoring (4 hours)
- [ ] Create modular `_draw_*()` methods
- [ ] Extract components from monolithic `setup_ui_layers()`
- [ ] Implement component rendering system
- [ ] Test rendering on Pi 2 for performance

### Phase 3.2.5: Animations & Effects (2 hours)
- [ ] Create `ui/animations.py` with animation utilities
- [ ] Implement pulsing, glitch, fade effects
- [ ] Add Matrix rain background option
- [ ] Performance test animations on Pi 2

### Phase 3.2.6: Testing & Docs (3 hours)
- [ ] Create `tests/` directory with unit tests
- [ ] Create `ui/diagnostics.py` for FPS/memory monitoring
- [ ] Update `DEVELOPER_GUIDE.md` with architecture
- [ ] Add code comments and type hints

**Total Estimated Time: 19 hours**

---

## Part 9: Success Metrics

### Before vs After Comparison

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Main file lines | 667 | 200 | < 250 |
| Time to add new tool | 30 min (copy-paste) | 10 min (inherit) | < 15 min |
| File dependencies | All in 1 | Modularized | < 5 per module |
| Unit test coverage | 0% | 60% | > 70% |
| Max frame time | 50ms | 33ms | < 40ms |
| Memory usage | 85MB | 75MB | < 80MB |
| Startup time | 4s | 3s | < 3.5s |
| Tools supported | 2 | 4+ | 20+ |

---

## Part 10: Migration Strategy

### Keep Current Version Running
```
dedsec_ui.py         (current production)
ui/main.py           (new refactored version)
ui/main_v1.py        (fallback)
```

### Gradual Replacement
1. **Week 1**: Architecture + Core components (feature parity)
2. **Week 2**: Theme system + Config
3. **Week 3**: Tool registration system
4. **Week 4**: Full UI refactoring

### Testing Before Cutover
- [ ] Feature parity test (same functionality)
- [ ] Performance test (no degradation)
- [ ] Compatibility test (all tools work)
- [ ] Integration test (end-to-end workflows)

### Rollback Plan
- Keep `dedsec_ui.py` as fallback
- `app.py` can quickly switch between versions
- Data format unchanged (backward compatible)

---

## Conclusion

This architecture transforms DedSecOS from a 667-line monolith into a **professional-grade, scalable system** that:

✅ Separates concerns (Model/View/Controller)  
✅ Enables component reusability  
✅ Supports 20+ tools without core changes  
✅ Provides consistent UI/UX  
✅ Improves maintainability and testability  
✅ Maintains performance on Pi 2  
✅ Enables future innovation (plugins, extensions)

**Ready to proceed with implementation?**

---

**Document Status**: 📋 Specification Complete  
**Next Action**: Execute Phase 3.2.1 (Core Architecture)  
**Estimated Completion**: December 6, 2025
