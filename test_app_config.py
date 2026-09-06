"""Unit tests for AppConfig and ConfigManager classes."""

import json
from pathlib import Path
import tempfile
import unittest

from app_config import AppConfig, ConfigManager


class TestAppConfig(unittest.TestCase):
    """Unit tests for AppConfig data model and ConfigManager persistence."""

    def test_default_config_values(self):
        config = AppConfig()
        self.assertEqual(config.directory, "D:/ABogue/Books/")
        self.assertEqual(config.pattern, "ai * pattern")
        self.assertEqual(config.extension, "pdf, epub, txt")
        self.assertEqual(config.sort_order, "published, publisher, modified")
        self.assertEqual(config.publisher, "")
        self.assertEqual(config.limit, 100)
        self.assertEqual(config.filter_result, "")

    def test_load_nonexistent_file_returns_defaults(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".filesearch" / "config"
            manager = ConfigManager(config_path=config_path)

            config = manager.load()
            self.assertEqual(config.directory, AppConfig.directory)
            self.assertEqual(config.pattern, AppConfig.pattern)

    def test_save_and_reload_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".filesearch" / "config"
            manager = ConfigManager(config_path=config_path)

            custom_config = AppConfig(
                directory="C:/MyBooks/Tech/",
                pattern="python * clean NOT draft",
                extension="pdf, epub, -java",
                sort_order="modified",
                publisher="packt, manning",
                limit=50,
                filter_result="clean",
            )

            success = manager.save(custom_config)
            self.assertTrue(success)
            self.assertTrue(config_path.exists())

            # Reload and verify
            loaded = manager.load()
            self.assertEqual(loaded.directory, "C:/MyBooks/Tech/")
            self.assertEqual(loaded.pattern, "python * clean NOT draft")
            self.assertEqual(loaded.extension, "pdf, epub, -java")
            self.assertEqual(loaded.sort_order, "modified")
            self.assertEqual(loaded.publisher, "packt, manning")
            self.assertEqual(loaded.limit, 50)
            self.assertEqual(loaded.filter_result, "clean")

    def test_load_corrupted_file_returns_defaults(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".filesearch" / "config"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text("{corrupted json content")

            manager = ConfigManager(config_path=config_path)
            loaded = manager.load()
            self.assertEqual(loaded.directory, AppConfig.directory)
            self.assertEqual(loaded.limit, AppConfig.limit)

    def test_load_partial_json_fills_defaults(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".filesearch" / "config"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(json.dumps({"directory": "E:/Books/", "limit": 25}))

            manager = ConfigManager(config_path=config_path)
            loaded = manager.load()
            self.assertEqual(loaded.directory, "E:/Books/")
            self.assertEqual(loaded.limit, 25)
            self.assertEqual(loaded.pattern, AppConfig.pattern)
            self.assertEqual(loaded.extension, AppConfig.extension)


if __name__ == "__main__":
    unittest.main()
