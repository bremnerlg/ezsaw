"""
Unit tests for auto_stat_facilities.py and locale.py.

Tests data model construction, query builders, locale loading,
DB config selection, and test name translation.
No real database connection required.
"""
import numpy as np

from src.core.auto_stat_facilities import (
    test_case,
    init_test_case,
    init_test_case_list,
    matricize_test_cases,
    build_outlier_query,
    build_outlier_query_by_vehicle,
    build_stat_family_query,
    apply_stat_ordering,
    load_stat_ordering,
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
    load_prefs,
)


# ===========================================================================
# test_case construction & tolerance logic
# ===========================================================================

class TestCaseConstruction:
    """Verify that test_case correctly stores fields and computes
    the out_of_tolerance flag."""

    def test_in_tolerance(self):
        tc = test_case('gap', 10.0, 'mm', 2.0, 3.5, 5.0, 'mm', 'VIN1', 'driver_front')
        assert tc.out_of_tolerance is False

    def test_below_tolerance(self):
        tc = test_case('gap', 10.0, 'mm', 2.0, 1.0, 5.0, 'mm', 'VIN1', 'driver_front')
        assert tc.out_of_tolerance is True

    def test_above_tolerance(self):
        tc = test_case('gap', 10.0, 'mm', 2.0, 6.0, 5.0, 'mm', 'VIN1', 'driver_front')
        assert tc.out_of_tolerance is True

    def test_at_lower_boundary(self):
        tc = test_case('gap', 10.0, 'mm', 2.0, 2.0, 5.0, 'mm', 'VIN1', 'driver_front')
        assert tc.out_of_tolerance is False

    def test_at_upper_boundary(self):
        tc = test_case('gap', 10.0, 'mm', 2.0, 5.0, 5.0, 'mm', 'VIN1', 'driver_front')
        assert tc.out_of_tolerance is False

    def test_fields_stored(self):
        tc = test_case('flush', 7.5, 'in', 0.5, 1.2, 2.0, 'in', 'VIN2', 'rear_hatch')
        assert tc.name == 'flush'
        assert tc.result_x == 7.5
        assert tc.result_x_unit == 'in'
        assert tc.result_y_lower == 0.5
        assert tc.result_y == 1.2
        assert tc.result_y_upper == 2.0
        assert tc.result_y_unit == 'in'
        assert tc.vehicle == 'VIN2'
        assert tc.location == 'rear_hatch'

    def test_vehicle_fields_stored(self):
        tc = test_case('gap', 10.0, 'mm', 2.0, 3.5, 5.0, 'mm', 'VIN99',
                       'driver_front', make='Honda', model='Accord',
                       mandate='2021-03-15')
        assert tc.make == 'Honda'
        assert tc.model == 'Accord'
        assert tc.mandate == '2021-03-15'
        assert tc.vehicle == 'VIN99'


# ===========================================================================
# init_test_case / init_test_case_list
# ===========================================================================

SAMPLE_ROW = {
    'test_name': 'gap',
    'result_x': 10.0,
    'result_x_unit': 'mm',
    'result_y_lower_lim': 2.0,
    'result_y': 3.5,
    'result_y_upper_lim': 5.0,
    'result_y_unit': 'mm',
    'vin': 'VIN1',
    'door_location': 'driver_front',
    'make': 'Honda',
    'model': 'Civic',
    'manufacture_date': '2022-03-14',
}


class TestInitTestCase:
    """Verify raw dict → test_case conversion."""

    def test_creates_test_case(self):
        tc = init_test_case(SAMPLE_ROW)
        assert isinstance(tc, test_case)
        assert tc.name == 'gap'
        assert tc.vehicle == 'VIN1'
        assert tc.make == 'Honda'
        assert tc.model == 'Civic'
        assert tc.mandate == '2022-03-14'

    def test_init_test_case_list(self):
        rows = [SAMPLE_ROW, SAMPLE_ROW]
        cases = init_test_case_list(rows)
        assert len(cases) == 2
        assert all(isinstance(tc, test_case) for tc in cases)

    def test_empty_list(self):
        assert init_test_case_list([]) == []


# ===========================================================================
# matricize_test_cases
# ===========================================================================

