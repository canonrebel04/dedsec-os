# QUICK START GUIDE: Using State & Theme Systems
**For:** DedSecOS UI Framework Phase 3.2+  
**Author:** GitHub Copilot  
**Last Updated:** November 22, 2025  

---

## 📋 TABLE OF CONTENTS

1. [State Management](#state-management)
2. [Theme System](#theme-system)
3. [Integration Examples](#integration-examples)
4. [Common Patterns](#common-patterns)
5. [API Reference](#api-reference)

---

## STATE MANAGEMENT

### Import

```python
from ui.state import MenuState, ToolState, StateContainer, PreferenceManager
```

### Menu Navigation

```python
from ui.state import MenuState

# Create menu state
menu = MenuState()

# Navigate
menu.push("tools")
menu.push("network_tools")
menu.push("port_scanner")

# Get current location
current = menu.current_menu  # "port_scanner"
breadcrumb = menu.get_breadcrumb()  # ["main", "tools", "network_tools", "port_scanner"]

# Go back
menu.back()  # Now at "network_tools"
menu.back()  # Now at "tools"

# Track selection
menu.set_selection(3)
menu.add_selection("item_1")
menu.toggle_selection("item_2")
```

### Tool State

```python
from ui.state import ToolState, ToolStatus

# Create tool-specific state class
class MyToolState(ToolState):
    def __init__(self):
        super().__init__("my_tool")
        self.custom_data = None
        self.results = []

# Use tool state
state = MyToolState()

# Track execution
state.mark_running()
state.set_progress(0.25)
state.set_progress(0.50)
state.set_progress(0.75)
state.mark_complete()

# Set results
state.set_result({"status": "success", "items": [1, 2, 3]})

# Handle errors
try:
    do_something()
except Exception as e:
    state.set_error(f"Failed: {e}")  # Auto-sets status to ERROR

# Check status
if state.status == ToolStatus.COMPLETED:
    print("Tool finished!")
    print(state.result)
```

### Central State Container

```python
from ui.state import StateContainer

# Create main state container
container = StateContainer()

# Menu operations
container.menu.push("settings")
container.menu.set_selection(0)

# Register tool states
scanner = MyToolState()
container.register_tool_state("my_tool", scanner)

# Access tool state
state = container.get_tool_state("my_tool")
state.mark_running()

# Global settings
container.set_setting("auto_scan", True)
container.set_setting("timeout", 30)

# Get settings
auto_scan = container.get_setting("auto_scan")
timeout = container.get_setting("timeout", 60)  # Default to 60 if not set

# Subscribe to changes
container.subscribe_changes(lambda: print("State changed!"))
```

### Preferences (Persistent Storage)

```python
from ui.state import PreferenceManager

# Initialize
prefs = PreferenceManager()

# Load from disk (~/.dedsec/prefs.json)
prefs.load()

# Get preferences with defaults
theme = prefs.get("theme", "neon_green")
brightness = prefs.get("brightness", 100)

# Set preferences
prefs.set("theme", "synthwave", auto_save=True)  # Auto-saves to disk
prefs.set("brightness", 75, auto_save=True)

# Manual save
prefs.save()

# Reset to defaults
prefs.reset_to_defaults()

# Export all
all_prefs = prefs.to_dict()
```

---

## THEME SYSTEM

### Import

```python
from ui.themes import ThemeManager, Theme, interpolate_color, hex_to_rgb, rgb_to_hex
```

### Basic Usage

```python
# Create manager with default theme
tm = ThemeManager(default_theme="neon_green")

# Get current theme
current = tm.current_theme  # Theme object
print(current.label)  # "Neon Green"

# Switch themes
tm.set_theme("synthwave")  # True if successful
tm.set_theme("invalid")    # False if not found

# Get colors
text_color = tm.get_color("text")
bg_color = tm.get_color("background")
button_bg = tm.get_color("button_bg")

# Get all colors
all_colors = tm.get_all_colors()
# Returns dict with 30+ color keys

# List available themes
themes = tm.get_available_themes()
# ['neon_green', 'synthwave', 'monochrome', 'acid_trip', 'stealth_mode']

# Get labels
labels = tm.get_theme_labels()
# {'neon_green': 'Neon Green', 'synthwave': 'Synthwave', ...}
```

### Available Themes

| Theme | Label | Use Case |
|-------|-------|----------|
| neon_green | Neon Green | Classic hacker, high contrast |
| synthwave | Synthwave | Modern cyberpunk, 80s aesthetic |
| monochrome | Monochrome | Accessibility, greyscale |
| acid_trip | Acid Trip | Special effects, fun mode |
| stealth_mode | Stealth Mode | Low power, minimal |

### Custom Themes

```python
# Create custom theme
from ui.themes import Theme

custom = Theme(
    name="my_theme",
    label="My Custom Theme",
    background="#FFFFFF",
    text="#000000",
    text_secondary="#333333",
    header_bg="#EEEEEE",
    header_text="#000000",
    button_bg="#CCCCCC",
    button_text="#000000",
    button_hover="#999999",
    button_active="#000000",
    button_disabled="#999999",
    modal_bg="#EEEEEE",
    modal_text="#000000",
    modal_border="#000000",
    input_bg="#FFFFFF",
    input_text="#000000",
    input_border="#000000",
    error_bg="#FFEEEE",
    error_text="#FF0000",
    success_bg="#EEFFEE",
    success_text="#00FF00",
    warning_bg="#FFFFEE",
    warning_text="#FFFF00",
    border="#000000",
    highlight="#000000",
    accent="#000000",
    muted="#999999",
    progress_bg="#EEEEEE",
    progress_fill="#000000",
    panel_bg="#FFFFFF",
    panel_border="#000000",
)

# Register and use
tm.register_theme(custom)
tm.set_theme("my_theme")
```

### Subscribe to Theme Changes

```python
# Subscribe to changes
tm.subscribe(lambda theme: print(f"Theme changed to: {theme.label}"))

# Changing theme triggers callback
tm.set_theme("synthwave")  # Prints: "Theme changed to: Synthwave"

# Multiple subscribers
def on_theme_change(theme):
    print(f"Updating UI colors...")
    prefs.set("theme", theme.name, auto_save=True)

tm.subscribe(on_theme_change)
```

### Color Utilities

```python
from ui.themes import hex_to_rgb, rgb_to_hex, interpolate_color

# Convert hex to RGB
rgb = hex_to_rgb("#FF0000")  # (255, 0, 0)

# Convert RGB to hex
hex_color = rgb_to_hex(255, 0, 0)  # "#FF0000"

# Interpolate between colors (for animations)
# Fade from red to blue over 10 steps
for i in range(11):
    color = interpolate_color("#FF0000", "#0000FF", i / 10.0)
    print(f"Step {i}: {color}")
    # Step 0: #FF0000 (red)
    # Step 5: #7F007F (purple)
    # Step 10: #0000FF (blue)

# Use with ThemeManager for theme transitions
for i in range(11):
    color = tm.interpolate("text", i / 10.0)
    # Smoothly transitions text color to next theme
```

---

## INTEGRATION EXAMPLES

### Example 1: Startup Sequence

```python
from ui.state import StateContainer, PreferenceManager
from ui.themes import ThemeManager

# Initialize systems in order
prefs = PreferenceManager()
prefs.load()

state = StateContainer()
tm = ThemeManager()

# Restore user preferences
saved_theme = prefs.get("theme", "neon_green")
tm.set_theme(saved_theme)

last_menu = prefs.get("last_menu", "main")
state.menu.push(last_menu)

# Subscribe to auto-save theme changes
tm.subscribe(lambda t: prefs.set("theme", t.name, auto_save=True))

# Subscribe to save menu changes
state.menu.subscribe_menu_change(
    lambda m: prefs.set("last_menu", m.current_menu, auto_save=True)
)

print(f"Started with theme: {tm.current_theme.label}")
print(f"Menu: {state.menu.current_menu}")
```

### Example 2: Running a Tool

```python
from ui.state import ToolState, StateContainer

class NetworkScanState(ToolState):
    def __init__(self):
        super().__init__("network_scan")
        self.networks = []
        self.signal_strength = {}

# Register tool
container = StateContainer()
scan_state = NetworkScanState()
container.register_tool_state("network_scan", scan_state)

# Run tool with progress
scan_state.mark_running()
try:
    networks = scan_networks()  # Hypothetical
    
    for i, network in enumerate(networks):
        progress = (i + 1) / len(networks)
        scan_state.set_progress(progress)
        
        strength = get_signal(network)
        scan_state.networks.append(network)
        scan_state.signal_strength[network] = strength
    
    scan_state.mark_complete()
    scan_state.set_result({
        "count": len(networks),
        "networks": networks,
        "signals": scan_state.signal_strength,
    })

except Exception as e:
    scan_state.set_error(f"Scan failed: {e}")
```

### Example 3: Menu Navigation with Theme Changes

```python
state = StateContainer()
tm = ThemeManager()

# Navigate to settings
state.menu.push("main")
state.menu.push("settings")
state.menu.push("theme_selector")

# Get list of themes
themes = tm.get_available_themes()
state.menu.selection_index = 0

# User selects theme (simulated)
selected_theme = themes[2]  # "monochrome"
tm.set_theme(selected_theme)

# Go back
state.menu.back()  # Now at "settings"
state.menu.back()  # Now at "main"

# Preferences auto-saved when theme changed
```

---

## COMMON PATTERNS

### Pattern 1: Reactive UI Updates

```python
# Subscribe to state changes for automatic UI updates
container.menu.subscribe_menu_change(
    lambda menu_state: redraw_menu(menu_state)
)

container.menu.subscribe_selection_change(
    lambda index: highlight_selection(index)
)

# Any menu change automatically redraws
container.menu.push("new_menu")  # Calls redraw_menu()
container.menu.set_selection(3)  # Calls highlight_selection()
```

### Pattern 2: Error Handling

```python
# Automatic error status
tool_state = ToolState("tool")
try:
    result = risky_operation()
    tool_state.set_result(result)
    tool_state.mark_complete()
except Exception as e:
    tool_state.set_error(str(e))  # Auto-sets status to ERROR

# Check for errors
if tool_state.status == ToolStatus.ERROR:
    show_error_dialog(tool_state.error)
```

### Pattern 3: Persisting Tool State

```python
# Save tool results
tool_state.mark_complete()
tool_state.set_result({"data": [1, 2, 3]})

# Serialize to dict
state_dict = tool_state.to_dict()

# Save to JSON (example)
import json
with open("tool_state.json", "w") as f:
    json.dump(state_dict, f)

# Restore later
with open("tool_state.json", "r") as f:
    restored_dict = json.load(f)
```

### Pattern 4: Multi-Step Wizards

```python
# Navigate through multi-step process
steps = ["step_1", "step_2", "step_3", "complete"]

for step in steps:
    state.menu.push(step)
    # Get user input
    if user_cancelled():
        state.menu.back()
        break
    # Process step
    process_step(step)

# Breadcrumb shows progress
print(state.menu.get_breadcrumb())
# ["main", "wizard", "step_1", "step_2"]
```

---

## API REFERENCE

### MenuState

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| push | `push(menu: str)` | None | Navigate to menu |
| back | `back()` | bool | Go back, False if at root |
| pop | `pop()` | str \| None | Remove from stack |
| clear | `clear()` | None | Reset to root |
| get_breadcrumb | `get_breadcrumb()` | List[str] | Get navigation path |
| set_selection | `set_selection(index: int)` | None | Set selected item |
| add_selection | `add_selection(item: str)` | None | Add to multi-select |
| remove_selection | `remove_selection(item: str)` | None | Remove from multi-select |
| toggle_selection | `toggle_selection(item: str)` | bool | Toggle in multi-select |
| subscribe_menu_change | `subscribe_menu_change(callback)` | None | Subscribe to menu changes |
| subscribe_selection_change | `subscribe_selection_change(callback)` | None | Subscribe to selection changes |

### ToolState

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| reset | `reset()` | None | Clear all state |
| set_result | `set_result(result: Dict)` | None | Set result |
| set_error | `set_error(error: str)` | None | Set error |
| mark_complete | `mark_complete()` | None | Mark done |
| mark_running | `mark_running()` | None | Mark running |
| set_progress | `set_progress(p: float)` | None | Set 0.0-1.0 progress |
| to_dict | `to_dict()` | Dict | Serialize |
| from_dict | `from_dict(data: Dict)` | ToolState | Deserialize |

### ThemeManager

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| set_theme | `set_theme(name: str)` | bool | Switch theme |
| get_theme | `get_theme(name: str)` | Theme \| None | Get theme |
| get_color | `get_color(key: str)` | str | Get color hex |
| get_all_colors | `get_all_colors()` | Dict[str, str] | Get all colors |
| get_available_themes | `get_available_themes()` | List[str] | List themes |
| get_theme_labels | `get_theme_labels()` | Dict[str, str] | Get labels |
| register_theme | `register_theme(theme: Theme)` | None | Add custom theme |
| interpolate | `interpolate(key: str, factor: float)` | str | Interpolate color |
| subscribe | `subscribe(callback)` | None | Subscribe to changes |

### PreferenceManager

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| load | `load()` | bool | Load from disk |
| save | `save()` | bool | Save to disk |
| get | `get(key: str, default)` | Any | Get preference |
| set | `set(key: str, value, auto_save)` | None | Set preference |
| reset_to_defaults | `reset_to_defaults()` | None | Reset to factory |
| to_dict | `to_dict()` | Dict | Export all |

---

## TROUBLESHOOTING

### Q: State changes aren't triggering subscribers?
**A:** Ensure you're actually changing the state:
```python
menu.push("new_menu")  # Triggers if different from current
menu.push("new_menu")  # Does NOT trigger (same as current)
```

### Q: Theme colors look wrong?
**A:** Check that you're getting colors from the ThemeManager, not hardcoded:
```python
# ✅ Correct
color = tm.get_color("text")

# ❌ Wrong
color = "#00FF00"  # Hardcoded
```

### Q: Preferences not saving?
**A:** Set auto_save=True or call save() explicitly:
```python
# ✅ Correct - auto-saves
prefs.set("theme", "synthwave", auto_save=True)

# ✅ Also correct - manual save
prefs.set("theme", "synthwave", auto_save=False)
prefs.save()

# ❌ Wrong - doesn't save
prefs.set("theme", "synthwave")  # auto_save defaults to True, so this is OK
```

### Q: Custom theme not being used?
**A:** Register before switching:
```python
tm.register_theme(my_theme)  # Must do this first
tm.set_theme("my_theme")     # Now it works
```

---

## NEXT STEPS

1. **Task #9:** Refactor Canvas Rendering - Use states & themes in dedsec_ui.py
2. **Task #12:** Extract Config - Move hardcoded values to config.py
3. **Task #10:** Tool Manager - Dynamic tool loading using ToolState
4. **Task #13:** Logging - Add structured logging throughout

---

*Version: 3.2.1*  
*Last Updated: November 22, 2025*
