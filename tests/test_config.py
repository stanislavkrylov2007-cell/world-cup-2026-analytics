"""Tests for application configuration."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from world_cup_analytics.config import AppConfig, load_config


class TestConfig(unittest.TestCase):
    """Test cases for configuration loading."""

    def test_load_config_reads_required_values(self) -> None:
        """Configuration should be built from environment variables."""
        env = {
            "APP_ENV": "test",
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "DB_NAME": "wc_analytics",
            "DB_USER": "postgres",
            "DB_PASSWORD": "secret",
        }

        with patch.dict(os.environ, env, clear=False):
            config = load_config()

        self.assertIsInstance(config, AppConfig)
        self.assertEqual(config.app_env, "test")
        self.assertEqual(config.db_host, "localhost")
        self.assertEqual(config.db_port, 5432)
        self.assertEqual(config.db_name, "wc_analytics")
        self.assertEqual(config.db_user, "postgres")
        self.assertEqual(config.db_password, "secret")

    def test_load_config_raises_for_missing_required_value(self) -> None:
        """Missing required variables should produce a clear error."""
        env = {
            "DB_NAME": "wc_analytics",
            "DB_USER": "postgres",
            "DB_PASSWORD": "secret",
        }

        with patch.dict(os.environ, env, clear=True):
            with self.assertRaisesRegex(ValueError, "DB_HOST"):
                load_config()


if __name__ == "__main__":
    unittest.main()
