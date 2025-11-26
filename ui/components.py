"""
DedSecOS UI Component Library

Reusable, themeable UI components built on the MVC architecture.
All components inherit from UIComponent and can be nested hierarchically.

Components:
    - Button: Clickable button with states
    - Modal: Dialog boxes with content and actions
    - TextDisplay: Terminal-like text rendering
    - SelectionMenu: Grid of selectable options
    - Gauge: Progress/status indicator
    - Panel: Container for grouping components
    - List: Scrollable list of items

Example:
    from ui.components import Button, Panel
    
    panel = Panel("MyPanel", Rectangle(0, 0, 320, 240))
    button = Button("OK", Rectangle(10, 10, 50, 20), on_click=lambda: print("Clicked!"))
    panel.add_child(button)
"""

from typing import Callable, List as ListType, Optional, Dict, Any, Tuple
from ui.architecture import UIComponent, Rectangle, UIState
import logging


class Button(UIComponent):
    """
    Clickable button component with visual feedback.
    
    States:
        NORMAL: Default appearance
        HOVER: Mouse over button
        PRESSED: Button being clicked
        DISABLED: Cannot interact
    
    Example:
        button = Button("SCAN", Rectangle(10, 10, 80, 30))
        button.on_click = lambda: scanner.execute()
    """
    
    def __init__(self, name: str, rect: Rectangle, on_click: Optional[Callable] = None):
        """Initialize button."""
        super().__init__(name, rect)
        self.on_click = on_click
        self.text = name
        self.click_count = 0
    
    def render(self, canvas) -> None:
        """Render button to canvas."""
        if not self.is_visible or not canvas:
            return
        
        # Get color based on state
        color_map = {
            UIState.NORMAL: "#00ff00",
            UIState.HOVER: "#00ff00",
            UIState.PRESSED: "#ffffff",
            UIState.DISABLED: "#333333",
        }
        color = color_map.get(self.state, "#00ff00")
        
        # Draw button rectangle
        canvas.create_rectangle(
            self.rect.x, self.rect.y,
            self.rect.x + self.rect.width, self.rect.y + self.rect.height,
            fill=color if self.state == UIState.PRESSED else "",
            outline=color,
            width=2 if self.state in [UIState.HOVER, UIState.PRESSED] else 1
        )
        
        # Draw button text
        canvas.create_text(
            self.rect.center_x, self.rect.center_y,
            text=self.text,
            fill=color,
            font=("Courier", 9, "bold")
        )
        
        # Render children
        for child in self.children:
            child.render(canvas)
    
    def on_touch(self, x: int, y: int) -> bool:
        """Handle button click."""
        if not self.is_enabled:
            return False
        
        self.click_count += 1
        self.logger.debug(f"Button '{self.name}' clicked (#{self.click_count})")
        
        if self.on_click:
            try:
                self.on_click()
            except Exception as e:
                self.logger.error(f"Error in button click handler: {e}")
        
        return True


class Modal(UIComponent):
    """
    Modal dialog component with title, content, and action buttons.
    
    Example:
        modal = Modal("Confirm", Rectangle(50, 50, 220, 140))
        modal.set_message("Continue?")
        modal.add_button("Yes", lambda: print("Yes clicked"))
        modal.add_button("No", lambda: print("No clicked"))
    """
    
    def __init__(self, title: str, rect: Rectangle):
        """Initialize modal."""
        super().__init__(title, rect)
        self.title = title
        self.message = ""
        self.buttons: list[Button] = []
        self.is_visible = False  # Modals are hidden by default
    
    def set_message(self, message: str) -> None:
        """Set modal message text."""
        self.message = message
    
    def add_button(self, text: str, on_click: Callable) -> Button:
        """Add action button to modal."""
        btn = Button(text, Rectangle(0, 0, 50, 20), on_click)
        self.add_child(btn)
        self.buttons.append(btn)
        return btn
    
    def render(self, canvas) -> None:
        """Render modal dialog."""
        if not self.is_visible or not canvas:
            return
        
        # Draw modal background
        canvas.create_rectangle(
            self.rect.x, self.rect.y,
            self.rect.x + self.rect.width, self.rect.y + self.rect.height,
            fill="#000000",
            outline="#00ff00",
            width=2
        )
        
        # Draw title
        canvas.create_text(
            self.rect.x + 5, self.rect.y + 5,
            text=self.title,
            fill="#00ff00",
            font=("Courier", 10, "bold"),
            anchor="nw"
        )
        
        # Draw message
        canvas.create_text(
            self.rect.center_x, self.rect.y + 40,
            text=self.message,
            fill="#ffffff",
            font=("Courier", 9),
            width=self.rect.width - 10
        )
        
        # Position and render buttons
        button_y = self.rect.y + self.rect.height - 30
        button_x = self.rect.x + 5
        for button in self.buttons:
            button.rect = Rectangle(button_x, button_y, 50, 20)
            button.render(canvas)
            button_x += 55
    
    def on_touch(self, x: int, y: int) -> bool:
        """Handle modal interaction."""
        # Check buttons first
        for button in self.buttons:
            if button.rect.contains_point(x, y):
                return button.on_touch(x, y)
        return False
    
    def show(self) -> None:
        """Show modal."""
        self.is_visible = True
        self.state = UIState.NORMAL
        self.logger.debug(f"Modal '{self.name}' shown")
    
    def hide(self) -> None:
        """Hide modal."""
        self.is_visible = False
        self.logger.debug(f"Modal '{self.name}' hidden")