class TestMatricize:
    """Verify that test_case lists are correctly converted to
    (2, n) numpy matrices for plotting."""

    def _make_tc(self, x, y, name='gap'):
        return test_case(name, x, 'mm', 0.0, y, 100.0, 'mm', 'V', 'df',
                         make='Honda', model='Civic', mandate='2022-03-14')

    def test_empty_input(self):
        result = matricize_test_cases([])
        assert result.shape == (2, 0)

    def test_single_stat(self):
        tc = self._make_tc(1.0, 2.0)
        result = matricize_test_cases([tc])
        assert result.shape == (2, 1)
        assert result[0, 0] == 1.0
        assert result[1, 0] == 2.0

    def test_multiple_same_name(self):
        cases = [self._make_tc(i, i * 10) for i in range(5)]
        result = matricize_test_cases(cases)
        assert result.shape == (2, 5)
        np.testing.assert_array_equal(result[0], [0, 1, 2, 3, 4])
        np.testing.assert_array_equal(result[1], [0, 10, 20, 30, 40])

    def test_stops_at_different_name(self):
        cases = [
            self._make_tc(1, 10, 'gap'),
            self._make_tc(2, 20, 'gap'),
            self._make_tc(3, 30, 'flush'),
            self._make_tc(4, 40, 'flush'),
        ]
        result = matricize_test_cases(cases)
        assert result.shape == (2, 2)
        np.testing.assert_array_equal(result[0], [1, 2])
        np.testing.assert_array_equal(result[1], [10, 20])

    def test_empty_name_includes_all(self):
        cases = [
            self._make_tc(1, 10, ''),
            self._make_tc(2, 20, ''),
            self._make_tc(3, 30, 'gap'),
        ]
        result = matricize_test_cases(cases)
        # Empty name branch includes all entries regardless of name
        assert result.shape[1] == 3


# ===========================================================================
# SQL query builders
# ===========================================================================

class TestQueryBuilders:
    """Verify that query builders produce correct SQL structure
    with proper JOINs, WHERE clauses, and parameter placeholders."""

    CONFIG = {
        'EZ_VEHICLES_TABLE_NAME': 'vehicles',
        'EZ_VEHICLES_PK': 'vin',
        'EZ_VEHICLES_MAKE_FIELD': 'make',
        'EZ_VEHICLES_MODEL_FIELD': 'model',
        'EZ_VEHICLES_MAN_DATE_FIELD': 'manufacture_date',
        'EZ_STAT_TABLE_NAME': 'auto_door_stats',
        'EZ_STAT_TABLE_PK': 'auto_door_stat_id',
        'EZ_STAT_NAME_FIELD': 'auto_door_stat_name',
        'EZ_STAT_INDEPENDENT_VAR_FIELD': 'result_x',
        'EZ_STAT_INDEPENDENT_VAR_UNIT_FIELD': 'result_x_unit',
        'EZ_STAT_DEPENDENT_VAR_LOWER_LIM_FIELD': 'result_y_lower_lim',
        'EZ_STAT_DEPENDENT_VAR_FIELD': 'result_y',
        'EZ_STAT_DEPENDENT_VAR_UPPER_LIM_FIELD': 'result_y_upper_lim',
        'EZ_STAT_DEPENDENT_VAR_UNIT_FIELD': 'result_y_unit',
        'EZ_JOINT_TABLE_NAME': 'steps',
        'EZ_JOINT_TABLE_STAT_FK': 'fk_steps_auto_door_stats',
        'EZ_JOINT_TABLE_DOOR_LOCATION_FIELD': 'door',
    }

    def test_outlier_query_has_where_clause(self):
        q = build_outlier_query(self.CONFIG)
        assert '"auto_door_stats"."result_y" < "auto_door_stats"."result_y_lower_lim"' in q
        assert '"auto_door_stats"."result_y" > "auto_door_stats"."result_y_upper_lim"' in q
        assert '%s' in q
        assert '"vehicles"."make"  AS make' in q
        assert '"vehicles"."model" AS model' in q
        assert '"vehicles"."manufacture_date" AS manufacture_date' in q
        assert 'JOIN "vehicles" ON' in q

    def test_stat_family_query_filters_name_and_door(self):
        q = build_stat_family_query(self.CONFIG)
        assert '"auto_door_stats"."auto_door_stat_name" = %s' in q
        assert '"steps"."door" = %s' in q
        assert 'JOIN' in q

    def test_outlier_query_by_vehicle_joins_vehicles(self):
        q = build_outlier_query_by_vehicle(self.CONFIG)
        assert 'JOIN "vehicles" ON' in q
        assert '"vehicles"."make" = %s' in q
        assert '"vehicles"."model" = %s' in q
        assert 'EXTRACT(YEAR FROM "vehicles"."manufacture_date")' in q
        assert '"auto_door_stats"."result_y" < "auto_door_stats"."result_y_lower_lim"' in q
        assert '"vehicles"."make"  AS make' in q
        assert '"vehicles"."model" AS model' in q
        assert '"vehicles"."manufacture_date"  AS manufacture_date' in q


# ===========================================================================
# Locale loading
# ===========================================================================

