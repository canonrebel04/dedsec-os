# Config Module Implementation Guide

## Overview

The `config.py` module provides centralized configuration for all DedSecOS constants:
- **Layout dimensions** (optimized for 320×240 Pi screen)
- **Color definitions** (with dynamic theme support)
- **Animation timings** (in milliseconds)
- **Debug flags** (for development/production)
- **Tool parameters** (timeouts, defaults)

**Location:** `/home/cachy/dedsec/config.py`  
**Size:** 400+ lines of configuration and helpers  
**Status:** ✅ Complete and tested

---

## Quick Start

### Import Configuration

```python
from config import LAYOUT, COLORS, TIMINGS, DEBUG, TOOLS
```

### Use Layout Constants

```python
from config import LAYOUT

canvas = tkinter.Canvas(
    root,
    width=LAYOUT.CANVAS_WIDTH,    # 320
    height=LAYOUT.CANVAS_HEIGHT,  # 240
    bg=COLORS.get("background")
)

# Position elements
header_rect = (0, 0, LAYOUT.CANVAS_WIDTH, LAYOUT.HEADER_HEIGHT)
sidebar_rect = (0, LAYOUT.HEADER_HEIGHT, LAYOUT.SIDEBAR_WIDTH, LAYOUT.CANVAS_HEIGHT)
content_rect = (LAYOUT.CONTENT_X, LAYOUT.CONTENT_Y, LAYOUT.CONTENT_WIDTH, LAYOUT.CONTENT_HEIGHT)
```

### Use Colors with Dynamic Theming

```python
from config import COLORS, set_theme_manager
from ui.themes import ThemeManager

# Initialize theme
tm = ThemeManager()
set_theme_manager(tm)

# Colors now use current theme
bg_color = COLORS.get("background")
text_color = COLORS.get("text")
button_color = COLORS.get("button_bg")

# When theme changes, colors update automatically
tm.set_theme("synthwave")
new_bg = COLORS.get("background")  # Gets synthwave color
```

### Use Animation Timings

```python
from config import TIMINGS

def on_button_click():
    # Flash button for BUTTON_PRESS_DURATION milliseconds
    canvas.after(TIMINGS.BUTTON_PRESS_DURATION, restore_button)
    
    # Update every CLOCK_UPDATE_INTERVAL
    canvas.after(TIMINGS.CLOCK_UPDATE_INTERVAL, update_clock)
```

### Use Debug Flags

```python
from config import DEBUG, enable_debug_mode, disable_debug_mode

# Development mode
if DEBUG.SHOW_FPS_COUNTER:
    display_fps_counter()

# Enable all debug flags
enable_debug_mode()

# Disable for production
disable_debug_mode()
```

---

## Configuration Objects

### LAYOUT: Screen Dimensions & Positioning

```python
from config import LAYOUT

# Screen size (Pi 2 touchscreen)
LAYOUT.CANVAS_WIDTH    # 320
LAYOUT.CANVAS_HEIGHT   # 240

# Header (menu bar + clock)
LAYOUT.HEADER_HEIGHT   # 30
LAYOUT.HEADER_PADDING  # 5

# Sidebar (tool menu)
LAYOUT.SIDEBAR_WIDTH   # 80
LAYOUT.SIDEBAR_ITEM_HEIGHT  # 40
LAYOUT.SIDEBAR_PADDING      # 5

# Content area
LAYOUT.CONTENT_X       # 85 (after sidebar)
LAYOUT.CONTENT_Y       # 35 (after header)
LAYOUT.CONTENT_WIDTH   # 235
LAYOUT.CONTENT_HEIGHT  # 170

# Status bar
LAYOUT.STATUS_BAR_HEIGHT   # 30
LAYOUT.STATUS_BAR_Y        # 210 (at bottom)
LAYOUT.STATUS_BAR_PADDING  # 5

# Modal dialog
LAYOUT.MODAL_WIDTH         # 280
LAYOUT.MODAL_HEIGHT        # 160
LAYOUT.MODAL_X             # 20 (centered)
LAYOUT.MODAL_Y             # 40 (centered)
LAYOUT.MODAL_PADDING       # 10

# Buttons
LAYOUT.BUTTON_WIDTH        # 60
LAYOUT.BUTTON_HEIGHT       # 25
LAYOUT.BUTTON_PADDING      # 5
LAYOUT.BUTTON_BORDER_WIDTH # 2

# Typography
LAYOUT.FONT_FAMILY         # "Courier"
LAYOUT.FONT_SIZE_HEADER    # 12
LAYOUT.FONT_SIZE_BODY      # 10
LAYOUT.FONT_SIZE_SMALL     # 8
```

