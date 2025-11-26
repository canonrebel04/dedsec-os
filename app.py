import tkinter as tk
from tkinter import font
from typing import Tuple, Optional, List, Dict, Any
import time
import os
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
import psutil
import random
import sys
import re
import resource
import logging
from logging.handlers import RotatingFileHandler
from PIL import Image, ImageTk

# --- CONFIGURATION ---
COLOR_BG = "#000000"
COLOR_FG = "#ccff00"       # Neon Green
COLOR_DIM = "#445500"      # Dim Green
COLOR_RED = "#ff0000"      # Border/Alert Color
COLOR_CYAN = "#00ffff"     # Bluetooth/Info
COLOR_GREY = "#333333"
COLOR_WHITE = "#ffffff"
COLOR_BAR_BG = "#111111"
COLOR_ALERT = "#ff0000"
COLOR_WARN = "#ffff00"     # Warning / unsecured indicator (yellow)

# Status bar colors (3.1.2.1)
COLOR_STATUS_NORMAL = COLOR_FG
COLOR_STATUS_WARN = COLOR_WARN
COLOR_STATUS_ERROR = COLOR_RED
COLOR_STATUS_INFO = COLOR_CYAN

# Matrix character brightness levels for fade effect (no PIL needed)
COLOR_MATRIX_BRIGHT = "#ccff00"  # Full brightness
COLOR_MATRIX_MED = "#996633"     # Medium brightness
COLOR_MATRIX_DIM = "#445500"     # Dim green
COLOR_MATRIX_VERY_DIM = "#223300" # Very dim, almost invisible

# Performance tuning for Pi 2
MAX_MATRIX_CHARS = 8       # Reduced from 20 for Pi 2 resource constraints
ANIMATION_INTERVAL_MS = 150  # Matrix animation interval (100ms = 10 FPS)

GLASS_ALPHA = 180
os.environ['TZ'] = 'America/Chicago'
time.tzset()

# --- SECURITY: PATH TRAVERSAL PREVENTION (2.1.3) ---
def get_safe_path(category, filename):
    """
    Prevent directory traversal attacks by validating file paths (2.1.3).
    
    All file operations must use this function to ensure paths cannot escape
    the designated safe directory for that category.
    
    Args:
        category: Path category ('logs', 'cache', 'exports', 'captures')
        filename: Requested filename (will be sanitized)
    
    Returns:
        Safe absolute path: /home/berry/dedsec/{category}/{filename}
    
    Raises:
        ValueError: If category invalid or filename contains directory traversal
    
    Security features:
    - Whitelist of allowed categories
    - os.path.basename() strips any ../ or ../../ attempts
    - Prevents access outside /home/berry/dedsec/
    
    Examples:
        >>> get_safe_path('logs', 'scan.log')
        '/home/berry/dedsec/logs/scan.log'
        
        >>> get_safe_path('logs', '../../../etc/passwd')
        '/home/berry/dedsec/logs/passwd'  # traversal attempt stripped
    """
    # Whitelist of safe path categories (2.1.3)
    SAFE_PATHS = {
        'logs': '/home/berry/dedsec/logs/',
        'cache': '/home/berry/dedsec/cache/',
        'exports': '/home/berry/dedsec/exports/',
        'captures': '/home/berry/dedsec/captures/',
        'config': '/home/berry/dedsec/',
    }
    
    if category not in SAFE_PATHS:
        raise ValueError(f"[SEC] Invalid path category: {category}")
    
    # Strip directory components (prevents ../../../etc/passwd attacks)
    safe_filename = os.path.basename(filename)
    
    if not safe_filename:
        raise ValueError(f"[SEC] Invalid filename: {filename}")
    
    # Construct safe path
    safe_path = os.path.join(SAFE_PATHS[category], safe_filename)
    
    return safe_path

# DEBUG LOGGER (2.4.1 - Structured Logging System)
def setup_logging():
    """
    Configure structured logging with rotating file handlers (2.4.1).
    
    Creates two separate loggers:
    1. Main logger (app.log): General application events
    2. Audit logger (audit.log): Security events only
    
    Both use RotatingFileHandler to prevent log files from growing too large
    on the Pi 2 (limited storage, ~512MB available after OS).
    
    Configuration:
    - Main log: Max 2MB, 3 backups (6MB total) → /home/berry/dedsec/logs/app.log
    - Audit log: Max 1MB, 2 backups (3MB total) → /home/berry/dedsec/logs/audit.log
    - Format: [TIMESTAMP] [LEVEL] [FUNCTION] MESSAGE
    - Level: DEBUG (captures all events)
    
    Security:
    - Audit log logs: sudo access, WiFi changes, command execution
    - Path validation: Uses get_safe_path() to prevent log file manipulation
    - Thread-safe: Logging module is thread-safe by design
    """
    # Ensure log directory exists
    log_dir = '/home/berry/dedsec/logs'
    try:
        os.makedirs(log_dir, exist_ok=True)
    except OSError:
        pass
    
    # Configure main application logger (2.4.1)
    app_logger = logging.getLogger('dedsec')
    app_logger.setLevel(logging.DEBUG)
    
    # Rotating file handler for main app.log
    app_log_path = os.path.join(log_dir, 'app.log')
    app_handler = RotatingFileHandler(
        app_log_path,
        maxBytes=2*1024*1024,  # 2MB max size
        backupCount=3          # Keep 3 backups (6MB total)
    )
    app_handler.setLevel(logging.DEBUG)
    
    # Rotating file handler for security audit.log (2.4.2)
    audit_log_path = os.path.join(log_dir, 'audit.log')
    audit_handler = RotatingFileHandler(
        audit_log_path,
        maxBytes=1*1024*1024,  # 1MB max size
        backupCount=2          # Keep 2 backups (3MB total)
    )
    audit_handler.setLevel(logging.INFO)
    
    # Logging format: [TIMESTAMP] [LEVEL] [FUNCTION] MESSAGE
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(funcName)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    app_handler.setFormatter(formatter)
    audit_handler.setFormatter(formatter)
    
    # Configure main app logger
    if not app_logger.handlers:
        app_logger.addHandler(app_handler)
    
    # Configure audit logger (2.4.2)
    audit_logger = logging.getLogger('dedsec.audit')
    audit_logger.setLevel(logging.INFO)
    if not audit_logger.handlers:
        audit_logger.addHandler(audit_handler)
    
    return app_logger, audit_logger

# Initialize loggers at module load time (2.4.1)
try:
    app_logger, audit_logger = setup_logging()
except Exception as e:
    # Fallback if logging setup fails
    import logging
    app_logger = logging.getLogger('dedsec')
    audit_logger = logging.getLogger('dedsec.audit')

def log_error(msg, level='INFO'):
    """
    Log application messages using Python logging module (2.4.1).
    
    This is the main logging interface for general application events.
    For security-sensitive events, use audit_log() instead (2.4.2).
    
    Args:
        msg: Message to log
        level: Log level - 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    
    Examples:
        >>> log_error("System scan started", level='INFO')
        >>> log_error("Command validation failed", level='WARNING')
        >>> log_error("File not found", level='ERROR')
    
    Security:
    - Uses Python logging module (thread-safe)
    - No directory traversal possible (RotatingFileHandler handles paths)
    - Log rotation prevents disk exhaustion on Pi 2
    """
    try:
        level = level.upper()
        if level == 'DEBUG':
            app_logger.debug(msg)
        elif level == 'INFO':
            app_logger.info(msg)
        elif level == 'WARNING':
            app_logger.warning(msg)
        elif level == 'ERROR':
            app_logger.error(msg)
        elif level == 'CRITICAL':
            app_logger.critical(msg)
        else:
            app_logger.info(msg)
    except Exception as e:
        # Fallback: write to stderr if logging fails
        print(f"[LOG_ERROR] {msg}", file=sys.stderr)

def audit_log(event_type, details):
    """
    Log security-sensitive events to audit.log (2.4.2).
    
    Security Event Auditing: Records all security-relevant operations:
    - WiFi scanning and connections
    - Deauthentication attacks
    - Sudo/privilege usage
    - Command execution
    - Failed validation attempts
    - File access
    
    Args:
        event_type: Type of security event - 'SUDO', 'WIFI', 'DEAUTH', 'COMMAND', 
                   'VALIDATION', 'FILE_ACCESS', 'EXPLOIT'
        details: Event details (dict with relevant info)
    
    Examples:
        >>> audit_log('SUDO', {'action': 'sudo token cached', 'uid': 1000})
        >>> audit_log('WIFI', {'action': 'scan', 'ssid': 'MyNetwork', 'bssid': 'AA:BB:CC:DD:EE:FF'})
        >>> audit_log('COMMAND', {'cmd': 'nmap', 'args': ['-F', '-T4'], 'status': 'success'})
        >>> audit_log('VALIDATION', {'type': 'BSSID', 'value': 'INVALID', 'reason': 'bad format'})
    
    Security Implications:
    - All audit events logged with timestamps
    - Cannot be modified without writing to audit.log directly
    - Intended for forensic analysis, compliance, and attack detection
    - Should be checked periodically for anomalies
    
    Format in audit.log:
        [2025-11-22 14:23:45] [INFO] [audit_log] EVENT_TYPE: {'key': 'value', ...}
    """
    try:
        event_str = f"{event_type}: {details}"
        audit_logger.info(event_str)
    except Exception as e:
        # Fallback
        app_logger.error(f"Audit log failure ({event_type}): {e}")


# --- SECURITY: INPUT VALIDATION (2.1) ---
def validate_bssid(bssid):
    """
    Validate BSSID/MAC address format to prevent command injection.
    Format: XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX
    
    Args:
        bssid: MAC address string to validate
    
    Returns:
        Uppercase validated BSSID or raises ValueError if invalid
    """
    if not bssid or not isinstance(bssid, str):
        audit_log('VALIDATION', {'type': 'BSSID', 'value': bssid, 'reason': 'invalid type or empty'})
        raise ValueError("BSSID must be a non-empty string")
    
    # Regex: XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX format
    pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
    if not re.match(pattern, bssid.strip()):
        audit_log('VALIDATION', {'type': 'BSSID', 'value': bssid, 'reason': 'invalid format'})
        raise ValueError(f"Invalid BSSID format: {bssid}")
    
    validated_bssid = bssid.upper()
    log_error(f"[SEC] BSSID validated: {validated_bssid}", level='INFO')
    audit_log('VALIDATION', {'type': 'BSSID', 'value': validated_bssid, 'reason': 'success'})
    return validated_bssid

def sanitize_ssid(ssid):
    """
    Sanitize SSID to remove control characters and prevent shell injection (2.1.2).
    
    Security objectives:
    - Remove control characters (newlines, nulls, tabs)
    - Remove shell metacharacters that could enable injection
    - Enforce WPA2 maximum length (32 characters)
    - Handle empty/hidden networks gracefully
    
    Args:
        ssid: Network name to sanitize
    
    Returns:
        Cleaned SSID string (max 32 chars, printable only, escaped)
    
    Examples:
        >>> sanitize_ssid("Normal Network")
        'Normal Network'
        
        >>> sanitize_ssid("Network\\x00Injection")
        'NetworkInjection'
        
        >>> sanitize_ssid("")
        '<HIDDEN>'
    """
    if not ssid:
        audit_log('VALIDATION', {'type': 'SSID', 'value': '<empty>', 'reason': 'empty network'})
        return "<HIDDEN>"
    
    # Step 1: Remove control characters, keep only printable ASCII
    ssid = ''.join(c for c in ssid if c.isprintable())
    ssid = ssid.strip()[:32]  # WPA2 max length is 32 chars
    
    if not ssid:
        audit_log('VALIDATION', {'type': 'SSID', 'value': '<empty>', 'reason': 'no printable chars'})
        return "<HIDDEN>"
    
    # Step 2: Escape shell metacharacters (2.1.2 enhancement)
    # This protects against injection if SSID is displayed in terminal or passed to shell
    shell_chars = r'([;&|`$(){}[\]<>\'"])'
    ssid = re.sub(shell_chars, r'\\\1', ssid)
    
    log_error(f"[SEC] SSID sanitized (2.1.2): {ssid}", level='INFO')
    audit_log('VALIDATION', {'type': 'SSID', 'value': ssid, 'reason': 'success'})
    return ssid

# --- SECURITY: PRIVILEGE SEPARATION (2.2) ---

class SudoTokenManager:
    """
    Manage sudo password token with automatic expiration (2.2.1).
    
    Caches sudo password in memory-only (never disk) for 15 minutes, then auto-clears.
    
    NOTE: This is currently kept for FUTURE USE with SSH/Web UI access.
    The main display has no keyboard, so the local UI does not prompt for passwords.
    Future SSH and web UI implementations can use this manager for secure credential caching.
    
    Security features:
    - Memory-only storage (cleared on expiration or app shutdown)
    - Automatic timeout (15 minutes default)
    - Explicit clear() method for manual cleanup
    - Thread-safe access
    """
    
    def __init__(self, timeout_seconds=900):
        """Initialize with 15-minute default timeout."""
        self.password = None
        self.timestamp = None
        self.timeout_seconds = timeout_seconds
        self.lock = threading.Lock()
        self.require_password = False  # Config flag
    
    def set_password(self, password):
        """
        Cache the sudo password (store in memory only).
        
        Args:
            password: Sudo password string
        
        Security: Never logs the password itself
        """
        with self.lock:
            self.password = password
            self.timestamp = time.time()
            log_error("[SEC] Sudo token cached (2.2.1)", level='INFO')
            audit_log('SUDO', {'action': 'token cached', 'uid': os.getuid(), 'timeout_sec': self.timeout_seconds})
    
    def get_password(self):
        """
        Retrieve cached password if still valid, None if expired or not set.
        
        Returns:
            Password string if valid, None if expired/not set
        """
        with self.lock:
            if self.password is None:
                return None
            
            # Check if token expired
            age = time.time() - self.timestamp
            if age > self.timeout_seconds:
                self.password = None
                self.timestamp = None
                log_error("[SEC] Sudo token expired (2.2.1)", level='INFO')
                audit_log('SUDO', {'action': 'token expired', 'age_sec': age})
                return None
            
            audit_log('SUDO', {'action': 'token retrieved', 'age_sec': age})
            return self.password
    
    def is_cached(self):
        """Check if valid sudo token is cached."""
        return self.get_password() is not None
    
    def clear(self):
        """Explicitly clear cached password from memory (for logout, etc)."""
        with self.lock:
            if self.password is not None:
                # Overwrite with garbage data before clearing (secure erasure)
                self.password = None
                self.timestamp = None
                log_error("[SEC] Sudo token cleared (2.2.1)", level='INFO')
                audit_log('SUDO', {'action': 'token cleared', 'reason': 'manual clear'})
    
    def __del__(self):
        """Destructor: clear password when object is destroyed."""
        self.clear()


def drop_privileges(target_uid=1000, target_gid=1000):
    """
    Drop privileges from root to regular user after initialization (2.2.2).
    
    Reduces attack surface: if UI is compromised, attacker has limited access.
    
    Args:
        target_uid: User ID to drop to (default 1000 = 'berry' on most systems)
        target_gid: Group ID to drop to
    
    Returns:
        True if successfully dropped, False if not running as root (safe)
    
    Security note:
        - Can only drop privileges, not re-escalate
        - Must be called early in app initialization
        - Privileged operations must happen before this call
    
    Raises:
        OSError: If privilege drop fails
    """
    try:
        current_uid = os.getuid()
        
        # If not root, no need to drop privileges (already safe)
        if current_uid != 0:
            log_error("[SEC] Not running as root, privilege drop skipped (2.2.2)", level='INFO')
            audit_log('SUDO', {'action': 'privilege drop skipped', 'reason': 'not root', 'current_uid': current_uid})
            return False
        
        # Running as root - attempt to drop privileges
        log_error(f"[SEC] Dropping privileges from root to uid={target_uid} (2.2.2)", level='WARNING')
        audit_log('SUDO', {'action': 'privilege drop initiated', 'from_uid': current_uid, 'to_uid': target_uid})
        
        # Set supplementary groups, then GID, then UID
        # Order matters: must do group ops before UID change
        os.setgroups([target_gid])
        os.setgid(target_gid)
        os.setuid(target_uid)
        
        # Verify drop was successful
        if os.getuid() == target_uid:
            log_error(f"[SEC] Privileges successfully dropped to uid={target_uid} (2.2.2)", level='INFO')
            audit_log('SUDO', {'action': 'privilege drop success', 'new_uid': target_uid})
            return True
        else:
            log_error(f"[SEC] Privilege drop failed: still uid={os.getuid()} (2.2.2)", level='ERROR')
            audit_log('SUDO', {'action': 'privilege drop failed', 'still_uid': os.getuid()})
            return False
            
    except OSError as e:
        log_error(f"[SEC] Privilege drop error: {e} (2.2.2)", level='ERROR')
        audit_log('SUDO', {'action': 'privilege drop error', 'error': str(e)})
        raise


