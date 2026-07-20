"""
Shared pytest fixtures for EZSAW tests.

The autouse _clean_prefs fixture ensures each test starts with a
pristine user_prefs.json and that module-level locale/DB config
globals in src.main are re-initialized to English defaults.
"""
import sys
import os
import json
import pytest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

_PREFS_FILE = Path(__file__).resolve().parent.parent / 'config' / 'user_prefs.json'


@pytest.fixture(autouse=True)
def _clean_prefs():
    """Reset user_prefs.json to English defaults before each test,
    re-initialize main module globals, and restore original prefs after."""
    original = _PREFS_FILE.read_text()
    clean = {'locale': 'en'}
    _PREFS_FILE.write_text(json.dumps(clean, indent=2))

    # Re-initialize module-level state so the form uses English locale
    import src.main as main_mod
    from src.core.locale import load_locale_strings, load_db_config_for_locale
    main_mod._LOCALE = load_locale_strings()
    main_mod._APP_CONFIG = load_db_config_for_locale()
    main_mod.DOOR_LOCATIONS = [
        (entry['label'], entry['value'])
        for entry in main_mod._APP_CONFIG['EZ_DOOR_LOCATIONS']
    ]

    yield

    # Restore the original prefs file
    _PREFS_FILE.write_text(original)