class TestLocale:
    """Verify locale string loading for all supported languages,
    fallback behaviour, and placeholder consistency."""

    def test_load_english_strings(self):
        strings = load_locale_strings('en')
        assert strings['EZ_LOCALE_CODE'] == 'en'
        assert strings['EZ_WINDOW_TITLE'] == 'EZSAW Version 4.0.0 Beta'
        assert 'EZ_BTN_QUERY' in strings
        assert 'EZ_STATUS_READY' in strings

    def test_load_german_strings(self):
        strings = load_locale_strings('de')
        assert strings['EZ_LOCALE_CODE'] == 'de'
        assert 'Deutsch' in strings['EZ_APP_TITLE'] or 'Statistisch' in strings['EZ_APP_TITLE']
        assert strings['EZ_BTN_QUERY'] == 'Abfragen'

    def test_load_french_strings(self):
        strings = load_locale_strings('fr')
        assert strings['EZ_LOCALE_CODE'] == 'fr'
        assert strings['EZ_BTN_QUERY'] == 'Requête'

    def test_load_spanish_strings(self):
        strings = load_locale_strings('es')
        assert strings['EZ_LOCALE_CODE'] == 'es'
        assert strings['EZ_BTN_QUERY'] == 'Consultar'

    def test_load_dutch_strings(self):
        strings = load_locale_strings('nl')
        assert strings['EZ_LOCALE_CODE'] == 'nl'
        assert strings['EZ_BTN_QUERY'] == 'Opvragen'

    def test_unknown_locale_falls_back_to_english(self):
        strings = load_locale_strings('xx')
        assert strings['EZ_LOCALE_CODE'] == 'en'

    def test_all_locales_have_same_keys(self):
        base_keys = set(load_locale_strings('en').keys())
        for code, _ in get_supported_locales():
            keys = set(load_locale_strings(code).keys())
            assert keys == base_keys, f'{code} has different keys'

    def test_format_placeholders_present(self):
        strings = load_locale_strings('en')
        assert '{label}' in strings['EZ_STATUS_NO_OUTLIERS']
        assert '{count}' in strings['EZ_STATUS_FOUND_OUTLIERS']
        assert '{vin}' in strings['EZ_STATUS_VIN_FORMAT']
        assert '{name}' in strings['EZ_STATUS_VIN_FORMAT']
        assert '{location}' in strings['EZ_STATUS_VIN_FORMAT']

    def test_db_config_for_locale_loads_correctly(self):
        cfg = load_db_config_for_locale('en')
        assert cfg['EZ_PG_DB'] == 'ezsaw3'
        cfg_de = load_db_config_for_locale('de')
        assert cfg_de['EZ_PG_DB'] == 'ezsaw_de'

    def test_supported_locales_returns_list(self):
        locales = get_supported_locales()
        assert isinstance(locales, list)
        assert len(locales) == 5
        codes = [code for code, _ in locales]
        assert 'en' in codes
        assert 'de' in codes

    def test_set_and_load_prefs(self):
        original_prefs = load_prefs()
        original_locale = original_prefs.get('locale', 'en')
        try:
            set_locale('de')
            assert get_current_locale() == 'de'
            set_locale('fr')
            assert get_current_locale() == 'fr'
        finally:
            set_locale(original_locale)

    def test_load_prefs_corrupt_file(self):
        import src.core.locale as locale_mod
        prefs_file = locale_mod._PREFS_FILE
        original_content = prefs_file.read_text()
        try:
            prefs_file.write_text('{corrupt json!!!')
            prefs = load_prefs()
            assert prefs == {'locale': 'en'}
        finally:
            prefs_file.write_text(original_content)


# ===========================================================================
# Database config selector
# ===========================================================================

class TestDbConfig:
    """Verify DB config discovery, ordering, and persistence."""

    def test_supported_db_configs_returns_list(self):
        configs = get_supported_db_configs()
        assert isinstance(configs, list)
        assert len(configs) >= 5

    def test_supported_db_configs_contain_expected_files(self):
        configs = get_supported_db_configs()
        files = [f for _, f in configs]
        assert 'db_config.json' in files
        assert 'db_config_de.json' in files
        assert 'db_config_fr.json' in files
        assert 'db_config_es.json' in files
        assert 'db_config_nl.json' in files

    def test_supported_db_configs_have_db_names(self):
        configs = get_supported_db_configs()
        names = [n for n, _ in configs]
        assert 'ezsaw3' in names
        assert 'ezsaw_de' in names

    def test_db_config_default_first(self):
        configs = get_supported_db_configs()
        assert configs[0][1] == 'db_config.json'

    def test_set_and_load_db_config(self):
        original = get_current_db_config_file()
        try:
            set_current_db_config_file('db_config_de.json')
            assert get_current_db_config_file() == 'db_config_de.json'
        finally:
            if original:
                set_current_db_config_file(original)
            else:
                prefs = load_prefs()
                prefs.pop('db_config', None)
                from src.core.locale import save_prefs
                save_prefs(prefs)

    def test_load_db_config_explicit_overrides_locale(self):
        original = get_current_db_config_file()
        try:
            set_current_db_config_file('db_config_de.json')
            cfg = load_db_config_for_locale('en')
            assert cfg['EZ_PG_DB'] == 'ezsaw_de'
        finally:
            if original:
                set_current_db_config_file(original)
            else:
                prefs = load_prefs()
                prefs.pop('db_config', None)
                from src.core.locale import save_prefs
                save_prefs(prefs)

    def test_load_db_config_falls_back_to_locale(self):
        original = get_current_db_config_file()
        try:
            prefs = load_prefs()
            prefs.pop('db_config', None)
            from src.core.locale import save_prefs
            save_prefs(prefs)
            cfg = load_db_config_for_locale('de')
            assert cfg['EZ_PG_DB'] == 'ezsaw_de'
        finally:
            if original:
                set_current_db_config_file(original)


