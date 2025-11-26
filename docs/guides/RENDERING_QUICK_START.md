# 🎨 RENDERING SYSTEM QUICK START

**Module:** `ui/rendering.py`  
**Added:** Phase 3.2, Task #9  
**Lines:** 650+  

---

## 🚀 QUICK START

### 1. Basic Setup

```python
import tkinter as tk
from ui.rendering import create_default_renderer
from ui.themes import ThemeManager
from config import LAYOUT

# Create window and canvas
root = tk.Tk()
canvas = tk.Canvas(root, bg="#000000", width=320, height=240)
canvas.pack(fill="both", expand=True)

# Create theme manager
theme_manager = ThemeManager()
theme_manager.set_theme('neon_green')

# Create renderer
renderer = create_default_renderer(canvas, theme_manager=theme_manager)
```

### 2. Render Full Screen

```python
# Background
renderer.draw_background(image_path="/path/to/bg.png")

# Header
renderer.draw_header(
    clock_text="12:34:56",
    network_icon="●",
    title_text="DEDSEC"
)

# Sidebar
renderer.draw_sidebar([
    {"label": "NMAP", "color": "#00ff00"},
    {"label": "WIFI", "color": "#ffff00"},
    {"label": "BLUETOOTH", "color": "#00ffff"},
    {"label": "PAYLOAD", "color": "#ff0000"}
])

# Terminal
renderer.draw_terminal(
    log_lines=[
        "# SYSTEM ONLINE",
        "# Initializing tools...",
        "NMAP: Ready"
    ],
    scroll_offset=0
)

# Status bar
renderer.draw_status_bar(
    cpu_pct=45.2,
    ram_gb=0.7,
    temp_c=62.5,
    battery_pct=87
)
```

### 3. Theme Switching

```python
# Change theme at runtime
theme_manager.set_theme('synthwave')

# Renderer automatically uses new colors
renderer.draw_header()  # Now uses Synthwave colors
```

### 4. Show Modal

```python
renderer.draw_modal(
    title="NETWORK DETAILS",
    content_text="SSID: MyNetwork\nSignal: 75%\nSecurity: WPA2",
    modal_type="info",
    buttons=[
        ("CONNECT", on_connect),
        ("CANCEL", on_cancel)
    ]
)
```

---

## 📖 FULL API REFERENCE

### ScreenRenderer Class

#### `__init__(canvas: tk.Canvas, context: RenderContext)`

Initialize renderer with canvas and context.

```python
from ui.rendering import ScreenRenderer, RenderContext

context = RenderContext(
    canvas=canvas,
    theme_manager=theme_manager,
    debug_mode=True
)
renderer = ScreenRenderer(canvas, context)
```

---

### Drawing Methods

#### `draw_background(image_path: Optional[str] = None, glass_alpha: int = 180)`

Render background layer.

**Args:**
- `image_path`: Path to background image (optional)
- `glass_alpha`: Alpha value for glass overlay (0-255)

**Example:**
```python
renderer.draw_background(
    image_path="/home/cachy/dedsec/bg.png",
    glass_alpha=180
)
```

---

#### `draw_header(clock_text: str = "00:00:00", network_icon: str = "●", title_text: str = "DEDSEC")`

Render header bar with clock, network status, title.

**Layout:**
```
| DEDSEC    ●    12:34:56 |
```

**Args:**
- `clock_text`: Time text (e.g., "12:34:56")
- `network_icon`: Network status indicator (●, ○, ✗)
- `title_text`: Title text (e.g., "DEDSEC", "SCANNING")

**Example:**
```python
renderer.draw_header(
    clock_text="14:23:45",
    network_icon="●",  # Connected
    title_text="NMAP_SCAN"
)
```

**Network Icons:**
- `●` = Connected
- `○` = Disconnected
- `✗` = Error/No Signal
- `◐` = Scanning

---

#### `draw_sidebar(buttons: List[Dict[str, Any]])`

Render left sidebar with vertical button menu.

**Layout:**
```
| NMAP  |
| WIFI  |
| BLUE  |
| PLOAD |
```

**Args:**
- `buttons`: List of button dictionaries with keys:
  - `label` (str): Button label
  - `color` (str): Border color
  - `label_color` (str): Text color (optional)
  - `callback` (callable): Click handler (optional)

**Example:**
```python
renderer.draw_sidebar([
    {"label": "NMAP", "color": "#00ff00", "label_color": "#00ff00"},
    {"label": "WIFI", "color": "#ffff00", "label_color": "#ffff00"},
    {"label": "BLUETOOTH", "color": "#00ffff", "label_color": "#00ffff"},
    {"label": "PAYLOAD", "color": "#ff0000", "label_color": "#ff0000"}
])
```

---

