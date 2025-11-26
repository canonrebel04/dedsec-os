# DedSec OS UI Framework - Developer Guide

**Version:** 3.2.1  
**Phase:** 3.2 - Comprehensive UI Refactoring Complete  
**Last Updated:** Phase 3.2 Completion

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [MVC Pattern Usage](#mvc-pattern-usage)
3. [Component System](#component-system)
4. [Theme Management](#theme-management)
5. [State Management](#state-management)
6. [Rendering Pipeline](#rendering-pipeline)
7. [Animation System](#animation-system)
8. [Tool Manager Integration](#tool-manager-integration)
9. [Configuration Reference](#configuration-reference)
10. [Logging Framework](#logging-framework)
11. [Testing Guide](#testing-guide)
12. [Performance Optimization](#performance-optimization)
13. [Diagnostics & Debugging](#diagnostics--debugging)

---

## Architecture Overview

DedSec OS uses a clean Model-View-Controller (MVC) architecture to separate concerns and enable scalability from 2 to 20+ security tools.

### Core Principles

- **Separation of Concerns:** Business logic (Model), UI rendering (View), and input handling (Controller) are independent
- **Reusable Components:** Button, Modal, TextDisplay components work across all tools
- **Theme-Driven UI:** All colors, fonts, and styles from centralized themes
- **State Persistence:** MenuState, ToolState, and preferences saved to JSON
- **Frame-Based Rendering:** Optimized for Raspberry Pi 2 (no time-based animations)

### Directory Structure

```
dedsec/
├── ui/                      # UI Framework (Phase 3.2)
│   ├── __init__.py          # Package exports
│   ├── architecture.py      # MVC base classes
│   ├── components.py        # Button, Modal, TextDisplay
│   ├── state.py             # State management
│   ├── themes.py            # Theme system
│   ├── rendering.py         # Canvas rendering
│   ├── tool_manager.py      # Tool registration & execution
│   ├── animations.py        # Animation framework
│   └── diagnostics.py       # Performance monitoring
├── tools.py                 # Tool implementations
├── app.py                   # Main application (legacy)
├── tests/                   # Test suite
│   ├── test_architecture.py
│   ├── test_components.py
│   ├── test_themes.py
│   ├── test_animations.py
│   └── test_diagnostics.py
└── docs/                    # Documentation
```

---

## MVC Pattern Usage

### Model: Business Logic

Models encapsulate tool functionality (port scanning, ARP spoofing, etc.) independent of UI.

**Example: Port Scanner Model**

```python
from ui.architecture import Model

class PortScanner(Model):
    def __init__(self):
        super().__init__(name="PortScanner")
        self.target = None
        self.port_range = None
        self.results = []
    
    def execute(self):
        """Run port scan."""
        self.logger.info(f"Scanning {self.target}:{self.port_range}")
        
        # Execute scan
        self.results = self._scan_ports(self.target, self.port_range)
        
        # Notify observers (views) of completion
        self.notify_observers("scan_complete", {"results": self.results})
    
    def _scan_ports(self, target, port_range):
        # Implementation here
        pass
```

**Key Methods:**
- `execute()`: Abstract method - implement tool logic here
- `notify_observers(event, data)`: Send updates to views
- `self.logger`: Pre-configured logger for your model

### View: UI Rendering

Views handle canvas rendering and respond to model updates.

**Example: Port Scanner View**

```python
from ui.architecture import View, Rectangle

class PortScannerView(View):
    def __init__(self, canvas):
        super().__init__(canvas)
        self.results_text = []
    
    def on_model_update(self, event, data):
        """Handle model updates."""
        if event == "scan_complete":
            self.results_text = data["results"]
            self.render()
    
    def render(self):
        """Draw results to canvas."""
        # Clear previous
        self.canvas.delete("scan_results")
        
        # Draw results
        y = 100
        for line in self.results_text:
            self.canvas.create_text(
                10, y,
                text=line,
                fill="#00ff00",
                font=("monospace", 9),
                anchor="nw",
                tags="scan_results"
            )
            y += 15
```

**Key Methods:**
- `on_model_update(event, data)`: React to model changes
- `render()`: Draw UI elements
- `self.controller`: Access controller for user actions

### Controller: Input Handling

Controllers coordinate between models and views, handling user input.

**Example: Port Scanner Controller**

```python
from ui.architecture import Controller

class PortScannerController(Controller):
    def __init__(self, model, view):
        super().__init__(model, view)
    
    def handle_action(self, action, data):
        """Handle user actions."""
        if action == "start_scan":
            self.model.target = data["target"]
            self.model.port_range = data["port_range"]
            self.model.execute()
        
        elif action == "cancel_scan":
            self.model.cancel()
```

**Key Methods:**
- `handle_action(action, data)`: Process user input
- `self.model`: Access model to trigger business logic
- `self.view`: Access view to update UI

---

## Component System

Reusable UI components for consistent interface across all tools.

### Button Component

**Basic Usage:**

```python
from ui.components import Button
from ui.architecture import Rectangle

# Create button
button = Button(
    canvas=canvas,
    rect=Rectangle(x=10, y=50, width=100, height=40),
    text="Scan",
    callback=lambda: self.start_scan()
)

# Render
button.render()

# Handle click (in touch handler)
if button.contains_point(touch_x, touch_y):
    button.on_click()
```

**Advanced Features:**

```python
# States
button.set_state(UIState.HOVER)
button.set_state(UIState.PRESSED)
button.set_state(UIState.DISABLED)

# Enable/Disable
button.disable()
button.enable()

# Update text
button.set_text("Scanning...")

# Custom styling (via theme)
button.bg_color = theme.get_color("accent")
button.text_color = theme.get_color("text")
```

### Modal Component

**Basic Usage:**

```python
from ui.components import Modal, Button

# Create modal
modal = Modal(
    canvas=canvas,
    title="Port Scanner",
    width=280,
    height=180
)

# Add components
scan_button = Button(...)
modal.add_component(scan_button)

# Show/hide
modal.show()
modal.hide()

# Render
modal.render()
```

**Layout Example:**

```python
# Compact layout for 320x240 screen
modal = Modal(canvas, "Port Scanner", width=280, height=180)

# Target buttons (3 in a row)
y = 40
for i, (label, ip) in enumerate([("Gateway", "192.168.1.1"), ...]):
    btn = Button(
        canvas, 
        Rectangle(10 + i*90, y, 85, 30),
        label,
        lambda ip=ip: set_target(ip)
    )
    modal.add_component(btn)

# Range buttons (5 in a row)
y = 80
for i, (label, range_val) in enumerate([("100", "1-100"), ...]):
    btn = Button(
        canvas,
        Rectangle(10 + i*54, y, 50, 25),
        label,
        lambda r=range_val: set_range(r)
    )
    modal.add_component(btn)

# Action button at bottom
scan_btn = Button(canvas, Rectangle(90, 145, 100, 30), "SCAN", scan)
modal.add_component(scan_btn)
```

### TextDisplay Component

**Basic Usage:**

```python
from ui.components import TextDisplay

# Create text display
display = TextDisplay(
    canvas=canvas,
    rect=Rectangle(10, 100, 300, 130),
    max_lines=10
)

# Add lines
display.add_line("Scanning 192.168.1.1...")
display.add_line("Port 22: OPEN")
display.add_line("Port 80: OPEN")

# Replace all text
display.set_text("Scan complete!\n3 ports open")

# Clear
display.clear()

# Render
display.render()
```

---

## Theme Management

Centralized theming for consistent styling across all UI elements.

### Available Themes

1. **dedsec** (Default): Cyberpunk green on black
2. **matrix**: Matrix-style bright green
3. **cyberpunk**: Neon cyan and magenta
4. **redteam**: Red hacker theme
5. **ghost**: Muted grey stealth theme

### Using Themes

```python
from ui.themes import ThemeManager

# Get manager instance
theme_manager = ThemeManager()

# Switch themes
theme_manager.switch_theme("matrix")
theme_manager.switch_theme("cyberpunk")

# Get colors
primary = theme_manager.get_color("primary")
bg = theme_manager.get_color("background")
text = theme_manager.get_color("text")
```

### Creating Custom Themes

```python
from ui.themes import Theme

# Define theme
custom_theme = Theme(
    name="custom",
    primary="#ff6600",
    secondary="#ff9933",
    accent="#ffcc00",
    background="#1a1a1a",
    text="#ffffff",
    success="#00ff00",
    error="#ff0000",
    warning="#ffaa00"
)

# Register
theme_manager.register_theme(custom_theme)

# Use it
theme_manager.switch_theme("custom")
```

### Theme-Aware Components

Components automatically use current theme colors:

```python
# Button uses theme colors
button = Button(canvas, rect, "Test", callback)
button.render()  # Uses theme.primary, theme.text, etc.

# Override for specific component
button.bg_color = "#custom_color"
button.render()
```

---

## State Management

Persistent state management for menus, tools, and user preferences.

### MenuState

Tracks current menu and navigation history.

```python
from ui.state import MenuState

menu_state = MenuState()

# Navigate menus
menu_state.set_current_menu("tools")
menu_state.set_current_menu("port_scanner")

# Go back
menu_state.go_back()

# Check state
current = menu_state.get_current_menu()  # Returns "tools"
can_go_back = menu_state.can_go_back()   # Returns True
```

### ToolState

Stores tool execution state and results.

```python
from ui.state import ToolState

tool_state = ToolState()

# Save tool state
tool_state.set_tool_data("port_scanner", {
    "last_target": "192.168.1.1",
    "last_range": "1-1000",
    "last_results": ["Port 22: OPEN", ...]
})

# Retrieve state
data = tool_state.get_tool_data("port_scanner")
target = data.get("last_target")
```

### PreferenceManager

User preferences with JSON persistence.

```python
from ui.state import PreferenceManager

prefs = PreferenceManager(config_path="/home/berry/dedsec/config.json")

# Set preferences
prefs.set("theme", "matrix")
prefs.set("fps_overlay", True)
prefs.set("log_level", "INFO")

# Get preferences
theme = prefs.get("theme", default="dedsec")
show_fps = prefs.get("fps_overlay", default=False)

# Save to disk
prefs.save()

# Load from disk
prefs.load()
```

---

## Rendering Pipeline

Layer-based rendering system with proper z-ordering.

### LayerZ Enum

```python
from ui.rendering import LayerZ

# Layer order (back to front):
LayerZ.BACKGROUND = 0    # Background gradients, patterns
LayerZ.CONTENT = 100     # Main content (text, results)
LayerZ.UI = 200          # Buttons, controls
LayerZ.MODAL = 300       # Modals, overlays
LayerZ.OVERLAY = 400     # Toast messages, FPS counter
```

### ScreenRenderer

```python
from ui.rendering import ScreenRenderer

renderer = ScreenRenderer(canvas, theme_manager)

# Draw background
renderer.draw_background(color="#000000")

# Draw components with layering
renderer.draw_button(button, layer=LayerZ.UI)
renderer.draw_modal(modal, layer=LayerZ.MODAL)

# Draw text with word wrapping
renderer.draw_text(
    text="Long text that needs wrapping...",
    x=10, y=50,
    max_width=300,
    layer=LayerZ.CONTENT
)

# Clear specific layer
renderer.clear_layer(LayerZ.MODAL)

# Clear all
renderer.clear_all()
```

### Rendering Best Practices

**1. Layer Management:**

```python
# Render in layer order
renderer.draw_background()           # LayerZ.BACKGROUND
renderer.draw_content()              # LayerZ.CONTENT
renderer.draw_buttons()              # LayerZ.UI
renderer.draw_modal()                # LayerZ.MODAL
renderer.draw_diagnostics_overlay()  # LayerZ.OVERLAY
```

**2. Avoid Flickering:**

```python
# BAD: Clear entire canvas
canvas.delete("all")

# GOOD: Clear specific layer
renderer.clear_layer(LayerZ.CONTENT)

# BETTER: Only update changed elements
if results_changed:
    renderer.clear_layer(LayerZ.CONTENT)
    renderer.draw_results()
```

**3. Text Wrapping:**

```python
# For 320x240 screen, wrap at 40 chars
renderer.draw_text(
    text="This is a long line of terminal output",
    x=10, y=100,
    max_width=300,
    wrap_chars=40,
    layer=LayerZ.CONTENT
)
```

---

## Animation System

Frame-based animation framework optimized for Raspberry Pi 2.

### Animation Classes

**ColorGradient:** Smooth color transitions

```python
from ui.animations import ColorGradient

# Create gradient
gradient = ColorGradient(
    start_color="#ccff00",
    end_color="#ffffff",
    duration_frames=30,
    loop=False
)

# Start animation
gradient.start()

# In main loop (60 FPS):
color = gradient.update()
canvas.itemconfig(item_id, fill=color)

if gradient.is_complete:
    # Animation finished
    pass
```

**PulsingEffect:** Rhythmic pulsing

```python
from ui.animations import PulsingEffect

# Create pulse (0.6 to 1.0 scale)
pulse = PulsingEffect(
    min_value=0.6,
    max_value=1.0,
    duration_frames=40,
    loop=True
)

pulse.start()

# In main loop:
scale = pulse.update()
# Apply to size, opacity, etc.
```

**GlitchEffect:** Cyberpunk glitch aesthetic

```python
from ui.animations import GlitchEffect

# Create glitch
glitch = GlitchEffect(
    glitch_texts=["ERROR", "HACK", "ACCESS", "DENIED", "BREACH"],
    glitch_colors=["#ff0000", "#00ff00", "#0000ff", "#ff00ff"],
    glitch_chance=0.3,
    duration_frames=150,
    loop=True
)

glitch.set_normal_state("DedSec OS", "#ccff00")
glitch.start()

# In main loop:
state = glitch.update()
canvas.itemconfig(
    logo_text_id,
    text=state['text'],
    fill=state['color']
)
canvas.coords(logo_text_id, base_x + state['offset_x'], base_y + state['offset_y'])
```

**FadeTransition:** Fade in/out

```python
from ui.animations import FadeTransition

# Fade in
fade_in = FadeTransition(fade_in=True, duration_frames=30)
fade_in.start()

# In main loop:
opacity = fade_in.update()
# Apply to alpha channel or item visibility
```

**MatrixRain:** Falling characters

```python
from ui.animations import MatrixRain

matrix = MatrixRain(
    max_chars=8,
    chars=['0', '1', 'A', 'B', 'X', 'Y'],
    duration_frames=150,
    loop=True
)

matrix.start()

# In main loop:
chars = matrix.update()
for char_data in chars:
    canvas.create_text(
        char_data['x'], char_data['y'],
        text=char_data['char'],
        fill=char_data['color'],
        font=("monospace", 10)
    )
```

### AnimationManager

Coordinate multiple animations:

```python
from ui.animations import AnimationManager

manager = AnimationManager()

# Register animations
manager.register("logo_glitch", glitch_effect)
manager.register("status_pulse", pulse_effect)
manager.register("button_press", gradient_effect)

# Start all
manager.start_all()

# Or start individual
manager.start("logo_glitch")

# In main loop:
states = manager.update_all()

logo_state = states.get("logo_glitch")
if logo_state:
    # Apply logo state
    pass
```

### Factory Functions

Quick animation creation:

```python
from ui.animations import (
    create_button_press_animation,
    create_status_pulse,
    create_logo_glitch,
    create_fade_in,
    create_fade_out,
    create_matrix_background
)

# Button press (5-frame color flash)
btn_anim = create_button_press_animation()

# Status pulsing (40-frame loop)
status_anim = create_status_pulse()

# Logo glitch (150-frame loop)
logo_anim = create_logo_glitch()

# Fade transitions
fade_in_anim = create_fade_in(duration_frames=30)
fade_out_anim = create_fade_out(duration_frames=20)

# Matrix background (8 chars, 150 frames)
matrix_anim = create_matrix_background()
```

---

## Tool Manager Integration

Register and execute security tools through the ToolManager.

### Registering Tools

```python
from ui.tool_manager import get_tool_manager, ToolDefinition

# Get manager
tool_manager = get_tool_manager()

# Define tool
port_scanner_tool = ToolDefinition(
    name="port_scanner",
    display_name="Port Scanner",
    description="Scan target for open ports",
    category="Network",
    execute_fn=execute_port_scan,
    requires_root=False
)

# Register
tool_manager.register_tool(port_scanner_tool)
```

### Executing Tools

```python
# Execute tool with parameters
context = tool_manager.execute_tool(
    "port_scanner",
    params={
        "target": "192.168.1.1",
        "port_range": "1-1000"
    }
)

# Check status
if context.status == ToolStatus.SUCCESS:
    results = context.results
elif context.status == ToolStatus.ERROR:
    error = context.error_message
```

### Tool Execution Context

```python
class ToolExecutionContext:
    tool_name: str
    status: ToolStatus  # IDLE, RUNNING, SUCCESS, ERROR
    start_time: float
    end_time: Optional[float]
    results: Any
    error_message: Optional[str]
```

---

## Configuration Reference

All configuration constants in `ui/__init__.py`:

### Display Settings

```python
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 240
FPS_TARGET = 60
```

### Layout Constants - Spacious Grid (Phase 3.2.2)

**Primary Zones:**

```python
HEADER_HEIGHT = 30           # Top bar (30px tall)
FOOTER_HEIGHT = 30           # Bottom bar (30px tall)
SIDEBAR_WIDTH = 70           # Left navigation (70px wide)
GUTTER_WIDTH = 10            # Blank separator (10px wide)
CONTENT_Y_START = 30         # Content starts after header
```

**Main Content Area** (calculated from grid):

```python
MAIN_CONTENT_X = 80          # Start position (SIDEBAR_WIDTH + GUTTER_WIDTH)
MAIN_CONTENT_Y = 30          # Start position (HEADER_HEIGHT)
MAIN_CONTENT_WIDTH = 240     # 320 - 70 (sidebar) - 10 (gutter)
MAIN_CONTENT_HEIGHT = 180    # 240 - 30 (header) - 30 (footer)
```

**Terminal Internal Padding** (5px safety margin):

```python
TERMINAL_PADDING_TOP = 5
TERMINAL_PADDING_BOTTOM = 5
TERMINAL_PADDING_LEFT = 5
TERMINAL_PADDING_RIGHT = 5
```

**Usable Terminal Space** (with padding applied):

```python
TERMINAL_USABLE_WIDTH = 230   # 240 - 5 (left) - 5 (right)
TERMINAL_USABLE_HEIGHT = 170  # 180 - 5 (top) - 5 (bottom)
```

**Modal Defaults:**

```python
MODAL_DEFAULT_WIDTH = 280
MODAL_DEFAULT_HEIGHT = 180
```

### Grid Layout Visualization

```
┌─────────────────────────────────────┐ 320px wide
│ HEADER (30px)                       │
├────────┬──┬─────────────────────────┤
│        │  │ MAIN CONTENT (240x180)  │
│ SIDE   │G │ ┌─────────────────────┐ │
│ BAR    │U │ │  Terminal Area      │ │ 240px tall
│ (70px) │T │ │  (230x170 usable)   │ │
│        │T │ │  5px padding        │ │
│        │E │ │  all sides          │ │
│        │R │ └─────────────────────┘ │
│        │  │                         │
├────────┴──┴─────────────────────────┤
│ FOOTER (30px)                       │
└─────────────────────────────────────┘

Dimensions:
- Sidebar: 70px × 180px (content area height)
- Gutter: 10px × 180px (visual separator)
- Main Content: 240px × 180px (outer boundary)
- Terminal Usable: 230px × 170px (after 5px padding)
- Character Columns: ~41 chars @ 9pt monospace
- Visible Lines: ~14 lines @ 12px line height
```

### Font Sizes

```python
FONT_HEADER = 12
FONT_BUTTON = 9
FONT_TEXT = 8
FONT_SMALL = 7
```

### Spacing

```python
PADDING_SMALL = 5
PADDING_MEDIUM = 10
PADDING_LARGE = 20
BUTTON_SPACING = 5
```

### Terminal Display

```python
TERMINAL_MAX_LINES = 200         # Total lines in memory buffer
TERMINAL_WRAP_CHARS = 41         # Optimal for 230px usable width
TERMINAL_LINE_HEIGHT = 12        # Pixels per line
TERMINAL_MAX_VISIBLE_LINES = 14  # Lines visible in 170px usable height
```

**Readability Improvements:**

The spacious grid design provides significant readability gains:

1. **Negative Space:** 10px gutter creates visual separation between navigation and content
2. **Safety Margins:** 5px padding ensures text never touches container edges
3. **Breathing Room:** 30px header/footer (up from 50px/30px) with vertically centered content
4. **Optimal Character Width:** 41 chars fits naturally in 230px usable width (5.5px per char @ 9pt monospace)
5. **Visible Lines:** 14 lines comfortably fit in 170px usable height (12px line spacing)

**Before vs After:**

```
BEFORE (cramped):                AFTER (spacious):
- Header: 50px (wasted space)    - Header: 30px (centered)
- Footer: 30px                   - Footer: 30px (centered)
- No gutter (cramped)            - Gutter: 10px (breathing room)
- No terminal padding            - Terminal padding: 5px all sides
- Text touches edges             - Text has 5px safety margin
- 40 char wrap (tight)           - 41 char wrap (optimal)
```

### Debug Flags

```python
DEBUG_MODE = False           # Enable diagnostics overlay
DEBUG_FPS = False            # Show FPS counter
DEBUG_TOUCH_EVENTS = False   # Log touch events
DEBUG_RENDERING = False      # Log rendering operations
```

---

## Logging Framework

Comprehensive logging system for debugging and monitoring.

### Logger Setup

```python
from ui import setup_logging

# Initialize logging
setup_logging(
    log_file="/home/berry/dedsec/dedsec.log",
    level="INFO",
    console=True
)
```

### Using Loggers

```python
import logging

# Get logger for module
logger = logging.getLogger(__name__)

# Log levels
logger.debug("Detailed debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical failure")

# With context
logger.info("Scanning target", extra={"target": "192.168.1.1"})
```

### Log Levels

- **DEBUG:** Detailed diagnostic info (frame updates, state changes)
- **INFO:** General events (menu navigation, tool execution)
- **WARNING:** Unexpected situations (missing config, deprecated usage)
- **ERROR:** Errors that don't crash app (failed scans, invalid input)
- **CRITICAL:** Severe errors (initialization failures)

### Example Logging

```python
class PortScanner(Model):
    def __init__(self):
        super().__init__(name="PortScanner")
        # self.logger automatically configured
    
    def execute(self):
        self.logger.info(f"Starting port scan: {self.target}")
        
        try:
            results = self._scan_ports()
            self.logger.info(f"Scan complete: {len(results)} ports found")
        except Exception as e:
            self.logger.error(f"Scan failed: {e}", exc_info=True)
```

---

## Testing Guide

Comprehensive test suite using unittest.

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Or use test runner
python tests/run_tests.py

# Run specific test file
python -m pytest tests/test_components.py -v

# Run specific test
python -m pytest tests/test_components.py::TestButton::test_on_click_normal -v
```

### Test Structure

```
tests/
├── __init__.py
├── run_tests.py             # Test runner
├── test_architecture.py     # MVC pattern tests
├── test_components.py       # Component tests
├── test_themes.py           # Theme system tests
├── test_animations.py       # Animation tests
└── test_diagnostics.py      # Diagnostics tests
```

### Writing Tests

**Example: Component Test**

```python
import unittest
from unittest.mock import MagicMock
from ui.components import Button
from ui.architecture import Rectangle

class TestButton(unittest.TestCase):
    def setUp(self):
        self.canvas = MagicMock()
        self.callback = MagicMock()
        self.button = Button(
            self.canvas,
            Rectangle(10, 10, 100, 40),
            "Test",
            self.callback
        )
    
    def test_on_click_calls_callback(self):
        self.button.on_click()
        self.callback.assert_called_once()
    
    def test_disabled_button_no_callback(self):
        self.button.disable()
        self.button.on_click()
        self.callback.assert_not_called()
```

---

## Performance Optimization

Tips for maintaining 60 FPS on Raspberry Pi 2.

### Frame-Based vs Time-Based

**Use frame-based animations:**

```python
# GOOD: Frame-based (consistent on Pi 2)
class MyAnimation(Animator):
    def update(self):
        self.current_frame += 1
        progress = self.current_frame / self.duration_frames
        return self.calculate_value(progress)

# AVOID: Time-based (inconsistent frame rate)
def update_animation():
    dt = time.time() - last_time
    position += velocity * dt
```

### Minimize Canvas Operations

```python
# BAD: Delete and recreate every frame
def render():
    canvas.delete("all")
    # Recreate everything

# GOOD: Only update changed items
def render():
    if text_changed:
        canvas.itemconfig(text_id, text=new_text)
    if color_changed:
        canvas.itemconfig(item_id, fill=new_color)
```

### Text Wrapping

```python
# Pre-wrap text instead of wrapping every frame
def log_line(text):
    wrapped = wrap_text(text, max_chars=40)
    for line in wrapped:
        terminal_lines.append(line)
```

### Batch Updates

```python
# Update multiple items, then refresh once
for item in items:
    canvas.itemconfig(item.id, fill=new_color)

canvas.update_idletasks()  # Single refresh
```

---

## Diagnostics & Debugging

Performance monitoring and debugging tools.

### Diagnostics Overlay

```python
from ui.diagnostics import create_diagnostics_overlay

# Create overlay
diagnostics = create_diagnostics_overlay(canvas, enabled=DEBUG_MODE)

# In main loop:
diagnostics.update()  # Update FPS, memory, CPU
diagnostics.draw()    # Render overlay

# Log touch events
def on_touch(event):
    diagnostics.log_touch(event.x, event.y, "click")
```

### Overlay Display

The overlay shows:
- **FPS:** Current frames per second
- **RAM:** Memory usage (MB and %)
- **CPU:** Process and system CPU usage
- **Frame:** Average frame time (ms)
- **Min/Max:** Frame time range
- **Touches:** Recent touch events (optional)

### Toggle Diagnostics

```python
# Toggle with keyboard shortcut
def on_key_press(event):
    if event.char == 'd':
        diagnostics.toggle()
```

### Custom Metrics

```python
# Access individual components
fps = diagnostics.fps_counter.get_fps()
memory_mb = diagnostics.memory_tracker.get_mb()
cpu_pct = diagnostics.cpu_monitor.get_process_percent()

# Check frame timing
stats = diagnostics.frame_timer.get_stats()
if stats['avg'] > 16.67:  # > 60 FPS target
    logger.warning(f"Slow frame: {stats['avg']:.1f}ms")
```

---

## Quick Reference Card

### Import Cheatsheet

```python
# Architecture
from ui.architecture import Model, View, Controller, Rectangle, UIState

# Components
from ui.components import Button, Modal, TextDisplay

# Themes
from ui.themes import ThemeManager, Theme

# State
from ui.state import MenuState, ToolState, PreferenceManager

# Rendering
from ui.rendering import ScreenRenderer, LayerZ

# Animations
from ui.animations import (
    ColorGradient, PulsingEffect, GlitchEffect,
    FadeTransition, MatrixRain, AnimationManager,
    create_button_press_animation, create_status_pulse,
    create_logo_glitch, create_fade_in, create_fade_out,
    create_matrix_background
)

# Diagnostics
from ui.diagnostics import create_diagnostics_overlay

# Tool Manager
from ui.tool_manager import get_tool_manager, ToolDefinition

# Logging
from ui import setup_logging
```

### Common Patterns

**Create a new tool:**

```python
# 1. Model
class MyTool(Model):
    def execute(self):
        # Logic here
        self.notify_observers("complete", {"results": data})

# 2. View
class MyToolView(View):
    def on_model_update(self, event, data):
        if event == "complete":
            self.render()
    
    def render(self):
        # Draw to canvas

# 3. Controller
class MyToolController(Controller):
    def handle_action(self, action, data):
        if action == "run":
            self.model.execute()

# 4. Wire together
model = MyTool()
view = MyToolView(canvas)
controller = MyToolController(model, view)
```

**Create a modal:**

```python
modal = Modal(canvas, "My Modal", 280, 180)

btn1 = Button(canvas, Rectangle(20, 50, 100, 35), "Option 1", callback1)
btn2 = Button(canvas, Rectangle(20, 95, 100, 35), "Option 2", callback2)

modal.add_component(btn1)
modal.add_component(btn2)

modal.show()
modal.render()
```

**Add animation:**

```python
anim = create_button_press_animation()
anim.start()

# In main loop:
color = anim.update()
canvas.itemconfig(button_id, fill=color)
```

---

## Support & Contributing

**Questions?** Check existing implementation in `app.py` for examples.

**Found a bug?** Check `dedsec.log` and diagnostics overlay first.

**Performance issues?** Enable diagnostics and check frame timing.

**Need help?** Review this guide and test suite examples.

---

**End of Developer Guide**
