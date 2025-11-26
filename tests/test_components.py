"""
Unit tests for UI Components (Button, Modal, TextDisplay)

Tests component rendering, state management, and event handling.
"""

import unittest
from unittest.mock import MagicMock, patch
from typing import List as ListType
from ui.components import Button, Modal, TextDisplay
from ui.architecture import Rectangle, UIState, UIComponent


# ============================================================================
# BUTTON TESTS
# ============================================================================

class TestButton(unittest.TestCase):
    """Tests for Button component."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.canvas = MagicMock()
        self.rect = Rectangle(10, 10, 100, 40)
        self.callback = MagicMock()
        self.button = Button(
            name="TestButton",
            rect=self.rect,
            on_click=self.callback
        )
    
    def test_initialization(self):
        """Test button initializes correctly."""
        self.assertEqual(self.button.text, "TestButton")
        self.assertEqual(self.button.rect, self.rect)
        self.assertEqual(self.button.state, UIState.NORMAL)
        self.assertTrue(self.button.is_enabled)
    
    def test_rect_contains_point_inside(self):
        """Test point detection inside button."""
        self.assertTrue(self.button.rect.contains_point(50, 25))
    
    def test_rect_contains_point_outside(self):
        """Test point detection outside button."""
        self.assertFalse(self.button.rect.contains_point(5, 5))
        self.assertFalse(self.button.rect.contains_point(150, 50))
    
    def test_rect_contains_point_edge(self):
        """Test point detection on edge."""
        self.assertTrue(self.button.rect.contains_point(10, 10))  # Top-left corner
        self.assertFalse(self.button.rect.contains_point(110, 50))  # Outside bottom-right
    
    def test_on_touch_normal(self):
        """Test button touch when enabled."""
        result = self.button.on_touch(50, 25)
        
        self.assertTrue(result)
        self.callback.assert_called_once()
    
    def test_on_touch_disabled(self):
        """Test button touch when disabled."""
        self.button.is_enabled = False
        
        result = self.button.on_touch(50, 25)
        
        self.assertFalse(result)
        self.callback.assert_not_called()
    
    def test_set_state(self):
        """Test state changes."""
        self.button.set_state(UIState.HOVER)
        self.assertEqual(self.button.state, UIState.HOVER)
        
        self.button.set_state(UIState.PRESSED)
        self.assertEqual(self.button.state, UIState.PRESSED)
    
    def test_enable_disable(self):
        """Test enable/disable functionality."""
        self.button.is_enabled = False
        self.assertFalse(self.button.is_enabled)
        
        self.button.is_enabled = True
        self.assertTrue(self.button.is_enabled)
    
    def test_text_property(self):
        """Test text property."""
        self.button.text = "Updated"
        self.assertEqual(self.button.text, "Updated")
    
    def test_render_visible(self):
        """Test render when visible."""
        self.button.render(self.canvas)
        
        # Should call canvas methods
        self.canvas.create_rectangle.assert_called()
        self.canvas.create_text.assert_called()
    
    def test_render_not_visible(self):
        """Test render when not visible."""
        self.button.is_visible = False
        self.button.render(self.canvas)
        
        # Should not call canvas methods
        self.canvas.create_rectangle.assert_not_called()
        self.canvas.create_text.assert_not_called()


# ============================================================================
# MODAL TESTS
# ============================================================================

class TestModal(unittest.TestCase):
    """Tests for Modal component."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.canvas = MagicMock()
        self.rect = Rectangle(50, 50, 200, 150)
        self.modal = Modal(
            title="Test Modal",
            rect=self.rect
        )
    
    def test_initialization(self):
        """Test modal initializes correctly."""
        self.assertEqual(self.modal.title, "Test Modal")
        self.assertEqual(self.modal.rect, self.rect)
        self.assertFalse(self.modal.is_visible)  # Modals hidden by default
    
    def test_show_hide(self):
        """Test modal visibility."""
        self.modal.show()
        self.assertTrue(self.modal.is_visible)
        
        self.modal.hide()
        self.assertFalse(self.modal.is_visible)
    
    def test_set_message(self):
        """Test setting modal message."""
        self.modal.set_message("Test message")
        
        self.assertEqual(self.modal.message, "Test message")
    
    def test_add_button(self):
        """Test adding buttons to modal."""
        callback = MagicMock()
        button = self.modal.add_button("OK", callback)
        
        self.assertIsInstance(button, Button)
        self.assertEqual(button.text, "OK")
        self.assertIn(button, self.modal.buttons)
    
    def test_render_visible(self):
        """Test rendering when visible."""
        self.modal.show()
        self.modal.render(self.canvas)
        
        # Should draw modal
        self.canvas.create_rectangle.assert_called()
        self.canvas.create_text.assert_called()
    
    def test_render_not_visible(self):
        """Test render does nothing when modal hidden."""
        self.modal.hide()
        self.modal.render(self.canvas)
        
        # Should not draw anything
        self.canvas.create_rectangle.assert_not_called()
        self.canvas.create_text.assert_not_called()
    
    def test_on_touch_button(self):
        """Test touch on modal button."""
        callback = MagicMock()
        button = self.modal.add_button("OK", callback)
        # Set button rect manually for testing
        button.rect = Rectangle(60, 120, 50, 20)
        
        result = self.modal.on_touch(70, 125)
        
        self.assertTrue(result)
        callback.assert_called_once()