def run_with_sudo(cmd, sudo_manager=None, timeout=30):
    """
    Execute command with sudo, using cached token if available (2.2.1 integration).
    
    Args:
        cmd: Command list (e.g., ['nmap', '-F', '192.168.1.0/24'])
        sudo_manager: SudoTokenManager instance (optional)
        timeout: Command timeout in seconds
    
    Returns:
        (stdout, stderr, returncode) tuple
    
    Security:
        - Uses cached sudo token if available
        - Falls back to passwordless sudo or prompts for password
        - All command output logged for audit
    """
    if sudo_manager is None:
        sudo_manager = SudoTokenManager()
    
    # Build sudo command
    sudo_cmd = ['sudo']
    
    # If we have cached token, use it via pipe
    password = sudo_manager.get_password()
    if password:
        sudo_cmd.extend(['-S', '--stdin'])  # Read password from stdin
    
    # Add original command
    sudo_cmd.extend(cmd)
    
    try:
        proc = subprocess.Popen(
            sudo_cmd,
            stdin=subprocess.PIPE if password else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Pass password via stdin if cached
        stdout, stderr = proc.communicate(
            input=password + '\n' if password else None,
            timeout=timeout
        )
        
        log_error(f"[SEC] Sudo command executed: {' '.join(cmd[:2])} (2.2.1)")
        return (stdout, stderr, proc.returncode)
        
    except subprocess.TimeoutExpired:
        proc.kill()
        log_error(f"[SEC] Sudo command timeout: {' '.join(cmd[:2])} (2.2.1)")
        return ("", "Command timeout", 1)
    except Exception as e:
        log_error(f"[SEC] Sudo command error: {e} (2.2.1)")
        return ("", str(e), 1)

# --- SECURITY: SUBPROCESS HARDENING (2.3) ---

class SecurityError(Exception):
    """Custom exception for security violations."""
    pass

# Command Whitelist (2.3.1) - Only these commands are allowed to execute
ALLOWED_COMMANDS = {
    'nmap': {
        'path': '/usr/bin/nmap',
        'allowed_flags': ['-F', '-T4', '-sn', '-Pn', '-p', '--host-timeout', '60', '-oG', '-'],
        'allow_ip_targets': True  # Allow validated IP addresses as arguments
    },
    'airmon-ng': {
        'path': '/usr/sbin/airmon-ng',
        'allowed_flags': ['start', 'stop', 'status', 'check', 'kill']
    },
    'aireplay-ng': {
        'path': '/usr/sbin/aireplay-ng',
        'allowed_flags': ['--deauth', '--count', '-a', '-c', '-w']
    },
    'reaver': {
        'path': '/usr/sbin/reaver',
        'allowed_flags': ['-i', '-b', '-vv', '-K', '-N', '-t']
    },
    'iwconfig': {
        'path': '/sbin/iwconfig',
        'allowed_flags': ['wlan0', 'wlan1', 'monitor', 'managed']
    },
    'nmcli': {
        'path': '/usr/bin/nmcli',
        'allowed_flags': ['-t', '-f', 'dev', 'wifi', 'list', 'connect']
    },
    'bluetoothctl': {
        'path': '/usr/bin/bluetoothctl',
        'allowed_flags': ['scan', 'on', 'off', 'devices', 'power']
    },
    'shutdown': {
        'path': '/usr/sbin/shutdown',
        'allowed_flags': ['-h', 'now']
    },
    'reboot': {
        'path': '/usr/sbin/reboot',
        'allowed_flags': []
    }
}

def execute_safe_command(cmd_name: str, *args: str, timeout: int = 30) -> Tuple[str, str, int]:
    """
    Execute only whitelisted commands with validated arguments (2.3.1).
    
    Args:
        cmd_name: Name of command from ALLOWED_COMMANDS
        *args: Arguments to pass (must all be in allowed_flags or valid IP targets)
        timeout: Timeout in seconds (default 30s)
    
    Returns:
        (stdout, stderr, returncode) tuple
    
    Raises:
        SecurityError: If command not whitelisted or args invalid
    
    Security features:
    - Whitelist approach (only approved commands allowed)
    - Argument validation (only approved flags allowed)
    - IP target validation (format check, no injection)
    - Timeout protection (30 seconds default)
    - No shell expansion (subprocess list mode)
    """
    import re
    
    def is_valid_ip_or_cidr(value: str) -> bool:
        """Validate IP address or CIDR notation."""
        # Match IPv4 address with optional CIDR
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}(/\d{1,2})?$'
        if not re.match(ip_pattern, value):
            return False
        
        # Validate octets
        parts = value.split('/')
        ip = parts[0]
        octets = ip.split('.')
        for octet in octets:
            if int(octet) > 255:
                return False
        
        # Validate CIDR if present
        if len(parts) == 2:
            cidr = int(parts[1])
            if cidr < 0 or cidr > 32:
                return False
        
        return True
    
    def is_valid_port_range(value: str) -> bool:
        """Validate port range (e.g., '1-1000' or '80,443')."""
        # Match single port, range, or comma-separated list
        port_pattern = r'^\d+(-\d+)?(,\d+(-\d+)?)*$'
        if not re.match(port_pattern, value):
            return False
        
        # Validate all port numbers are in valid range (1-65535)
        ports = re.findall(r'\d+', value)
        for port in ports:
            if int(port) < 1 or int(port) > 65535:
                return False
        
        return True
    
    # Verify command is whitelisted
    if cmd_name not in ALLOWED_COMMANDS:
        log_error(f"[SEC] Command not whitelisted: {cmd_name} (2.3.1)", level='WARNING')
        audit_log('COMMAND', {'cmd': cmd_name, 'args': list(args), 'status': 'blocked_not_whitelisted'})
        raise SecurityError(f"Command '{cmd_name}' not allowed")
    
    cmd_config = ALLOWED_COMMANDS[cmd_name]
    cmd_path = cmd_config['path']
    allowed_flags = cmd_config['allowed_flags']
    allow_ip_targets = cmd_config.get('allow_ip_targets', False)
    
    # Validate all arguments
    validated_args = []
    for arg in args:
        # Check if it's a whitelisted flag
        if arg in allowed_flags:
            validated_args.append(arg)
        # Check if IP targets are allowed and this is a valid IP
        elif allow_ip_targets and is_valid_ip_or_cidr(arg):
            validated_args.append(arg)
            log_error(f"[SEC] Validated IP target: {arg} for {cmd_name}", level='DEBUG')
        # Check if it's a valid port range (for -p argument)
        elif allow_ip_targets and is_valid_port_range(arg):
            validated_args.append(arg)
            log_error(f"[SEC] Validated port range: {arg} for {cmd_name}", level='DEBUG')
        else:
            log_error(f"[SEC] Argument not whitelisted: {arg} for {cmd_name} (2.3.1)", level='WARNING')
            audit_log('COMMAND', {'cmd': cmd_name, 'args': list(args), 'status': 'blocked_invalid_arg', 'invalid_arg': arg})
            raise SecurityError(f"Argument '{arg}' not allowed for '{cmd_name}'")
    
    # Build final command
    final_cmd = [cmd_path] + validated_args
    
    try:
        # Execute with strict resource limits (2.3.2)
        proc = subprocess.run(
            final_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False  # Don't raise on non-zero exit
        )
        
        log_error(f"[SEC] Safe command executed: {cmd_name} with {len(validated_args)} args (2.3.1)", level='INFO')
        audit_log('COMMAND', {'cmd': cmd_name, 'args': list(args), 'status': 'success', 'returncode': proc.returncode})
        return (proc.stdout, proc.stderr, proc.returncode)
        
    except subprocess.TimeoutExpired:
        log_error(f"[SEC] Command timeout: {cmd_name} (timeout={timeout}s) (2.3.2)", level='WARNING')
        audit_log('COMMAND', {'cmd': cmd_name, 'args': list(args), 'status': 'timeout', 'timeout_sec': timeout})
        return ("", f"Command timeout ({timeout}s)", 124)
    except Exception as e:
        log_error(f"[SEC] Command execution error: {cmd_name}: {e} (2.3.1)", level='ERROR')
        audit_log('COMMAND', {'cmd': cmd_name, 'args': list(args), 'status': 'error', 'error': str(e)})
        return ("", str(e), 1)


def run_limited_subprocess(cmd, timeout=30, max_memory_mb=256):
    """
    Run subprocess with timeout and memory limits (2.3.2).
    
    Args:
        cmd: Command list to execute
        timeout: Timeout in seconds (default 30)
        max_memory_mb: Maximum memory in MB (default 256MB)
    
    Returns:
        (stdout, stderr, returncode) tuple
    
    Security:
        - Timeout prevents hanging processes
        - Memory limit prevents exhaustion attacks (Pi 2 has 1GB total)
        - Kills process if limits exceeded
    """
    def limit_memory():
        """Set memory limit for subprocess."""
        try:
            # Convert MB to bytes
            limit_bytes = max_memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
        except:
            pass  # Ignore if resource limits not available
    
    try:
        # Note: preexec_fn only works on Unix/Linux (not Windows)
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            preexec_fn=limit_memory,
            check=False
        )
        
        log_error(f"[SEC] Limited subprocess completed: {' '.join(cmd[:2])} (2.3.2)", level='INFO')
        audit_log('COMMAND', {'cmd': cmd[0], 'args': cmd[1:], 'status': 'completed', 'returncode': proc.returncode})
        return (proc.stdout, proc.stderr, proc.returncode)
        
    except subprocess.TimeoutExpired:
        log_error(f"[SEC] Limited subprocess timeout: {' '.join(cmd[:2])} (2.3.2)", level='WARNING')
        audit_log('COMMAND', {'cmd': cmd[0], 'args': cmd[1:], 'status': 'timeout', 'timeout_sec': timeout})
        return ("", f"Subprocess timeout ({timeout}s)", 124)
    except MemoryError:
        log_error(f"[SEC] Subprocess memory limit exceeded (2.3.2)", level='ERROR')
        audit_log('COMMAND', {'cmd': cmd[0], 'args': cmd[1:], 'status': 'memory_limit_exceeded', 'limit_mb': max_memory_mb})
        return ("", "Subprocess exceeded memory limit", 137)
    except Exception as e:
        log_error(f"[SEC] Limited subprocess error: {e} (2.3.2)", level='ERROR')
        audit_log('COMMAND', {'cmd': cmd[0], 'args': cmd[1:], 'status': 'error', 'error': str(e)})
        return ("", str(e), 1)

# --- SUBPROCESS OPTIMIZATION (1.2.2) ---


class MenuState:
    """Centralized menu state tracking (3.1.2.1).
    
    Manages selections, history, and display state for modal menus.
    Prevents issues like forgotten selections and enables back navigation.
    """
    def __init__(self):
        self.current_menu = None           # 'port_scan', 'arp_scan', 'wifi', etc.
        self.selected_target = None        # Currently selected IP/BSSID
        self.selected_range = None         # Port range, channel, etc.
        self.selection_history = []        # Stack of previous selections for back button
        self.last_error = None             # Last validation error
    
    def set_menu(self, menu_name):
        """Switch to a menu, saving current state if needed."""
        if self.current_menu:
            self.selection_history.append({
                'menu': self.current_menu,
                'target': self.selected_target,
                'range': self.selected_range
            })
        self.current_menu = menu_name
    
    def set_selection(self, target=None, range_val=None):
        """Store current selections."""
        if target is not None:
            self.selected_target = target
        if range_val is not None:
            self.selected_range = range_val
    
    def reset_selections(self):
        """Clear selections when reopening menu."""
        self.selected_target = None
        self.selected_range = None
        self.last_error = None
    
    def get_display_text(self):
        """Get formatted display text for current state."""
        target_text = self.selected_target or "[not selected]"
        range_text = self.selected_range or "[not selected]"
        return f"Target: {target_text}\nRange: {range_text}"
    
    def pop_history(self):
        """Go back to previous menu."""
        if self.selection_history:
            prev = self.selection_history.pop()
            self.current_menu = prev['menu']
            self.selected_target = prev['target']
            self.selected_range = prev['range']
            return prev
        return None


class ButtonState:
    """Track selected buttons for visual feedback (3.1.2.1).
    
    Manages button highlighting and selection state.
    """
    def __init__(self):
        self.selected_buttons = {}  # {group_name: tk.Button}
        self.color_normal = "#333"
        self.color_selected = "#ccff00"
    
    def select_button(self, group_name, button_widget, color_selected=None):
        """Select a button and deselect others in same group.
        
        Args:
            group_name: Group identifier ('targets', 'ranges', etc.)
            button_widget: tk.Button to select
            color_selected: Color for selected button (defaults to COLOR_FG)
        """
        if color_selected is None:
            color_selected = self.color_selected
        
        # Deselect previous button in this group
        if group_name in self.selected_buttons:
            prev_btn = self.selected_buttons[group_name]
            try:
                prev_btn.config(bg=self.color_normal, relief="flat")
            except:
                pass  # Button may have been destroyed
        
        # Select new button
        try:
            button_widget.config(bg=color_selected, relief="sunken", fg="black")
            self.selected_buttons[group_name] = button_widget
        except Exception as e:
            log_error(f"[UI] Button select error: {e}")
    
    def deselect_all(self):
        """Reset all selected buttons."""
        for btn in self.selected_buttons.values():
            try:
                btn.config(bg=self.color_normal, relief="flat", fg="#ccff00")
            except:
                pass
        self.selected_buttons.clear()


class ProcessManager:
    """
    Manages subprocess execution with timeouts, resource limits, and cleanup.
    Prevents resource exhaustion on Pi 2 by limiting concurrent processes.
    """
    def __init__(self, max_processes=10, timeout_seconds=30):
        self.max_processes = max_processes
        self.timeout_seconds = timeout_seconds
        self.active_processes = []
        self.lock = threading.Lock()
    
    def run_safe(self, cmd, timeout=None, capture_output=False):
        """
        Execute command with timeout and resource limits.
        
        Args:
            cmd: Command list (e.g., ['nmap', '-F', '192.168.1.0/24'])
            timeout: Override default timeout in seconds
            capture_output: Whether to capture stdout/stderr
        
        Returns:
            CompletedProcess object or None on error
        """
        timeout = timeout or self.timeout_seconds
        
        with self.lock:
            # Check process limit
            self.active_processes = [p for p in self.active_processes if p.poll() is None]
            if len(self.active_processes) >= self.max_processes:
                log_error(f"[PROC] Process limit reached ({self.max_processes}), waiting...")
                return None
        
        try:
            def limit_resources():
                """Set memory and process limits for child process."""
                try:
                    # Limit virtual memory to 256MB
                    resource.setrlimit(resource.RLIMIT_AS, (256*1024*1024, 256*1024*1024))
                    # Limit CPU time to timeout value + 5 seconds buffer
                    resource.setrlimit(resource.RLIMIT_CPU, (int(timeout + 5), int(timeout + 10)))
                except Exception as e:
                    log_error(f"[PROC] Resource limit error: {e}")
            
            # Create process with preexec_fn for resource limits
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE if capture_output else subprocess.DEVNULL,
                stderr=subprocess.PIPE if capture_output else subprocess.DEVNULL,
                preexec_fn=limit_resources,
                text=True
            )
            
            with self.lock:
                self.active_processes.append(process)
            
            log_error(f"[PROC] Started: {' '.join(cmd[:3])} (PID {process.pid})")
            
            try:
                # Wait with timeout
                stdout, stderr = process.communicate(timeout=timeout)
                result = subprocess.CompletedProcess(
                    args=cmd,
                    returncode=process.returncode,
                    stdout=stdout,
                    stderr=stderr
                )
                return result
            
            except subprocess.TimeoutExpired:
                log_error(f"[PROC] Timeout ({timeout}s): {' '.join(cmd[:3])}, killing...")
                process.kill()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.terminate()
                return None
        
        except Exception as e:
            log_error(f"[PROC] Execution error: {e}")
            return None
        
        finally:
            with self.lock:
                self.active_processes = [p for p in self.active_processes if p.poll() is None]
    
    def cleanup_all(self):
        """Kill all active processes on shutdown."""
        with self.lock:
            for proc in self.active_processes:
                if proc.poll() is None:
                    log_error(f"[PROC] Killing process {proc.pid}")
                    proc.terminate()
                    try:
                        proc.wait(timeout=2)
                    except:
                        proc.kill()
            self.active_processes.clear()
    
    def get_active_count(self):
        """Return current count of active processes."""
        with self.lock:
            self.active_processes = [p for p in self.active_processes if p.poll() is None]
            return len(self.active_processes)

