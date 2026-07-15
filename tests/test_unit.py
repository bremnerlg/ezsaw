"""Unit tests for auto_stat_facilities.py — no real DB required."""
import numpy as np

from src.core.auto_stat_facilities import (
    test_case,
    init_test_case,
    init_test_case_list,
    matricize_test_cases,
    build_outlier_query,
    build_stat_family_query,
    door_location,
)


# ---------------------------------------------------------------------------
# test_case construction & tolerance logic
# ---------------------------------------------------------------------------

class TestCaseConstruction:
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


# ---------------------------------------------------------------------------
# init_test_case / init_test_case_list
# ---------------------------------------------------------------------------

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
}


class TestInitTestCase:
    def test_creates_test_case(self):
        tc = init_test_case(SAMPLE_ROW)
        assert isinstance(tc, test_case)
        assert tc.name == 'gap'
        assert tc.vehicle == 'VIN1'

    def test_init_test_case_list(self):
        rows = [SAMPLE_ROW, SAMPLE_ROW]
        cases = init_test_case_list(rows)
        assert len(cases) == 2
        assert all(isinstance(tc, test_case) for tc in cases)

    def test_empty_list(self):
        assert init_test_case_list([]) == []


# ---------------------------------------------------------------------------
# matricize_test_cases
# ---------------------------------------------------------------------------

class TestMatricize:
    def _make_tc(self, x, y, name='gap'):
        return test_case(name, x, 'mm', 0.0, y, 100.0, 'mm', 'V', 'df')

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
        # empty name branch includes all
        assert result.shape[1] == 3


# ---------------------------------------------------------------------------
# SQL query builders
# ---------------------------------------------------------------------------

class TestQueryBuilders:
    CONFIG = {
        'EZ_VEHICLES_TABLE_NAME': 'vehicles',
        'EZ_VEHICLES_PK': 'vin',
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
        assert 'auto_door_stats.result_y < auto_door_stats.result_y_lower_lim' in q
        assert 'auto_door_stats.result_y > auto_door_stats.result_y_upper_lim' in q
        assert '%s' in q

    def test_stat_family_query_filters_name_and_door(self):
        q = build_stat_family_query(self.CONFIG)
        assert 'auto_door_stat_name = %s' in q
        assert 'door = %s' in q
        assert 'JOIN' in q


# ---------------------------------------------------------------------------
# door_location enum
# ---------------------------------------------------------------------------

class TestDoorLocation:
    def test_values(self):
        assert door_location.DRIVER_FRONT.value == 'driver_front'
        assert door_location.REAR_HATCH.value == 'trunk/hatch'
        assert door_location.HOOD.value == 'hood'
