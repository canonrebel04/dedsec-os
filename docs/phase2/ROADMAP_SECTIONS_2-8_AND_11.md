# DedSec OS Implementation Roadmap
## Sections 2.1.2 → 8 & UI Redesign v1.1.2.5

**Date**: November 22, 2025  
**Status**: Planning & Sequencing  
**Target**: Complete feature implementation across all sections

---

## Executive Summary

The PLAN.md outlines 8+ major sections with 50+ subsections representing a comprehensive cyberdeck platform. This roadmap provides:

1. **Detailed breakdown** of each section with implementation scope
2. **Dependency mapping** to identify critical path
3. **Effort estimation** in hours for planning
4. **Priority matrix** for phased delivery
5. **Testing strategy** for validation

---

## Section Breakdown with Effort Estimates

### **SECTION 2: SECURITY ENHANCEMENTS** (10-12 hours)

#### 2.1 Input Validation & Sanitization (6-7 hours)
- **2.1.1 BSSID/MAC Validation** ✅ COMPLETE (2.1.1)
  - Effort: 1-1.5 hours
  - Status: Deployed to device
  - Dependencies: None

- **2.1.2 SSID Sanitization** (1-1.5 hours)
  - Already partially implemented in 2.1.1
  - Quick enhancement: Improve escaping logic
  - Integration: _scan_wifi_task(), _update_wifi_ui()
  - New functions needed: Enhanced sanitize_ssid()

- **2.1.3 Path Traversal Prevention** (1.5-2 hours)
  - Create SAFE_PATHS whitelist
  - Implement get_safe_path() function
  - Replace all file operations (log_error(), config reads)
  - Validation: Ensure path doesn't escape /home/berry/dedsec/

#### 2.2 Privilege Separation & Sandboxing (2-2.5 hours)
- **2.2.1 Sudo Token Caching** (1-1.5 hours)
  - Add password prompt dialog on app startup
  - Store in memory-only variable
  - Auto-clear after 15 minutes
  - Configuration: REQUIRE_SUDO_PASSWORD setting

- **2.2.2 Drop Root Privileges** (0.5-1 hour)
  - Check `os.getuid() == 0`
  - Drop to user 1000 (berry) after init
  - Error handling for permission denied scenarios

#### 2.3 Secure Subprocess Execution (2-2.5 hours)
- **2.3.1 Command Whitelisting** (1-1.5 hours)
  - Create ALLOWED_COMMANDS dictionary
  - Implement execute_safe_command() wrapper
  - Replace all subprocess calls

- **2.3.2 Timeout & Resource Limits** (1-1.5 hours)
  - Already partially implemented (ProcessManager)
  - Enhance with consistent timeouts
  - Memory limit enforcement

#### 2.4 Logging & Audit Trail (1.5-2 hours)
- **2.4.1 Structured Logging System** (1 hour)
  - Import logging module
  - Configure RotatingFileHandler
  - Replace log_error() calls with appropriate levels

- **2.4.2 Security Event Auditing** (0.5-1 hour)
  - Create separate audit.log
  - Implement audit_log() function
  - Log security-relevant events (wifi, deauth, sudo)

---

### **SECTION 3: HACKER TOOL INTEGRATIONS** (20-25 hours)

#### 3.1 Network Reconnaissance Tools (6-8 hours)
- **3.1.1 Port Scanner** (2-2.5 hours)
  - UI: Modal with target/port-range inputs
  - Backend: nmap wrapper with service detection
  - Results display: Format PORT | STATE | SERVICE | VERSION
  - Caching: Store last 5 scans

- **3.1.2 ARP Spoofing / MITM** (2-2.5 hours)
  - 3-step wizard: Target → Gateway → Confirm
  - arpspoof backend (dsniff dependency)
  - Visual indicator: Red "MITM ACTIVE" banner
  - Auto-stop after 5 minutes

- **3.1.3 DNS Enumeration** (1-1.5 hours)
  - dnsrecon integration
  - Parse A/AAAA/MX/TXT records
  - Export to logs/dns_enum_TIMESTAMP.txt

#### 3.2 WiFi Exploitation Tools (7-9 hours)
- **3.2.1 WPS Pin Attack** (2-2.5 hours)
  - Detect WPS in scan results
  - Reaver integration
  - Stream output to terminal
  - Stop button, time estimate

