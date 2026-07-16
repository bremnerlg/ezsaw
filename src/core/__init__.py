"""
EZSAW core package.

Re-exports public API from the database query layer and locale system
so consumers can do: from src.core import vin_query, load_locale_strings
"""
from src.core.auto_stat_facilities import (
    test_case,
    vin_query,
    vehicle_query,
    fetch_stat_family,
    fetch_makes,
    fetch_models,
    fetch_years,
    init_test_case,
    init_test_case_list,
    matricize_test_cases,
    build_outlier_query,
    build_outlier_query_by_vehicle,
    build_stat_family_query,
    load_db_config,
    ezsaw_default_connect,
)
from src.core.locale import (
    load_locale_strings,
    load_db_config_for_locale,
    get_current_locale,
    set_locale,
    get_supported_locales,
    get_supported_db_configs,
    get_current_db_config_file,
    set_current_db_config_file,
    translate_test_name,
    save_prefs,
    load_prefs,
)