# ===========================================================================
# Test name translation
# ===========================================================================

class TestTranslateTestName:
    """Verify that English test names are correctly translated
    using the EZ_TEST_NAMES dictionary in each locale."""

    def test_english_identity(self):
        strings = load_locale_strings('en')
        name = 'Striker Alignment (Sampled)'
        assert translate_test_name(name, strings) == name

    def test_german_translates(self):
        strings = load_locale_strings('de')
        name = 'Striker Alignment (Sampled)'
        result = translate_test_name(name, strings)
        assert result != name
        assert 'Schließbolzen' in result

    def test_french_translates(self):
        strings = load_locale_strings('fr')
        name = 'Seal Dynamics (Sampled)'
        result = translate_test_name(name, strings)
        assert result != name
        assert 'joint' in result

    def test_spanish_translates(self):
        strings = load_locale_strings('es')
        name = 'Static Closing Force (Sampled)'
        result = translate_test_name(name, strings)
        assert result != name
        assert 'cierre' in result

    def test_dutch_translates(self):
        strings = load_locale_strings('nl')
        name = 'Hinge Bind (Sampled)'
        result = translate_test_name(name, strings)
        assert result != name
        assert 'scharnier' in result.lower()

    def test_unknown_name_passes_through(self):
        strings = load_locale_strings('en')
        name = 'Some Unknown Test (Foo)'
        assert translate_test_name(name, strings) == name

    def test_all_names_translated_for_each_locale(self):
        english_names = [
            'Closing Energy from First Position (Sampled)',
            'Closing Energy from Full Open (Sampled)',
            'Door Check Performance No Cabin (Sampled)',
            'Hinge and Doorcheck Performance (Sampled)',
            'Hinge Bind (Sampled)',
            'Hinge Inclination (Sampled)',
            'Seal Dynamics (Sampled)',
            'Static Closing Force (Sampled)',
            'Striker Alignment (Sampled)',
        ]
        for code, _ in get_supported_locales():
            strings = load_locale_strings(code)
            test_names = strings.get('EZ_TEST_NAMES', {})
            for name in english_names:
                assert name in test_names, f'{name} missing from {code}'


# ===========================================================================
# Stat ordering
# ===========================================================================

class TestStatOrdering:
    """Verify that apply_stat_ordering correctly reorders stats
    according to stat_ordering.json branch rules."""

    def _make_tc(self, name, x=1.0, y=2.0):
        return test_case(name, x, 'mm', 0.0, y, 100.0, 'mm', 'V', 'df',
                         make='Honda', model='Civic', mandate='2022-03-14')

    def test_load_stat_ordering_returns_dict(self):
        ordering = load_stat_ordering()
        assert 'default_order' in ordering
        assert 'branches' in ordering

    def test_alphabetical_default(self):
        stats = [
            self._make_tc('zebra'),
            self._make_tc('alpha'),
            self._make_tc('gamma'),
        ]
        result = apply_stat_ordering(stats)
        assert [s.name for s in result] == ['alpha', 'gamma', 'zebra']

    def test_empty_list(self):
        assert apply_stat_ordering([]) == []

    def test_single_stat(self):
        stats = [self._make_tc('alpha')]
        result = apply_stat_ordering(stats)
        assert len(result) == 1
        assert result[0].name == 'alpha'

    def test_branch_ordering_applied(self):
        stats = [
            self._make_tc('Hinge Bind (Sampled)'),
            self._make_tc('Striker Alignment (Sampled)'),
            self._make_tc('Closing Energy from First Position (Sampled)'),
        ]
        result = apply_stat_ordering(stats)
        # The branch in stat_ordering.json should reorder these
        assert result[0].name == 'Striker Alignment (Sampled)'
        assert result[1].name == 'Hinge Bind (Sampled)'
        assert result[2].name == 'Closing Energy from First Position (Sampled)'
