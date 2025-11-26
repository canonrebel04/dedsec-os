## UI/UX Redesign Plan v1.1.2.5

### Target Hardware
- **Screen**: 2.8" TFT 320x240 touchscreen
- **Device**: Raspberry Pi 2 cyberdeck
- **Resolution**: 320 × 240 pixels (extreme constraints)

### Design Philosophy
Professional UI/UX best practices applied to a small touchscreen hacking tool:
- **Modularity**: Tool system easy to extend
- **Touch-friendly**: 44px+ minimum touch targets
- **Space-efficient**: Every pixel optimized
- **Professional**: Functional first, aesthetic second
- **Consistent**: Design tokens and reusable components

---

## Screen Layout (320×240)

```
┌──────────────────────────────────────────────────────────────┐
│ [time]  [signal] [batt] [cpu%]                      STATUS (16px)
├──────────────────────────────────────────────────────────────┤
│                                                               │
│                   PRIMARY CONTENT AREA                        │
│                      (188px height)                           │
│                   Tool-specific layouts                       │
│                      Scrollable                               │
│                   Consistent padding: 8px                     │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│ [SCAN|WIFI|BT|TOOLS|MENU]                         NAVIGATION (20px)
├──────────────────────────────────────────────────────────────┤
│ CPU:▆ RAM:▇ TEMP:42° UP:12K DN:45K                    INFO (16px)
└──────────────────────────────────────────────────────────────┘
```

---

## Tab Layouts

### SCAN Tab
```
[Nmap Results]
╔════════════════════════════════╗
║ 192.168.1.1 - Router (open)    ║
║ 192.168.1.5 - MyPC (ssh open)  ║
║ 192.168.1.10 - NAS (multi)  ▶  ║
║ ... (scroll)                   ║
╚════════════════════════════════╝

[SCAN] [PORT] [STOP] [EXPORT]
```

### WIFI Tab  
```
[Networks]
╔════════════════════════════════╗
║ ► MyNetwork ▇▇▇ WPA2 ▶        ║
║ ► OpenWiFi ▇▇░░ OPEN ▶        ║
║ ► Guest ▇░░░ WPA ▶            ║
╚════════════════════════════════╝

[SCAN] [FILTER] [INFO] [CONNECT]
```

### Detail Modal
```
┌────────────────────────────────┐
│ MyNetwork - DETAILS            │
├────────────────────────────────┤
│ SSID: MyNetwork                │
│ BSSID: AA:BB:CC:DD:EE:FF       │
│ Security: WPA2                 │
│ Channel: 6                     │
│ Signal: -65dBm (▇▇▇)           │
│ WPS: Enabled ⚠                 │
├────────────────────────────────┤
│ [DEAUTH] [WPS] [CRACK] [BACK]  │
└────────────────────────────────┘
```

### BT Tab
```
[Devices]
╔════════════════════════════════╗
║ ◐ iPhone12 (Apple) ▇▇▇ ▶     ║
║ ◐ Beats Studio ▇▇░░ ▶         ║
║ ◐ Unknown ⚠ ▶                 ║
║ ◐ Smart Watch ✓               ║
╚════════════════════════════════╝

[SCAN] [ENUM] [VULN] [SNIFF]
```

### TOOLS Tab
```
[Available Tools]
╔════════════════════════════════╗
║ Payload Generator              ║
║ MITM Attack                    ║
║ ARP Spoof                      ║
║ DNS Spoof                      ║
║ Evil Twin AP                   ║
║ MAC Randomizer                 ║
║ ... (scroll)                   ║
╚════════════════════════════════╝

[SELECT] [INFO] [CONFIG] [EXECUTE]
```

### MENU Tab
```
[Settings & System]
╔════════════════════════════════╗
║ Settings                       ║
║ Help & Shortcuts               ║
║ System Info                    ║
║ Logs                           ║
║ About DedSec                   ║
║ Shutdown / Reboot              ║
╚════════════════════════════════╝

[EDIT] [VIEW] [EXECUTE] [BACK]
```

---

## Design System

### Colors
```
PRIMARY:        #00ff00 (Neon Green)
SECONDARY:      #ffff00 (Yellow)
ACCENT:         #00ffff (Cyan)
BACKGROUND:     #000000 (Black)
BG_ALT:         #111111 (Slightly lighter)
BORDER:         #00ff00
TEXT_PRIMARY:   #00ff00
TEXT_SECONDARY: #888888
ERROR:          #ff0000
SUCCESS:        #00ff00
```