# ============================================================================
# TEXT DISPLAY TESTS
# ============================================================================

class TestTextDisplay(unittest.TestCase):
    """Tests for TextDisplay component."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.canvas = MagicMock()
        self.rect = Rectangle(10, 10, 300, 200)
        self.text_display = TextDisplay(
            name="TestDisplay",
            rect=self.rect
        )
    
    def test_initialization(self):
        """Test text display initializes correctly."""
        self.assertEqual(len(self.text_display.lines), 0)
        self.assertEqual(self.text_display.scroll_offset, 0)
    
    def test_add_line(self):
        """Test adding text lines."""
        self.text_display.add_line("Line 1")
        self.text_display.add_line("Line 2")
        
        self.assertEqual(len(self.text_display.lines), 2)
        self.assertEqual(self.text_display.lines[0], "Line 1")
        self.assertEqual(self.text_display.lines[1], "Line 2")
    
    def test_clear(self):
        """Test clearing all lines."""
        self.text_display.add_line("Line 1")
        self.text_display.add_line("Line 2")
        
        self.text_display.clear()
        
        self.assertEqual(len(self.text_display.lines), 0)
        self.assertEqual(self.text_display.scroll_offset, 0)
    
    def test_render_visible(self):
        """Test render when visible."""
        self.text_display.add_line("Test line")
        self.text_display.render(self.canvas)
        
        # Should draw border and text
        self.canvas.create_rectangle.assert_called()
        self.canvas.create_text.assert_called()
    
    def test_render_not_visible(self):
        """Test render when not visible."""
        self.text_display.is_visible = False
        self.text_display.add_line("Test line")
        self.text_display.render(self.canvas)
        
        self.canvas.create_rectangle.assert_not_called()


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class ComponentIntegrationTest(unittest.TestCase):
    """Integration tests for components."""
    
    def test_button_in_modal(self):
        """Test button inside modal via add_button."""
        canvas = MagicMock()
        rect = Rectangle(50, 50, 200, 150)
        modal = Modal("Test", rect)
        
        callback = MagicMock()
        button = modal.add_button("Click Me", callback)
        
        modal.show()
        modal.render(canvas)
        
        # Button should be in modal's buttons
        self.assertIn(button, modal.buttons)
    
    def test_modal_interaction_flow(self):
        """Test typical modal interaction flow."""
        rect = Rectangle(50, 50, 200, 100)
        modal = Modal("Confirm", rect)
        
        yes_callback = MagicMock()
        no_callback = MagicMock()
        
        yes_button = modal.add_button("Yes", yes_callback)
        no_button = modal.add_button("No", no_callback)
        
        # Set button rects for touch testing
        yes_button.rect = Rectangle(55, 75, 50, 20)
        no_button.rect = Rectangle(110, 75, 50, 20)
        
        # Show and click Yes
        modal.show()
        modal.on_touch(60, 80)  # Within yes button
        
        yes_callback.assert_called_once()
        no_callback.assert_not_called()
    
    def test_nested_components(self):
        """Test UIComponent parent-child relationships."""
        parent_rect = Rectangle(0, 0, 320, 240)
        child_rect = Rectangle(10, 10, 50, 20)
        
        # Create parent and child buttons
        parent = Button("Parent", parent_rect)
        child = Button("Child", child_rect)
        
        parent.add_child(child)
        
        self.assertIn(child, parent.children)
        self.assertEqual(child.parent, parent)
    
    def test_remove_child(self):
        """Test removing child component."""
        parent = Button("Parent", Rectangle(0, 0, 100, 100))
        child = Button("Child", Rectangle(10, 10, 20, 20))
        
        parent.add_child(child)
        self.assertIn(child, parent.children)
        
        parent.remove_child(child)
        self.assertNotIn(child, parent.children)
        self.assertIsNone(child.parent)


if __name__ == '__main__':
    unittest.main()
