"""
Unit tests for Theme Manager

Tests theme loading, switching, and color retrieval.
"""

import unittest
from unittest.mock import MagicMock, patch
from ui.themes import ThemeManager, Theme, ThemeType, get_theme_neon_green, get_theme_synthwave


class TestTheme(unittest.TestCase):
    """Tests for Theme class."""

    def test_neon_green_theme(self):
        """Test neon green theme."""
        theme = get_theme_neon_green()

        # Check colors
        self.assertEqual(theme.name, "neon_green")
        self.assertEqual(theme.text, "#00FF00")
        self.assertEqual(theme.background, "#000000")

    def test_synthwave_theme(self):
        """Test synthwave theme."""
        theme = get_theme_synthwave()

        self.assertEqual(theme.name, "synthwave")
        self.assertEqual(theme.text, "#FF006E")
        self.assertEqual(theme.background, "#0A0E27")

    def test_theme_get_color(self):
        """Test theme get_color method."""
        theme = get_theme_neon_green()

        color = theme.get_color("text")
        self.assertEqual(color, "#00FF00")

        missing = theme.get_color("nonexistent")
        self.assertIsNone(missing)

    def test_theme_to_dict(self):
        """Test theme to_dict method."""
        theme = get_theme_neon_green()

        colors = theme.to_dict()

        self.assertIsInstance(colors, dict)
        self.assertIn("background", colors)
        self.assertIn("text", colors)
        self.assertEqual(colors["text"], "#00FF00")


class TestThemeManager(unittest.TestCase):
    """Tests for ThemeManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.theme_manager = ThemeManager()

    def test_initialization(self):
        """Test theme manager initializes with default theme."""
        self.assertIsNotNone(self.theme_manager.current_theme)
        self.assertEqual(self.theme_manager.current_theme.name, "neon_green")

    def test_get_available_themes(self):
        """Test retrieving available themes."""
        themes = self.theme_manager.get_available_themes()

        self.assertGreater(len(themes), 0)
        self.assertIn("neon_green", themes)
        self.assertIn("synthwave", themes)

    def test_set_theme_valid(self):
        """Test switching to valid theme."""
        result = self.theme_manager.set_theme("synthwave")

        self.assertTrue(result)
        self.assertEqual(self.theme_manager.current_theme.name, "synthwave")

    def test_set_theme_invalid(self):
        """Test switching to invalid theme."""
        original_theme = self.theme_manager.current_theme

        result = self.theme_manager.set_theme("nonexistent")

        self.assertFalse(result)
        self.assertEqual(self.theme_manager.current_theme, original_theme)

    def test_get_color(self):
        """Test retrieving color from current theme."""
        color = self.theme_manager.get_color("text")

        self.assertIsInstance(color, str)
        self.assertTrue(color.startswith("#"))

    def test_get_color_fallback(self):
        """Test get_color returns fallback for missing color."""
        color = self.theme_manager.get_color("nonexistent_color")

        # Should return fallback color
        self.assertEqual(color, "#000000")

    def test_get_all_colors(self):
        """Test get_all_colors method."""
        colors = self.theme_manager.get_all_colors()

        self.assertIsInstance(colors, dict)
        self.assertIn("text", colors)
        self.assertIn("background", colors)

    def test_register_theme(self):
        """Test registering new theme."""
        custom_theme = Theme(
            name="test_theme",
            label="Test Theme",
            background="#123456",
            text="#abcdef",
            text_secondary="#999999",
            header_bg="#111111",
            header_text="#ffffff",
            button_bg="#222222",
            button_text="#ffffff",
            button_hover="#333333",
            button_active="#444444",
            button_disabled="#555555",
            modal_bg="#111111",
            modal_text="#ffffff",
            modal_border="#00ff00",
            input_bg="#000000",
            input_text="#ffffff",
            input_border="#00ff00",
            error_bg="#ff0000",
            error_text="#ffffff",
            success_bg="#00ff00",
            success_text="#000000",
            warning_bg="#ffff00",
            warning_text="#000000",
            border="#00ff00",
            highlight="#00ff00",
            accent="#ff00ff",
            muted="#666666",
            progress_bg="#333333",
            progress_fill="#00ff00",
            panel_bg="#111111",
            panel_border="#00ff00",
        )

        self.theme_manager.register_theme(custom_theme)

        themes = self.theme_manager.get_available_themes()
        self.assertIn("test_theme", themes)

        # Can switch to it
        result = self.theme_manager.set_theme("test_theme")
        self.assertTrue(result)
        self.assertEqual(self.theme_manager.current_theme.background, "#123456")

    def test_get_theme(self):
        """Test get_theme method."""
        # Get current theme
        current = self.theme_manager.get_theme()
        self.assertEqual(current, self.theme_manager.current_theme)

        # Get specific theme
        synthwave = self.theme_manager.get_theme("synthwave")
        self.assertIsNotNone(synthwave)
        if synthwave is not None:
            self.assertEqual(synthwave.name, "synthwave")

        # Get nonexistent theme
        missing = self.theme_manager.get_theme("nonexistent")
        self.assertIsNone(missing)

    def test_get_theme_labels(self):
        """Test get_theme_labels method."""
        labels = self.theme_manager.get_theme_labels()

        self.assertIsInstance(labels, dict)
        self.assertIn("neon_green", labels)
        self.assertEqual(labels["neon_green"], "Neon Green")


class ThemeIntegrationTest(unittest.TestCase):
    """Integration tests for theming."""

    def test_all_default_themes_loadable(self):
        """Test all default themes can be loaded."""
        manager = ThemeManager()
        themes = manager.get_available_themes()

        for theme_name in themes:
            result = manager.set_theme(theme_name)
            self.assertTrue(result, f"Failed to load theme: {theme_name}")

            # Verify theme has required colors
            theme = manager.current_theme
            self.assertIsNotNone(theme.text)
            self.assertIsNotNone(theme.background)

    def test_theme_colors_valid_hex(self):
        """Test all theme colors are valid hex."""
        manager = ThemeManager()
        themes = manager.get_available_themes()

        for theme_name in themes:
            manager.set_theme(theme_name)
            theme = manager.current_theme

            # Check key color attributes
            for attr in ["background", "text", "button_bg", "border", "accent"]:
                color = getattr(theme, attr, None)
                if color:
                    self.assertTrue(color.startswith("#"), f"{theme_name}.{attr} invalid: {color}")
                    self.assertIn(
                        len(color),
                        [4, 7],  # #RGB or #RRGGBB
                        f"{theme_name}.{attr} wrong length: {color}",
                    )

    def test_theme_type_enum(self):
        """Test ThemeType enum values match available themes."""
        manager = ThemeManager()
        themes = manager.get_available_themes()

        for theme_type in ThemeType:
            self.assertIn(
                theme_type.value, themes, f"ThemeType.{theme_type.name} not in available themes"
            )


if __name__ == "__main__":
    unittest.main()
