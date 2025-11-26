"""
Unit tests for UI Architecture (MVC base classes)

Tests Model, View, Controller base classes and their interaction.
"""

import unittest
from unittest.mock import MagicMock, patch, call
from ui.architecture import Model, View, Controller, Observer, Rectangle


# ============================================================================
# CONCRETE IMPLEMENTATIONS FOR TESTING
# ============================================================================

class ConcreteModel(Model):
    """Concrete Model implementation for testing."""
    
    def __init__(self, name: str = "TestModel"):
        super().__init__(name)
        self.data = ""
    
    def execute(self) -> None:
        """Execute model operation."""
        self.is_running = True
        self.notify_observers()
    
    def set_data(self, value: str) -> None:
        """Set data and notify observers."""
        self.data = value
        self.notify_observers()


class ConcreteView(View, Observer):
    """Concrete View implementation for testing (also acts as Observer)."""
    
    def __init__(self, name: str = "TestView", canvas=None):
        super().__init__(name, canvas)
        self.last_render_rect = None
        self.model_changed_count = 0
    
    def render(self, rect: Rectangle) -> None:
        """Render view content."""
        self.last_render_rect = rect
    
    def on_model_changed(self, model: Model) -> None:
        """Called when model state changes."""
        self.model_changed_count += 1


class ConcreteController(Controller):
    """Concrete Controller implementation for testing."""
    
    def __init__(self, name: str = "TestController"):
        super().__init__(name)
        self.last_touch = None
    
    def on_touch(self, x: int, y: int) -> None:
        """Handle touch input."""
        self.last_touch = (x, y)


class MockObserver(Observer):
    """Mock Observer for testing."""
    
    def __init__(self):
        self.update_count = 0
        self.last_model = None
    
    def on_model_changed(self, model: Model) -> None:
        """Called when model state changes."""
        self.update_count += 1
        self.last_model = model


# ============================================================================
# MODEL TESTS
# ============================================================================

class TestModel(unittest.TestCase):
    """Tests for Model base class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.model = ConcreteModel("test_model")
    
    def test_initialization(self):
        """Test model initializes with empty observers."""
        self.assertEqual(len(self.model.observers), 0)
        self.assertEqual(self.model.name, "test_model")
        self.assertFalse(self.model.is_running)
    
    def test_subscribe_observer(self):
        """Test subscribing observers."""
        observer1 = MockObserver()
        observer2 = MockObserver()
        
        self.model.subscribe(observer1)
        self.model.subscribe(observer2)
        
        self.assertEqual(len(self.model.observers), 2)
        self.assertIn(observer1, self.model.observers)
        self.assertIn(observer2, self.model.observers)
    
    def test_unsubscribe_observer(self):
        """Test unsubscribing observers."""
        observer = MockObserver()
        
        self.model.subscribe(observer)
        self.assertEqual(len(self.model.observers), 1)
        
        self.model.unsubscribe(observer)
        self.assertEqual(len(self.model.observers), 0)
    
    def test_unsubscribe_nonexistent_observer(self):
        """Test unsubscribing observer that wasn't subscribed."""
        observer = MockObserver()
        
        # Should not raise error
        self.model.unsubscribe(observer)
        self.assertEqual(len(self.model.observers), 0)
    
    def test_notify_observers(self):
        """Test notifying observers."""
        observer1 = MockObserver()
        observer2 = MockObserver()
        
        self.model.subscribe(observer1)
        self.model.subscribe(observer2)
        
        # Notify observers
        self.model.notify_observers()
        
        self.assertEqual(observer1.update_count, 1)
        self.assertEqual(observer2.update_count, 1)
        self.assertEqual(observer1.last_model, self.model)
        self.assertEqual(observer2.last_model, self.model)
    
    def test_notify_no_observers(self):
        """Test notify with no observers subscribed."""
        # Should not raise error
        self.model.notify_observers()
    
    def test_execute(self):
        """Test execute method."""
        observer = MockObserver()
        self.model.subscribe(observer)
        
        self.model.execute()
        
        self.assertTrue(self.model.is_running)
        self.assertEqual(observer.update_count, 1)
    
    def test_reset(self):
        """Test reset method."""
        self.model.is_running = True
        self.model.error_state = Exception("test error")
        
        self.model.reset()
        
        self.assertFalse(self.model.is_running)
        self.assertIsNone(self.model.error_state)
    
    def test_set_error(self):
        """Test set_error method."""
        observer = MockObserver()
        self.model.subscribe(observer)
        
        error = Exception("test error")
        self.model.set_error(error)
        
        self.assertEqual(self.model.error_state, error)
        self.assertEqual(observer.update_count, 1)


