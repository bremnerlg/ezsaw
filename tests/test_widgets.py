"""Widget tests for intro_form — uses pytest-qt with offscreen rendering."""
import os
import sys
from unittest.mock import patch

import pytest

os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from PyQt5.QtWidgets import QApplication

# Ensure QApplication exists before any widget is created
app = QApplication.instance() or QApplication(sys.argv)

from src.main import intro_form, DOOR_LOCATIONS


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def form(qtbot):
    w = intro_form()
    qtbot.addWidget(w)
    return w


def _make_raw_row(test_name='gap', x=10.0, y=3.5, y_low=2.0, y_high=5.0,
                  vin='VIN1', door='driver_front'):
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



# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

class TestInitialUI:
    def test_window_title(self, form):
        assert '3.1.2' in form.windowTitle()

    def test_vin_placeholder(self, form):
        assert form.edit_vin.placeholderText() == 'Enter a VIN...'

    def test_vin_text_is_empty(self, form):
        assert form.edit_vin.text() == ''

    def test_nav_buttons_disabled_initially(self, form):
        assert form.button_next.isEnabled() is False
        assert form.button_prev.isEnabled() is False

    def test_door_list_populated(self, form):
        assert form.door_location_widget.count() == len(DOOR_LOCATIONS)

    def test_first_door_selected(self, form):
        assert form.door_location_widget.currentRow() == 0

    def test_stats_selection_empty(self, form):
        assert form.stats_selection == []
        assert form.current_stat == 0


# ---------------------------------------------------------------------------
# VIN validation
# ---------------------------------------------------------------------------

class TestValidation:
    def test_empty_vin_shows_error(self, form, qtbot):
        form.init_plots()
        assert 'please enter a vin' in form.statusBar().currentMessage().lower()

    def test_whitespace_vin_shows_error(self, form, qtbot):
        form.edit_vin.setText('   ')
        form.init_plots()
        assert 'please enter a vin' in form.statusBar().currentMessage().lower()


# ---------------------------------------------------------------------------
# Door selection helper
# ---------------------------------------------------------------------------

class TestDoorSelection:
    def test_selected_door_key_returns_value(self, form):
        form.door_location_widget.setCurrentRow(2)
        assert form._selected_door_key() == 'passenger_front'

    def test_selected_door_key_first(self, form):
        assert form._selected_door_key() == 'driver_front'


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

class TestNavigation:
    @patch('src.main.vin_query')
    def test_next_prev_cycles_through_outliers(self, mock_query, form, qtbot):
        mock_query.return_value = [
            _make_raw_row(test_name='gap', y=1.0),
            _make_raw_row(test_name='gap', y=6.0),
            _make_raw_row(test_name='gap', y=0.5),
        ]
        form.edit_vin.setText('VIN1')
        form.init_plots()

        assert len(form.stats_selection) == 3
        assert form.current_stat == 0
        assert form.button_next.isEnabled() is True
        assert form.button_prev.isEnabled() is False

        form.show_next()
        assert form.current_stat == 1
        assert form.button_prev.isEnabled() is True

        form.show_next()
        assert form.current_stat == 2
        assert form.button_next.isEnabled() is False

        form.show_prev()
        assert form.current_stat == 1

    @patch('src.main.vin_query')
    def test_no_outliers_disables_buttons(self, mock_query, form, qtbot):
        mock_query.return_value = []
        form.edit_vin.setText('VIN1')
        form.init_plots()

        assert form.button_next.isEnabled() is False
        assert form.button_prev.isEnabled() is False
        assert 'No outlier' in form.statusBar().currentMessage()


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

class TestPlotting:
    @patch('src.main.fetch_stat_family')
    @patch('src.main.vin_query')
    def test_plot_selection_draws_family_and_highlight(self, mock_query, mock_family, form, qtbot):
        mock_query.return_value = [_make_raw_row(y=1.0)]
        mock_family.return_value = [
            _make_raw_row(vin='V_OTHER_1', y=3.0),
            _make_raw_row(vin='V_OTHER_2', y=4.0),
        ]
        form.edit_vin.setText('VIN1')
        form.init_plots()

        # PlotWidget should have a PlotItem with data items
        plot_items = form.plot.getPlotItem().items
        assert len(plot_items) >= 3  # family scatter + highlight + 2 lines

    def test_clear_plot_removes_items(self, form, qtbot):
        form.plot.plot([1, 2], [3, 4])
        assert len(form.plot.getPlotItem().items) > 0
        form._clear_plot()
        assert len(form.plot.getPlotItem().items) == 0


# ---------------------------------------------------------------------------
# cache_relevant_stats with door filter
# ---------------------------------------------------------------------------

class TestDoorFilter:
    @patch('src.main.vin_query')
    def test_filters_by_door(self, mock_query, form, qtbot):
        mock_query.return_value = [
            _make_raw_row(door='driver_front', y=1.0),
            _make_raw_row(door='rear_hatch', y=6.0),
            _make_raw_row(door='driver_front', y=0.5),
        ]
        form.door_location_widget.setCurrentRow(0)  # driver_front
        result = form.cache_relevant_stats('VIN1')
        assert len(result) == 2
        assert all(tc.location == 'driver_front' for tc in result)

    @patch('src.main.vin_query')
    def test_all_matching_door(self, mock_query, form, qtbot):
        mock_query.return_value = [
            _make_raw_row(door='driver_front', y=1.0),
            _make_raw_row(door='rear_hatch', y=6.0),
        ]
        form.door_location_widget.setCurrentRow(0)  # driver_front
        result = form.cache_relevant_stats('VIN1')
        assert len(result) == 1
        assert result[0].location == 'driver_front'
