"""
Configuration Module

Manages application settings and user preferences.
Loads configuration from JSON files and provides easy access to settings.
"""

import json
import os
from typing import Any, Dict, Optional


class Config:
    """
    Configuration manager for the Amazon Firefly III integration.

    Handles loading and accessing configuration settings from JSON files.
    Provides default values and type-safe access to configuration options.
    """

    def __init__(self, config_file: str = "config/settings.json"):
        """
        Initialize configuration manager.

        Args:
            config_file: Path to configuration JSON file
        """
        self.config_file = config_file
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """
        Load configuration from JSON file.
        Uses default values if file doesn't exist or is invalid.
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                print(f"Loaded configuration from {self.config_file}")
            else:
                print(f"Configuration file {self.config_file} not found, using defaults")
                self._config = self._get_default_config()
        except json.JSONDecodeError as e:
            print(f"Error parsing configuration file: {e}")
            print("Using default configuration")
            self._config = self._get_default_config()
        except Exception as e:
            print(f"Error loading configuration: {e}")
            print("Using default configuration")
            self._config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration values.

        Returns:
            Dictionary with default configuration
        """
        return {
            "amazon_url": "https://www.amazon.it",
            "order_history_url": "https://www.amazon.it/gp/your-account/order-history",
            "output_dir": "output",
            "session_file": "config/session.pkl",
            "date_format": "%Y-%m-%d",
            "csv_delimiter": ",",
            "max_orders_per_page": 10,
            "page_load_timeout": 30,
            "element_wait_timeout": 10,
            "start_year": None,  # None means current year
            "end_year": None,    # None means current year
            "headless_mode": False,
            "debug_mode": False
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.

        Args:
            key: Configuration key
            value: Value to set
        """
        self._config[key] = value

    def save(self) -> bool:
        """
        Save current configuration to file.

        Returns:
            True if save successful, False otherwise
        """
        try:
            # Ensure config directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)

            print(f"Configuration saved to {self.config_file}")
            return True

        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False

    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values.

        Returns:
            Copy of configuration dictionary
        """
        return self._config.copy()

    def update_from_dict(self, updates: Dict[str, Any]) -> None:
        """
        Update configuration from dictionary.

        Args:
            updates: Dictionary with configuration updates
        """
        self._config.update(updates)

    def validate(self) -> bool:
        """
        Validate configuration values.

        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Validate URLs
            amazon_url = self.get('amazon_url', '')
            if not amazon_url.startswith('https://'):
                print("Warning: amazon_url should start with https://")

            order_history_url = self.get('order_history_url', '')
            if not order_history_url.startswith('https://'):
                print("Warning: order_history_url should start with https://")

            # Validate timeouts
            timeouts = ['page_load_timeout', 'element_wait_timeout']
            for timeout_key in timeouts:
                timeout = self.get(timeout_key, 0)
                if not isinstance(timeout, (int, float)) or timeout <= 0:
                    print(f"Warning: {timeout_key} should be a positive number")

            # Validate output directory
            output_dir = self.get('output_dir', '')
            if output_dir and not os.path.isdir(output_dir):
                try:
                    os.makedirs(output_dir, exist_ok=True)
                except Exception as e:
                    print(f"Warning: Cannot create output directory {output_dir}: {e}")

            return True

        except Exception as e:
            print(f"Configuration validation error: {e}")
            return False

    def __str__(self) -> str:
        """String representation of configuration."""
        return f"Config(file='{self.config_file}', keys={list(self._config.keys())})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Config(config_file='{self.config_file}', config={self._config})"