class TextDisplay(UIComponent):
    """
    Terminal-like text display component with scrolling support.
    
    Example:
        text_area = TextDisplay("Logs", Rectangle(65, 40, 250, 160))
        text_area.add_line("# SYSTEM ONLINE")
        text_area.add_line("# USER: berry")
    """
    
    def __init__(self, name: str, rect: Rectangle):
        """Initialize text display."""
        super().__init__(name, rect)
        self.lines: list[str] = []
        self.scroll_offset = 0
        self.max_visible_lines = rect.height // 12  # Assuming 12px line height
    
    def add_line(self, text: str) -> None:
        """Add line of text."""
        self.lines.append(text)
        # Auto-scroll to show latest line
        if len(self.lines) > self.max_visible_lines:
            self.scroll_offset = len(self.lines) - self.max_visible_lines
    
    def clear(self) -> None:
        """Clear all text."""
        self.lines.clear()
        self.scroll_offset = 0
    
    def render(self, canvas) -> None:
        """Render text display."""
        if not self.is_visible or not canvas:
            return
        
        # Draw border
        canvas.create_rectangle(
            self.rect.x, self.rect.y,
            self.rect.x + self.rect.width, self.rect.y + self.rect.height,
            outline="#00ff00",
            fill="#000000",
            width=1
        )
        
        # Draw text lines
        start_line = self.scroll_offset
        for i, line in enumerate(self.lines[start_line:]):
            if i >= self.max_visible_lines:
                break
            y_pos = self.rect.y + 5 + (i * 12)
            canvas.create_text(
                self.rect.x + 5, y_pos,
                text=f"> {line}",
                fill="#ffffff",
                font=("Courier", 9),
                anchor="nw"
            )
    
    def on_touch(self, x: int, y: int) -> bool:
        """Handle scrolling or selection."""
        return False


class SelectionMenu(UIComponent):
    """
    Grid of selectable options with highlight support.
    
    Example:
        menu = SelectionMenu("Targets", Rectangle(10, 10, 300, 200))
        menu.add_option("Option 1", lambda: print("Selected 1"))
        menu.add_option("Option 2", lambda: print("Selected 2"))
    """
    
    def __init__(self, name: str, rect: Rectangle, columns: int = 1):
        """Initialize selection menu."""
        super().__init__(name, rect)
        self.options: list[dict[str, Any]] = []
        self.columns = columns
        self.selected_index = -1
    
    def add_option(self, text: str, on_select: Callable) -> None:
        """Add option to menu."""
        self.options.append({
            'text': text,
            'on_select': on_select,
            'button': None
        })
    
    def render(self, canvas) -> None:
        """Render menu options."""
        if not self.is_visible or not canvas:
            return
        
        # Draw background
        canvas.create_rectangle(
            self.rect.x, self.rect.y,
            self.rect.x + self.rect.width, self.rect.y + self.rect.height,
            fill="#000000",
            outline="#00ff00",
            width=1
        )
        
        # Draw options in grid
        item_height = 25
        item_width = self.rect.width // self.columns
        
        for i, option in enumerate(self.options):
            row = i // self.columns
            col = i % self.columns
            
            x = self.rect.x + (col * item_width)
            y = self.rect.y + (row * item_height)
            
            is_selected = i == self.selected_index
            color = "#ffffff" if is_selected else "#00ff00"
            
            # Draw option button
            canvas.create_rectangle(
                x + 2, y + 2,
                x + item_width - 2, y + item_height - 2,
                outline=color,
                fill="#111111" if is_selected else "#000000",
                width=2 if is_selected else 1
            )
            
            # Draw option text
            canvas.create_text(
                x + item_width // 2, y + item_height // 2,
                text=option['text'],
                fill=color,
                font=("Courier", 8)
            )
            
            option['button'] = Rectangle(x, y, item_width, item_height)
    
    def on_touch(self, x: int, y: int) -> bool:
        """Handle option selection."""
        for i, option in enumerate(self.options):
            if option['button'] and option['button'].contains_point(x, y):
                self.selected_index = i
                if option['on_select']:
                    try:
                        option['on_select']()
                    except Exception as e:
                        self.logger.error(f"Error in selection handler: {e}")
                return True
        return False


