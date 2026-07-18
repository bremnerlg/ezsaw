"""
Locale loading for EZSAW.

Manages UI text strings (from locale_*.json), DB connection configs
(from db_config*.json), and user language/database persistence
(via user_prefs.json).
"""

import json
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / 'config'
_PREFS_FILE = _CONFIG_DIR / 'user_prefs.json'

# ---------------------------------------------------------------------------
# Locale file registry
# ---------------------------------------------------------------------------

_LOCALE_FILES = {
    'en': 'locale_en.json',
    'de': 'locale_de.json',
    'fr': 'locale_fr.json',
    'es': 'locale_es.json',
    'nl': 'locale_nl.json',
}

_SUPPORTED_LOCALES = [
    ('en', 'English'),
    ('de', 'Deutsch'),
    ('fr', 'Français'),
    ('es', 'Español'),
    ('nl', 'Nederlands'),
]


# ---------------------------------------------------------------------------
# User preferences (locale & database selection)
# ---------------------------------------------------------------------------

def load_prefs():
    """Load user preferences from user_prefs.json. Returns defaults if
    the file is missing or corrupt."""
    if _PREFS_FILE.exists():
        try:
            with open(_PREFS_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {'locale': 'en'}


def save_prefs(prefs):
    """Persist user preferences to user_prefs.json."""
    try:
        with open(_PREFS_FILE, 'w') as f:
            json.dump(prefs, f, indent=2)
    except OSError:
        pass


def get_current_locale():
    """Return the currently selected locale code (e.g. 'en', 'de')."""
    prefs = load_prefs()
    return prefs.get('locale', 'en')


def set_locale(locale_code):
    """Set the active locale and persist it."""
    prefs = load_prefs()
    prefs['locale'] = locale_code
    save_prefs(prefs)


# ---------------------------------------------------------------------------
# Locale string loading
# ---------------------------------------------------------------------------

def load_locale_strings(locale_code=None):
    """Load UI text strings for the given locale (or the current one).

    Falls back to English if the requested locale file is missing or corrupt.
    """
    if locale_code is None:
        locale_code = get_current_locale()
    locale_file = _LOCALE_FILES.get(locale_code, _LOCALE_FILES['en'])
    locale_filepath = _CONFIG_DIR / locale_file
    if not locale_filepath.exists():
        locale_filepath = _CONFIG_DIR / _LOCALE_FILES['en']
    try:
        with open(locale_filepath) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return json.loads('{}')


# ---------------------------------------------------------------------------
# DB config loading
# ---------------------------------------------------------------------------

def load_db_config_for_locale(locale_code=None):
    """Load the database connection config for the given locale.

    Resolution order:
      1. Explicit db_config file from user_prefs (if set via DB selector)
      2. Load default db_config.json, then merge locale-specific overrides
      3. Fallback to empty dict
    """
    explicit = get_current_db_config_file()
    if explicit:
        filepath = _CONFIG_DIR / explicit
        if filepath.exists():
            try:
                with open(filepath) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

    db_config = {}
    default_path = _CONFIG_DIR / 'db_config.json'
    try:
        with open(default_path) as f:
            db_config = json.load(f)
    except (json.JSONDecodeError, OSError):
        pass

    locale_strings = load_locale_strings(locale_code)
    config_override_file = locale_strings.get('EZ_DB_CONFIG_FILE', 'db_config.json')
    if config_override_file != 'db_config.json':
        override_filepath = _CONFIG_DIR / config_override_file
        if override_filepath.exists():
            try:
                with open(override_filepath) as f:
                    db_config.update(json.load(f))
            except (json.JSONDecodeError, OSError):
                pass

    # Environment variable overrides (take precedence over file values)
    env_overrides = {
        'EZ_PG_DB': os.environ.get('EZ_PG_DB'),
        'EZ_PG_USER': os.environ.get('EZ_PG_USER'),
        'EZ_PG_PASS': os.environ.get('EZ_PG_PASS'),
        'EZ_PG_HOST': os.environ.get('EZ_PG_HOST'),
        'EZ_PG_PORT': os.environ.get('EZ_PG_PORT'),
    }
    for key, val in env_overrides.items():
        if val is not None:
            db_config[key] = val

    return db_config


# ---------------------------------------------------------------------------
# Supported locales & DB configs
# ---------------------------------------------------------------------------

def get_supported_locales():
    """Return list of (code, display_name) tuples for all supported locales."""
    return list(_SUPPORTED_LOCALES)


def get_supported_db_configs():
    """Return a sorted list of (db_name, config_filename) tuples.

    The default db_config.json is always listed first.
    """
    configs = []
    for filepath in sorted(_CONFIG_DIR.glob('db_config*.json')):
        try:
            with open(filepath) as f:
                data = json.load(f)
            db_name = data.get('EZ_PG_DB', filepath.stem)
            configs.append((db_name, filepath.name))
        except (json.JSONDecodeError, OSError):
            continue
    default = 'db_config.json'
    configs.sort(key=lambda c: (c[1] != default, c[0]))
    return configs


# ---------------------------------------------------------------------------
# DB config file persistence
# ---------------------------------------------------------------------------

def get_current_db_config_file():
    """Return the explicitly selected db_config filename, or None."""
    prefs = load_prefs()
    return prefs.get('db_config')


def set_current_db_config_file(filename):
    """Set the active db_config filename and persist it."""
    prefs = load_prefs()
    prefs['db_config'] = filename
    save_prefs(prefs)


# ---------------------------------------------------------------------------
# Test name translation
# ---------------------------------------------------------------------------

def translate_test_name(name, locale_strings=None):
    """Translate an English test name using the EZ_TEST_NAMES dictionary
    from the locale strings. Returns the original name if no translation
    is found."""
    if locale_strings is None:
        locale_strings = load_locale_strings()
    test_names = locale_strings.get('EZ_TEST_NAMES', {})
    return test_names.get(name, name)
