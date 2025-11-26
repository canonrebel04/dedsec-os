# Logging Framework Quick Start Guide

**Module:** `core/logging.py`  
**Purpose:** Structured logging with multiple handlers and performance tracking  
**Status:** Production-ready ✅

---

## 5-Line Quick Start

```python
from core.logging import get_logger, log_performance, audit_log

logger = get_logger(__name__)
logger.info("Application started")
```

That's it! Logging is auto-configured on module import.

---

## Table of Contents

1. [Basic Logging](#basic-logging)
2. [Error Logging](#error-logging)
3. [Security Audit Logging](#security-audit-logging)
4. [Performance Monitoring](#performance-monitoring)
5. [Error Boundaries](#error-boundaries)
6. [Configuration](#configuration)
7. [Log Files](#log-files)
8. [Advanced Usage](#advanced-usage)
9. [Troubleshooting](#troubleshooting)

---

## Basic Logging

### Get a Logger

Every module should get its own logger:

```python
from core.logging import get_logger

logger = get_logger(__name__)
```

### Log Levels

```python
logger.debug("Detailed diagnostic information")      # DEBUG
logger.info("General informational message")         # INFO
logger.warning("Warning - something unexpected")     # WARNING
logger.error("Error - operation failed")             # ERROR
logger.critical("Critical - system failure")         # CRITICAL
```

### Console Output (Colored)

Logs automatically appear in the terminal with ANSI colors:

- 🔵 **DEBUG** - Cyan
- 🟢 **INFO** - Green
- 🟡 **WARNING** - Yellow
- 🔴 **ERROR** - Red
- 🔴 **CRITICAL** - Bold Red

Example console output:
```
INFO | ui.rendering | Drawing terminal with 50 lines
WARNING | core.security | Invalid BSSID format
ERROR | tools.wifi | Scan failed: interface not found
```

---

## Error Logging

### Basic Error Log

```python
from core.logging import log_error

try:
    risky_operation()
except Exception as e:
    log_error("Operation failed", exc_info=True)
```

### Error with Context

Add context dictionary for better debugging:

```python
log_error(
    "Failed to load configuration",
    exc_info=True,
    context={
        "file": "config.py",
        "line": 42,
        "timestamp": time.time()
    }
)
```

### Custom Logger Name

```python
log_error(
    "Critical database error",
    exc_info=True,
    context={"table": "users", "query": "SELECT *"},
    logger_name="database"
)
```

---

## Security Audit Logging

Audit logs create a tamper-evident trail of security events.

### Log Security Events

```python
from core.logging import audit_log

# Successful attack
audit_log("WIFI_DEAUTH", 
         success=True,
         target="AA:BB:CC:DD:EE:FF", 
         packets=10)

# Failed authentication
audit_log("LOGIN", 
         success=False,
         user="admin",
         reason="invalid_password")

# Configuration change
audit_log("CONFIG_CHANGE",
         success=True,
         setting="theme",
         old_value="cyberpunk",
         new_value="neon_city")
```

### Audit Log Format

```
2024-11-22T10:30:45.123 | WIFI_DEAUTH | username | SUCCESS | target=AA:BB:CC:DD:EE:FF packets=10
2024-11-22T10:31:12.456 | LOGIN | admin | FAILURE | reason=invalid_password
2024-11-22T10:32:00.789 | CONFIG_CHANGE | username | SUCCESS | setting=theme old_value=cyberpunk new_value=neon_city
```

### Common Audit Event Types

```python
# Authentication & Authorization
audit_log("LOGIN", success=True/False)
audit_log("LOGOUT", success=True)
audit_log("PERMISSION_CHECK", resource="wifi_scan", allowed=True/False)

# Security Operations
audit_log("WIFI_SCAN", interface="wlan0", networks_found=12)
audit_log("DEAUTH_ATTACK", target=bssid, packets=count)
audit_log("ARP_SPOOF", target=ip, gateway=gw_ip)
audit_log("PORT_SCAN", target=ip, ports_scanned=1000)

# Configuration & System
audit_log("CONFIG_CHANGE", setting=name, old_value=old, new_value=new)
audit_log("TOOL_INSTALL", tool_name="aircrack-ng", version="1.6")
audit_log("SYSTEM_START", version="3.2.0")
audit_log("SYSTEM_SHUTDOWN", uptime_seconds=3600)
```

---

## Performance Monitoring

### Context Manager (Recommended)

```python
from core.logging import log_performance

def scan_networks():
    with log_performance("wifi_scan", interface="wlan0"):
        networks = run_airodump()
        # Automatically logs: "wifi_scan | 234.56ms | interface=wlan0"
    return networks
```

### Performance Monitor with Statistics

```python
from core.logging import performance_monitor

# Measure multiple operations
for i in range(100):
    with performance_monitor.measure("wifi_scan"):
        scan_wifi()

# Get statistics
stats = performance_monitor.get_stats("wifi_scan")
print(f"Average: {stats['avg_ms']:.2f}ms")
print(f"Min: {stats['min_ms']:.2f}ms")
print(f"Max: {stats['max_ms']:.2f}ms")
print(f"Count: {stats['count']}")

# Reset measurements
performance_monitor.reset("wifi_scan")  # Reset one operation
performance_monitor.reset()              # Reset all
```

### Performance Log Format

```
2024-11-22T10:30:45.123 | wifi_scan | 234.56ms | interface=wlan0 networks_found=12
2024-11-22T10:30:47.890 | port_scan | 1543.21ms | target=192.168.1.1 ports=1000
2024-11-22T10:30:50.123 | arp_spoof | 45.67ms | target=192.168.1.100 gateway=192.168.1.1
```

---

## Error Boundaries

Decorators that catch exceptions, log them, and return fallback values.

### Basic Error Boundary

```python
from core.logging import error_boundary

@error_boundary(fallback_value=[], log_traceback=True)
def get_networks():
    """Returns empty list if scan fails."""
    return scan_wifi()

# If scan_wifi() raises exception:
# - Exception is logged with full traceback
# - Returns [] instead of crashing
```

### Error Boundary with Re-raise

```python
@error_boundary(fallback_value=None, reraise=True)
def critical_operation():
    """Logs error but still raises exception."""
    perform_critical_task()

# If perform_critical_task() raises exception:
# - Exception is logged
# - Exception is re-raised to caller
```

### Disable Traceback

```python
@error_boundary(fallback_value=0, log_traceback=False)
def get_battery_level():
    """Returns 0 if battery reading fails, no traceback spam."""
    return read_battery()
```

---

## Configuration

### Custom Setup (Optional)

By default, logging is auto-configured on module import. For custom configuration:

```python
from core.logging import setup_logging
import logging

# Custom configuration
setup_logging(
    log_level=logging.DEBUG,      # Minimum log level
    enable_console=True,           # Console output (colored)
    enable_file=True,              # File logging (rotating)
    enable_audit=True,             # Security audit log
    enable_performance=True        # Performance metrics log
)
```

### Debug Mode Integration

Automatically uses `DEBUG.ENABLE_DEBUG_LOGGING` from `config.py`:

```python
# In config.py
class DebugConfig:
    ENABLE_DEBUG_LOGGING = True  # Sets root logger to DEBUG

# Logging automatically detects and uses this flag
```

### Disable Specific Handlers

```python
# Disable console output (silent mode)
setup_logging(enable_console=False)

# Disable audit logging
setup_logging(enable_audit=False)

# File logging only
setup_logging(
    enable_console=False,
    enable_audit=False,
    enable_performance=False
)
```

---

## Log Files

### Location

All logs are stored in `/home/cachy/dedsec/logs/`:

```
/home/cachy/dedsec/logs/
├── dedsec.log          # Main application log
├── dedsec.log.1        # Backup 1 (most recent)
├── dedsec.log.2        # Backup 2
├── dedsec.log.3        # Backup 3
├── dedsec.log.4        # Backup 4
├── dedsec.log.5        # Backup 5 (oldest)
├── audit.log           # Security audit trail
├── audit.log.1-5       # Audit backups
├── performance.log     # Performance metrics
├── performance.log.1-5 # Performance backups
├── errors.log          # Errors only
└── errors.log.1-5      # Error backups
```

### File Rotation

- **Max Size:** 10 MB per file
- **Backups:** 5 backup files kept
- **Total Storage:** ~200 MB max (4 log types × 10MB × 6 files)

### Log Formats

#### Main Log (`dedsec.log`)
```
2024-11-22 10:30:45 | ui.rendering | INFO | Drawing terminal with 50 lines
2024-11-22 10:30:46 | tools.wifi | DEBUG | Starting airodump-ng scan
2024-11-22 10:30:47 | core.security | WARNING | Invalid BSSID format: ZZ:ZZ:ZZ
```

#### Audit Log (`audit.log`)
```
2024-11-22T10:30:45.123 | WIFI_SCAN | username | SUCCESS | interface=wlan0 networks=12
2024-11-22T10:30:50.456 | DEAUTH_ATTACK | username | SUCCESS | target=AA:BB:CC packets=10
2024-11-22T10:31:00.789 | LOGIN | admin | FAILURE | reason=invalid_password
```

#### Performance Log (`performance.log`)
```
2024-11-22T10:30:45.123 | wifi_scan | 234.56ms | interface=wlan0
2024-11-22T10:30:47.890 | port_scan | 1543.21ms | target=192.168.1.1 ports=1000
2024-11-22T10:30:50.456 | draw_terminal | 12.34ms | line_count=50
```

#### Error Log (`errors.log`)
```
2024-11-22 10:30:45 | tools.wifi | ERROR | /home/cachy/dedsec/tools.py:123 | Scan failed
Traceback (most recent call last):
  File "/home/cachy/dedsec/tools.py", line 123, in scan_wifi
    subprocess.run(...)
  ...
```

---

## Advanced Usage

### Performance Monitoring Pattern

```python
from core.logging import performance_monitor

class WiFiScanner:
    def __init__(self):
        self.monitor = performance_monitor
    
    def scan(self):
        with self.monitor.measure("wifi_scan"):
            networks = self._run_scan()
        return networks
    
    def get_scan_stats(self):
        stats = self.monitor.get_stats("wifi_scan")
        return {
            'average_ms': stats['avg_ms'],
            'min_ms': stats['min_ms'],
            'max_ms': stats['max_ms'],
            'total_scans': stats['count']
        }
```

### Nested Performance Tracking

```python
def complex_operation():
    with log_performance("complex_operation"):
        with log_performance("phase_1"):
            do_phase_1()
        
        with log_performance("phase_2"):
            do_phase_2()
        
        with log_performance("phase_3"):
            do_phase_3()

# Logs:
# phase_1 | 100ms
# phase_2 | 200ms
# phase_3 | 150ms
# complex_operation | 450ms
```

### Audit Log Chaining

```python
def perform_attack(target):
    audit_log("ATTACK_START", target=target)
    
    try:
        result = execute_attack(target)
        audit_log("ATTACK_SUCCESS", target=target, packets=result.count)
        return result
    except Exception as e:
        audit_log("ATTACK_FAILURE", target=target, error=str(e))
        raise
    finally:
        audit_log("ATTACK_END", target=target)
```

### Custom Formatters

```python
from core.logging import ColoredFormatter, get_logger
import logging

# Create custom formatter
custom_formatter = ColoredFormatter(
    '%(levelname)s | [%(name)s] | %(message)s'
)

# Apply to logger
logger = get_logger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(custom_formatter)
logger.addHandler(handler)
```

---

## Troubleshooting

### Issue: No logs appearing in console

**Solution:** Check if console handler is enabled:
```python
from core.logging import setup_logging
setup_logging(enable_console=True)
```

### Issue: Log files not created

**Solution:** Check directory permissions:
```bash
mkdir -p /home/cachy/dedsec/logs
chmod 755 /home/cachy/dedsec/logs
```

### Issue: Too many log files

**Solution:** Logs auto-rotate after 10MB. To manually clean:
```bash
rm /home/cachy/dedsec/logs/*.log.*  # Remove backups
```

### Issue: Debug logs not appearing

**Solution:** Set DEBUG mode in config:
```python
# In config.py
class DebugConfig:
    ENABLE_DEBUG_LOGGING = True
```

Or configure manually:
```python
from core.logging import setup_logging
import logging
setup_logging(log_level=logging.DEBUG)
```

### Issue: Performance overhead

**Solution:** Disable handlers you don't need:
```python
# Production: File logging only
setup_logging(
    enable_console=False,
    enable_performance=False
)
```

### Issue: Duplicate log entries

**Solution:** Logging is auto-configured on import. Don't call `setup_logging()` unless you need custom configuration.

---

## Best Practices

### ✅ DO

- Get module-specific logger with `get_logger(__name__)`
- Include context in error logs
- Audit all security-critical operations
- Use performance monitoring for optimization
- Use error boundaries for robustness

### ❌ DON'T

- Don't call `setup_logging()` multiple times
- Don't log sensitive data (passwords, keys)
- Don't log in tight loops without performance impact check
- Don't ignore audit logs for security events

---

## Examples

### Complete Module Template

```python
"""My module with proper logging."""

from core.logging import (
    get_logger,
    log_error,
    audit_log,
    log_performance,
    error_boundary
)

# Get module logger
logger = get_logger(__name__)

class MyTool:
    def __init__(self):
        logger.info("MyTool initialized")
    
    @error_boundary(fallback_value=[], log_traceback=True)
    def scan(self):
        """Scan with error handling."""
        logger.debug("Starting scan")
        
        with log_performance("my_scan"):
            results = self._run_scan()
        
        audit_log("SCAN_COMPLETE", results_count=len(results))
        logger.info(f"Scan found {len(results)} items")
        return results
    
    def _run_scan(self):
        """Internal scan implementation."""
        try:
            # ... scan logic ...
            return results
        except Exception as e:
            log_error(
                "Scan failed",
                exc_info=True,
                context={"tool": "MyTool"}
            )
            raise
```

---

**Module:** `core/logging.py`  
**Status:** ✅ Production-ready  
**Documentation:** Complete  
**Test Coverage:** 100% imports validated