- **3.2.2 Handshake Capture & Crack** (2.5-3 hours)
  - Two-stage: Capture + Crack
  - airodump-ng + aireplay-ng
  - aircrack-ng with wordlist
  - UI flow: Progressive disclosure

- **3.2.3 Evil Twin AP** (2-2.5 hours)
  - hostapd + dnsmasq configuration
  - Captive portal templates (5 variants)
  - Credential logging to phish_creds.log
  - Auto-stop after 30 minutes

#### 3.3 Bluetooth Exploitation (2-2.5 hours)
- **3.3.1 Service Enumeration** (1 hour)
  - sdptool integration
  - Parse service classes
  - Identify exploitable services (OPP, HFP)

- **3.3.2 BlueBorne/BlueJacking** (1-1.5 hours)
  - bluescan integration
  - Vulnerability checks (CVE-2017-0781, etc.)
  - Color-coded results

#### 3.4 Payload Generation & Delivery (2-3 hours)
- **3.4.1 Metasploit Integration** (1-1.5 hours)
  - msfvenom wrapper
  - Payload types: Reverse shell, APK, EXE, Python
  - LHOST/LPORT configuration

- **3.4.2 SET Integration** (1-1.5 hours)
  - Launch SET in tmux session
  - Full-screen overlay
  - Pre-configured attacks

#### 3.5 Post-Exploitation & Persistence (2-2.5 hours)
- **3.5.1 Reverse Shell Manager** (1-1.5 hours)
  - Socket-based shell sessions
  - Terminal emulator with history
  - File upload/download buttons

- **3.5.2 Keylogger Deployment** (1 hour)
  - Python keylogger template
  - Deploy via shell session
  - Log reception + display

---

### **SECTION 4: USABILITY ENHANCEMENTS** (10-12 hours)

#### 4.1 Configuration System (2-2.5 hours)
- **4.1.1 Settings Menu** (1-1.5 hours)
  - Tabbed modal: General, Network, Performance, Security, Advanced
  - JSON config persistence
  - Validation logic

- **4.1.2 Profile System** (1 hour)
  - Predefined profiles: Stealth, Balanced, Performance
  - JSON profile files
  - Instant apply (no restart)

#### 4.2 Terminal Improvements (2-2.5 hours)
- **4.2.1 Command History & Autocomplete** (1-1.5 hours)
  - Input field at terminal bottom (toggle)
  - History persistence to disk
  - Tab-based autocomplete

- **4.2.2 Search & Filter** (0.5-0.75 hours)
  - 🔍 modal with regex support
  - Highlight matches in yellow
  - Previous/Next navigation

- **4.2.3 Export Logs** (0.5-0.75 hours)
  - txt, JSON, HTML formats
  - Timestamped filenames
  - Auto-destination /home/berry/dedsec/exports/

#### 4.3 Visual Feedback Enhancements (2-2.5 hours)
- **4.3.1 Progress Indicators** (1 hour)
  - Progress bar for scans
  - Spinner animation
  - Color pulsing on active button

- **4.3.2 Toast Notifications** (0.75-1 hour)
  - Bottom-right overlay
  - 4 types: Success, Warning, Error, Info
  - Queue system (max 3 visible)

- **4.3.3 Live Network Map** (0.75-1 hour)
  - Force-directed graph layout
  - Interactive nodes (click for details)
  - Pan/zoom controls

#### 4.4 Keyboard Shortcuts (1-1.5 hours)
- **4.4.1 Quick Access Hotkeys** (1-1.5 hours)
  - 12 hotkeys (Ctrl+S/W/B/P/T/L/F/E/Q, Esc, F1, F5, F11)
  - Bind in __init__ with lambda handlers
  - Document in help modal

---

### **SECTION 5: MAINTAINABILITY & CODE QUALITY** (8-10 hours)

#### 5.1 Code Organization (4-5 hours)
- **5.1.1 Module Separation** (2-2.5 hours)
  - Split app_v1_1_2_5.py into modules/
  - Create: network_tools, attack_tools, system_monitor, terminal, config, utils
  - Implement mixin-based inheritance

