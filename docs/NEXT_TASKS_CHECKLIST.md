# Implementation Checklist: Sections 2.1.2 → 2.1.3

## Next Immediate Tasks (Prioritized)

### ✅ COMPLETED
- [x] 2.1.1 BSSID/MAC Address Validation - DEPLOYED
- [x] validate_bssid() function
- [x] Integration in _scan_wifi_task()
- [x] Integration in show_wifi_detail()

---

## TODO: Next 3 Tasks (In Order)

### Task 1: 2.1.2 SSID Sanitization Enhancement
**Status**: READY TO IMPLEMENT  
**Estimated Time**: 1-1.5 hours  
**Difficulty**: Easy  

**What to do**:
- Enhance sanitize_ssid() function (already in code)
- Add shell metacharacter escaping
- Test with malicious SSID patterns
- Deploy and verify

**Code Location**: app_v1_1_2_5.py, lines 64-82  
**Integration Points**:
- _scan_wifi_task() - already integrated
- show_wifi_detail() - already integrated

**Testing**:
- Test with SSID: `Network\x00;ls -la`
- Test with SSID: `Test$(whoami)`
- Test with 100+ char SSID (should truncate to 32)
- Verify display doesn't crash UI

---

### Task 2: 2.1.3 Path Traversal Prevention
**Status**: READY TO IMPLEMENT  
**Estimated Time**: 1.5-2 hours  
**Difficulty**: Medium  

**What to do**:
1. Create SAFE_PATHS dictionary at top of file:
```python
SAFE_PATHS = {
    'logs': '/home/berry/dedsec/logs/',
    'cache': '/home/berry/dedsec/cache/',
    'exports': '/home/berry/dedsec/exports/',
}
```

2. Create get_safe_path() function:
```python
def get_safe_path(category, filename):
    if category not in SAFE_PATHS:
        raise ValueError(f"Invalid path category: {category}")
    filename = os.path.basename(filename)  # Strip any ../ attempts
    return os.path.join(SAFE_PATHS[category], filename)
```

3. Replace all file operations:
- log_error() - already uses hardcoded path, OK
- Config reads - check if any dynamic paths
- Export functions - use get_safe_path('exports', filename)

**Code Location**: app_v1_1_2_5.py, top-level functions + ProcessManager  
**Integration Points**:
- log_error() function
- Configuration loading
- Export functions (future)

**Testing**:
- Test: get_safe_path('logs', '../../../etc/passwd') → should fail or sanitize
- Test: get_safe_path('logs', 'test.log') → /home/berry/dedsec/logs/test.log ✓
- Test: Invalid category → ValueError raised
- Verify all file ops use validated paths

---

### Task 3: 2.2 Privilege Separation & Sandboxing
**Status**: READY TO IMPLEMENT  
**Estimated Time**: 2-2.5 hours  
**Difficulty**: Medium  

**Subtasks**:

#### 2.2.1 Sudo Token Caching (1-1.5 hrs)
**What to do**:
1. Add CONFIG setting: `REQUIRE_SUDO_PASSWORD = False` (default)
2. Create on-startup prompt dialog:
   - Show modal asking for sudo password (if REQUIRE_SUDO_PASSWORD = True)
   - Store in memory-only: `self.sudo_password`
   - Auto-clear after 900 seconds (15 min)
3. Create use_sudo() helper:
```python
def use_sudo(self, cmd):
    if self.sudo_password:
        # Use echo password | sudo -S
        full_cmd = f"echo '{self.sudo_password}' | sudo -S {cmd}"
    else:
        full_cmd = f"sudo {cmd}"
    return subprocess.run(full_cmd, shell=True, ...)
```

#### 2.2.2 Drop Root Privileges (0.5-1 hr)
**What to do**:
1. At app startup, check: `if os.getuid() == 0:`
2. If root, execute privileged operations (monitor mode setup, etc.)
3. Drop privileges: `os.setuid(1000)`  # berry user
4. Add error handling for permission denied

---

## Implementation Priority

**High Priority** (Start with these):
1. ✅ 2.1.1 BSSID Validation (COMPLETE)
2. ⏳ 2.1.2 SSID Sanitization (Quick win, 1-1.5 hrs)
3. ⏳ 2.1.3 Path Traversal (2 hrs, security critical)

**Medium Priority** (After above):
4. 2.2 Privilege Separation (2-2.5 hrs)
5. 2.4 Logging & Audit Trail (1.5-2 hrs)
6. 5.1 Code Organization (4-5 hrs)

**Lower Priority** (Parallel/Later):
7. 2.3 Subprocess Security (already partially done)
8. 4.1 Configuration System
9. 11 UI/UX Redesign

---

## Quick Command Reference

**Deploy to device**:
```bash
scp /home/cachy/dedsec/app_v1_1_2_5.py berry@berry:/home/berry/dedsec/app_v1_1_2_5.py
```

**Verify compilation**:
```bash
ssh berry@berry "python3 -m py_compile /home/berry/dedsec/app_v1_1_2_5.py && echo OK"
```

**Check syntax locally**:
```bash
python3 -m py_compile /home/cachy/dedsec/app_v1_1_2_5.py
```

---

## Dependency Check

**Before starting 2.1.2**:
- ✅ sanitize_ssid() function exists? YES (lines 64-82)
- ✅ Applied in _scan_wifi_task()? YES
- ✅ Applied in show_wifi_detail()? YES

**Before starting 2.1.3**:
- ✅ SAFE_PATHS pattern understood? YES (whitelist approach)
- ✅ os.path.basename() imported? YES (os module imported)
- ✅ All file ops identified? NEED TO SCAN

**Before starting 2.2.1**:
- ✅ Tkinter simple dialog available? YES (tk.simpledialog)
- ✅ Threading for auto-clear available? YES (self.root.after)
- ✅ subprocess module available? YES

---

## Notes

- 2.1.2 is partially done - just needs enhancement to escaping logic
- 2.1.3 is blocked until we identify all file operations in code
- 2.2.1 is optional for now (current: no password required)
- All changes maintain backward compatibility
- Device is updated with 2.1.1 already

---

**Next: Decide on 2.1.2 vs 2.1.3 or implement both in sequence?**