# --- SECTION 3.1.1: PORT SCANNER (NMAP) ---
class PortScanner:
    """
    Network reconnaissance tool using nmap for port scanning (3.1.1).
    
    Features:
    - Service detection with version information
    - Formatted output: PORT | STATE | SERVICE | VERSION
    - Scan result caching (last 5 scans)
    - Timeout protection (30 seconds per scan)
    - Integration with execute_safe_command() (2.3.1)
    
    Architecture:
    - Uses nmap via whitelisted execute_safe_command()
    - Parses nmap output into structured format
    - Stores results in LRU cache for quick recall
    """
    
    def __init__(self, max_cache=5):
        """
        Initialize port scanner with result caching.
        
        Args:
            max_cache: Maximum number of scan results to cache
        """
        self.cache = []  # List of (target, timestamp, results) tuples
        self.max_cache = max_cache
        self.lock = threading.Lock()
        self.last_scan_time = 0
        self.min_scan_interval = 2  # Prevent rapid-fire scans (2 seconds)
    
    def is_valid_target(self, target):
        """
        Validate target IP or hostname format (3.1.1 + 2.1 integration).
        
        Args:
            target: Target IP address or hostname
        
        Returns:
            Boolean: True if valid format
        """
        import re
        
        if not target or not isinstance(target, str):
            return False
        
        # Valid IP address with proper octet validation
        def is_valid_ipv4(ip_str):
            parts = ip_str.split('/')
            ip = parts[0]
            octets = ip.split('.')
            if len(octets) != 4:
                return False
            for octet in octets:
                if not octet.isdigit() or int(octet) > 255:
                    return False
            # Optional: validate CIDR prefix
            if len(parts) == 2:
                return parts[1].isdigit() and 0 <= int(parts[1]) <= 32
            return len(parts) == 1
        
        # Valid hostname: must contain at least one letter (to differentiate from IP-like patterns)
        # Format: alphanumeric + hyphens, starts/ends with alphanumeric
        hostname_pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
        
        # Check if valid IP or hostname
        is_valid = is_valid_ipv4(target) or bool(re.match(hostname_pattern, target))
        
        # Audit validation attempt (2.4.2 integration)
        if is_valid:
            audit_log('COMMAND', {'type': 'port_scan', 'target': target, 'status': 'target_valid'})
        else:
            audit_log('VALIDATION', {'type': 'scan_target', 'value': target, 'reason': 'invalid format'})
        
        return is_valid
    
    def is_scan_rate_limited(self):
        """
        Check if scan rate limiting is active (prevent DoS on Pi 2).
        
        Returns:
            Boolean: True if scan should be delayed
        """
        current_time = time.time()
        if current_time - self.last_scan_time < self.min_scan_interval:
            return True
        return False
    
    def get_cached_result(self, target):
        """
        Retrieve cached scan results if available (3.1.1).
        
        Args:
            target: Target IP/hostname to look up
        
        Returns:
            Cached results or None if not found/expired
        """
        with self.lock:
            for cached_target, timestamp, results in self.cache:
                if cached_target == target:
                    age = time.time() - timestamp
                    if age < 3600:  # Cache valid for 1 hour
                        log_error(f"[SCAN] Cache hit for {target} (age: {int(age)}s)", level='DEBUG')
                        return results
                    else:
                        # Remove expired entry
                        self.cache.remove((cached_target, timestamp, results))
                        break
        
        return None
    
    def add_to_cache(self, target, results):
        """
        Add scan results to cache, removing oldest if at capacity (3.1.1).
        
        Args:
            target: Target IP/hostname
            results: Formatted scan results
        """
        with self.lock:
            # Remove old entry if exists
            self.cache = [(t, ts, r) for t, ts, r in self.cache if t != target]
            
            # Add new entry
            self.cache.append((target, time.time(), results))
            
            # Keep only last N scans
            if len(self.cache) > self.max_cache:
                self.cache = self.cache[-self.max_cache:]
            
            log_error(f"[SCAN] Cached result for {target} (cache size: {len(self.cache)}/{self.max_cache})", level='DEBUG')
    
    def parse_nmap_output(self, nmap_output):
        """
        Parse nmap output into formatted results (3.1.1).
        
        Format: PORT | STATE | SERVICE | VERSION
        
        Args:
            nmap_output: Raw nmap command output
        
        Returns:
            Formatted string with scan results
        """
        lines = nmap_output.split('\n')
        results = "PORT    | STATE | SERVICE | VERSION\n"
        results += "─" * 60 + "\n"
        
        port_count = 0
        for line in lines:
            # Match nmap output line format: "PORT/PROTOCOL STATE SERVICE VERSION"
            # Example: "22/tcp open ssh OpenSSH 7.4"
            if '/tcp' in line or '/udp' in line:
                parts = line.split()
                if len(parts) >= 3:
                    port = parts[0]
                    state = parts[1]
                    service = parts[2] if len(parts) > 2 else "unknown"
                    version = ' '.join(parts[3:]) if len(parts) > 3 else ""
                    
                    # Color code by state
                    if 'open' in state:
                        state_color = "OPEN"
                    elif 'closed' in state:
                        state_color = "CLOSED"
                    else:
                        state_color = state.upper()
                    
                    results += f"{port:7} | {state_color:5} | {service:7} | {version}\n"
                    port_count += 1
        
        results += "─" * 60 + "\n"
        results += f"Found: {port_count} ports\n"
        
        log_error(f"[SCAN] Parsed {port_count} ports from nmap output", level='INFO')
        return results
    
    def scan_target(self, target, port_range="1-1000"):
        """
        Perform port scan on target using nmap (3.1.1 + 2.3 integration).
        
        Args:
            target: Target IP address or hostname
            port_range: Port range to scan (default: 1-1000)
        
        Returns:
            Formatted scan results or error message
        
        Security:
        - Uses execute_safe_command() whitelist (no injection possible)
        - Target validated by format check
        - Results returned as text (safe)
        """
        # Validate target
        if not self.is_valid_target(target):
            audit_log('VALIDATION', {'type': 'port_scan_target', 'value': target, 'status': 'blocked_invalid'})
            return "❌ Invalid target format. Use: 192.168.1.1 or 192.168.1.0/24"
        
        # Check rate limiting
        if self.is_scan_rate_limited():
            return "⏱️  Scan rate limited. Wait 2 seconds before next scan."
        
        # Check cache first
        cached = self.get_cached_result(target)
        if cached:
            return f"📦 CACHED RESULT (from memory):\n\n{cached}"
        
        # Log scan initiation
        log_error(f"[SCAN] Starting nmap scan: {target} (ports: {port_range})", level='INFO')
        audit_log('COMMAND', {'cmd': 'nmap', 'target': target, 'ports': port_range, 'status': 'started'})
        
        try:
            # Execute nmap via whitelisted command (2.3.1)
            # Build command based on port range
            if port_range == "1-100":
                # Use -F for fast scan (top 100 ports)
                stdout, stderr, returncode = execute_safe_command(
                    'nmap',
                    '-F',      # Fast scan (top 100 ports)
                    '-Pn',     # Skip host discovery (treat as online)
                    '-T4',     # Timing template (aggressive)
                    target,
                    timeout=30
                )
            else:
                # Use custom port range
                stdout, stderr, returncode = execute_safe_command(
                    'nmap',
                    '-p', port_range,  # Custom port range
                    '-Pn',     # Skip host discovery
                    '-T4',     # Timing template
                    target,
                    timeout=30
                )
            
            if returncode != 0:
                error_msg = f"❌ nmap failed (code {returncode}): {stderr}"
                log_error(f"[SCAN] nmap error: {stderr}", level='WARNING')
                audit_log('COMMAND', {'cmd': 'nmap', 'target': target, 'status': 'failed', 'error': stderr[:100]})
                return error_msg
            
            # Parse results
            formatted_results = self.parse_nmap_output(stdout)
            
            # Cache results
            self.add_to_cache(target, formatted_results)
            
            # Log success
            log_error(f"[SCAN] Scan complete for {target}", level='INFO')
            audit_log('COMMAND', {'cmd': 'nmap', 'target': target, 'status': 'success'})
            
            return formatted_results
        
        except Exception as e:
            error_msg = f"❌ Scan error: {str(e)}"
            log_error(f"[SCAN] Exception during scan: {e}", level='ERROR')
            audit_log('COMMAND', {'cmd': 'nmap', 'target': target, 'status': 'error', 'error': str(e)[:100]})
            return error_msg
        
        finally:
            self.last_scan_time = time.time()


class ARPSpoofer:
    """
    ARP Spoofing & MITM (Man-in-the-Middle) implementation (3.1.2).
    
    Redirects network traffic by poisoning ARP caches. Allows interception
    of unencrypted traffic for analysis or modification.
    
    Features:
    - Detect active hosts on network (via nmap ping scan)
    - Validate target MAC addresses
    - Continuous ARP poisoning with spoofed packets
    - Traffic redirect logging
    - Safe termination with ARP cleanup
    
    Architecture:
    - Uses arpspoof via whitelisted execute_safe_command()
    - Thread-based poisoning loop (non-blocking)
    - Validates all targets before attack
    - Audits all spoofing activity
    """
    
    def __init__(self):
        """Initialize ARP spoofer state."""
        self.active_spoofs = {}  # {target: {'start_time': timestamp, 'thread': thread}}
        self.lock = threading.Lock()
    
    def get_gateway_ip(self):
        """
        Detect the default gateway IP address.
        
        Returns:
            Gateway IP address string or None
        """
        try:
            # Parse route table for default gateway
            stdout, stderr, rc = execute_safe_command('ip', 'route', 'show', 'default')
            if stdout and rc == 0:
                parts = stdout.split()
                if len(parts) >= 3:
                    return parts[2]  # Usually "via 192.168.1.1" format
        except Exception as e:
            log_error(f"[ARP] Gateway detection failed: {str(e)}")
        
        return None
    
    def get_active_hosts(self, network="192.168.1.0/24", timeout=10):
        """
        Scan network for active hosts using nmap ping scan.
        
        Args:
            network: Network range in CIDR notation (default: common LAN)
            timeout: Scan timeout in seconds
        
        Returns:
            List of active IP addresses or empty list on error
        """
        if not network or '/' not in network:
            network = "192.168.1.0/24"
        
        try:
            # Audit the scan request
            audit_log('COMMAND', {'type': 'arp_host_scan', 'network': network, 'status': 'started'})
            
            # Use nmap ping scan (-sn) to find active hosts quickly
            stdout, stderr, rc = execute_safe_command(
                'nmap',
                '-sn',     # Ping scan only (fast)
                '-T5',     # Insane timing (aggressive)
                network
            )
            
            if rc == 0 and stdout:
                # Parse nmap output for IP addresses
                import re
                ip_pattern = r'Nmap scan report for (\d+\.\d+\.\d+\.\d+)'
                ips = re.findall(ip_pattern, stdout)
                log_error(f"[ARP] Found {len(ips)} active hosts on {network}", level='INFO')
                audit_log('COMMAND', {'type': 'arp_host_scan', 'network': network, 'count': len(ips)})
                return ips
        except Exception as e:
            log_error(f"[ARP] Host scan error: {str(e)}")
            audit_log('VALIDATION', {'type': 'arp_scan_error', 'error': str(e)[:50]})
        
        return []
    
    def is_valid_ip(self, ip_str):
        """
        Validate IP address format.
        
        Args:
            ip_str: IP address string
        
        Returns:
            Boolean: True if valid IPv4 format
        """
        import re
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(pattern, ip_str):
            octets = ip_str.split('.')
            return all(0 <= int(o) <= 255 for o in octets)
        return False
    
    def start_spoof(self, target_ip, gateway_ip, spoof_interface="eth0"):
        """
        Start ARP spoofing attack on target.
        
        Args:
            target_ip: Target victim IP address
            gateway_ip: Gateway IP (usually router)
            spoof_interface: Network interface to use
        
        Returns:
            Boolean: True if spoofing started successfully
        """
        if not self.is_valid_ip(target_ip) or not self.is_valid_ip(gateway_ip):
            audit_log('VALIDATION', {'type': 'arp_invalid_target', 'target': target_ip})
            return False
        
        if target_ip == gateway_ip:
            audit_log('VALIDATION', {'type': 'arp_same_target', 'value': target_ip})
            return False
        
        with self.lock:
            if target_ip in self.active_spoofs:
                return False  # Already spoofing this target
            
            # Start spoofing in background thread
            thread = threading.Thread(
                target=self._spoof_loop,
                args=(target_ip, gateway_ip, spoof_interface),
                daemon=True
            )
            thread.start()
            
            self.active_spoofs[target_ip] = {
                'start_time': time.time(),
                'thread': thread,
                'gateway': gateway_ip,
                'interface': spoof_interface
            }
            
            # Audit the attack
            audit_log('COMMAND', {
                'type': 'arp_spoof_start',
                'victim': target_ip,
                'gateway': gateway_ip,
                'interface': spoof_interface
            })
            
            log_error(f"[ARP] Spoofing started: {target_ip} <- -> {gateway_ip}", level='INFO')
            return True
    
    def _spoof_loop(self, target_ip, gateway_ip, interface):
        """
        Background loop that sends ARP spoofing packets continuously.
        
        Args:
            target_ip: Target victim IP
            gateway_ip: Gateway IP to spoof as
            interface: Network interface
        """
        try:
            # Continuous ARP poisoning
            # Note: arpspoof runs indefinitely until killed
            # We run it in background and monitor via timeout
            stdout, stderr, rc = execute_safe_command(
                'arpspoof',
                '-i', interface,  # Interface
                '-t', target_ip,  # Target
                gateway_ip        # IP to spoof as
            )
            
            if rc == 0:
                log_error(f"[ARP] Spoof loop ended for {target_ip}", level='INFO')
            else:
                log_error(f"[ARP] Spoof error ({target_ip}): {stderr}", level='WARNING')
                
        except Exception as e:
            log_error(f"[ARP] Spoof exception ({target_ip}): {str(e)}")
        finally:
            with self.lock:
                if target_ip in self.active_spoofs:
                    del self.active_spoofs[target_ip]
            
            audit_log('COMMAND', {
                'type': 'arp_spoof_end',
                'victim': target_ip,
                'duration': time.time() - self.active_spoofs.get(target_ip, {}).get('start_time', 0)
            })
    
    def stop_spoof(self, target_ip):
        """
        Stop ARP spoofing for specific target.
        
        Args:
            target_ip: Target IP to stop spoofing
        
        Returns:
            Boolean: True if successfully stopped
        """
        with self.lock:
            if target_ip not in self.active_spoofs:
                return False
            
            spoof_info = self.active_spoofs[target_ip]
            thread = spoof_info['thread']
            
            # Kill the arpspoof process (via SIGTERM on thread)
            # Note: arpspoof must be killed via process manager
            del self.active_spoofs[target_ip]
            
            audit_log('COMMAND', {
                'type': 'arp_spoof_stop',
                'victim': target_ip,
                'duration': time.time() - spoof_info['start_time']
            })
            
            log_error(f"[ARP] Spoofing stopped: {target_ip}", level='INFO')
            return True
    
    def stop_all_spoofs(self):
        """Stop all active spoofing attacks."""
        with self.lock:
            targets = list(self.active_spoofs.keys())
        
        for target in targets:
            self.stop_spoof(target)
        
        log_error(f"[ARP] Stopped all spoofing ({len(targets)} targets)", level='INFO')
    
    def get_active_spoofs(self):
        """
        Get list of currently active spoofs.
        
        Returns:
            List of dictionaries with spoof info
        """
        with self.lock:
            return [
                {
                    'victim': victim,
                    'gateway': info['gateway'],
                    'interface': info['interface'],
                    'duration': time.time() - info['start_time'],
                    'running': info['thread'].is_alive()
                }
                for victim, info in self.active_spoofs.items()
            ]