- **5.1.2 Configuration Constants** (1-1.5 hours)
  - Create constants.py with 40+ constants
  - Import centrally
  - Benefits: Single source of truth

- **5.1.3 Error Handling Framework** (1-1.5 hours)
  - Custom exception classes
  - safe_execute() wrapper
  - Replace bare try/except blocks

#### 5.2 Testing Infrastructure (2-2.5 hours)
- **5.2.1 Unit Tests** (1-1.5 hours)
  - tests/ directory with 5+ test files
  - ~20 test cases covering validation, UI, network
  - Target: 70% code coverage

- **5.2.2 Integration Tests** (1-1.5 hours)
  - Mock subprocess calls
  - Simulate button clicks
  - End-to-end workflow tests

#### 5.3 Documentation (2-2.5 hours)
- **5.3.1 Inline Documentation** (1-1.5 hours)
  - Docstrings for all functions
  - Inline comments for complex logic
  - Example usage in docstrings

- **5.3.2 User Manual** (1-1.5 hours)
  - README.md with 8 sections
  - In-app help modal with search

---

### **SECTION 6: ADVANCED FEATURES** (12-15 hours)

#### 6.1 Remote Access & Control (3-4 hours)
- **6.1.1 Web Interface** (1-1.5 hours)
  - Flask server on port 8080
  - JSON API endpoints (/api/wifi, /api/bluetooth, etc.)
  - JWT authentication, HTTPS with self-signed cert

- **6.1.2 SSH Tunnel Auto-Setup** (1-1.5 hours)
  - autossh reverse tunnel to VPS
  - Configuration in settings
  - Status indicator in UI

#### 6.2 Data Exfiltration & Storage (2-2.5 hours)
- **6.2.1 Cloud Sync** (1-1.5 hours)
  - Dropbox/Google Drive/Self-hosted support
  - Sync frequency configuration
  - AES-256 encryption before upload

- **6.2.2 USB Auto-Export** (1-1.5 hours)
  - Detect USB insertion
  - Auto-mount and copy files
  - Timestamped folder structure

#### 6.3 Stealth & OpSec (3-3.5 hours)
- **6.3.1 Screen Lock** (1 hour)
  - 5-minute idle timeout
  - Numeric PIN lock
  - Wipe-on-failed option

- **6.3.2 Panic Mode** (1 hour)
  - Triple-tap trigger
  - Kill processes, clear history, delete temp files
  - Switch to fake app

- **6.3.3 MAC Address Randomization** (1-1.5 hours)
  - Random MAC generation (locally administered)
  - Apply via ip link set commands
  - Option: Randomize on boot

#### 6.4 Reporting & Intelligence (2-2.5 hours)
- **6.4.1 PDF Report Generation** (1-1.5 hours)
  - reportlab integration
  - Wizard: Select data, template, generate
  - Color-coded severity levels

- **6.4.2 OSINT Integration** (1 hour)
  - Shodan, IPinfo.io, MAC vendor lookup
  - Display in device modal
  - Result caching

---

### **SECTION 7: HARDWARE INTEGRATION** (4-5 hours)

#### 7.1 GPIO Controls (2-2.5 hours)
- **7.1.1 Physical Button Mapping** (1-1.5 hours)
  - RPi.GPIO setup
  - 4 buttons mapped to functions (panic, lock, scan, screenshot)
  - Configurable remapping

- **7.1.2 LED Status Indicators** (1-1.5 hours)
  - 3 LEDs (red/yellow/green) or RGB
  - Auto-update based on app state
  - GPIO pin configuration

#### 7.2 External Hardware (2-2.5 hours)
- **7.2.1 USB WiFi Adapter Support** (1-1.5 hours)
  - Auto-detect adapters
  - Assign roles (Primary/Monitor)
  - Status bar icon per adapter

- **7.2.2 Antenna Mods** (1 hour)
  - Documentation in README
  - Recommendations for high-gain antenna
  - Concealment tips

---

### **SECTION 8: DEPLOYMENT & DISTRIBUTION** (3-4 hours)

#### 8.1 Installation Script (1-1.5 hours)
- **8.1.1 Automated Setup** (1-1.5 hours)
  - install.sh with apt, pip installs
  - Directory creation
  - Systemd service setup

