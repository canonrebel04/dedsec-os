## Phase 2 Roadmap: Advanced Object Pooling Optimizations

After Phase 1 (completed), the following optimizations can further improve performance on Pi 2.

---

## Phase 2.1: Terminal Text Dirty Rectangle Tracking

**Current behavior:** Every scroll/log event releases ALL terminal text items and reacquires only visible ones.

**Optimization:** Track which items are still visible after scroll and update them in-place.

```python
def draw_terminal_optimized(self):
    """Render terminal with dirty rectangle tracking."""
    start_x = self.term_left
    start_y = self.term_top + self.scroll_y
    
    # Build set of currently visible line indices
    visible_indices = set()
    for i, line in enumerate(self.log_lines):
        y_pos = start_y + (i * self.line_height)
        if self.term_top - 10 < y_pos < self.term_bottom + 5:
            visible_indices.add(i)
    
    # Release items for no-longer-visible lines
    old_items = self.terminal_pool_items.copy()
    for item_id in old_items:
        # Determine which line this was for (need reverse mapping)
        # If line no longer visible, release it
        pass
    
    # Update in-place or acquire new items as needed
    for i in visible_indices:
        line = self.log_lines[i]
        y_pos = start_y + (i * self.line_height)
        # Check if we already have item for this line
        # If yes, update coords + text
        # If no, acquire from pool
        pass
```

**Benefits:**
- Partial scrolls: 70% reduction in acquire/release operations
- Full terminal scroll: Same as Phase 1 (release all, reacquire all)
- Memory: Identical (50 objects)
- Complexity: +30 lines, moderate

**Difficulty:** Medium | **Time:** 1-2 hours | **Impact:** High

---

## Phase 2.2: Network Icon Reuse

**Current behavior:** Network icon (5 items: bars + text) recreated every 2 seconds.

**Current code location:** `update_network_icon()` method

**Optimization:**
```python
def __init__(self):
    # Pre-create network icon items once
    self.id_net_bar1 = self.pool.acquire(165, 209, "I", COLOR_DIM)
    self.id_net_bar2 = self.pool.acquire(170, 209, "I", COLOR_DIM)
    self.id_net_bar3 = self.pool.acquire(175, 209, "I", COLOR_DIM)
    self.id_net_icon_text = self.pool.acquire(190, 209, "OK", COLOR_FG)

def update_network_icon(self):
    # Instead of delete + create, just update colors
    bars_to_fill = self.get_signal_strength()
    
    color1 = COLOR_FG if bars_to_fill >= 1 else COLOR_DIM
    color2 = COLOR_FG if bars_to_fill >= 2 else COLOR_DIM
    color3 = COLOR_FG if bars_to_fill >= 3 else COLOR_DIM
    
    self.pool.update(self.id_net_bar1, fill=color1)
    self.pool.update(self.id_net_bar2, fill=color2)
    self.pool.update(self.id_net_bar3, fill=color3)
    self.pool.update(self.id_net_icon_text, text=signal_text)
```

**Benefits:**
- 5 fewer acquire/release per 2 seconds
- Eliminates network icon flicker
- Clean up current code

**Difficulty:** Easy | **Time:** 30 mins | **Impact:** Low-Medium

---

## Phase 2.3: Dynamic Pool Sizing

**Current behavior:** Fixed pool size of 50.

**Optimization:** Monitor peak utilization and grow pool if needed.

```python
class CanvasObjectPool:
    def __init__(self, canvas, initial_size=50, max_size=200):
        self.initial_size = initial_size
        self.max_size = max_size
        self.pool_size = initial_size
        # ... existing code ...
        
    def acquire(self, x, y, text, fill=COLOR_DIM, font=("Courier", 10)):
        if not self.available:
            # If peak usage is 95%+, grow pool
            if self.utilization_peak > (self.pool_size * 0.95):
                self._grow_pool()
            else:
                log_error(f"[POOL EXHAUSTED] Consider increasing pool size")
                return None
        # ... rest of acquire ...
    
    def _grow_pool(self, increment=20):
        """Dynamically add more objects to pool."""
        if self.pool_size >= self.max_size:
            log_error(f"[POOL] Max size {self.max_size} reached, cannot grow")
            return
        
        for i in range(increment):
            item_id = self.canvas.create_text(-1000, -1000, ...)
            self.available.append(item_id)
        
        self.pool_size += increment
        log_error(f"[POOL] Grew from {self.pool_size-increment} to {self.pool_size}")
```