# ============================================================================
# VIEW TESTS
# ============================================================================

class TestView(unittest.TestCase):
    """Tests for View base class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_canvas = MagicMock()
        self.view = ConcreteView("test_view", self.mock_canvas)
    
    def test_initialization(self):
        """Test view initializes correctly."""
        self.assertEqual(self.view.name, "test_view")
        self.assertEqual(self.view.canvas, self.mock_canvas)
        self.assertTrue(self.view.is_visible)
    
    def test_set_rect(self):
        """Test setting rect."""
        rect = Rectangle(10, 20, 100, 50)
        self.view.set_rect(rect)
        
        self.assertEqual(self.view.rect, rect)
    
    def test_show_hide(self):
        """Test show/hide methods."""
        self.view.hide()
        self.assertFalse(self.view.is_visible)
        
        self.view.show()
        self.assertTrue(self.view.is_visible)
    
    def test_render(self):
        """Test render method."""
        rect = Rectangle(0, 0, 100, 100)
        self.view.render(rect)
        
        self.assertEqual(self.view.last_render_rect, rect)


# ============================================================================
# CONTROLLER TESTS
# ============================================================================

class TestController(unittest.TestCase):
    """Tests for Controller base class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.controller = ConcreteController("test_controller")
    
    def test_initialization(self):
        """Test controller initializes correctly."""
        self.assertEqual(self.controller.name, "test_controller")
        self.assertIsNone(self.controller.model)
        self.assertIsNone(self.controller.view)
    
    def test_set_model(self):
        """Test setting model."""
        model = ConcreteModel("model")
        
        self.controller.set_model(model)
        
        self.assertEqual(self.controller.model, model)
    
    def test_set_view(self):
        """Test setting view."""
        view = ConcreteView("view")
        
        self.controller.set_view(view)
        
        self.assertEqual(self.controller.view, view)
    
    def test_on_touch(self):
        """Test touch handling."""
        self.controller.on_touch(50, 100)
        
        self.assertEqual(self.controller.last_touch, (50, 100))
    
    def test_on_command(self):
        """Test command handling."""
        # Base implementation should not raise
        self.controller.on_command("test_command", {"arg": "value"})


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class MVCIntegrationTest(unittest.TestCase):
    """Integration tests for MVC pattern."""
    
    def test_full_mvc_flow(self):
        """Test complete MVC data flow."""
        # Set up MVC
        canvas = MagicMock()
        model = ConcreteModel("integration_model")
        view = ConcreteView("integration_view", canvas)
        controller = ConcreteController("integration_controller")
        
        # Wire up
        controller.set_model(model)
        controller.set_view(view)
        model.subscribe(view)  # View observes model
        
        # Execute action
        model.set_data("test123")
        
        # Verify model state
        self.assertEqual(model.data, "test123")
    
    def test_observer_receives_updates(self):
        """Test observer receives model updates."""
        model = ConcreteModel("model")
        observer = MockObserver()
        
        model.subscribe(observer)
        model.set_data("update1")
        model.set_data("update2")
        
        self.assertEqual(observer.update_count, 2)
        self.assertEqual(observer.last_model, model)


if __name__ == '__main__':
    unittest.main()