### COLORS: Dynamic Color System

```python
from config import COLORS, set_theme_manager
from ui.themes import ThemeManager

# Enable theme integration
tm = ThemeManager()
set_theme_manager(tm)

# Get individual colors
bg = COLORS.get("background")
text = COLORS.get("text")
error = COLORS.get("error_text")

# Get with fallback
custom = COLORS.get("my_color", "#FFFFFF")

# Get all colors as dict
all_colors = COLORS.get_all()

# Available color names (30+):
"background", "text", "text_secondary", "border",
"header_bg", "header_text",
"sidebar_bg", "sidebar_item_bg", "sidebar_item_hover", "sidebar_item_active",
"button_bg", "button_text", "button_hover", "button_active", "button_disabled",
"modal_bg", "modal_text", "modal_border",
"input_bg", "input_text", "input_border", "input_cursor",
"error_bg", "error_text",
"success_bg", "success_text",
"warning_bg", "warning_text",
"highlight", "accent", "muted",
"progress_bg", "progress_fill",
"status_ok", "status_warning", "status_error",
"panel_bg", "panel_border",
"terminal_bg", "terminal_text", "terminal_border",
```

### TIMINGS: Animation & Refresh Intervals

```python
from config import TIMINGS

# Button interactions (milliseconds)
TIMINGS.BUTTON_PRESS_DURATION      # 100 - Flash duration
TIMINGS.BUTTON_HOVER_DELAY         # 50  - Delay before hover

# Update cycles
TIMINGS.CLOCK_UPDATE_INTERVAL      # 1000 - Every 1 second
TIMINGS.STATUS_UPDATE_INTERVAL     # 500  - Every 0.5 seconds
TIMINGS.TOOL_PROGRESS_UPDATE       # 100  - Every 0.1 seconds

# Tool execution
TIMINGS.TOOL_TIMEOUT_WARNING       # 30000 - Warn if >30 seconds

# Animations (duration in ms)
TIMINGS.FADE_DURATION              # 300
TIMINGS.SLIDE_DURATION             # 200
TIMINGS.PULSING_DURATION           # 600
TIMINGS.GLITCH_DURATION            # 200

# Menu
TIMINGS.MENU_TRANSITION_DURATION   # 150
TIMINGS.SELECTION_CHANGE_DELAY     # 50

# Rendering
TIMINGS.FRAME_RATE                 # 30 FPS
TIMINGS.FRAME_DELAY                # 33 ms per frame

# Monitoring
TIMINGS.FPS_COUNTER_UPDATE         # 1000 - Update every 1 second
TIMINGS.MEMORY_CHECK_INTERVAL      # 5000 - Every 5 seconds
```

### DEBUG: Feature Flags & Monitoring

```python
from config import DEBUG, enable_debug_mode, disable_debug_mode

# Logging
DEBUG.ENABLE_LOGGING               # True/False
DEBUG.LOG_LEVEL                    # "DEBUG", "INFO", "WARNING", etc.
DEBUG.LOG_FILE                     # "/tmp/dedsec.log"

# Performance monitoring
DEBUG.SHOW_FPS_COUNTER             # Show frame rate
DEBUG.SHOW_MEMORY_USAGE            # Show RAM usage
DEBUG.SHOW_CPU_USAGE               # Show CPU percentage
DEBUG.PROFILE_RENDERING            # Profile render time

# Input debugging
DEBUG.LOG_TOUCH_EVENTS             # Log touch coordinates
DEBUG.SHOW_TOUCH_COORDINATES       # Display touch points

# Visual debugging
DEBUG.DEBUG_RECTANGLES             # Draw debug outlines
DEBUG.DEBUG_GRID                   # Show grid overlay
DEBUG.DEBUG_REGIONS                # Highlight regions

# Tool simulation
DEBUG.LOG_TOOL_EXECUTION           # Log tool runs
DEBUG.TOOL_SIMULATION_MODE         # Simulate without running

# Canvas
DEBUG.CANVAS_CLEAR_PREVIOUS        # Clear each frame
DEBUG.CANVAS_DOUBLE_BUFFER         # Use double buffering

# Helpers
enable_debug_mode()   # Enable all debug flags
disable_debug_mode()  # Disable all debug flags
```