#### `draw_terminal(log_lines: List[str], scroll_offset: int = 0, line_height: int = 12, pool: Optional[Any] = None)`

Render scrollable terminal with log lines.

**Layout:**
```
HEADER (30px)
+----+------------------+
|    | LOG OUTPUT       | <- Terminal area
|    | More log here    |
|    | And more...      |
+----+------------------+
STATUS BAR (24px)
```

**Args:**
- `log_lines`: List of log line strings
- `scroll_offset`: Y-offset for scrolling (negative = scroll up)
- `line_height`: Height of each line in pixels (default: 12)
- `pool`: Optional CanvasObjectPool for object reuse

**Example:**
```python
renderer.draw_terminal(
    log_lines=[
        "# SYSTEM ONLINE",
        "NMAP: Scanning 192.168.1.0/24",
        "Found 12 hosts"
    ],
    scroll_offset=-120  # Scroll up by 120 pixels
)
```

---

#### `draw_status_bar(cpu_pct: float = 0.0, ram_gb: float = 0.0, temp_c: float = 0.0, battery_pct: float = 0.0)`

Render bottom status bar with system metrics.

**Layout:**
```
CPU: [====----] 45% | RAM: 0.7GB | TEMP: 62°C | BAT: 87%
```

**Args:**
- `cpu_pct`: CPU usage percentage (0-100)
  - Color: Green (0%) → Yellow (50%) → Red (100%)
- `ram_gb`: RAM usage in GB
- `temp_c`: CPU temperature in Celsius
  - Color: Green if < 70°C, Red if >= 70°C
- `battery_pct`: Battery level percentage (0-100)
  - Color: Green if > 20%, Yellow 10-20%, Red < 10%

**Example:**
```python
renderer.draw_status_bar(
    cpu_pct=45.2,
    ram_gb=0.7,
    temp_c=62.5,
    battery_pct=87
)
```

---

#### `draw_modal(title: str, content_text: str, modal_type: str = "info", buttons: List[Tuple[str, callable]] = None)`

Render centered modal dialog.

**Layout:**
```
    ╔═══════════════════════╗
    ║ TITLE          [×]    ║
    ╟───────────────────────╢
    ║ Content text here     ║
    ║ Multiple lines        ║
    ║ supported             ║
    ╟───────────────────────╢
    ║ [BUTTON1] [BUTTON2]   ║
    ╚═══════════════════════╝
```

**Args:**
- `title`: Modal title (e.g., "WARNING", "SCAN RESULTS")
- `content_text`: Modal content
- `modal_type`: "info", "warning", "error", or "success"
  - info: Cyan border
  - warning: Yellow border
  - error: Red border
  - success: Green border
- `buttons`: List of (label, callback) tuples

**Example:**
```python
renderer.draw_modal(
    title="WARNING",
    content_text="Execute payload on 192.168.1.100?",
    modal_type="warning",
    buttons=[
        ("EXECUTE", lambda: execute_payload()),
        ("CANCEL", lambda: hide_modal())
    ]
)
```

---

### Helper Methods

#### `_get_color(color_key: str, fallback: str = "#00ff00") -> str`

Get current color from ThemeManager or config.

**Args:**
- `color_key`: Color name (e.g., 'background', 'text_primary')
- `fallback`: Fallback color if key not found

**Returns:**
- Hex color string (e.g., '#00ff00')

**Priority:**
1. ThemeManager.get_color(key)
2. COLORS.get(key)
3. Fallback parameter

**Example:**
```python
bg_color = renderer._get_color('background')  # "#000000"
text_color = renderer._get_color('text_primary')  # "#00ff00"
```

---

#### `_get_heat_color(percent: float) -> str`

Get CPU heat color gradient.

**Colors:**
- 0%: `#ccff00` (green)
- 50%: `#ffff00` (yellow)
- 100%: `#ff0000` (red)

**Example:**
```python
color = renderer._get_heat_color(45)  # Interpolated green-yellow
```

---

#### `update_layer_z_order()`

Update z-order of all elements for proper layering.

**Z-Order (bottom to top):**
1. Background
2. Glass panel
3. Terminal text
4. UI elements
5. Modal background
6. Modal content
7. Overlay

**Example:**
```python
# Call after adding/removing elements
renderer.update_layer_z_order()
```

---

## 🎨 COLOR SYSTEM

### Available Color Keys

```python
# Layout colors
'background'           # "#000000"
'text_primary'         # "#00ff00"
'text_secondary'       # "#00cc00"
'border'               # "#00ff00"

# Header
'header_bg'            # "#001a00"
'header_text'          # "#00ff00"

# Sidebar
'sidebar_bg'           # "#000000"
'button_bg'            # "#003300"

# Modals
'modal_bg'             # "#001a00"
'modal_info'           # "#00ffff"
'modal_warning'        # "#ffff00"
'modal_error'          # "#ff0000"
'modal_success'        # "#00ff00"

# Status indicators
'error'                # "#ff0000"
'warning'              # "#ffff00"
'success'              # "#00ff00"
'network_active'       # "#00ff00"
```