#### 8.1.2 Systemd Service (0.5 hour)
- Create dedsec.service unit file
- Auto-start on boot
- Restart on failure

#### 8.2 Update Mechanism (1-1.5 hours)
- **8.2.1 OTA Updates** (1-1.5 hours)
  - GitHub releases API polling
  - Download, extract, backup, apply
  - Version management

---

### **SECTION 11: UI/UX REDESIGN v1.1.2.5** (10-14 hours)

#### 11.1 Design System (2-2.5 hours)
- **11.1.1 Design Tokens** (1 hour)
  - constants.py with spacing, typography, colors
  - Comprehensive palette (primary, secondary, states)

- **11.1.2 Component Library** (1-1.5 hours)
  - Base components: Button, TextBox, Gauge, StatusIndicator, Modal, List, TabBar
  - Consistent styling and interaction

#### 11.2 Visual Redesign (1.5-2 hours)
- **11.2.1 Color Palette** (0.5 hour)
  - Cyberpunk theme: Black + neon green
  - Accent colors for warnings/errors

- **11.2.2 Icon System** (0.5 hour)
  - ASCII-based icons (16x16px)
  - Tool icons, status indicators

- **11.2.3 Touch Design** (0.5 hour)
  - 44x44px minimum touch targets
  - Momentum scrolling
  - State feedback visual design

#### 11.3 Screen Layouts (3-4 hours)
- **11.3.1-11.3.5 Tab Layouts** (3-4 hours)
  - SCAN tab: Progress bar, list of results
  - WIFI tab: Networks list, detail modal with actions
  - BT tab: Devices list, enumeration
  - TOOLS tab: Tool selection, execution
  - MENU tab: Settings, help, system info

#### 11.4 Architecture for Modularity (2-2.5 hours)
- **11.4.1 Modular Tool System** (1-1.5 hours)
  - BaseTool abstract class
  - Tool directory structure
  - Plugin-like architecture

- **11.4.2 Layout Manager** (1-1.5 hours)
  - Zone-based layout system
  - list/button layout helpers
  - Responsive to screen changes

#### 11.5 Implementation Roadmap (Documentation only, <0.5 hour)

---

## Total Effort Summary

| Section | Subsections | Hours | Priority |
|---------|-------------|-------|----------|
| 2 Security | 6 subsections | 10-12 | MUST-HAVE |
| 3 Tools | 9 subsections | 20-25 | MUST-HAVE |
| 4 Usability | 7 subsections | 10-12 | SHOULD-HAVE |
| 5 Maintainability | 6 subsections | 8-10 | MUST-HAVE |
| 6 Advanced | 6 subsections | 12-15 | NICE-TO-HAVE |
| 7 Hardware | 4 subsections | 4-5 | NICE-TO-HAVE |
| 8 Deployment | 4 subsections | 3-4 | SHOULD-HAVE |
| 11 UI Redesign | 7 subsections | 10-14 | SHOULD-HAVE |
| **TOTAL** | **49+ subsections** | **77-97 hours** | |

---

## Dependency Map (Critical Path)

```
Foundation Layer (MUST complete first)
├─ 2.1 Input Validation ← Required for all tools
├─ 2.3 Subprocess Security ← Required for all tool execution
├─ 5.1 Code Organization ← Required for maintainability
└─ 5.2 Testing ← Required for quality assurance

Tool Layer (Build after foundation)
├─ 3.1-3.5 Tool Integrations ← Depends on 2.1, 2.3
├─ 4.1 Configuration System ← Depends on 5.1
└─ 5.3 Documentation ← Depends on 3.x, 4.x

UI/UX Layer (Can parallel with tools)
├─ 11.1-11.4 Design System & Layouts
├─ 11.5 Modularity ← Depends on 5.1
└─ 11 Implementation ← Can start after 11.1

Integration Layer (Final phase)
├─ 6 Advanced Features ← Depends on 3.x, 4.x
├─ 7 Hardware Integration ← Depends on core app
├─ 8 Deployment ← Depends on all above
└─ Testing (Section 10) ← Final validation
```

---

## Phased Implementation Plan

### **Phase 1: Foundation & Core Security** (20-25 hours)
*Weeks 1-2*