### Typography
```
TITLE:   Courier 10pt  (#00ff00)
BODY:    Courier 8pt   (#00ff00)
LABEL:   Courier 7pt   (#888888)
ICON:    Courier 16pt
```

### Spacing
```
GRID_UNIT = 4px (base)
PADDING_SMALL = 8px (2 units)
PADDING_MED = 12px (3 units)
PADDING_LARGE = 16px (4 units)

Consistent 8px padding inside containers
4px spacing between buttons
```

### Touch Targets
```
Minimum: 44×32px (Material Design standard)
Button width: ~38px (8 buttons per row with 4px spacing)
List item height: 20px
Modal width: 260px (centered)
```

---

## Icons (ASCII-based, 16×16px)

```
Tools:
  SCAN:   ⊓  (network)
  WIFI:   ▤  (signal)
  BT:     ◐  (bluetooth)
  TOOLS:  ⚙  (gear)
  MENU:   ☰  (hamburger)

Status:
  IDLE:      ○  (circle)
  RUNNING:   ◐  (half circle, rotating)
  ERROR:     ✗  (red X)
  SUCCESS:   ✓  (green check)

Connectivity:
  Signal:    ▇ ▇ ▆ ░  (4 levels)
  Battery:   ▓ ▒ ░  (3 levels)
  Online:    ✓
  Offline:   ✗
```

---

## Modular Tool Architecture

```
tools/
├── base_tool.py        # Abstract interface
├── scan/               # SCAN tab
│   ├── nmap_scanner.py
│   ├── port_scanner.py
│   └── ui.py
├── wifi/               # WIFI tab
│   ├── scanner.py
│   ├── attacks.py
│   └── ui.py
├── bluetooth/          # BT tab
│   ├── scanner.py
│   ├── enumeration.py
│   └── ui.py
├── misc/               # TOOLS tab
│   ├── payload_gen.py
│   ├── mitm.py
│   └── ui.py
└── system/             # MENU tab
    ├── settings.py
    ├── help.py
    └── ui.py

ui/
├── components/
│   ├── button.py
│   ├── list.py
│   ├── modal.py
│   ├── gauge.py
│   └── ...
├── design_system.py    # All colors/fonts/spacing
├── layout_manager.py   # Screen positioning
└── app.py              # Main app + tab management
```

### Tool Interface
```python
class BaseTool:
    name = "Tool Name"
    icon = "⚙"
    
    def on_enter(self): pass      # Tab selected
    def on_exit(self): pass       # Tab deselected
    def on_touch(x, y): pass      # Tap detected
    def render(canvas, rect): pass # Draw UI
    def get_status(): pass        # Status string
```

---

## Implementation Phases

### Phase 1: Framework (2-3 hours)
- [ ] Design system constants
- [ ] Base components (Button, List, Modal, Gauge)
- [ ] Layout manager
- [ ] Tab navigation system

### Phase 2: Screen Redesign (3-4 hours)
- [ ] SCAN tab
- [ ] WIFI tab
- [ ] BT tab
- [ ] TOOLS tab
- [ ] MENU tab

### Phase 3: Tool Refactoring (3-4 hours)
- [ ] ScanTool class
- [ ] WiFiTool class
- [ ] BluetoothTool class
- [ ] ToolsTool class
- [ ] MenuTool class

### Phase 4: Polish & Testing (2-3 hours)
- [ ] Touch responsiveness
- [ ] Performance profiling
- [ ] Visual polish
- [ ] Documentation

**Total: ~10-14 hours**

---

## Performance Targets

- **Touch response**: <100ms (tap to visual feedback)
- **Tab switching**: <300ms (render next tab)
- **List scroll**: Smooth 30fps minimum
- **Memory**: <200MB total
- **Draw calls**: <50 per frame

---

## Success Criteria

✅ All 5 tabs fully functional  
✅ Touch targets ≥44px  
✅ Visual hierarchy clear  
✅ No excessive modals  
✅ New tools addable in <1 hour  
✅ Watch Dogs 2 aesthetic maintained  
✅ Performance targets met  
✅ +50% code maintainability  

---

## Design Best Practices Applied

1. **Consistency**: Same component style everywhere
2. **Hierarchy**: Clear visual order, important content prominent
3. **Feedback**: Immediate response to user actions
4. **Constraints**: Designed for the medium (small screen)
5. **Accessibility**: High contrast, clear labels, large targets
6. **Efficiency**: Minimal clicks to features
7. **Clarity**: Unambiguous meanings
8. **Modularity**: Tools are plugins
9. **Performance**: Every pixel optimized
10. **Aesthetics**: Professional cyberpunk theme