### TOOLS: Security Tool Configuration

```python
from config import TOOLS

# Network scanning
TOOLS.PORT_SCAN_TIMEOUT            # 5000 ms per port
TOOLS.PORT_SCAN_DEFAULT_PORTS      # "1-1024"
TOOLS.PING_TIMEOUT                 # 2000 ms

# Wireless
TOOLS.WIFI_SCAN_TIMEOUT            # 10000 ms
TOOLS.WIFI_CONNECT_TIMEOUT         # 15000 ms

# General
TOOLS.DEFAULT_TOOL_TIMEOUT         # 30000 ms (30 seconds)
TOOLS.MAX_OUTPUT_LINES             # 500 lines
TOOLS.MAX_RESULT_SIZE              # 10 MB
```

---

## Integration Examples

### Example 1: Initialize App with Config & Theme

```python
import tkinter as tk
from config import LAYOUT, COLORS, set_theme_manager
from ui.themes import ThemeManager

# Initialize theme system
theme_manager = ThemeManager(default_theme="neon_green")
set_theme_manager(theme_manager)

# Create canvas with config
root = tk.Tk()
root.geometry(f"{LAYOUT.CANVAS_WIDTH}x{LAYOUT.CANVAS_HEIGHT}")
canvas = tk.Canvas(
    root,
    width=LAYOUT.CANVAS_WIDTH,
    height=LAYOUT.CANVAS_HEIGHT,
    bg=COLORS.get("background"),
    highlightthickness=0
)
canvas.pack()

# Now colors automatically use current theme
print(f"Background: {COLORS.get('background')}")  # Neon Green color

# Switch theme
theme_manager.set_theme("synthwave")
canvas.config(bg=COLORS.get("background"))  # Updates to synthwave color
```

### Example 2: Animate with Config Timings

```python
from config import TIMINGS, COLORS
import tkinter as tk

canvas = tk.Canvas(root, width=320, height=240)

def animate_button_press():
    # Flash white for BUTTON_PRESS_DURATION
    canvas.create_rectangle(10, 10, 60, 35, fill="white")
    canvas.after(TIMINGS.BUTTON_PRESS_DURATION, restore_button)

def restore_button():
    # Restore original color
    canvas.create_rectangle(10, 10, 60, 35, fill=COLORS.get("button_bg"))
    
    # Update again after BUTTON_HOVER_DELAY
    canvas.after(TIMINGS.BUTTON_HOVER_DELAY, check_hover)

canvas.bind("<Button-1>", lambda e: animate_button_press())
```

### Example 3: Tool Execution with Config Timeouts

```python
from config import TOOLS, TIMINGS, DEBUG

def run_port_scan(target_ip):
    timeout = TOOLS.PORT_SCAN_TIMEOUT  # 5000 ms per port
    
    for port in range(1, 1025):
        result = scan_port(target_ip, port, timeout=timeout)
        
        # Log if enabled
        if DEBUG.LOG_TOOL_EXECUTION:
            print(f"Port {port}: {result}")
        
        # Update progress every TOOL_PROGRESS_UPDATE_INTERVAL
        update_progress(port / 1024.0)
        
    # Warn if took too long
    if elapsed_time > TIMINGS.TOOL_TIMEOUT_WARNING:
        show_warning("Tool took longer than expected")
```

### Example 4: Debug Monitoring

```python
from config import DEBUG, enable_debug_mode
import psutil

# Enable debug mode for development
enable_debug_mode()

def render_debug_overlay():
    if DEBUG.SHOW_FPS_COUNTER:
        draw_text(f"FPS: {current_fps}")
    
    if DEBUG.SHOW_MEMORY_USAGE:
        memory = psutil.virtual_memory().percent
        draw_text(f"Memory: {memory:.1f}%")
    
    if DEBUG.SHOW_CPU_USAGE:
        cpu = psutil.cpu_percent()
        draw_text(f"CPU: {cpu:.1f}%")
    
    if DEBUG.DEBUG_RECTANGLES:
        draw_debug_outlines()
```