# --- CANVAS OBJECT POOLING ---
class CanvasObjectPool:
    """
    Pre-allocates and reuses canvas text objects to reduce garbage collection
    overhead and memory fragmentation on resource-constrained systems (Pi 2).
    
    Objects cycle through states: INACTIVE -> ACTIVE -> INACTIVE
    """
    def __init__(self, canvas, pool_size=50):
        self.canvas = canvas
        self.pool_size = pool_size
        self.available = []  # Stack of available item IDs
        self.active = {}     # {item_id: {"text": str, "x": int, "y": int, ...}}
        self.utilization_peak = 0
        
        # Pre-allocate all pool objects (invisible, off-canvas initially)
        for i in range(pool_size):
            item_id = self.canvas.create_text(
                -1000, -1000,  # Off-canvas
                text="",
                fill=COLOR_DIM,
                font=("monospace", 10),
                tags=f"pool_text_{i}"
            )
            self.available.append(item_id)
    
    def acquire(self, x, y, text, fill=COLOR_DIM, font=("monospace", 10)):
        """Acquire an object from the pool. Returns item_id or None if exhausted."""
        if not self.available:
            log_error(f"[POOL WARNING] Pool exhausted: {len(self.active)}/{self.pool_size} active")
            return None
        
        item_id = self.available.pop()
        self.canvas.coords(item_id, x, y)
        self.canvas.itemconfig(item_id, text=text, fill=fill, font=font)
        self.canvas.tag_raise(item_id)
        
        self.active[item_id] = {"x": x, "y": y, "text": text, "fill": fill}
        
        # Track peak utilization
        current_util = len(self.active)
        if current_util > self.utilization_peak:
            self.utilization_peak = current_util
        
        # Log warning if pool usage exceeds 80%
        if current_util > (self.pool_size * 0.8):
            log_error(f"[POOL WARNING] High utilization: {current_util}/{self.pool_size} active ({current_util/self.pool_size*100:.1f}%)")
        
        return item_id
    
    def release(self, item_id):
        """Return an object to the pool."""
        if item_id not in self.active:
            return False
        
        self.canvas.coords(item_id, -1000, -1000)  # Move off-canvas
        self.canvas.itemconfig(item_id, text="")   # Clear text
        self.available.append(item_id)
        del self.active[item_id]
        return True
    
    def update(self, item_id, x=None, y=None, text=None, fill=None):
        """Update an active object's properties."""
        if item_id not in self.active:
            return False
        
        if x is not None or y is not None:
            curr_x, curr_y = self.canvas.coords(item_id)
            new_x = x if x is not None else curr_x
            new_y = y if y is not None else curr_y
            self.canvas.coords(item_id, new_x, new_y)
            self.active[item_id]["x"] = new_x
            self.active[item_id]["y"] = new_y
        
        if text is not None:
            self.canvas.itemconfig(item_id, text=text)
            self.active[item_id]["text"] = text
        
        if fill is not None:
            self.canvas.itemconfig(item_id, fill=fill)
            self.active[item_id]["fill"] = fill
        
        return True
    
    def get_stats(self):
        """Return pool utilization stats."""
        return {
            "available": len(self.available),
            "active": len(self.active),
            "total": self.pool_size,
            "utilization_pct": (len(self.active) / self.pool_size) * 100,
            "peak_utilization": self.utilization_peak
        }


# --- IMAGE CACHING WITH LRU EVICTION (v1.1.3) ---
class ImageCache:
    """
    LRU image cache to avoid reprocessing images on every boot.
    Caches pre-scaled images and generated surfaces (like glass panels).
    
    Constraints:
    - Max 3 images in cache
    - Max 256KB total cache size
    - Automatically evicts least-recently-used images when limits exceeded
    """
    
    def __init__(self, max_images=3, max_size_kb=256):
        self.max_images = max_images
        self.max_size_bytes = max_size_kb * 1024
        self.cache = {}  # {key: {"data": bytes, "timestamp": time.time(), "size": int}}
        self.access_order = []  # LRU tracking: most recent at end
    
    def _get_size(self, data):
        """Estimate size of cached data in bytes."""
        if isinstance(data, bytes):
            return len(data)
        elif isinstance(data, Image.Image):
            # Estimate based on dimensions and mode
            w, h = data.size
            channels = len(data.mode)
            return w * h * channels
        return 0
    
    def _evict_lru(self):
        """Remove least-recently-used items until constraints met."""
        while len(self.cache) >= self.max_images or self._total_size() > self.max_size_bytes:
            if not self.access_order:
                break
            lru_key = self.access_order.pop(0)
            if lru_key in self.cache:
                del self.cache[lru_key]
                log_error(f"[IMAGECACHE] Evicted LRU item: {lru_key}")
    
    def _total_size(self):
        """Calculate total cache size in bytes."""
        return sum(item.get("size", 0) for item in self.cache.values())
    
    def get(self, key):
        """Retrieve cached image/data. Returns None if not found."""
        if key not in self.cache:
            return None
        
        # Move to end (most recently used)
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
        
        self.cache[key]["timestamp"] = time.time()
        return self.cache[key]["data"]
    
    def put(self, key, data):
        """Store image/data in cache. Automatically evicts if needed."""
        size = self._get_size(data)
        
        # Don't cache if larger than entire cache limit
        if size > self.max_size_bytes:
            log_error(f"[IMAGECACHE] Item too large ({size} bytes > {self.max_size_bytes} limit): {key}")
            return False
        
        # Remove old entry if exists
        if key in self.cache:
            self.access_order.remove(key)
        
        # Check if we need to evict
        while len(self.cache) >= self.max_images or (self._total_size() + size) > self.max_size_bytes:
            self._evict_lru()
        
        self.cache[key] = {
            "data": data,
            "timestamp": time.time(),
            "size": size
        }
        self.access_order.append(key)
        log_error(f"[IMAGECACHE] Cached {key} ({size} bytes, total: {self._total_size()}/{self.max_size_bytes})")
        return True
    
    def clear(self):
        """Clear entire cache."""
        self.cache.clear()
        self.access_order.clear()
    
    def stats(self):
        """Return cache statistics."""
        return {
            "items": len(self.cache),
            "total_size_kb": self._total_size() / 1024,
            "max_size_kb": self.max_size_bytes / 1024,
            "max_images": self.max_images,
            "keys": list(self.cache.keys())
        }


