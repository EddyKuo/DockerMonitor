"""Translation manager for i18n support."""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class TranslationManager:
    """Manages translations for different languages."""

    def __init__(self, locale: str = "en"):
        """
        Initialize translation manager.

        Args:
            locale: Language locale (e.g., 'en', 'zh_TW').
        """
        self.locale = locale
        self._translations: Dict[str, Any] = {}
        self._load_translations()

    def _load_translations(self) -> None:
        """Load translation file for current locale."""
        locales_dir = Path(__file__).parent.parent.parent / "locales"
        locale_file = locales_dir / f"{self.locale}.yaml"

        if not locale_file.exists():
            # Fallback to English
            locale_file = locales_dir / "en.yaml"
            if not locale_file.exists():
                # If even English doesn't exist, use empty dict
                self._translations = {}
                return

        try:
            with open(locale_file, "r", encoding="utf-8") as f:
                self._translations = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Error loading translations: {e}")
            self._translations = {}

    def get(self, key: str, **kwargs) -> str:
        """
        Get translated string for key.

        Args:
            key: Translation key (dot notation supported, e.g., 'ui.title').
            **kwargs: Format arguments for string interpolation.

        Returns:
            Translated string, or key if not found.
        """
        # Navigate nested dictionary with dot notation
        keys = key.split(".")
        value = self._translations

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                # Return key if not found
                return key

        # Format string if kwargs provided
        if kwargs and isinstance(value, str):
            try:
                return value.format(**kwargs)
            except KeyError:
                return value

        return str(value)

    def t(self, key: str, **kwargs) -> str:
        """Alias for get() method."""
        return self.get(key, **kwargs)

    def set_locale(self, locale: str) -> None:
        """
        Change current locale.

        Args:
            locale: New locale code.
        """
        self.locale = locale
        self._load_translations()


# Global translator instance
_translator: Optional[TranslationManager] = None


def get_translator(locale: Optional[str] = None) -> TranslationManager:
    """
    Get global translator instance.

    Args:
        locale: Optional locale to set. If None, uses existing or default.

    Returns:
        TranslationManager instance.
    """
    global _translator

    if _translator is None:
        _translator = TranslationManager(locale or "en")
    elif locale and locale != _translator.locale:
        _translator.set_locale(locale)

    return _translator