---

## Modifying Configuration

### Change Layout Dimensions

```python
from config import LAYOUT

# Resize for different screen
LAYOUT.CANVAS_WIDTH = 480
LAYOUT.CANVAS_HEIGHT = 320

# All dependent calculations use LAYOUT constants
```

### Add Custom Colors

```python
from config import COLORS

# Add to defaults
COLORS.DEFAULTS["my_custom_color"] = "#FF0080"

# Use it
my_color = COLORS.get("my_custom_color")
```

### Adjust Animation Timings

```python
from config import TIMINGS

# Make animations slower
TIMINGS.FADE_DURATION = 500
TIMINGS.SLIDE_DURATION = 300

# Faster button response
TIMINGS.BUTTON_PRESS_DURATION = 75
```

### Enable Production Debug Logging

```python
from config import DEBUG

# Keep essential logging
DEBUG.LOG_LEVEL = "WARNING"
DEBUG.SHOW_FPS_COUNTER = False
DEBUG.LOG_TOOL_EXECUTION = True
```

---

## Best Practices

### ✅ DO
- Use constants from `config` instead of magic numbers
- Set theme manager early in startup: `set_theme_manager(tm)`
- Use `COLORS.get(name, default)` for safe color lookups
- Enable debug mode during development: `enable_debug_mode()`

### ❌ DON'T
- Hardcode magic numbers: ❌ `rect = (10, 10, 60, 35)`
  - Use instead: ✅ `rect = (10, 10, LAYOUT.BUTTON_WIDTH, LAYOUT.BUTTON_HEIGHT)`
- Hardcode colors: ❌ `fill="#00FF00"`
  - Use instead: ✅ `fill=COLORS.get("text")`
- Use fixed timings: ❌ `canvas.after(1000, update)`
  - Use instead: ✅ `canvas.after(TIMINGS.CLOCK_UPDATE_INTERVAL, update)`

---

## File Structure

```
/home/cachy/dedsec/
├── config.py                (NEW - 400+ lines)
│   ├── LayoutConfig        (Screen dimensions)
│   ├── ColorConfig         (30+ colors)
│   ├── TimingConfig        (Animation timings)
│   ├── DebugConfig         (Feature flags)
│   ├── ToolConfig          (Tool parameters)
│   └── Helper functions    (set_theme_manager, etc.)
│
├── ui/
│   ├── themes.py           (ThemeManager, 5 themes)
│   ├── state.py            (MenuState, ToolState)
│   └── ...
│
└── dedsec_ui.py            (To be refactored with config)
```

---

## Next Steps

### Task #9: Refactor Canvas Rendering
Replace hardcoded values in `dedsec_ui.py` with config constants:
```python
# Before
canvas = tk.Canvas(root, width=320, height=240, bg="#000000")

# After
from config import LAYOUT, COLORS
canvas = tk.Canvas(root, width=LAYOUT.CANVAS_WIDTH, height=LAYOUT.CANVAS_HEIGHT, bg=COLORS.get("background"))
```

### Task #13: Logging Framework
Use `DEBUG` flags and `TIMINGS` for structured logging:
```python
if DEBUG.LOG_TOOL_EXECUTION:
    logger.info(f"Tool started, timeout: {TIMINGS.DEFAULT_TOOL_TIMEOUT}")
```

### Task #14: Animation System
Reference `TIMINGS` for smooth animations:
```python
for i in range(TIMINGS.FADE_DURATION // TIMINGS.FRAME_DELAY):
    alpha = i / (TIMINGS.FADE_DURATION // TIMINGS.FRAME_DELAY)
    # Animate...
```

---

## Summary

The `config.py` module centralizes all hardcoded values, enabling:
- ✅ Easy customization without code changes
- ✅ Consistent dimensions across the app
- ✅ Dynamic theme colors via ThemeManager
- ✅ Debug monitoring during development
- ✅ Tool parameter tuning

**Status:** ✅ Complete and ready for use  
**Next:** Refactor `dedsec_ui.py` to use config (Task #9)

---

*Generated: November 22, 2025*  
*Version: 3.2.1*
