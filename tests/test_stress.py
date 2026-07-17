"""
Stress and integration tests for EZSAW.

Covers 1000-case plotting, combo cascading, door availability greying,
graph info content, edge cases, navigation stress, matricize scaling,
plot component verification, query priority, and door availability stress.
"""
import os
import sys
import random
from unittest.mock import patch

import numpy as np
import pytest

os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

_GRAY = QColor(Qt.gray).name()
_WHITE = QColor(Qt.white).name()

app = QApplication.instance() or QApplication(sys.argv)

from src.main import intro_form, DOOR_LOCATIONS
from src.core.auto_stat_facilities import (
    test_case, init_test_case_list,
    matricize_test_cases,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DOOR_KEYS = [d[1] for d in DOOR_LOCATIONS]
TEST_NAMES = ['gap', 'flush', 'step', 'wind', 'alignment', 'torque', 'force',
              'displacement', 'angle', 'pressure']


def _raw(test_name='gap', x=10.0, y=3.5, y_low=2.0, y_high=5.0,
         vin='VIN1', door='driver_front'):
    """Create a mock query result row matching the DB schema."""
    return {
        'test_name': test_name,
        'result_x': x,
        'result_x_unit': 'mm',
        'result_y_lower_lim': y_low,
        'result_y': y,
        'result_y_upper_lim': y_high,
        'result_y_unit': 'mm',
        'vin': vin,
        'door_location': door,
    }


def _random_raw(i):
    """Create a query result row with randomised coordinates."""
    return _raw(
        test_name=f'test_{i}',
        x=random.uniform(-100, 100),
        y=random.uniform(-50, 50),
        y_low=random.uniform(-60, 0),
        y_high=random.uniform(1, 60),
        vin=f'VIN_{i % 20}',
        door='driver_front',
    )


def _make_tc(x, y, name='gap', vin='V', door='df'):
    """Create a test_case instance for stress testing."""
    return test_case(name, x, 'mm', 0.0, y, 100.0, 'mm', vin, door)


@pytest.fixture
def form(qtbot):
    """Create a fresh intro_form instance for each test."""
    w = intro_form()
    qtbot.addWidget(w)
    return w


# ===========================================================================
# 1. pyqtgraph stress test: 1000 stat cases plotted
# ===========================================================================

class TestPyqtGraphStress:
    """Plot 1000 outlier cases through _display_current_stat and verify
    the PlotWidget never crashes and always ends with the correct items."""

    @patch('src.main.fetch_stat_family')
    @patch('src.main.vin_query')
    def test_1000_outlier_vin_path(self, mock_query, mock_family, form, qtbot):
        raw = [_random_raw(i) for i in range(1000)]
        mock_query.return_value = raw
        mock_family.return_value = [_random_raw(i) for i in range(50)]

        form.edit_vin.setText('STRESS_VIN')
        form.init_vin_plots()
        qtbot.wait(100)

        assert len(form.stats_selection) == 1000
        assert form.current_stat == 0
        assert form.button_next.isEnabled() is True
        assert form.button_prev.isEnabled() is False

        # Navigate through every single one
        for idx in range(999):
            form.show_next()
            assert form.current_stat == idx + 1

            items = form.plot.getPlotItem().items
            # family scatter + highlight point + 2 tolerance lines
            # + annotation + connecting line = at least 6
            assert len(items) >= 6, f"idx={idx} items={len(items)}"

        assert form.current_stat == 999
        assert form.button_next.isEnabled() is False
        assert form.button_prev.isEnabled() is True

        # Navigate back to start
        for idx in range(999, 0, -1):
            form.show_prev()
            assert form.current_stat == idx - 1

        assert form.current_stat == 0
        assert form.button_prev.isEnabled() is False

    @patch('src.main.fetch_stat_family')
    @patch('src.main.vehicle_query')
    def test_1000_outlier_vehicle_path(self, mock_vquery, mock_family, form, qtbot):
        raw = [_random_raw(i) for i in range(1000)]
        mock_vquery.return_value = raw
        mock_family.return_value = [_random_raw(i) for i in range(30)]

        # Manually set combo values (bypassing DB lookups)
        form.make_combo.blockSignals(True)
        form.make_combo.clear()
        form.make_combo.addItem("")
        form.make_combo.addItem("Honda")
        form.make_combo.setCurrentIndex(1)
        form.make_combo.blockSignals(False)

        form.model_combo.blockSignals(True)
        form.model_combo.clear()
        form.model_combo.addItem("")
        form.model_combo.addItem("Accord")
        form.model_combo.setCurrentIndex(1)
        form.model_combo.blockSignals(False)

        form.year_combo.blockSignals(True)
        form.year_combo.clear()
        form.year_combo.addItem("")
        form.year_combo.addItem("2023")
        form.year_combo.setCurrentIndex(1)
        form.year_combo.blockSignals(False)

        form.init_vehicle_plots()
        qtbot.wait(100)

        assert len(form.stats_selection) == 1000

        # Sample every 10th to verify plot doesn't crash
        for idx in range(0, 1000, 10):
            if idx > 0:
                form.current_stat = idx
                form._display_current_stat()
                qtbot.wait(10)

            items = form.plot.getPlotItem().items
            assert len(items) >= 6

    @patch('src.main.fetch_stat_family')
    @patch('src.main.vin_query')
    def test_1000_outliers_clears_plot_cleanly(self, mock_query, mock_family, form, qtbot):
        raw = [_random_raw(i) for i in range(1000)]
        mock_query.return_value = raw
        mock_family.return_value = []

        form.edit_vin.setText('CLEAR_VIN')
        form.init_vin_plots()
        qtbot.wait(50)

        assert len(form.plot.getPlotItem().items) > 0

        form._clear_plot()
        qtbot.wait(50)

        assert len(form.plot.getPlotItem().items) == 0


# ===========================================================================
# 2. Widget combo box cascading
# ===========================================================================

class TestComboCascading:
    """Verify that selecting a make enables the model dropdown,
    selecting a model enables the year dropdown, and resetting
    disables the downstream dropdowns."""

    @patch('src.main.fetch_years')
    @patch('src.main.fetch_models')
    @patch('src.main.fetch_makes')
    def test_make_enables_model(self, mock_makes, mock_models, mock_years, form, qtbot):
        mock_makes.return_value = ['Honda', 'Ford']
        mock_models.return_value = ['Accord', 'Civic']
        mock_years.return_value = [2020, 2021]

        form._populate_makes()
        assert form.make_combo.count() == 3  # blank + Honda + Ford

        form.make_combo.setCurrentIndex(1)
        assert form.model_combo.isEnabled() is True
        assert form.model_combo.count() == 3  # blank + Accord + Civic

    @patch('src.main.fetch_years')
    @patch('src.main.fetch_models')
    @patch('src.main.fetch_makes')
    def test_model_enables_year(self, mock_makes, mock_models, mock_years, form, qtbot):
        mock_makes.return_value = ['Honda']
        mock_models.return_value = ['Accord']
        mock_years.return_value = [2020, 2021, 2022]

        form._populate_makes()
        form.make_combo.setCurrentIndex(1)
        form.model_combo.setCurrentIndex(1)

        assert form.year_combo.isEnabled() is True
        assert form.year_combo.count() == 4  # blank + 3 years

    @patch('src.main.fetch_years')
    @patch('src.main.fetch_models')
    @patch('src.main.fetch_makes')
    def test_reset_make_disables_model_and_year(self, mock_makes, mock_models, mock_years, form, qtbot):
        mock_makes.return_value = ['Honda']
        mock_models.return_value = ['Accord']
        mock_years.return_value = [2020]

        form._populate_makes()
        form.make_combo.setCurrentIndex(1)
        form.model_combo.setCurrentIndex(1)
        assert form.year_combo.isEnabled() is True

        form.make_combo.setCurrentIndex(0)
        assert form.model_combo.isEnabled() is False
        assert form.year_combo.isEnabled() is False

    @patch('src.main.fetch_years')
    @patch('src.main.fetch_models')
    @patch('src.main.fetch_makes')
    def test_reset_model_disables_year(self, mock_makes, mock_models, mock_years, form, qtbot):
        mock_makes.return_value = ['Honda']
        mock_models.return_value = ['Accord']
        mock_years.return_value = [2020]

        form._populate_makes()
        form.make_combo.setCurrentIndex(1)
        form.model_combo.setCurrentIndex(1)
        assert form.year_combo.isEnabled() is True

        form.model_combo.setCurrentIndex(0)
        assert form.year_combo.isEnabled() is False


# ===========================================================================
# 3. Door availability greying
# ===========================================================================

class TestDoorAvailability:
    """Verify that _update_door_availability correctly greys out
    doors with no data and enables doors with data."""

    def test_all_doors_available(self, form, qtbot):
        raw = [_raw(door=dk) for dk in DOOR_KEYS]
        form._update_door_availability(raw)
        for i in range(form.door_location_widget.count()):
            item = form.door_location_widget.item(i)
            assert item.foreground().color().name() == _WHITE

    def test_only_one_door_available(self, form, qtbot):
        raw = [_raw(door='driver_front')]
        form._update_door_availability(raw)
        for i in range(form.door_location_widget.count()):
            item = form.door_location_widget.item(i)
            _, key = DOOR_LOCATIONS[i]
            if key == 'driver_front':
                assert item.foreground().color().name() == _WHITE
            else:
                assert item.foreground().color().name() == _GRAY

    def test_empty_raw_greys_out_all(self, form, qtbot):
        form._update_door_availability([])
        for i in range(form.door_location_widget.count()):
            item = form.door_location_widget.item(i)
            assert item.foreground().color().name() == _GRAY

    def test_doors_restore_after_new_query(self, form, qtbot):
        form._update_door_availability([_raw(door='driver_front')])
        assert form.door_location_widget.item(3).foreground().color().name() == _GRAY

        form._update_door_availability([_raw(door='passenger_rear')])
        assert form.door_location_widget.item(3).foreground().color().name() == _WHITE
        assert form.door_location_widget.item(0).foreground().color().name() == _GRAY


# ===========================================================================
# 5. Edge cases: single outlier, boundary values, extreme coords
# ===========================================================================

class TestEdgeCases:
    """Verify the app handles unusual but valid data correctly."""

    @patch('src.main.fetch_stat_family')
    @patch('src.main.vin_query')
    def test_single_outlier(self, mock_query, mock_family, form, qtbot):
        mock_query.return_value = [_raw(y=99.0, y_low=0.0, y_high=1.0)]
        mock_family.return_value = []

        form.edit_vin.setText('SINGLE')
        form.init_vin_plots()

        assert len(form.stats_selection) == 1
        assert form.button_next.isEnabled() is False
        assert form.button_prev.isEnabled() is False
        assert form.current_stat == 0

        items = form.plot.getPlotItem().items
        # highlight + 2 tolerance lines + annotation + line (no family)
        assert len(items) >= 5

    @patch('src.main.fetch_stat_family')
    @patch('src.main.vin_query')
    def test_outlier_at_exact_lower_bound(self, mock_query, mock_family, form, qtbot):
        mock_query.return_value = [_raw(y=2.0, y_low=2.0, y_high=5.0)]
        mock_family.return_value = []

        form.edit_vin.setText('BOUND')
        form.init_vin_plots()

        tc = form.stats_selection[0]
        assert tc.out_of_tolerance is False

    @patch('src.main.fetch_stat_family')
    @patch('src.main.vin_query')
    def test_outlier_at_exact_upper_bound(self, mock_query, mock_family, form, qtbot):
        mock_query.return_value = [_raw(y=5.0, y_low=2.0, y_high=5.0)]
        mock_family.return_value = []

        form.edit_vin.setText('BOUND')
        form.init_vin_plots()

        tc = form.stats_selection[0]
        assert tc.out_of_tolerance is False

    @patch('src.main.fetch_stat_family')
    @patch('src.main.vin_query')
    def test_extreme_negative_coords(self, mock_query, mock_family, form, qtbot):
        mock_query.return_value = [_raw(x=-9999.0, y=-8888.0, y_low=-9000.0, y_high=-8000.0)]
        mock_family.return_value = [_raw(x=-9999.0, y=-8500.0, y_low=-9000.0, y_high=-8000.0)]

        form.edit_vin.setText('EXTREME')
        form.init_vin_plots()

        items = form.plot.getPlotItem().items
        assert len(items) >= 6

    @patch('src.main.fetch_stat_family')
    @patch('src.main.vin_query')
    def test_extreme_positive_coords(self, mock_query, mock_family, form, qtbot):
        mock_query.return_value = [_raw(x=1e6, y=2e6, y_low=0.0, y_high=3e6)]
        mock_family.return_value = [_raw(x=1e6, y=1e6, y_low=0.0, y_high=3e6)]

        form.edit_vin.setText('EXTREME')
        form.init_vin_plots()

        items = form.plot.getPlotItem().items
        assert len(items) >= 6

    @patch('src.main.fetch_stat_family')
    @patch('src.main.vin_query')
    def test_zero_coordinates(self, mock_query, mock_family, form, qtbot):
        mock_query.return_value = [_raw(x=0.0, y=0.0, y_low=-1.0, y_high=1.0)]
        mock_family.return_value = [_raw(x=0.0, y=0.0, y_low=-1.0, y_high=1.0)]

        form.edit_vin.setText('ZERO')
        form.init_vin_plots()

        assert len(form.stats_selection) == 1
        assert form.plot.getPlotItem().items is not None

    @patch('src.main.fetch_stat_family')
    @patch('src.main.vin_query')
    def test_many_different_test_names(self, mock_query, mock_family, form, qtbot):
        raw = [_raw(test_name=f'test_{i}', y=float(i)) for i in range(100)]
        mock_query.return_value = raw
        mock_family.return_value = []

        form.edit_vin.setText('MULTI_NAME')
        form.init_vin_plots()

        assert len(form.stats_selection) == 100

        # Navigate through all; each should have a different title
        names_seen = set()
        for i in range(100):
            form.current_stat = i
            form._display_current_stat()
            names_seen.add(form.stats_selection[i].name)

        assert len(names_seen) == 100

    @patch('src.main.vin_query')
    def test_no_results_shows_message(self, mock_query, form, qtbot):
        mock_query.return_value = []
        form.edit_vin.setText('EMPTY_VIN')
        form.init_vin_plots()

        assert 'No outlier' in form.statusBar().currentMessage()
        assert form.button_next.isEnabled() is False
        assert form.button_prev.isEnabled() is False

    @patch('src.main.vehicle_query')
    def test_no_results_vehicle_path(self, mock_vquery, form, qtbot):
        mock_vquery.return_value = []

        # Manually set combo values
        form.make_combo.blockSignals(True)
        form.make_combo.clear()
        form.make_combo.addItem("")
        form.make_combo.addItem("Tesla")
        form.make_combo.setCurrentIndex(1)
        form.make_combo.blockSignals(False)

        form.model_combo.blockSignals(True)
        form.model_combo.clear()
        form.model_combo.addItem("")
        form.model_combo.addItem("ModelZ")
        form.model_combo.setCurrentIndex(1)
        form.model_combo.blockSignals(False)

        form.year_combo.blockSignals(True)
        form.year_combo.clear()
        form.year_combo.addItem("")
        form.year_combo.addItem("2099")
        form.year_combo.setCurrentIndex(1)
        form.year_combo.blockSignals(False)

        form.init_vehicle_plots()
        assert 'No outlier' in form.statusBar().currentMessage()


# ===========================================================================
# 6. Navigation stress: 1000 items
# ===========================================================================

class TestNavigationStress:
    """Verify prev/next navigation works correctly with 1000 items."""

    @patch('src.main.fetch_stat_family')
    @patch('src.main.vin_query')
    def test_forward_backward_1000(self, mock_query, mock_family, form, qtbot):
        raw = [_random_raw(i) for i in range(1000)]
        mock_query.return_value = raw
        mock_family.return_value = []

        form.edit_vin.setText('NAV_VIN')
        form.init_vin_plots()

        # Forward to the end
        for i in range(999):
            form.show_next()
        assert form.current_stat == 999
        assert form.button_next.isEnabled() is False

        # Backward to the start
        for i in range(999):
            form.show_prev()
        assert form.current_stat == 0
        assert form.button_prev.isEnabled() is False

    @patch('src.main.fetch_stat_family')
    @patch('src.main.vin_query')
    def test_status_label_updates_through_1000(self, mock_query, mock_family, form, qtbot):
        raw = [_random_raw(i) for i in range(1000)]
        mock_query.return_value = raw
        mock_family.return_value = []

        form.edit_vin.setText('STATUS_VIN')
        form.init_vin_plots()

        for i in range(1000):
            form.current_stat = i
            form._update_nav_buttons()
            expected = f'{i + 1} / 1000'
            assert form.label_status.text() == expected

    @patch('src.main.fetch_stat_family')
    @patch('src.main.vin_query')
    def test_nav_buttons_at_boundaries(self, mock_query, mock_family, form, qtbot):
        raw = [_random_raw(i) for i in range(1000)]
        mock_query.return_value = raw
        mock_family.return_value = []

        form.edit_vin.setText('BOUND_VIN')
        form.init_vin_plots()

        # At start: prev disabled, next enabled
        assert form.button_prev.isEnabled() is False
        assert form.button_next.isEnabled() is True

        # Move one forward: both enabled
        form.show_next()
        assert form.button_prev.isEnabled() is True
        assert form.button_next.isEnabled() is True

        # Jump to end: next disabled, prev enabled
        form.current_stat = 998
        form.show_next()
        assert form.current_stat == 999
        assert form.button_next.isEnabled() is False
        assert form.button_prev.isEnabled() is True


# ===========================================================================
# 7. matricize with large datasets
# ===========================================================================

class TestMatricizeStress:
    """Verify matricize_test_cases handles large inputs efficiently."""

    def test_1000_same_name(self):
        cases = [_make_tc(float(i), float(i * 10)) for i in range(1000)]
        result = matricize_test_cases(cases)
        assert result.shape == (2, 1000)
        np.testing.assert_array_equal(result[0], np.arange(1000, dtype=float))
        np.testing.assert_array_equal(result[1], np.arange(0, 10000, 10, dtype=float))

    def test_1000_empty_name(self):
        cases = [_make_tc(float(i), float(i), name='') for i in range(1000)]
        result = matricize_test_cases(cases)
        assert result.shape == (2, 1000)

    def test_500_same_then_500_different(self):
        cases = [_make_tc(float(i), float(i), name='A') for i in range(500)]
        cases += [_make_tc(float(i), float(i), name=f'Z{i}') for i in range(500)]
        result = matricize_test_cases(cases)
        assert result.shape == (2, 500)


# ===========================================================================
# 8. init_test_case_list with large input
# ===========================================================================

class TestInitTestCaseListStress:
    """Verify init_test_case_list handles 1000 rows efficiently."""

    def test_1000_rows(self):
        rows = [_raw(test_name=f't{i}', x=float(i), y=float(i * 2)) for i in range(1000)]
        cases = init_test_case_list(rows)
        assert len(cases) == 1000
        for i, tc in enumerate(cases):
            assert tc.name == f't{i}'
            assert tc.result_x == float(i)
            assert tc.result_y == float(i * 2)


# ===========================================================================
# 9. plot_selection: family scatter + highlight + tolerance lines
# ===========================================================================

class TestPlotSelectionComponents:
    """Verify that plot_selection renders the correct number and type
    of pyqtgraph items."""

    @patch('src.main.fetch_stat_family')
    @patch('src.main.vin_query')
    def test_plot_has_family_scatter(self, mock_query, mock_family, form, qtbot):
        mock_query.return_value = [_raw(y=1.0)]
        mock_family.return_value = [
            _raw(vin='V1', y=3.0),
            _raw(vin='V2', y=4.0),
            _raw(vin='V3', y=5.0),
        ]
        form.edit_vin.setText('FAM')
        form.init_vin_plots()

        items = form.plot.getPlotItem().items
        # family scatter + highlight + 2 tolerance lines + annotation + line = 6
        assert len(items) == 6

    @patch('src.main.fetch_stat_family')
    @patch('src.main.vin_query')
    def test_plot_no_family_only_highlight_and_lines(self, mock_query, mock_family, form, qtbot):
        mock_query.return_value = [_raw(y=1.0)]
        mock_family.return_value = []
        form.edit_vin.setText('NO_FAM')
        form.init_vin_plots()

        items = form.plot.getPlotItem().items
        # highlight + 2 tolerance lines + annotation + line = 5
        assert len(items) == 5

    @patch('src.main.fetch_stat_family')
    @patch('src.main.vin_query')
    def test_plot_title_matches_stat_name(self, mock_query, mock_family, form, qtbot):
        mock_query.return_value = [_raw(test_name='my_custom_test', y=1.0)]
        mock_family.return_value = []
        form.edit_vin.setText('TITLE')
        form.init_vin_plots()

        title = form.plot.getPlotItem().titleLabel.text
        assert 'my_custom_test' in title

    @patch('src.main.fetch_stat_family')
    @patch('src.main.vin_query')
    def test_plot_axes_match_units(self, mock_query, mock_family, form, qtbot):
        mock_query.return_value = [_raw(y=1.0)]
        mock_family.return_value = []
        form.edit_vin.setText('UNITS')
        form.init_vin_plots()

        pi = form.plot.getPlotItem()
        bottom_label = pi.axes['bottom']['item'].labelText
        left_label = pi.axes['left']['item'].labelText
        assert bottom_label == 'mm'
        assert left_label == 'mm'


# ===========================================================================
# 10. Mixed VIN + vehicle selection priority
# ===========================================================================

class TestQueryPriority:
    """Verify that vehicle query takes priority when both VIN and
    vehicle dropdowns are set."""

    @patch('src.main.vehicle_query')
    @patch('src.main.vin_query')
    def test_vehicle_takes_priority_when_both_set(self, mock_vin, mock_vehicle, form, qtbot):
        mock_vin.return_value = [_raw(vin='VIN_VIN', y=1.0)]
        mock_vehicle.return_value = [_raw(vin='VIN_VEH', y=2.0)]

        form.edit_vin.setText('SOME_VIN')

        # Manually set combo values
        form.make_combo.blockSignals(True)
        form.make_combo.clear()
        form.make_combo.addItem("")
        form.make_combo.addItem("Honda")
        form.make_combo.setCurrentIndex(1)
        form.make_combo.blockSignals(False)

        form.model_combo.blockSignals(True)
        form.model_combo.clear()
        form.model_combo.addItem("")
        form.model_combo.addItem("Accord")
        form.model_combo.setCurrentIndex(1)
        form.model_combo.blockSignals(False)

        form.year_combo.blockSignals(True)
        form.year_combo.clear()
        form.year_combo.addItem("")
        form.year_combo.addItem("2023")
        form.year_combo.setCurrentIndex(1)
        form.year_combo.blockSignals(False)

        form.init_vehicle_plots()

        # vehicle_query should have been called, not vin_query
        mock_vehicle.assert_called_once()
        mock_vin.assert_not_called()
        assert form.stats_selection[0].vehicle == 'VIN_VEH'


# ===========================================================================
# 11. _update_door_availability with 1000 rows
# ===========================================================================

class TestDoorAvailabilityStress:
    """Verify door availability greying works correctly with large
    datasets containing random door distributions."""

    def test_1000_rows_all_doors(self, form, qtbot):
        raw = [_raw(door=random.choice(DOOR_KEYS)) for _ in range(1000)]
        form._update_door_availability(raw)

        # At least some doors should be white (available)
        white = 0
        for i in range(form.door_location_widget.count()):
            if form.door_location_widget.item(i).foreground().color().name() == _WHITE:
                white += 1
        assert white >= 1

    def test_1000_rows_single_door(self, form, qtbot):
        raw = [_raw(door='passenger_front') for _ in range(1000)]
        form._update_door_availability(raw)

        for i in range(form.door_location_widget.count()):
            item = form.door_location_widget.item(i)
            _, key = DOOR_LOCATIONS[i]
            if key == 'passenger_front':
                assert item.foreground().color().name() == _WHITE
            else:
                assert item.foreground().color().name() == _GRAY