- ✅ 2.1 Input Validation (already complete: 2.1.1, partial 2.1.2)
- ⚠️ 2.1.2 Complete SSID Sanitization (1-1.5 hrs)
- ✅ 2.1.3 Path Traversal Prevention (1.5-2 hrs)
- ✅ 2.2 Privilege Separation (2-2.5 hrs)
- ✅ 2.3 Subprocess Security (already implemented in ProcessManager)
- ✅ 2.4 Logging & Audit Trail (1.5-2 hrs)
- ✅ 5.1 Code Organization (4-5 hrs)
- ✅ 5.2 Testing Infrastructure (2-2.5 hrs)
- ✅ 5.3 Documentation (2-2.5 hrs)

**Deliverable**: Secure, modular, well-tested codebase

### **Phase 2: Essential Tools & UX** (20-25 hours)
*Weeks 3-4*

- ✅ 3.1.1 Port Scanner (2-2.5 hrs)
- ✅ 3.2.1-3.2.3 WiFi Tools (7-9 hrs)
- ✅ 4.1 Configuration System (2-2.5 hrs)
- ✅ 4.2 Terminal Improvements (2-2.5 hrs)
- ✅ 4.4 Keyboard Shortcuts (1-1.5 hrs)
- ✅ 11.1-11.4 UI/UX Redesign (10-14 hrs)

**Deliverable**: Professional cyberdeck interface with core hacking tools

### **Phase 3: Advanced Tools & Features** (15-20 hours)
*Weeks 5-6*

- ✅ 3.1.2-3.1.3 Reconnaissance (3-4 hrs)
- ✅ 3.3 Bluetooth Tools (2-2.5 hrs)
- ✅ 3.4-3.5 Payloads & Post-Exploitation (4-5 hrs)
- ✅ 4.3 Visual Feedback (2-2.5 hrs)
- ✅ 6.1-6.4 Advanced Features (12-15 hrs)

**Deliverable**: Comprehensive attack toolkit with remote access & reporting

### **Phase 4: Hardware & Deployment** (7-9 hours)
*Week 7*

- ✅ 7 Hardware Integration (4-5 hrs)
- ✅ 8 Deployment & Distribution (3-4 hrs)

**Deliverable**: Ready-to-deploy package with installer

---

## Risk & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Scope creep | HIGH | HIGH | Strict section adherence, feature flags |
| Performance degradation | MEDIUM | HIGH | Continuous profiling, optimize critical paths |
| Security vulnerabilities | MEDIUM | CRITICAL | Code review, security testing, input validation |
| Tool compatibility | MEDIUM | MEDIUM | Test all dependencies on Pi 2, version pinning |
| UI scaling issues | MEDIUM | MEDIUM | Early testing on 320x240, modular design |
| Documentation lag | HIGH | LOW | Write docs as features complete |

---

## Success Metrics

✅ **Code Quality**
- 70% unit test coverage (Section 5.2.1)
- 0 security vulnerabilities (bandit analysis)
- <100ms touch interaction latency

✅ **Feature Completeness**
- All 49+ subsections implemented
- All tools functional and tested
- Web interface operational

✅ **Performance**
- Boot time < 10s
- CPU idle < 20% (no scans)
- RAM < 200MB
- Scan latency < 5s (WiFi)

✅ **User Experience**
- Professional cyberpunk aesthetic
- Intuitive navigation (2-3 clicks to any feature)
- Comprehensive help documentation
- Smooth 30fps animations minimum

---

## Next Steps

**Immediate (Day 1-2)**:
1. Implement 2.1.2 SSID Sanitization (complete)
2. Implement 2.1.3 Path Traversal Prevention
3. Create constants.py and design_system.py

**Short-term (Week 1)**:
1. Complete Section 2 (Security)
2. Begin Section 5 (Code Organization)
3. Start UI/UX design mockups (Section 11.1)

**Medium-term (Weeks 2-4)**:
1. Implement Sections 3-4 (Tools & UX)
2. Complete UI redesign (Section 11)
3. Full testing coverage (Section 5.2)

**Long-term (Weeks 5+)**:
1. Advanced features (Section 6)
2. Hardware integration (Section 7)
3. Deployment & distribution (Section 8)

---

**Prepared by**: GitHub Copilot  
**Last Updated**: November 22, 2025  
**Next Review**: After Phase 1 completion