class Gauge(UIComponent):
    """
    Progress/status indicator gauge.
    
    Example:
        gauge = Gauge("CPU", Rectangle(40, 224, 60, 10))
        gauge.set_value(75)
    """
    
    def __init__(self, name: str, rect: Rectangle):
        """Initialize gauge."""
        super().__init__(name, rect)
        self.value = 0.0  # 0.0 to 1.0
        self.label = name
    
    def set_value(self, value: float) -> None:
        """Set gauge value (0.0 to 1.0)."""
        self.value = max(0.0, min(1.0, value))
    
    def render(self, canvas) -> None:
        """Render gauge."""
        if not self.is_visible or not canvas:
            return
        
        # Draw gauge background
        canvas.create_rectangle(
            self.rect.x, self.rect.y,
            self.rect.x + self.rect.width, self.rect.y + self.rect.height,
            fill="#111111",
            outline="#00ff00",
            width=1
        )
        
        # Draw gauge fill
        fill_width = int(self.rect.width * self.value)
        canvas.create_rectangle(
            self.rect.x, self.rect.y,
            self.rect.x + fill_width, self.rect.y + self.rect.height,
            fill="#00ff00",
            outline=""
        )
        
        # Draw label text
        canvas.create_text(
            self.rect.x + 5, self.rect.y + self.rect.height + 5,
            text=self.label,
            fill="#ffffff",
            font=("Courier", 8),
            anchor="nw"
        )


class Panel(UIComponent):
    """
    Container panel for grouping components.
    
    Example:
        panel = Panel("MainPanel", Rectangle(0, 0, 320, 240))
        button = Button("OK", Rectangle(10, 10, 50, 20))
        panel.add_child(button)
    """
    
    def __init__(self, name: str, rect: Rectangle, show_border: bool = False):
        """Initialize panel."""
        super().__init__(name, rect)
        self.show_border = show_border
    
    def render(self, canvas) -> None:
        """Render panel and children."""
        if not self.is_visible or not canvas:
            return
        
        # Draw border if enabled
        if self.show_border:
            canvas.create_rectangle(
                self.rect.x, self.rect.y,
                self.rect.x + self.rect.width, self.rect.y + self.rect.height,
                outline="#00ff00",
                fill="",
                width=1
            )
        
        # Render children
        for child in self.children:
            child.render(canvas)
    
    def on_touch(self, x: int, y: int) -> bool:
        """Handle touch on children."""
        for child in reversed(self.children):
            if child.handle_touch(x, y):
                return True
        return False


class List(UIComponent):
    """
    Scrollable list component for displaying items.
    
    Example:
        item_list = List("Items", Rectangle(10, 10, 300, 200))
        item_list.add_item("Item 1")
        item_list.add_item("Item 2")
    """
    
    def __init__(self, name: str, rect: Rectangle):
        """Initialize list."""
        super().__init__(name, rect)
        self.items: list[str] = []
        self.scroll_index = 0
        self.selected_index = -1
        self.item_height = 20
    
    def add_item(self, text: str) -> None:
        """Add item to list."""
        self.items.append(text)
    
    def remove_item(self, index: int) -> None:
        """Remove item from list."""
        if 0 <= index < len(self.items):
            self.items.pop(index)
    
    def clear(self) -> None:
        """Clear all items."""
        self.items.clear()
        self.selected_index = -1
    
    def render(self, canvas) -> None:
        """Render list."""
        if not self.is_visible or not canvas:
            return
        
        # Draw list border
        canvas.create_rectangle(
            self.rect.x, self.rect.y,
            self.rect.x + self.rect.width, self.rect.y + self.rect.height,
            outline="#00ff00",
            fill="#000000",
            width=1
        )
        
        # Draw items
        visible_items = (self.rect.height - 4) // self.item_height
        for i in range(visible_items):
            item_idx = self.scroll_index + i
            if item_idx >= len(self.items):
                break
            
            y_pos = self.rect.y + 2 + (i * self.item_height)
            is_selected = item_idx == self.selected_index
            
            # Draw item background
            if is_selected:
                canvas.create_rectangle(
                    self.rect.x + 2, y_pos,
                    self.rect.x + self.rect.width - 2, y_pos + self.item_height - 2,
                    fill="#333333",
                    outline=""
                )
            
            # Draw item text
            canvas.create_text(
                self.rect.x + 5, y_pos + self.item_height // 2,
                text=self.items[item_idx],
                fill="#00ff00" if is_selected else "#ffffff",
                font=("Courier", 9),
                anchor="w"
            )
    
    def on_touch(self, x: int, y: int) -> bool:
        """Handle list item selection."""
        visible_items = (self.rect.height - 4) // self.item_height
        for i in range(visible_items):
            item_idx = self.scroll_index + i
            if item_idx >= len(self.items):
                break
            
            y_pos = self.rect.y + 2 + (i * self.item_height)
            item_rect = Rectangle(
                self.rect.x + 2, y_pos,
                self.rect.width - 4, self.item_height - 2
            )
            
            if item_rect.contains_point(x, y):
                self.selected_index = item_idx
                self.logger.debug(f"Selected item {item_idx}: {self.items[item_idx]}")
                return True
        
        return False


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'Button',
    'Modal',
    'TextDisplay',
    'SelectionMenu',
    'Gauge',
    'Panel',
    'List',
]