**Benefits:**
- Automatically adapts to demand
- No more pool exhaustion crashes
- Peak utilization tracking becomes useful

**Difficulty:** Easy | **Time:** 30 mins | **Impact:** Medium (safety feature)

---

## Phase 2.4: Memory Profiling & Benchmarking

**Goal:** Quantify memory savings on actual Pi 2.

**Steps:**
1. Install memory profiler:
   ```bash
   pip3 install memory_profiler
   ```

2. Create profiling wrapper:
   ```python
   @profile
   def update_system_stats(self):
       # Existing code...
       pass
   ```

3. Run with profiler:
   ```bash
   python3 -m memory_profiler dedsec_ui.py
   ```

4. Record metrics:
   - Baseline (before pooling) vs. After (with pooling)
   - Memory growth over time
   - GC collection frequency

**Documentation:** Create PERFORMANCE_REPORT.md with graphs

**Difficulty:** Easy | **Time:** 1 hour | **Impact:** Documentation

---

## Phase 2.5: Batch Canvas Updates

**Current behavior:** Each pool.acquire() calls canvas.coords() + canvas.itemconfig() immediately.

**Optimization:** Accumulate updates, flush once per animation frame.

```python
class CanvasObjectPool:
    def __init__(self, canvas, pool_size=50, batched=True):
        # ... existing ...
        self.batched = batched
        self.pending_updates = []  # List of (item_id, action, args)
    
    def acquire(self, x, y, text, ...):
        if self.batched:
            self.pending_updates.append((item_id, 'coords', (x, y)))
            self.pending_updates.append((item_id, 'itemconfig', {'text': text, ...}))
        else:
            # Current behavior: update immediately
            self.canvas.coords(item_id, x, y)
            self.canvas.itemconfig(item_id, ...)
    
    def flush_updates(self):
        """Apply all pending updates at once."""
        for item_id, action, args in self.pending_updates:
            if action == 'coords':
                self.canvas.coords(item_id, *args)
            elif action == 'itemconfig':
                self.canvas.itemconfig(item_id, **args)
        self.pending_updates.clear()
```

Call `flush_updates()` once per animation frame (~10ms).

**Benefits:**
- Reduces Tkinter event queue thrashing
- 20-30% fewer redraws on scrolling

**Difficulty:** Medium | **Time:** 1.5 hours | **Impact:** Medium

---

## Phase 3: Post-Exploitation (Future)

Once Phase 1-2 complete, consider:

1. **Audio Streaming** (no GC pressure)
2. **Hardware Acceleration** (GPU rendering for matrix effect)
3. **Custom Canvas Renderer** (pure pygame/pygame_sdl2)
4. **Interrupt-Driven Updates** (vs. polling)

---

## Recommended Implementation Order

1. **Phase 2.2** (30 mins) - Quick win, network icon reuse
2. **Phase 2.3** (30 mins) - Safety feature, dynamic sizing
3. **Phase 2.4** (1 hour) - Profiling & documentation
4. **Phase 2.1** (2 hours) - Terminal dirty rect tracking (higher complexity)
5. **Phase 2.5** (1.5 hours) - Batched updates (if profiling shows need)

**Total Phase 2 effort:** ~5 hours → ~5-10% additional performance gain on Pi 2

---

## Testing Strategy for Phase 2

For each enhancement:
1. Create `test_phase2_X.py` unit tests
2. Run memory profiler before/after
3. Verify no visual regressions
4. Benchmark on actual Pi 2 if available
5. Add to test suite and CI/CD

---

## Success Metrics

After Phase 1+2 complete:
- ✅ Memory allocation rate: ~0 objects/sec (from 10+/sec)
- ✅ Memory fragmentation: Eliminated
- ✅ GC pause time: <10ms (from 50ms+)
- ✅ Terminal scroll smoothness: 60 FPS (or max possible on Pi 2)
- ✅ Battery life: +10-15% improvement (estimated)