---

## 🎯 THEME SWITCHING

### Available Themes

```python
# Switch theme
theme_manager.set_theme('neon_green')     # Classic
theme_manager.set_theme('synthwave')      # 80s
theme_manager.set_theme('monochrome')     # B&W
theme_manager.set_theme('acid_trip')      # Rainbow
theme_manager.set_theme('stealth_mode')   # Power-saving
```

**Renderer automatically updates colors:**

```python
# Before
renderer.draw_header()  # Uses Neon Green colors

# Change theme
theme_manager.set_theme('synthwave')

# After
renderer.draw_header()  # Now uses Synthwave colors
```

---

## 📊 CONFIGURATION

### Layout Constants

```python
from config import LAYOUT

LAYOUT.CANVAS_WIDTH         # 320
LAYOUT.CANVAS_HEIGHT        # 240
LAYOUT.HEADER_HEIGHT        # 30
LAYOUT.SIDEBAR_WIDTH        # 80
LAYOUT.STATUS_BAR_HEIGHT    # 30
LAYOUT.MODAL_WIDTH          # 280
LAYOUT.MODAL_HEIGHT         # 160
```

### Color Defaults

```python
from config import COLORS

COLORS.get('background')    # "#000000"
COLORS.get('text_primary')  # "#00ff00"
COLORS.get('border')        # "#00ff00"
```

### Animation Timings

```python
from config import TIMINGS

TIMINGS.BUTTON_PRESS_DURATION       # 100ms
TIMINGS.CLOCK_UPDATE_INTERVAL       # 1000ms
TIMINGS.ANIMATION_DURATION          # 500ms
```

---

## 🔧 ADVANCED USAGE

### Custom Colors

```python
# Override default colors
custom_colors = {
    'background': '#001100',
    'text_primary': '#00ff00',
    'border': '#00ff00'
}

# Pass to ThemeManager
theme_manager.set_custom_colors(custom_colors)
renderer.draw_header()  # Uses custom colors
```

### Object Pooling

```python
from ui.rendering import ScreenRenderer
from dedsec_ui import CanvasObjectPool

# Create pool
pool = CanvasObjectPool(canvas, pool_size=50)

# Use with rendering (reduces GC pressure)
renderer.draw_terminal(log_lines, pool=pool)
```

### Debug Mode

```python
# Enable debug logging
context = RenderContext(
    canvas=canvas,
    theme_manager=theme_manager,
    debug_mode=True
)
renderer = ScreenRenderer(canvas, context)

# Logs render operations to console
```

---

## 📈 PERFORMANCE TIPS

### Pi 2 Optimization

1. **Use object pooling for terminal:**
   ```python
   renderer.draw_terminal(log_lines, pool=pool)
   ```

2. **Reduce animation intervals:**
   ```python
   # In config.py
   TIMINGS.CLOCK_UPDATE_INTERVAL = 5000  # Update every 5s instead of 1s
   ```

3. **Disable expensive effects:**
   ```python
   # In config.py
   DEBUG.SHOW_ANIMATIONS = False
   DEBUG.SHOW_GLASS_EFFECT = False
   ```

4. **Batch screen updates:**
   ```python
   # Update multiple regions at once
   renderer.draw_header()
   renderer.draw_sidebar(buttons)
   renderer.draw_terminal(log_lines)
   canvas.update_idletasks()  # Single update
   ```

---

## 🐛 TROUBLESHOOTING

### Modal not appearing?

```python
# Ensure modal is raised to front
renderer.update_layer_z_order()
canvas.tag_raise("modal")
```

### Colors not changing after theme switch?

```python
# Renderer caches theme manager reference
# If theme manager changes, create new renderer
renderer = create_default_renderer(canvas, theme_manager=new_tm)
```

### Terminal text invisible?

```python
# Ensure terminal text is above backgrounds
renderer.canvas.tag_raise("terminal_text")
```

### Poor performance?

```python
# Check debug output
context.debug_mode = True

# Use object pooling
pool = CanvasObjectPool(canvas)
renderer.draw_terminal(log_lines, pool=pool)
```

---

## 📚 RELATED DOCUMENTATION

- `COMPLETION_TASK_9.md` - Full technical details
- `ui/themes.py` - Theme system API
- `config.py` - Configuration constants
- `ui/components.py` - Component library

---

*Module: `ui/rendering.py` | Task: #9 | Status: ✅ Complete*