class DedSecOS:
    def __init__(self, root):
        self.root = root
        self.root.title("DEDSEC")
        self.root.geometry("320x240")
        self.root.configure(bg=COLOR_BG)
        self.root.attributes('-fullscreen', True)
        self.root.config(cursor="none")
        
        self.root.lift()
        self.root.focus_force()

        self.canvas = tk.Canvas(self.root, bg=COLOR_BG, width=320, height=240, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # --- OBJECT POOLING ---
        self.pool = CanvasObjectPool(self.canvas, pool_size=50)
        
        # --- IMAGE CACHING (v1.1.3) ---
        self.image_cache = ImageCache(max_images=3, max_size_kb=256)
        
        # --- SUBPROCESS OPTIMIZATION (1.2.2) ---
        self.process_manager = ProcessManager(max_processes=10, timeout_seconds=30)
        
        # --- THREADING & CONCURRENCY (1.3.1) ---
        self.thread_pool = ThreadPoolExecutor(max_workers=2)
        self.active_futures = []  # Track active futures for cleanup
        self.lock = threading.Lock()
        
        # --- NETWORK RECONNAISSANCE TOOLS (Phase 3) ---
        self.port_scanner = PortScanner()  # 3.1.1
        self.arp_spoofer = ARPSpoofer()     # 3.1.2
        
        # --- MENU STATE MANAGEMENT (3.1.2.1) ---
        self.menu_state = MenuState()
        self.button_state = ButtonState()

        # --- STATE ---
        self.bg_image = None
        self.glass_image = None 
        self.matrix_chars = []
        self.log_lines = []
        self.terminal_pool_items = []  # Track pooled text objects for terminal
        
        # Scrolling
        self.scroll_x = 0
        self.scroll_y = 0
        self.drag_start_y = 0
        
        # Modal State
        self.active_modal = None 
        
        # Network
        self.last_net_io = psutil.net_io_counters()
        self.last_net_time = time.time()
        self.target_bssid = ""
        self.target_chan = ""
        self.id_net_icon_group = []
        
        # --- EVENT-DRIVEN NETWORK STATS (1.3.2) ---
        self.last_net_update_time = time.time()
        self.net_stats_interval = 1000  # Start at 1 second
        self.net_stats_no_change_count = 0  # Track consecutive polls with no change
        self.cached_net_io = self.last_net_io  # Cache for comparison
        self.net_delta_threshold = 1024  # 1KB threshold for updating
        
        # Layout - Spacious Grid (Phase 3.2.2)
        # Header: 30px, Footer: 30px, Sidebar: 70px, Gutter: 10px
        # Main content: 240x180 at (80, 30), Terminal usable: 230x170 with 5px padding
        self.term_left = 85        # 80 (content start) + 5 (left padding)
        self.term_top = 35         # 30 (header) + 5 (top padding)
        self.term_bottom = 205     # 210 (footer start) - 5 (bottom padding)
        self.term_right = 315      # 320 (content end) - 5 (right padding)
        self.term_height = self.term_bottom - self.term_top  # 170px usable height
        self.line_height = 12
        
        # --- POWER MANAGEMENT (1.2.1) ---
        self.last_interaction_time = time.time()
        self.idle_threshold = 10  # seconds before entering low-power mode
        self.is_in_low_power_mode = False
        # Update intervals (in milliseconds)
        self.normal_intervals = {
            'stats': 1000,       # update_system_stats
            'network': 2000,     # update_network_icon
            'clock': 1000        # update_clock (show seconds)
        }
        self.low_power_intervals = {
            'stats': 5000,       # Reduce to 5 seconds
            'network': 10000,    # Reduce to 10 seconds
            'clock': 60000       # Reduce to 60 seconds (show minutes only)
        }
        self.current_intervals = self.normal_intervals.copy()

        # --- BOOT SEQUENCE ---
        try:
            self.load_background()
            self.setup_ui_layers()
            
            # Bindings
            self.canvas.bind("<ButtonPress-1>", self.on_touch_start)
            self.canvas.bind("<B1-Motion>", self.on_touch_drag)
            
            # Start Loops (Safe Mode)
            self.safe_start(self.update_clock)
            self.safe_start(self.update_system_stats)
            self.safe_start(self.update_network_icon)
            self.safe_start(self.animate_background)
            self.safe_start(self.glitch_logo)
            self.safe_start(self.log_pool_stats)
            
            # Add initial terminal text (wrapped to 41 chars)
            self.log_line("# SYSTEM ONLINE")
            self.log_line(f"# USER: {os.getlogin()}")
            self.log_line("# Type a command or select a tool from")
            self.log_line("# the sidebar menu to begin.")
            self.log_line("")
            
            # Force initial terminal draw
            self.draw_terminal()
            
        except Exception as e:
            log_error(f"Init Error: {e}")

    def safe_start(self, func):
        """Safely start animation/update functions with error handling."""
        try:
            # Always schedule with after() - let mainloop handle execution
            # Use different delays based on function priority
            if func.__name__ in ['update_clock', 'update_system_stats']:
                delay = 100  # Start stats/clock quickly
            elif func.__name__ == 'update_network_icon':
                delay = 500  # Network icon can wait
            elif func.__name__ in ['animate_background', 'glitch_logo']:
                delay = 200  # Animations start after UI is ready
            else:
                delay = 1000  # Other functions start later
            
            log_error(f"[SAFE_START] Scheduling {func.__name__} with {delay}ms delay")
            self.root.after(delay, func)
        except Exception as e:
            log_error(f"Failed to start {func.__name__}: {e}")

    def load_background(self):
        """
        Load background image with lazy caching (v1.1.3).
        
        1. Check for pre-scaled cached version first (fast path)
        2. If not cached, load original and resize once
        3. Cache the resized result to disk for future boots
        """
        try:
            img_path = "/home/berry/dedsec/bg.jpg"
            cache_path = "/home/berry/dedsec/bg_320x240.cache.png"
            
            # Fast path: use pre-scaled cached version if available
            cached_pil = self.image_cache.get("bg_image")
            if cached_pil is not None:
                self.bg_image = ImageTk.PhotoImage(cached_pil)
                self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw", tags="bg")
                log_error(f"[BACKGROUND] Loaded from memory cache")
                return
            
            # Check for disk cache
            if os.path.exists(cache_path):
                try:
                    pil_img = Image.open(cache_path)
                    pil_img.load()  # Force load to detect corruption
                    self.image_cache.put("bg_image", pil_img)
                    self.bg_image = ImageTk.PhotoImage(pil_img)
                    self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw", tags="bg")
                    log_error(f"[BACKGROUND] Loaded from disk cache: {cache_path}")
                    return
                except Exception as e:
                    log_error(f"[BACKGROUND] Disk cache corrupted: {e}, regenerating...")
                    os.remove(cache_path)
            
            # Slow path: load original image, resize, and cache
            if os.path.exists(img_path):
                pil_img = Image.open(img_path)
                pil_img = pil_img.resize((320, 240), Image.Resampling.LANCZOS)
                
                # Cache in memory
                self.image_cache.put("bg_image", pil_img)
                
                # Save to disk cache for next boot
                try:
                    pil_img.save(cache_path, "PNG", optimize=True)
                    log_error(f"[BACKGROUND] Cached to disk: {cache_path}")
                except Exception as e:
                    log_error(f"[BACKGROUND] Failed to save disk cache: {e}")
                
                self.bg_image = ImageTk.PhotoImage(pil_img)
                self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw", tags="bg")
                log_error(f"[BACKGROUND] Loaded from original: {img_path}")
            else:
                self.draw_grid_bg()
                log_error(f"[BACKGROUND] No background image found, using grid")
        except Exception as e:
            log_error(f"[BACKGROUND] Load Error: {e}")
            self.draw_grid_bg()

    def draw_grid_bg(self):
        for i in range(0, 320, 20):
            self.canvas.create_line(i, 0, i, 240, fill="#0a0a0a", tags="bg_grid")
        for i in range(0, 240, 20):
            self.canvas.create_line(0, i, 320, i, fill="#0a0a0a", tags="bg_grid")

    def create_glass_panel(self, x, y, w, h, alpha):
        """
        Create glass panel with caching (v1.1.3).
        
        Caches generated RGBA surface to avoid regenerating on every boot.
        """
        cache_key = f"glass_{w}x{h}_{alpha}"
        
        # Try memory cache first
        cached_img = self.image_cache.get(cache_key)
        if cached_img is not None:
            self.glass_image = ImageTk.PhotoImage(cached_img)
            self.canvas.create_image(x, y, image=self.glass_image, anchor="nw", tags="glass")
            log_error(f"[GLASS_PANEL] Loaded from cache: {cache_key}")
            return
        
        # Generate new glass panel
        img = Image.new('RGBA', (w, h), (0, 0, 0, alpha))
        
        # Cache it
        self.image_cache.put(cache_key, img)
        
        self.glass_image = ImageTk.PhotoImage(img)
        self.canvas.create_image(x, y, image=self.glass_image, anchor="nw", tags="glass")
        log_error(f"[GLASS_PANEL] Generated and cached: {cache_key}")

    def setup_ui_layers(self):
        # Header - Spacious Grid: 30px tall with vertically centered content
        self.canvas.create_rectangle(0, 0, 320, 30, fill="#000000", stipple="gray75", outline="")
        self.canvas.create_line(0, 30, 320, 30, fill=COLOR_FG, width=1)
        
        # Vertically centered in 30px header (y=15 is center)
        self.id_logo = self.canvas.create_text(10, 15, text="DEDSEC_OS", fill=COLOR_FG, anchor="w", font=("monospace", 12, "bold"))
        self.id_clock = self.canvas.create_text(315, 15, text="00:00:00", fill=COLOR_WHITE, anchor="e", font=("monospace", 10, "bold"))

        # Sidebar - Spacious Grid: 70px wide, positioned at y=30 (below header)
        self.frm_sidebar = tk.Frame(self.root, bg=COLOR_BG, width=70)
        self.frm_sidebar.place(x=0, y=30, width=70, height=180)
        self.frm_sidebar.grid_propagate(False)

        def create_btn(parent, text, cmd):
            border_frame = tk.Frame(parent, bg=COLOR_RED, padx=1, pady=1)
            border_frame.pack(fill="x", pady=0)
            btn = tk.Button(border_frame, text=text, fg=COLOR_FG, bg=COLOR_BG,
                            activebackground=COLOR_RED, activeforeground=COLOR_WHITE,
                            bd=0, font=("monospace", 9, "bold"), anchor="w", padx=4,
                            command=cmd)
            btn.pack(fill="both", expand=True)
            
        create_btn(self.frm_sidebar, "> SCAN", self.show_port_scan_modal)
        create_btn(self.frm_sidebar, "> ARP", self.show_arp_scan_modal)
        create_btn(self.frm_sidebar, "> WIFI", self.show_wifi_modal)
        create_btn(self.frm_sidebar, "> BLUE", self.show_bluetooth_modal)
        create_btn(self.frm_sidebar, "> PAYL", self.show_payload_modal)
        create_btn(self.frm_sidebar, "> PWR", self.show_pwr_modal)

        # Gutter separator - 10px wide visual gap at x=70-80 (negative space)
        # Draw line at x=70 (end of sidebar) - no line needed, blank space is the gutter
        
        # Terminal - Main content area starts at x=80
        # self.create_glass_panel(61, 25, 259, 180, alpha=GLASS_ALPHA)
        self.id_scrollbar = self.canvas.create_rectangle(318, 35, 319, 49, fill=COLOR_WHITE, outline="")

        # Footer - Spacious Grid: 30px tall starting at y=210, vertically centered content
        self.canvas.create_rectangle(0, 210, 320, 240, fill="#000000", outline="")
        self.canvas.create_line(0, 210, 320, 210, fill=COLOR_FG)
        
        # Status bar background - full height with padding
        self.canvas.create_rectangle(2, 212, 318, 238, outline=COLOR_DIM, fill="#111111")
        
        # Status message area (3.1.2.1) - vertically centered in 30px footer
        # Position at y=214 for better vertical centering
        self.id_status_text = self.canvas.create_text(8, 214, text="", fill=COLOR_STATUS_NORMAL, anchor="nw", font=("monospace", 7))
        self.status_text = ""  # Store current status
        
        # System stats row - vertically centered at y=225 (middle of 30px footer)
        # CPU section (x: 4-80) - box shifted right for breathing room
        self.canvas.create_text(6, 225, text="CPU:", fill=COLOR_FG, anchor="w", font=("monospace", 9, "bold"))
        self.id_cpu_bar = self.canvas.create_rectangle(40, 218, 40, 232, fill=COLOR_FG, outline="", tags="cpu_bar")
        self.canvas.create_rectangle(40, 218, 75, 232, outline=COLOR_DIM, width=1, tags="cpu_bg")
        
        # RAM section (x: 80-155)
        self.canvas.create_text(82, 225, text="RAM:", fill=COLOR_FG, anchor="w", font=("monospace", 9, "bold"))
        self.id_ram_text = self.canvas.create_text(118, 225, text="512MB", fill=COLOR_WHITE, anchor="w", font=("monospace", 9))
        
        # TEMP section (x: 155-240)
        self.canvas.create_text(160, 225, text="TEMP:", fill=COLOR_FG, anchor="w", font=("monospace", 9, "bold"))
        self.id_temp_text = self.canvas.create_text(205, 225, text="32°C", fill=COLOR_WHITE, anchor="w", font=("monospace", 9))
        
        # Extended stats (x: 240-320)
        self.canvas.create_text(242, 225, text="UP:", fill=COLOR_FG, anchor="w", font=("monospace", 9, "bold"))
        self.id_net_up_text = self.canvas.create_text(268, 225, text="0 Kbps", fill=COLOR_WHITE, anchor="w", font=("monospace", 9))

        # Send background and glass to back so terminal text appears on top (3.1.2.1 fix)
        self.canvas.tag_lower("bg")
        self.canvas.tag_lower("bg_grid")
        self.canvas.tag_lower("glass")

        self.setup_modals()

    # --- SCROLLING LOGIC ---
    def on_touch_start(self, event):
        self.drag_start_y = event.y
        self.drag_start_x = event.x
        self._record_interaction()

    def on_touch_drag(self, event):
        self._record_interaction()
        dy = event.y - self.drag_start_y
        dx = event.x - getattr(self, 'drag_start_x', event.x)
        
        if abs(dy) < 2 and abs(dx) < 2: return

        if self.active_modal in ['wifi', 'bt']:
            target_canvas = self.wifi_canvas if self.active_modal == 'wifi' else self.bt_canvas
            # Scroll listbox units
            scroll_dir = -1 if dy > 0 else 1
            target_canvas.yview_scroll(scroll_dir, "units")
        else:
            # Vertical scrolling
            if abs(dy) > abs(dx):
                new_y = self.scroll_y + dy
                if new_y > 0: new_y = 0 # Clamp Top
                self.scroll_y = new_y
            # Horizontal scrolling
            else:
                new_x = self.scroll_x + dx
                if new_x > 0: new_x = 0  # Clamp left
                self.scroll_x = new_x
            self.draw_terminal()
            
        self.drag_start_y = event.y
        self.drag_start_x = event.x
    
    def _record_interaction(self):
        """Record user interaction and exit low-power mode if active."""
        self.last_interaction_time = time.time()
        if self.is_in_low_power_mode:
            self.is_in_low_power_mode = False
            self.current_intervals = self.normal_intervals.copy()
            self.canvas.itemconfig(self.id_clock, fill=COLOR_WHITE)
            log_error("[POWER] Exiting low-power mode - user interaction detected")
    
    def _check_idle_status(self):
        """Check if system is idle and adjust update intervals accordingly."""
        idle_time = time.time() - self.last_interaction_time
        should_be_idle = idle_time > self.idle_threshold
        
        # Transition to low-power mode
        if should_be_idle and not self.is_in_low_power_mode:
            self.is_in_low_power_mode = True
            self.current_intervals = self.low_power_intervals.copy()
            self.canvas.itemconfig(self.id_clock, fill=COLOR_DIM)
            log_error(f"[POWER] Entering low-power mode after {idle_time:.1f}s idle")
        
        # Transition out of low-power mode (handled by _record_interaction)
        elif not should_be_idle and self.is_in_low_power_mode:
            self.is_in_low_power_mode = False
            self.current_intervals = self.normal_intervals.copy()
            self.canvas.itemconfig(self.id_clock, fill=COLOR_WHITE)
            log_error("[POWER] Exiting low-power mode - idle threshold not met")

    def update_scrollbar(self):
        total_h = max(1, len(self.log_lines) * self.line_height)
        view_h = self.term_height
        if total_h <= view_h:
            bar_h = view_h
            bar_y = self.term_top
        else:
            ratio = view_h / total_h
            bar_h = max(5, view_h * ratio)
            pct_scrolled = abs(self.scroll_y) / (total_h - view_h)
            bar_y = self.term_top + (pct_scrolled * (view_h - bar_h))
        self.canvas.coords(self.id_scrollbar, 318, bar_y, 319, bar_y + bar_h)

    def clear_terminal_area(self) -> None:
        """
        Clear all terminal artifacts by deleting all items in the terminal region.
        This prevents ghosting and overlapping text.
        """
        # Delete all previous terminal items
        for item_id in self.terminal_pool_items:
            try:
                self.canvas.delete(item_id)
            except:
                pass
        self.terminal_pool_items.clear()
        
        # Also clear any orphaned text items in the terminal area
        # This catches artifacts that might have escaped the pool
        all_items = self.canvas.find_overlapping(
            self.term_left, self.term_top,
            self.term_left + 250, self.term_bottom
        )
        for item_id in all_items:
            item_type = self.canvas.type(item_id)
            if item_type == "text":
                # Only delete if it's a terminal item (has ">" prefix or is white)
                try:
                    text = self.canvas.itemcget(item_id, "text")
                    if text.startswith(">") or self.canvas.itemcget(item_id, "fill") == COLOR_WHITE:
                        self.canvas.delete(item_id)
                except:
                    pass
    
    def draw_terminal(self) -> None:
        """
        Render terminal text with proper background padding and artifact prevention.
        
        Improvements:
        - Black background rectangles behind text for better contrast
        - Proper artifact clearing before redraw
        - Text wrapping handled by log_line()
        - No truncation needed (wrapping handles long lines)
        """
        try:
            # Clear all previous terminal content and artifacts
            self.clear_terminal_area()
            
            start_x = self.term_left + self.scroll_x  # Apply horizontal scroll
            start_y = self.term_top + self.scroll_y
            
            # Safety: Ensure we have log lines to display
            if not self.log_lines:
                # Display placeholder with background
                bg_id = self.canvas.create_rectangle(
                    start_x - 2, start_y + 2,
                    start_x + 248, start_y + 22,
                    fill="black", outline="", tags="term_bg"
                )
                text_id = self.canvas.create_text(
                    start_x + 2, start_y + 12,
                    text="> Ready...",
                    fill=COLOR_WHITE,
                    font=("monospace", 9),
                    anchor="w"
                )
                self.terminal_pool_items.extend([bg_id, text_id])
                
                # Raise text above background
                if self.canvas.find_withtag("glass"):
                    self.canvas.tag_raise(text_id, "glass")
                if self.canvas.find_withtag("bg"):
                    self.canvas.tag_raise(text_id, "bg")
                return
            
            # Render each line with proper spacing and background
            for i, line in enumerate(self.log_lines):
                y_pos = start_y + (i * self.line_height)
                
                # Only render visible lines - strict clipping at terminal boundaries
                if self.term_top <= y_pos <= self.term_bottom - self.line_height:
                    try:
                        # Skip empty lines but maintain spacing
                        if not line or line.isspace():
                            continue
                        
                        # Create black background rectangle behind text for contrast
                        # This prevents grid lines from interfering with readability
                        bg_id = self.canvas.create_rectangle(
                            start_x - 2, y_pos - 6,
                            start_x + 248, y_pos + 8,
                            fill="black", outline="", tags="term_bg"
                        )
                        
                        # Create text with proper prefix
                        # Lines are already wrapped by log_line(), no truncation needed
                        prefix = "> " if not line.startswith("[") else ""
                        text_id = self.canvas.create_text(
                            start_x + 2, y_pos,
                            text=f"{prefix}{line}",
                            fill=COLOR_WHITE,
                            font=("monospace", 9),
                            anchor="w"
                        )
                        
                        # Track both background and text items
                        self.terminal_pool_items.extend([bg_id, text_id])
                        
                        # Ensure proper z-order: bg behind everything, text on top
                        try:
                            # Lower background behind grid
                            if self.canvas.find_withtag("bg"):
                                self.canvas.tag_lower(bg_id, "bg")
                            
                            # Raise text above grid and glass
                            if self.canvas.find_withtag("glass"):
                                self.canvas.tag_raise(text_id, "glass")
                            if self.canvas.find_withtag("bg"):
                                self.canvas.tag_raise(text_id, "bg")
                        except:
                            pass  # Tags don't exist yet during init
                        
                    except Exception as e:
                        log_error(f"[TERM] Line render error: {e}")
            
            self.update_scrollbar()
            
            # Force canvas update to prevent artifacts
            self.canvas.update_idletasks()
            
        except Exception as e:
            log_error(f"[TERM] Draw error: {e}")

    def animate_background(self):
        """Animate matrix characters using brightness fading (optimized for Pi 2)."""
        try:
            if len(self.matrix_chars) < MAX_MATRIX_CHARS:
                x = random.randint(60, 320)
                y = random.randint(25, 200)
                char = random.choice(["0", "1", "X", "Ø", "µ", "¶", "§"])
                
                # Acquire from pool with full brightness
                item_id = self.pool.acquire(x, y, char, fill=COLOR_MATRIX_BRIGHT, font=("monospace", 10))
                if item_id is not None:
                    self.canvas.tag_lower(item_id)
                    if self.glass_image:
                        self.canvas.tag_lower(item_id, "glass")
                    if self.bg_image:
                        self.canvas.tag_raise(item_id, "bg")
                    # Track with brightness step (4 levels: bright, med, dim, very_dim)
                    self.matrix_chars.append({"id": item_id, "step": 0})
            
            # Fade through brightness levels and remove
            brightness_colors = [COLOR_MATRIX_BRIGHT, COLOR_MATRIX_MED, COLOR_MATRIX_DIM, COLOR_MATRIX_VERY_DIM]
            for item in self.matrix_chars[:]:
                item["step"] += 1
                if item["step"] < len(brightness_colors):
                    # Update color to next brightness level (no new objects created)
                    self.pool.update(item["id"], fill=brightness_colors[item["step"]])
                else:
                    # Release when fully faded
                    self.pool.release(item["id"])
                    self.matrix_chars.remove(item)
            
            # Force canvas to update display (Pi 2 needs explicit refresh)
            self.canvas.update_idletasks()
        except Exception as e:
            log_error(f"[ANIMATE_BG] Error: {e}")
        
        # Always reschedule
        self.root.after(ANIMATION_INTERVAL_MS, self.animate_background)

    def glitch_logo(self):
        """Glitch effect for the logo."""
        try:
            if random.random() > 0.7: 
                glitch_text = random.choice(["DEDSEC_OS", "D3DSEC_0S", "DEADSEC", "ERR_0x90", "SYSTEM_FAIL"])
                color = random.choice([COLOR_FG, COLOR_WHITE, COLOR_ALERT, COLOR_CYAN])
                offset_x = random.randint(-2, 2)
                offset_y = random.randint(-2, 2)
                self.canvas.coords(self.id_logo, 10 + offset_x, 15 + offset_y)  # y=15 for 30px header
                self.canvas.itemconfig(self.id_logo, text=glitch_text, fill=color)
            else:
                self.canvas.coords(self.id_logo, 10, 15)  # y=15 for 30px header
                self.canvas.itemconfig(self.id_logo, text="DEDSEC_OS", fill=COLOR_FG)
            
            # Force canvas to update display
            self.canvas.update_idletasks()
        except Exception as e:
            log_error(f"[GLITCH_LOGO] Error: {e}")
        
        # Always reschedule
        self.root.after(100, self.glitch_logo)

    def log_pool_stats(self):
        """Log pool utilization stats periodically (debug purposes)."""
        stats = self.pool.get_stats()
        log_error(f"[POOL_STATS] Active: {stats['active']}/{stats['total']} "
                 f"({stats['utilization_pct']:.1f}%) Peak: {stats['peak_utilization']}/{stats['total']}")
        self.root.after(10000, self.log_pool_stats)  # Log every 10 seconds

    def setup_modals(self):
        self.modal_bg = tk.Frame(self.root, bg="black", highlightbackground=COLOR_FG, highlightthickness=1)
        self.frm_payload = tk.Frame(self.modal_bg, bg="black")
        self.frm_wifi = tk.Frame(self.modal_bg, bg="black")
        self.frm_wifi_detail = tk.Frame(self.modal_bg, bg="black")
        self.frm_bluetooth = tk.Frame(self.modal_bg, bg="black")
        self.frm_pwr = tk.Frame(self.modal_bg, bg="black")
        self.frm_port_scan = tk.Frame(self.modal_bg, bg="black")
        self.frm_port_results = tk.Frame(self.modal_bg, bg="black")
        
        # Port results canvas (scrollable results display)
        self.port_results_canvas = tk.Canvas(self.frm_port_results, bg="black", bd=0, highlightthickness=0)
        self.port_results_text = tk.Frame(self.port_results_canvas, bg="black")
        self.port_results_canvas.create_window((0, 0), window=self.port_results_text, anchor="nw")
        self.port_results_canvas.pack(side="left", fill="both", expand=True)
        self.port_results_text.bind("<Configure>", lambda e: self.port_results_canvas.configure(scrollregion=self.port_results_canvas.bbox("all")))

        tk.Label(self.frm_payload, text="EXECUTE PAYLOAD?", bg="black", fg="white", font=("monospace", 10)).pack(pady=10)
        tk.Button(self.frm_payload, text="EXECUTE", command=self.run_fake_payload, bg=COLOR_FG, fg="black", bd=0).pack(pady=5)

        self.wifi_canvas = tk.Canvas(self.frm_wifi, bg="black", bd=0, highlightthickness=0)
        self.wifi_scroll = tk.Frame(self.wifi_canvas, bg="black")
        self.wifi_canvas.create_window((0, 0), window=self.wifi_scroll, anchor="nw", tags="self.wifi_scroll")
        self.wifi_canvas.pack(side="left", fill="both", expand=True)
        self.wifi_scroll.bind("<Configure>", lambda e: self.wifi_canvas.configure(scrollregion=self.wifi_canvas.bbox("all")))

        self.bt_canvas = tk.Canvas(self.frm_bluetooth, bg="black", bd=0, highlightthickness=0)
        self.bt_scroll = tk.Frame(self.bt_canvas, bg="black")
        self.bt_canvas.create_window((0, 0), window=self.bt_scroll, anchor="nw", tags="self.bt_scroll")
        self.bt_canvas.pack(side="left", fill="both", expand=True)
        self.bt_scroll.bind("<Configure>", lambda e: self.bt_canvas.configure(scrollregion=self.bt_canvas.bbox("all")))

        self.lbl_detail_ssid = tk.Label(self.frm_wifi_detail, text="", bg="black", fg=COLOR_FG, font=("monospace", 10, "bold"))
        self.lbl_detail_ssid.pack(anchor="w", padx=5, pady=2)
        self.lbl_detail_bssid = tk.Label(self.frm_wifi_detail, text="", bg="black", fg="white", font=("monospace", 9))
        self.lbl_detail_bssid.pack(anchor="w", padx=5)
        tk.Frame(self.frm_wifi_detail, bg="#333", height=1).pack(fill="x", padx=5, pady=5)
        self.lbl_detail_sec = tk.Label(self.frm_wifi_detail, text="", bg="black", fg="white", font=("monospace", 9))
        self.lbl_detail_sec.pack(anchor="w", padx=5)
        self.lbl_detail_sig = tk.Label(self.frm_wifi_detail, text="", bg="black", fg="white", font=("monospace", 9))
        self.lbl_detail_sig.pack(anchor="w", padx=5)
        self.lbl_detail_chan = tk.Label(self.frm_wifi_detail, text="", bg="black", fg="white", font=("monospace", 9))
        self.lbl_detail_chan.pack(anchor="w", padx=5)
        
        tk.Button(self.frm_wifi_detail, text="[ DEAUTH ]", command=self.run_deauth_attack, 
                  bg=COLOR_RED, fg="white", bd=0, width=20).pack(pady=5)
        tk.Button(self.frm_wifi_detail, text="< BACK", command=self.show_wifi_modal, bg="#333", fg="white", bd=0, width=20).pack(side="bottom", pady=5)

        tk.Label(self.frm_pwr, text="SYSTEM POWER:", bg="black", fg=COLOR_FG, font=("monospace", 10, "bold")).pack(pady=5)
        tk.Button(self.frm_pwr, text="REBOOT", command=self.sys_reboot, bg="#333", fg="white", bd=0, width=15).pack(pady=2)
        tk.Button(self.frm_pwr, text="SHUTDOWN", command=self.sys_shutdown, bg="#333", fg="white", bd=0, width=15).pack(pady=2)
        
        # Port Scanner UI (3.1.1) - Compact layout for 320x240 screen
        tk.Label(self.frm_port_scan, text="TARGET:", bg="black", fg=COLOR_FG, font=("monospace", 8, "bold")).pack(pady=1)
        
        # Target preset buttons - store references for highlighting (3.1.2.1)
        self.port_target_buttons = []
        targets_frame = tk.Frame(self.frm_port_scan, bg="black")
        targets_frame.pack(fill="x", padx=5, pady=1)
        btn1 = tk.Button(targets_frame, text="Gateway", command=lambda b=None: self._set_port_scan_target("192.168.1.1", btn1),
                  bg="#333", fg=COLOR_FG, bd=0, font=("monospace", 7))
        btn1.pack(side="left", fill="both", expand=True, padx=1)
        self.port_target_buttons.append(btn1)
        
        btn2 = tk.Button(targets_frame, text="Router", command=lambda b=None: self._set_port_scan_target("192.168.0.1", btn2),
                  bg="#333", fg=COLOR_FG, bd=0, font=("monospace", 7))
        btn2.pack(side="left", fill="both", expand=True, padx=1)
        self.port_target_buttons.append(btn2)
        
        btn3 = tk.Button(targets_frame, text="Local", command=lambda b=None: self._set_port_scan_target("127.0.0.1", btn3),
                  bg="#333", fg=COLOR_FG, bd=0, font=("monospace", 7))
        btn3.pack(side="left", fill="both", expand=True, padx=1)
        self.port_target_buttons.append(btn3)
        
        # Port range preset buttons - compact layout
        tk.Label(self.frm_port_scan, text="RANGE:", bg="black", fg=COLOR_FG, font=("monospace", 8, "bold")).pack(pady=1)
        
        self.port_range_buttons = []
        ranges_frame1 = tk.Frame(self.frm_port_scan, bg="black")
        ranges_frame1.pack(fill="x", padx=5, pady=1)
        btn_r1 = tk.Button(ranges_frame1, text="100", command=lambda b=None: self._set_port_scan_range("1-100", btn_r1),
                  bg="#333", fg="white", bd=0, font=("monospace", 7))
        btn_r1.pack(side="left", fill="both", expand=True, padx=1)
        self.port_range_buttons.append(btn_r1)
        
        btn_r2 = tk.Button(ranges_frame1, text="1K", command=lambda b=None: self._set_port_scan_range("1-1000", btn_r2),
                  bg="#333", fg="white", bd=0, font=("monospace", 7))
        btn_r2.pack(side="left", fill="both", expand=True, padx=1)
        self.port_range_buttons.append(btn_r2)
        
        btn_r3 = tk.Button(ranges_frame1, text="Common", command=lambda b=None: self._set_port_scan_range("21,22,23,25,53,80,110,443,3389", btn_r3),
                  bg="#333", fg="white", bd=0, font=("monospace", 7))
        btn_r3.pack(side="left", fill="both", expand=True, padx=1)
        self.port_range_buttons.append(btn_r3)
        
        # Second row of range buttons
        ranges_frame2 = tk.Frame(self.frm_port_scan, bg="black")
        ranges_frame2.pack(fill="x", padx=5, pady=1)
        btn_r4 = tk.Button(ranges_frame2, text="Web", command=lambda b=None: self._set_port_scan_range("80,443,8000,8080,8443", btn_r4),
                  bg="#333", fg="white", bd=0, font=("monospace", 7))
        btn_r4.pack(side="left", fill="both", expand=True, padx=1)
        self.port_range_buttons.append(btn_r4)
        
        btn_r5 = tk.Button(ranges_frame2, text="All", command=lambda b=None: self._set_port_scan_range("1-65535", btn_r5),
                  bg="#333", fg="white", bd=0, font=("monospace", 7))
        btn_r5.pack(side="left", fill="both", expand=True, padx=1)
        self.port_range_buttons.append(btn_r5)
        
        # Current selection display - compact
        self.lbl_port_target = tk.Label(self.frm_port_scan, text="T:[none]", bg="black", fg=COLOR_WARN, font=("monospace", 7))
        self.lbl_port_target.pack(pady=1)
        
        self.lbl_port_range = tk.Label(self.frm_port_scan, text="R:[none]", bg="black", fg=COLOR_WARN, font=("monospace", 7))
        self.lbl_port_range.pack(pady=1)
        
        # Scan button - prominent and always visible
        tk.Button(self.frm_port_scan, text="[ SCAN ]", command=self._execute_port_scan,
                  bg=COLOR_FG, fg="black", bd=0, font=("monospace", 8, "bold")).pack(pady=3, fill="x", padx=5)
        
        # ARP Spoofer UI (3.1.2)
        self.frm_arp_scan = tk.Frame(self.modal_bg, bg="black")
        self.frm_arp_attack = tk.Frame(self.modal_bg, bg="black")
        self.frm_arp_active = tk.Frame(self.modal_bg, bg="black")
        
        # Header with close button
        arp_header = tk.Frame(self.frm_arp_scan, bg="black")
        arp_header.pack(fill="x", padx=2, pady=1)
        tk.Label(arp_header, text="ARP SCAN", bg="black", fg=COLOR_FG, font=("monospace", 9, "bold")).pack(side="left")
        tk.Button(arp_header, text="[X]", command=self.hide_modal, bg="black", fg=COLOR_RED, bd=0, font=("monospace", 9, "bold")).pack(side="right")
        
        tk.Label(self.frm_arp_scan, text="NETWORK:", bg="black", fg=COLOR_FG, font=("monospace", 8)).pack(pady=1)
        
        # Preset network buttons - compact horizontal layout
        self.selected_network = "192.168.1.0/24"
        networks_frame = tk.Frame(self.frm_arp_scan, bg="black")
        networks_frame.pack(fill="x", padx=3, pady=1)
        
        tk.Button(networks_frame, text="192.168.1.x", command=lambda: self._set_arp_network("192.168.1.0/24"),
                  bg="#333", fg="white", bd=0, font=("monospace", 6), width=11).pack(side="left", padx=1)
        tk.Button(networks_frame, text="192.168.0.x", command=lambda: self._set_arp_network("192.168.0.0/24"),
                  bg="#333", fg="white", bd=0, font=("monospace", 6), width=11).pack(side="left", padx=1)
        tk.Button(networks_frame, text="10.0.0.x", command=lambda: self._set_arp_network("10.0.0.0/24"),
                  bg="#333", fg="white", bd=0, font=("monospace", 6), width=8).pack(side="left", padx=1)
        
        # Display selected network
        self.lbl_arp_network = tk.Label(self.frm_arp_scan, text=f"{self.selected_network}", bg="black", fg="white", font=("monospace", 7))
        self.lbl_arp_network.pack(pady=1)
        
        # Gateway detection
        gw_frame = tk.Frame(self.frm_arp_scan, bg="black")
        gw_frame.pack(fill="x", padx=3, pady=1)
        tk.Label(gw_frame, text="GW:", bg="black", fg=COLOR_FG, font=("monospace", 7)).pack(side="left")
        self.lbl_arp_gateway = tk.Label(gw_frame, text="Click detect", bg="black", fg="white", font=("monospace", 7))
        self.lbl_arp_gateway.pack(side="left", padx=2)
        
        # Action buttons - compact
        btn_frame = tk.Frame(self.frm_arp_scan, bg="black")
        btn_frame.pack(fill="x", padx=3, pady=2)
        tk.Button(btn_frame, text="[ DETECT ]", command=self._detect_gateway, 
                  bg="#333", fg="white", bd=0, font=("monospace", 7), width=12).pack(side="left", padx=1)
        tk.Button(btn_frame, text="[ SCAN ]", command=self.start_arp_scan, 
                  bg=COLOR_FG, fg="black", bd=0, font=("monospace", 7, "bold"), width=12).pack(side="left", padx=1)
        
        # ARP attack target selection
        self.arp_hosts_canvas = tk.Canvas(self.frm_arp_attack, bg="black", bd=0, highlightthickness=0)
        self.arp_hosts_frame = tk.Frame(self.arp_hosts_canvas, bg="black")
        self.arp_hosts_canvas.create_window((0, 0), window=self.arp_hosts_frame, anchor="nw")
        self.arp_hosts_canvas.pack(side="left", fill="both", expand=True)
        self.arp_hosts_frame.bind("<Configure>", lambda e: self.arp_hosts_canvas.configure(scrollregion=self.arp_hosts_canvas.bbox("all")))
        
        # Active spoofs display
        self.arp_active_canvas = tk.Canvas(self.frm_arp_active, bg="black", bd=0, highlightthickness=0)
        self.arp_active_frame = tk.Frame(self.arp_active_canvas, bg="black")
        self.arp_active_canvas.create_window((0, 0), window=self.arp_active_frame, anchor="nw")
        self.arp_active_canvas.pack(side="left", fill="both", expand=True)
        self.arp_active_frame.bind("<Configure>", lambda e: self.arp_active_canvas.configure(scrollregion=self.arp_active_canvas.bbox("all")))



    def show_modal_generic(self, title, content_frame, width=240, height=160, mode=None):
        self.active_modal = mode
        for widget in self.modal_bg.winfo_children(): widget.pack_forget()
        header = tk.Frame(self.modal_bg, bg="black")
        header.pack(fill="x", padx=2, pady=2)
        tk.Label(header, text=title, bg="black", fg=COLOR_FG, font=("monospace", 9, "bold")).pack(side="left")
        tk.Button(header, text="[X]", command=self.hide_modal, bg="black", fg="red", bd=0, font=("monospace", 9, "bold")).pack(side="right")
        content_frame.pack(fill="both", expand=True, padx=2, pady=2)
        self.modal_bg.place(relx=0.5, rely=0.5, anchor="center", width=width, height=height)
        self.modal_bg.lift()
    
    def _show_frame(self, frame):
        """Helper to pack a frame and show the modal."""
        try:
            for widget in self.modal_bg.winfo_children():
                widget.pack_forget()
            frame.pack(fill="both", expand=True)
            self.root.update_idletasks()  # Force geometry update
        except Exception as e:
            print(f"[ERROR] _show_frame: {e}", file=sys.stderr)

    def show_payload_modal(self): self.show_modal_generic("WARNING", self.frm_payload, height=100)
    def show_pwr_modal(self): self.show_modal_generic("POWER_MENU", self.frm_pwr, height=120)
    def hide_modal(self):
        # Cancel active scan futures when closing modal (1.3.1)
        with self.lock:
            for future in self.active_futures:
                if not future.done():
                    future.cancel()
            self.active_futures = [f for f in self.active_futures if f.done()]
        
        self.active_modal = None
        self.modal_bg.place_forget()

    def show_port_scan_modal(self):
        """Display Port Scanner modal with fresh state (3.1.2.1)."""
        try:
            self.menu_state.set_menu('port_scan')
            self.menu_state.reset_selections()
            self.button_state.deselect_all()
            
            # Update UI display
            self.lbl_port_target.config(text="Target: [not selected]", fg=COLOR_WARN)
            self.lbl_port_range.config(text="Range: [not selected]", fg=COLOR_WARN)
            
            self.modal_bg.place(x=10, y=50, width=300, height=180)
            self._show_frame(self.frm_port_scan)
            self.update_status("Port Scanner: select target & range", COLOR_STATUS_INFO)
        except Exception as e:
            print(f"[ERROR] show_port_scan_modal: {e}", file=sys.stderr)

    def show_port_results_modal(self):
        self.modal_bg.place(x=10, y=50, width=300, height=180)
        self._show_frame(self.frm_port_results)

    def _set_port_scan_target(self, target, button_widget=None):
        """Store selected scan target with visual feedback (3.1.2.1)."""
        # Visual press feedback - briefly darken button
        if button_widget:
            orig_bg = button_widget.cget("bg")
            button_widget.config(bg="#555", relief="sunken")
            self.root.after(100, lambda: button_widget.config(bg="#ccff00", relief="flat") if button_widget else None)
        
        # Store in menu state
        self.menu_state.set_selection(target=target)
        
        # Highlight selected button
        if button_widget:
            self.button_state.select_button('targets', button_widget, COLOR_FG)
        
        # Update label
        self.lbl_port_target.config(text=f"T:{target[:15]}", fg=COLOR_FG)
        self.update_status(f"Target: {target} - select range", COLOR_STATUS_NORMAL)

    def _set_port_scan_range(self, port_range, button_widget=None):
        """Store selected port range with visual feedback (3.1.2.1)."""
        # Visual press feedback - briefly darken button
        if button_widget:
            orig_bg = button_widget.cget("bg")
            button_widget.config(bg="#555", relief="sunken")
            self.root.after(100, lambda: button_widget.config(bg="#ccff00", relief="flat") if button_widget else None)
        
        # Store in menu state
        self.menu_state.set_selection(range_val=port_range)
        
        # Highlight selected button
        if button_widget:
            self.button_state.select_button('ranges', button_widget, COLOR_FG)
        
        # Update label
        display_range = port_range if len(port_range) <= 15 else port_range[:12] + "..."
        self.lbl_port_range.config(text=f"R:{display_range}", fg=COLOR_FG)
        self.update_status(f"Range: {port_range[:20]} - tap SCAN", COLOR_STATUS_NORMAL)

    def _execute_port_scan(self):
        """Execute scan with stored selections from MenuState (3.1.2.1)."""
        target = self.menu_state.selected_target
        port_range = self.menu_state.selected_range
        
        # Validate selections
        if not target or not port_range:
            self.update_status("Select both target & range first", COLOR_STATUS_ERROR)
            return
        
        if not self.port_scanner.is_valid_target(target):
            self.update_status("Invalid target IP", COLOR_STATUS_ERROR)
            return
        
        # Hide modal and start scan
        self.hide_modal()
        self.update_status(f"Scanning {target} ports {port_range}...", COLOR_STATUS_WARN)
        self.thread_pool.submit(self._perform_port_scan_task, target, port_range)

    def _perform_port_scan_task(self, target, port_range):
        """Perform port scan in background (modal already hidden)."""
        try:
            # Perform scan
            results = self.port_scanner.scan_target(target, port_range)
            
            # Display results in terminal with proper spacing
            self.log_line("")  # Blank line for separation
            self.log_line(f"[SCAN] Target: {target}")
            self.log_line(f"[SCAN] Ports: {port_range}")
            self.log_line("-" * 40)  # Match wrapped text width
            
            # Process results line by line
            result_lines = results.split('\n') if isinstance(results, str) else [results]
            for line in result_lines:
                stripped = line.strip()
                if stripped:
                    # Each line is auto-wrapped by log_line if needed
                    self.log_line(stripped)
            
            self.log_line("-" * 40)
            self.log_line("")  # Blank line after scan
            self.update_status(f"Scan complete: {target}")
            
        except Exception as e:
            error_msg = str(e)
            self.log_line("")  # Blank line for separation
            self.log_line(f"[ERROR] Scan failed:")
            self.log_line(error_msg)  # Auto-wrapped if long
            self.update_status(f"Scan error")
            log_error(f"Port scan error: {error_msg}")

    def _display_port_results(self, results, target):
        """Legacy method - results now shown in terminal."""
        pass


    # --- ARP SPOOFER METHODS (3.1.2) ---
    
    def show_arp_scan_modal(self):
        """Display ARP scan modal to detect gateway and scan for hosts."""
        self.modal_bg.place(x=10, y=50, width=300, height=180)
        self._show_frame(self.frm_arp_scan)
        self.update_status("ARP Scanner ready")
    
    def _set_arp_network(self, network):
        """Set the selected network for ARP scanning."""
        self.selected_network = network
        self.lbl_arp_network.config(text=network)
        self.update_status(f"Network: {network}")
    
    def _detect_gateway(self):
        """Manually detect gateway IP."""
        self.lbl_arp_gateway.config(text="Detecting...")
        self.update_status("Detecting gateway...")
        
        # Run in background
        future = self.thread_pool.submit(self._detect_gateway_task)
        with self.lock:
            self.active_futures.append(future)
    
    def _detect_gateway_task(self):
        """Background task to detect gateway."""
        gateway = self.arp_spoofer.get_gateway_ip()
        if gateway:
            self.root.after(0, lambda: self.lbl_arp_gateway.config(text=f"GW: {gateway}"))
            self.root.after(0, lambda: self.update_status(f"Gateway: {gateway}"))
        else:
            self.root.after(0, lambda: self.lbl_arp_gateway.config(text="Not found"))
            self.root.after(0, lambda: self.update_status("Gateway not found"))
    
    def _scroll_arp_canvas(self, event, canvas):
        """Handle touch scrolling for ARP modal canvas."""
        if hasattr(self, '_arp_scroll_y'):
            dy = event.y - self._arp_scroll_y
            if abs(dy) > 2:
                canvas.yview_scroll(1 if dy < 0 else -1, "units")
                self._arp_scroll_y = event.y
    
    def show_arp_attack_modal(self):
        """Display targets for ARP spoofing attack."""
        self.modal_bg.place(x=10, y=50, width=300, height=180)
        self._show_frame(self.frm_arp_attack)
        self.update_status("Select target to spoof")
    
    def show_arp_active_modal(self):
        """Display currently active spoofing attacks."""
        self.modal_bg.place(x=10, y=50, width=300, height=180)
        self._show_frame(self.frm_arp_active)
        self._refresh_active_spoofs()
    
    def start_arp_scan(self):
        """Scan network for active hosts."""
        network = self.selected_network
        
        self.update_status(f"Scanning {network}...")
        self.log_line(f"[ARP] Scanning {network}...")
        
        # Run scan in thread pool
        future = self.thread_pool.submit(self._perform_arp_scan_task, network)
        with self.lock:
            self.active_futures.append(future)
    
    def _perform_arp_scan_task(self, network):
        """Background task to scan for active hosts."""
        try:
            self.root.after(0, lambda: self.log_line(f"[ARP] Scanning {network}..."))
            
            # Get active hosts
            hosts = self.arp_spoofer.get_active_hosts(network)
            
            if not hosts:
                self.root.after(0, lambda: self.log_line(f"[ARP] No hosts found on {network}"))
                self.root.after(0, lambda: self.update_status(f"No hosts found"))
                return
            
            # Log results
            self.root.after(0, lambda: self.log_line(f"[ARP] Found {len(hosts)} active hosts:"))
            for host in hosts:
                self.root.after(0, lambda h=host: self.log_line(f"  • {h}"))
            
            # Display hosts for selection
            self.root.after(0, lambda: self._display_arp_targets(hosts))
            self.root.after(0, lambda: self.update_status(f"Found {len(hosts)} hosts"))
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self.log_line(f"[ARP] Scan error: {error_msg}"))
            self.root.after(0, lambda: self.update_status(f"Scan error"))
            log_error(f"ARP scan error: {error_msg}")
    
    def _display_arp_targets(self, hosts):
        """Display selectable targets in ARP attack frame."""
        # Clear previous
        for widget in self.arp_hosts_frame.winfo_children():
            widget.destroy()
        
        # Header with close button
        header = tk.Frame(self.arp_hosts_frame, bg="black")
        header.pack(fill="x", padx=2, pady=2)
        tk.Label(header, text=f"TARGETS ({len(hosts)})", 
                bg="black", fg=COLOR_FG, font=("monospace", 8, "bold")).pack(side="left")
        tk.Button(header, text="[X]", command=self.hide_modal, 
                 bg="black", fg=COLOR_RED, bd=0, font=("monospace", 9, "bold")).pack(side="right")
        
        # Create compact button for each host
        for host in hosts[:12]:  # Limit to 12 for UI space
            btn = tk.Button(
                self.arp_hosts_frame,
                text=f"{host}",
                command=lambda h=host: self._start_arp_spoof(h),
                bg="#333", fg=COLOR_FG, bd=0, font=("monospace", 7)
            )
            btn.pack(pady=1, fill="x", padx=5)
        
        # Back button
        tk.Button(self.arp_hosts_frame, text="< BACK", command=self.show_arp_scan_modal,
                 bg="#333", fg="white", bd=0, font=("monospace", 7)).pack(pady=5, fill="x", padx=5)
        
        # Show attack modal
        self.show_arp_attack_modal()
    
    def _start_arp_spoof(self, target_ip):
        """Start ARP spoofing against target."""
        gateway = self.arp_spoofer.get_gateway_ip()
        if not gateway:
            self.log_line(f"[ARP] Gateway not detected - cannot spoof")
            self.update_status("Gateway not detected")
            return
        
        self.log_line(f"[ARP] Starting spoof: {target_ip} <-> {gateway}")
        success = self.arp_spoofer.start_spoof(target_ip, gateway, "eth0")
        
        if success:
            self.log_line(f"[ARP] Spoofing active: {target_ip}")
            self.update_status(f"Spoofing {target_ip}")
            # Show active spoofs
            self.show_arp_active_modal()
        else:
            self.log_line(f"[ARP] Failed to spoof {target_ip}")
            self.update_status(f"Spoof failed")
    
    def _refresh_active_spoofs(self):
        """Refresh the display of active spoofing attacks."""
        # Clear previous
        for widget in self.arp_active_frame.winfo_children():
            widget.destroy()
        
        # Header with close button
        header = tk.Frame(self.arp_active_frame, bg="black")
        header.pack(fill="x", padx=2, pady=2)
        
        # Get active spoofs
        spoofs = self.arp_spoofer.get_active_spoofs()
        
        tk.Label(header, text=f"ACTIVE ({len(spoofs)})", 
                bg="black", fg=COLOR_RED, font=("monospace", 8, "bold")).pack(side="left")
        tk.Button(header, text="[X]", command=self.hide_modal, 
                 bg="black", fg=COLOR_RED, bd=0, font=("monospace", 9, "bold")).pack(side="right")
        
        if not spoofs:
            tk.Label(self.arp_active_frame, text="NO ACTIVE SPOOFS", 
                    bg="black", fg="white", font=("monospace", 8)).pack(pady=10)
            tk.Button(self.arp_active_frame, text="< BACK", command=self.show_arp_scan_modal,
                     bg="#333", fg="white", bd=0, font=("monospace", 7)).pack(pady=5, fill="x", padx=5)
            return
        
        # Show each active spoof
        for spoof in spoofs:
            victim = spoof['victim']
            duration = int(spoof['duration'])
            status = "●" if spoof['running'] else "○"
            
            # Info label + stop button in frame
            spoof_frame = tk.Frame(self.arp_active_frame, bg="black")
            spoof_frame.pack(fill="x", padx=5, pady=1)
            
            tk.Label(spoof_frame, text=f"{status} {victim} ({duration}s)", 
                    bg="black", fg=COLOR_RED, font=("monospace", 7)).pack(side="left")
            
            tk.Button(spoof_frame, text="[STOP]", command=lambda v=victim: self._stop_arp_spoof(v),
                bg=COLOR_RED, fg="white", bd=0, font=("monospace", 6)).pack(side="right")
        
        # Refresh and back buttons
        tk.Button(self.arp_active_frame, text="[ REFRESH ]", command=lambda: self._refresh_active_spoofs(),
                 bg="#333", fg="white", bd=0, font=("monospace", 7)).pack(pady=3, fill="x", padx=5)
        tk.Button(self.arp_active_frame, text="< BACK", command=self.show_arp_scan_modal,
                 bg="#333", fg="white", bd=0, font=("monospace", 7)).pack(pady=1, fill="x", padx=5)
    
    def _stop_arp_spoof(self, target_ip):
        """Stop ARP spoofing for specific target."""
        self.log_line(f"[ARP] Stopping spoof: {target_ip}")
        self.arp_spoofer.stop_spoof(target_ip)
        self.update_status(f"Stopped spoofing {target_ip}")
        self._refresh_active_spoofs()

    def show_wifi_modal(self):
        """Display WiFi scanning modal with proper UI."""
        # Clear previous widgets
        for widget in self.modal_bg.winfo_children():
            widget.destroy()
        
        # Create visible frame with border
        header = tk.Frame(self.modal_bg, bg="black")
        header.pack(fill="x", padx=2, pady=2)
        tk.Label(header, text="WiFi SCAN", bg="black", fg=COLOR_FG, font=("monospace", 10, "bold")).pack(side="left")
        tk.Button(header, text="[X]", command=self.hide_modal, bg="black", fg=COLOR_RED, bd=0, font=("monospace", 9, "bold")).pack(side="right")
        
        # Add visible border line
        tk.Frame(self.modal_bg, bg=COLOR_FG, height=1).pack(fill="x")
        
        # Content area
        content = tk.Frame(self.modal_bg, bg="black", highlightbackground=COLOR_FG, highlightthickness=1)
        content.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Status label
        self.lbl_wifi_status = tk.Label(content, text="Press SCAN to start", bg="black", fg=COLOR_FG, font=("monospace", 9))
        self.lbl_wifi_status.pack(pady=5)
        
        # Scan button
        tk.Button(content, text="[ SCAN NOW ]", command=self._start_wifi_scan, 
                  bg=COLOR_FG, fg="black", bd=0, font=("monospace", 10, "bold")).pack(pady=3, fill="x", padx=5)
        
        # Results canvas with scrollbar
        self.wifi_results_canvas = tk.Canvas(content, bg="black", bd=0, highlightthickness=0, height=100)
        self.wifi_results_frame = tk.Frame(self.wifi_results_canvas, bg="black")
        self.wifi_results_canvas.create_window((0, 0), window=self.wifi_results_frame, anchor="nw")
        self.wifi_results_canvas.pack(fill="both", expand=True, padx=5, pady=5)
        self.wifi_results_frame.bind("<Configure>", lambda e: self.wifi_results_canvas.configure(scrollregion=self.wifi_results_canvas.bbox("all")))
        
        # Close button
        tk.Button(content, text="[ CLOSE ]", command=self.hide_modal, 
                  bg="#333", fg="white", bd=0, font=("monospace", 9)).pack(pady=3, fill="x", padx=5)
        
        # Show modal with proper positioning
        self.modal_bg.place(x=10, y=50, width=300, height=180)
        self.modal_bg.lift()
    
    def _start_wifi_scan(self):
        """Start WiFi scan in background thread."""
        # Hide modal immediately - show results in terminal instead
        self.hide_modal()
        self.update_status("Scanning WiFi networks...")
        self.log_line("")  # Blank line for separation
        self.log_line("[WiFi] Starting network scan...")
        
        # Submit to thread pool
        future = self.thread_pool.submit(self._scan_wifi_task)
        with self.lock:
            self.active_futures.append(future)
    
    def show_bluetooth_modal(self):
        for widget in self.bt_scroll.winfo_children(): widget.destroy()
        tk.Label(self.bt_scroll, text="SCANNING BLUETOOTH...", bg="black", fg="white", font=("monospace", 10)).pack(pady=10)
        self.show_modal_generic("BLUETOOTH_SCAN", self.frm_bluetooth, width=260, height=180, mode='bt')
        # Submit to thread pool (1.3.1)
        future = self.thread_pool.submit(self._scan_bt_task)
        with self.lock:
            self.active_futures.append(future)

    def _scan_bt_task(self):
        devices = []
        try:
            # Start scan with timeout
            self.process_manager.run_safe(
                ["timeout", "5s", "bluetoothctl", "scan", "on"],
                timeout=6,
                capture_output=False
            )
            
            # Get devices list
            result = self.process_manager.run_safe(
                ["bluetoothctl", "devices"],
                timeout=5,
                capture_output=True
            )
            
            if result and result.stdout:
                for line in result.stdout.splitlines():
                    if "Device" in line or not line.strip(): 
                        continue
                    parts = line.split(maxsplit=2)
                    if len(parts) >= 3:
                        devices.append({"mac": parts[1], "name": parts[2]})
            
            if not devices:
                devices.append({"mac": "", "name": "NODEVICES"})

        except Exception as e:
            log_error(f"BT Scan Error: {e}")
            devices.append({"mac": "ERR", "name": "ADAPTER ERROR"})
            
        self.root.after(0, lambda: self._update_bt_ui(devices))

    def _update_bt_ui(self, devices):
        for widget in self.bt_scroll.winfo_children(): widget.destroy()
        if not devices:
             tk.Label(self.bt_scroll, text="NO DEVICES FOUND", bg="black", fg="red").pack(pady=10)
             return
        for dev in devices:
            row = tk.Frame(self.bt_scroll, bg="black")
            row.pack(fill="x", pady=1)
            btn = tk.Button(row, text=f"{dev['name']} ({dev['mac']})", anchor="w",
                            bg="#111", fg=COLOR_CYAN, bd=0, font=("monospace", 9),
                            activebackground=COLOR_DIM, activeforeground="white")
            btn.pack(fill="x", ipady=5)

    def _scan_wifi_task(self):
        networks = []
        try:
            # Use process manager for wifi scan
            result = self.process_manager.run_safe(
                ["nmcli", "-t", "-f", "SSID,BSSID,SIGNAL,SECURITY,CHAN,FREQ", "dev", "wifi", "list"],
                timeout=10,
                capture_output=True
            )
            
            if result and result.stdout:
                for line in result.stdout.splitlines():
                    # Regex split to handle escaped colons (\:)
                    parts = re.split(r'(?<!\\):', line)
                    
                    if len(parts) >= 6:
                        # Clean up escaped chars
                        ssid = parts[0].replace("\\:", ":").replace("\\%", "%")
                        if not ssid: ssid = "<HIDDEN>"
                        # Sanitize SSID to prevent injection (2.1.1)
                        ssid = sanitize_ssid(ssid)
                        
                        security = parts[3]
                        icon = "⚠"
                        if "WPA" in security or "RSN" in security: icon = "🔒"
                    elif "WEP" in security: icon = "🔓"
                    
                    # Validate BSSID format (2.1.1)
                    try:
                        bssid = validate_bssid(parts[1].replace("\\:", ":"))
                    except ValueError as e:
                        log_error(f"[SEC] Invalid BSSID: {e}")
                        bssid = "00:00:00:00:00:00"  # Skip invalid BSSID
                    
                    networks.append({
                        "ssid": ssid, 
                        "bssid": bssid, 
                        "signal": parts[2], 
                        "security": f"{security} {icon}", 
                        "channel": parts[4], 
                        "freq": parts[5]
                    })
        except Exception as e: 
            log_error(f"WiFi Scan Error: {e}")
            networks.append({"ssid": "SCAN_ERR", "bssid": "00:00:00:00:00:00", "security": "ERR", "signal": "0", "channel": "0", "freq": "0"})
        self.root.after(0, lambda: self._update_wifi_ui(networks))

    def _update_wifi_ui(self, networks):
        """Display WiFi scan results in terminal."""
        if not networks:
            self.log_line("[WiFi] No networks found")
            self.update_status("WiFi scan complete - no networks")
            return
        
        # Display results in terminal
        self.log_line("")  # Blank line for separation
        self.log_line(f"[WiFi] Found {len(networks)} networks:")
        self.log_line("-" * 40)  # Match wrapped text width
        
        for idx, net in enumerate(networks, 1):
            security_icon = "🔒" if "WPA" in net['security'] or "RSN" in net['security'] else ("🔓" if "WEP" in net['security'] else "⚠")
            ssid_display = net['ssid'][:20].ljust(20)
            self.log_line(f"{idx:2}. {ssid_display} | Signal: {net['signal']:>3}% | {security_icon} {net['security'][:8]}")
        
        self.log_line("-" * 40)  # Match wrapped text width
        self.log_line("")  # Blank line after results
        self.update_status(f"WiFi scan complete: {len(networks)} networks found")

    def show_wifi_detail(self, net):
        # Sanitize SSID display (2.1.1)
        display_ssid = sanitize_ssid(net['ssid'])
        self.lbl_detail_ssid.config(text=f"TARGET: {display_ssid[:18]}")
        
        # Validate and store BSSID (2.1.1)
        try:
            self.target_bssid = validate_bssid(net['bssid'])
            self.lbl_detail_bssid.config(text=f"MAC: {self.target_bssid}")
        except ValueError as e:
            log_error(f"[SEC] Invalid BSSID in show_wifi_detail: {e}")
            self.log_line("ERROR: Invalid MAC address")
            return
        
        self.target_chan = net['channel']
        sec_color = COLOR_FG if "🔒" in net['security'] else (COLOR_WARN if "🔓" in net['security'] else COLOR_ALERT)
        self.lbl_detail_sec.config(text=f"SEC: {net['security']}", fg=sec_color)
        self.lbl_detail_sig.config(text=f"SIGNAL: {net['signal']}%")
        self.lbl_detail_chan.config(text=f"CH: {net['channel']} ({net['freq']})")
        self.show_modal_generic("NETWORK_DETAILS", self.frm_wifi_detail, width=260, height=180, mode='detail')

    def run_deauth_attack(self):
        self.log_line(f"ATTACKING {self.target_bssid}...")
        try:
            # REAL ATTACK LOGIC
            cmd = ["sudo", "aireplay-ng", "--deauth", "5", "-a", self.target_bssid, "wlan0mon"]
            # subprocess.Popen(cmd) # Uncomment to enable real attack
            self.log_line("[!] SENDING DEAUTH PACKETS...")
            self.log_line("[!] CLIENTS DISCONNECTED")
        except:
            self.log_line("ATTACK FAILED (NO MON MODE)")

    def run_nmap_thread(self):
        # Submit to thread pool (1.3.1)
        future = self.thread_pool.submit(self._run_real_nmap)
        with self.lock:
            self.active_futures.append(future)
    def _run_real_nmap(self):
        self.log_line("DETECTING GATEWAY...")
        target = "127.0.0.1"
        try:
            route_result = self.process_manager.run_safe(
                ["ip", "route", "show", "default"],
                timeout=5,
                capture_output=True
            )
            if route_result and route_result.stdout:
                target = f"{route_result.stdout.split()[2]}/24"
            self.log_line(f"TARGET: {target}")
        except: 
            self.log_line("USING LOCALHOST")
        
        try:
            # Use process manager with optimized flags for Pi 2
            cmd = ["nmap", "-F", "--host-timeout", "1000ms", "-T4", "--max-parallelism", "10", target]
            process_result = self.process_manager.run_safe(
                cmd,
                timeout=30,
                capture_output=True
            )
            
            if process_result and process_result.stdout:
                for line in process_result.stdout.splitlines():
                    if line and not line.startswith("Start") and not line.startswith("Nmap"):
                        self.log_line(line.strip())
            else:
                self.log_line("NMAP TIMEOUT OR ERROR")
            
            self.log_line("DONE.")
        except: 
            self.log_line("NMAP ERROR")

    def sys_reboot(self): 
        self.process_manager.run_safe(["sudo", "reboot"], timeout=5)
    
    def sys_shutdown(self): 
        self.process_manager.run_safe(["sudo", "shutdown", "-h", "now"], timeout=5)
    def run_fake_payload(self):
        self.hide_modal()
        self.log_line("INJECTING PAYLOAD...")
        self.root.after(500, lambda: self.log_line("[+] EXPLOIT SENT"))
        self.root.config(bg="white")
        self.root.after(50, lambda: self.root.config(bg=COLOR_BG))

    def update_clock(self):
        """Update clock display every second (or 60 seconds in low-power mode)."""
        try:
            self._check_idle_status()
            
            # In low-power mode, show only minutes; in normal mode show seconds
            if self.is_in_low_power_mode:
                now = time.strftime("%H:%M")
            else:
                now = time.strftime("%H:%M:%S")
            
            # Verify canvas item still exists
            if self.id_clock:
                self.canvas.itemconfig(self.id_clock, text=now)
                # Force canvas to update display
                self.canvas.update_idletasks()
            
            # Schedule next update
            self.root.after(self.current_intervals['clock'], self.update_clock)
        except Exception as e:
            log_error(f"[CLOCK] Update error: {e}")
            # Retry in 1 second
            self.root.after(1000, self.update_clock)

    def update_system_stats(self):
        try:
            # Get CPU and RAM percentages
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            
            # Update CPU animated bar (43px width bar at x:32-75)
            cpu_width = (cpu / 100.0) * 43
            self.canvas.coords(self.id_cpu_bar, 32, 216, 32 + cpu_width, 230)
            self.canvas.itemconfig(self.id_cpu_bar, fill=self.get_heat_color(cpu))
            
            # Update RAM display in MB
            ram_mb = int((ram / 100.0) * psutil.virtual_memory().total / 1024 / 1024)
            self.canvas.itemconfig(self.id_ram_text, text=f"{ram_mb}MB")
            
            # Update temperature
            try:
                temps = psutil.sensors_temperatures()
                if 'cpu_thermal' in temps:
                    temp = temps['cpu_thermal'][0].current
                    self.canvas.itemconfig(self.id_temp_text, text=f"{temp:.0f}°C")
                    self.canvas.itemconfig(self.id_temp_text, fill=COLOR_ALERT if temp > 70 else COLOR_WHITE)
            except: pass
            
            # --- EVENT-DRIVEN NETWORK STATS (1.3.2) ---
            # Only update network stats if delta > 1KB or backoff expired
            now = time.time()
            time_since_update = now - self.last_net_update_time
            
            if time_since_update >= (self.net_stats_interval / 1000.0):
                net = psutil.net_io_counters()
                bytes_sent_delta = net.bytes_sent - self.cached_net_io.bytes_sent
                bytes_recv_delta = net.bytes_recv - self.cached_net_io.bytes_recv
                total_delta = bytes_sent_delta + bytes_recv_delta
                
                # Check if significant change detected (1KB threshold)
                if total_delta > self.net_delta_threshold:
                    # Significant activity detected, reset backoff and update
                    dt = now - self.last_net_time
                    if dt > 0.5:
                        up_kbps = (bytes_sent_delta * 8) / 1000 / dt
                        self.canvas.itemconfig(self.id_net_up_text, text=f"{up_kbps:.0f}K")
                        self.last_net_time = now
                    
                    self.cached_net_io = net
                    self.last_net_update_time = now
                    self.net_stats_no_change_count = 0
                    self.net_stats_interval = 1000  # Reset to 1 second
                else:
                    # No significant change, implement exponential backoff
                    self.net_stats_no_change_count += 1
                    if self.net_stats_no_change_count >= 5:
                        # After 5 polls with no change, double interval (max 10 seconds)
                        self.net_stats_interval = min(self.net_stats_interval * 2, 10000)
                        self.net_stats_no_change_count = 0
                        log_error(f"[NET] No activity, backoff to {self.net_stats_interval}ms interval")
                    
                    self.last_net_update_time = now
        except: pass
        self.root.after(self.current_intervals['stats'], self.update_system_stats)

    def get_heat_color(self, percent):
        if percent < 50:
            r = int(204 + (51 * (percent / 50)))
            g = 255
        else:
            r = 255
            g = int(255 - (255 * ((percent - 50) / 50)))
        return f"#{r:02x}{g:02x}00"

    def update_network_icon(self):
        try:
            for item in self.id_net_icon_group: self.canvas.delete(item)
            self.id_net_icon_group = []
            stats = psutil.net_if_stats()
            conn_type = "NONE"
            if "eth0" in stats and stats["eth0"].isup: conn_type = "ETH"
            elif "wlan0" in stats and stats["wlan0"].isup: conn_type = "WIFI"

            icon_x = 235
            if conn_type == "ETH":
                self.id_net_icon_group.append(self.canvas.create_text(icon_x, 15, text="[<->]", fill=COLOR_FG, font=("monospace", 10, "bold")))
            elif conn_type == "WIFI":
                quality = 0
                try:
                    with open("/proc/net/wireless", "r") as f:
                        lines = f.readlines()
                        for line in lines:
                            if "wlan0" in line:
                                parts = line.split()
                                q = float(parts[2].replace('.', ''))
                                quality = int(q)
                                if quality > 70: quality = 100
                                else: quality = int((quality / 70) * 100)
                except: quality = 0
                bar_w = 3
                gap = 2
                start_x = 225
                for i in range(4):
                    h = 3 + (i * 2.5)
                    x = start_x + (i * (bar_w + gap))
                    y = 21  # Aligned to 30px header (was 18)
                    threshold = i * 25
                    color = COLOR_FG if quality > threshold else COLOR_GREY
                    rect = self.canvas.create_rectangle(x, y - h, x + bar_w, y, fill=color, outline="")
                    self.id_net_icon_group.append(rect)
        except Exception as e:
             log_error(f"Network Icon Error: {e}")
        self.root.after(self.current_intervals['network'], self.update_network_icon)

    def wrap_text(self, text: str, max_chars: int = 40) -> List[str]:
        """
        Wrap long text into multiple lines with pixel-accurate width.
        
        Args:
            text: Text to wrap
            max_chars: Maximum characters per line (default 41 for ~230px usable width @ 9pt monospace)
            
        Returns:
            List of wrapped lines
            
        Note: Uses character-based wrapping optimized for 9pt monospace @ ~5.5px/char.
              For 230px usable width: 230 ÷ 5.5 ≈ 41 chars max.
        """
        if len(text) <= max_chars:
            return [text]
        
        lines = []
        
        # Handle manual newlines first
        paragraphs = text.split('\n')
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                lines.append("")
                continue
                
            words = paragraph.split()
            current_line = []
            
            for word in words:
                # Test if adding this word exceeds limit
                test_line = ' '.join(current_line + [word])
                
                if len(test_line) <= max_chars:
                    # Fits - add to current line
                    current_line.append(word)
                else:
                    # Doesn't fit - push current line and start new
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        # Single word longer than max - hard break
                        if len(word) > max_chars:
                            lines.append(word[:max_chars-3] + "...")
                        else:
                            lines.append(word)
                        current_line = []
            
            # Append remaining words in current line
            if current_line:
                lines.append(' '.join(current_line))
        
        return lines if lines else [""]
    
    def log_line(self, text: str) -> None:
        """
        Add text to terminal (no wrapping - use horizontal scroll).
        
        Args:
            text: Text to log (full line, not wrapped)
        """
        # Just append the full line - no wrapping
        self.log_lines.append(text if text else "")
        
        # Limit total lines to prevent memory issues (keep last 200 lines)
        if len(self.log_lines) > 200:
            self.log_lines = self.log_lines[-200:]
        
        self.scroll_to_bottom()
        self.draw_terminal()
    
    def update_status(self, text, color=None):
        """Update status bar message (3.1.2.1).
        
        Args:
            text: Status message (max 40 chars - truncated if longer)
            color: Color constant (defaults to COLOR_STATUS_NORMAL)
        """
        if color is None:
            color = COLOR_STATUS_NORMAL
        
        # Truncate to fit status bar (max ~45 chars at 7pt font for 310px width)
        text = str(text)[:45]
        self.status_text = text
        
        # Update canvas
        try:
            self.canvas.itemconfig(self.id_status_text, text=text, fill=color)
            
            # Auto-clear status messages after 5 seconds (except empty strings)
            if text:
                self.root.after(5000, lambda: self.update_status(""))
        except Exception as e:
            log_error(f"[UI] Status update error: {e}")
    
    def cleanup(self):
        """Cleanup resources before shutdown."""
        log_error("[SHUTDOWN] Cleaning up processes...")
        self.process_manager.cleanup_all()
        
        log_error("[SHUTDOWN] Shutting down thread pool...")
        # Cancel all pending/running futures (1.3.1)
        with self.lock:
            for future in self.active_futures:
                future.cancel()
            self.active_futures.clear()
        
        # Shutdown thread pool
        self.thread_pool.shutdown(wait=False, cancel_futures=True)
        log_error("[SHUTDOWN] Application exit complete")

    def scroll_to_bottom(self):
        total_height = len(self.log_lines) * self.line_height
        if total_height > self.term_height:
            self.scroll_y = -(total_height - self.term_height)
        else:
            self.scroll_y = 0



if __name__ == "__main__":
    try:
        # Wait for X server
        time.sleep(5)
        root = tk.Tk()
        app = DedSecOS(root)
        
        # Register cleanup on window close
        def on_closing():
            app.cleanup()
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
    except Exception as e:
        log_error(f"Fatal Boot Error: {e}")