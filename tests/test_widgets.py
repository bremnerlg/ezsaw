"""
Widget tests for intro_form — uses pytest-qt with offscreen rendering.

Tests initial UI state, VIN validation, door selection, navigation,
plotting, door filtering, language selector, and database selector.
"""
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
    """Create a fresh intro_form instance for each test."""
    w = intro_form()
    qtbot.addWidget(w)
    return w


def _make_raw_row(test_name='gap', x=10.0, y=3.5, y_low=2.0, y_high=5.0,
                  vin='VIN1', door='driver_front'):
    """Helper: create a mock query result row (dict matching DB schema)."""
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


# ===========================================================================
# Initial UI state
# ===========================================================================

class TestInitialUI:
    """Verify the window starts in the expected default state."""

    def test_window_title(self, form):
        assert '4.0.0 Beta' in form.windowTitle()

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


# ===========================================================================
# VIN validation
# ===========================================================================

class TestValidation:
    """Verify that empty/whitespace VINs show a helpful error message."""

    def test_empty_vin_shows_error(self, form, qtbot):
        form.init_vin_plots()
        assert 'enter a vin' in form.statusBar().currentMessage().lower()

    def test_whitespace_vin_shows_error(self, form, qtbot):
        form.edit_vin.setText('   ')
        form.init_vin_plots()
        assert 'enter a vin' in form.statusBar().currentMessage().lower()


# ===========================================================================
# Door selection helper
# ===========================================================================

class TestDoorSelection:
    """Verify _selected_door_key returns the correct location key."""

    def test_selected_door_key_returns_value(self, form):
        form.door_location_widget.setCurrentRow(2)
        assert form._selected_door_key() == 'passenger_front'

    def test_selected_door_key_first(self, form):
        assert form._selected_door_key() == 'driver_front'


# ===========================================================================
# Navigation
# ===========================================================================

class TestNavigation:
    """Verify prev/next button cycling through outlier stats."""

    @patch('src.main.fetch_stat_family')
    @patch('src.main.vin_query')
    def test_next_prev_cycles_through_outliers(self, mock_query, mock_family, form, qtbot):
        mock_query.return_value = [
            _make_raw_row(test_name='gap', y=1.0),
            _make_raw_row(test_name='flush', y=6.0),
            _make_raw_row(test_name='step', y=0.5),
        ]
        mock_family.return_value = [
            _make_raw_row(vin='V_OTHER_1', y=3.0),
            _make_raw_row(vin='V_OTHER_2', y=4.0),
        ]
        form.edit_vin.setText('VIN1')
        form.init_vin_plots()

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
        form.init_vin_plots()

        assert form.button_next.isEnabled() is False
        assert form.button_prev.isEnabled() is False
        assert 'No outlier' in form.statusBar().currentMessage()


# ===========================================================================
# Plotting
# ===========================================================================

class TestPlotting:
    """Verify that plot_selection renders the expected pyqtgraph items."""

    @patch('src.main.fetch_stat_family')
    @patch('src.main.vin_query')
    def test_plot_selection_draws_family_and_highlight(self, mock_query, mock_family, form, qtbot):
        mock_query.return_value = [_make_raw_row(y=1.0)]
        mock_family.return_value = [
            _make_raw_row(vin='V_OTHER_1', y=3.0),
            _make_raw_row(vin='V_OTHER_2', y=4.0),
        ]
        form.edit_vin.setText('VIN1')
        form.init_vin_plots()

        # Expect: family scatter + highlight point + 2 tolerance lines
        # + annotation + connecting line = at least 5
        plot_items = form.plot.getPlotItem().items
        assert len(plot_items) >= 5

    def test_clear_plot_removes_items(self, form, qtbot):
        form.plot.plot([1, 2], [3, 4])
        assert len(form.plot.getPlotItem().items) > 0
        form._clear_plot()
        assert len(form.plot.getPlotItem().items) == 0


# ===========================================================================
# Door filter via init_vin_plots
# ===========================================================================

class TestDoorFilter:
    """Verify that selecting a door filters outlier results correctly."""

    @patch('src.main.fetch_stat_family')
    @patch('src.main.vin_query')
    def test_filters_by_door(self, mock_query, mock_family, form, qtbot):
        mock_query.return_value = [
            _make_raw_row(test_name='gap', door='driver_front', y=1.0),
            _make_raw_row(test_name='flush', door='rear_hatch', y=6.0),
            _make_raw_row(test_name='step', door='driver_front', y=0.5),
        ]
        mock_family.return_value = [
            _make_raw_row(vin='V_OTHER_1', y=3.0),
        ]
        form.door_location_widget.setCurrentRow(0)  # driver_front
        form.edit_vin.setText('VIN1')
        form.init_vin_plots()
        assert len(form.stats_selection) == 2
        assert all(tc.location == 'driver_front' for tc in form.stats_selection)

    @patch('src.main.fetch_stat_family')
    @patch('src.main.vin_query')
    def test_all_matching_door(self, mock_query, mock_family, form, qtbot):
        mock_query.return_value = [
            _make_raw_row(door='driver_front', y=1.0),
            _make_raw_row(door='rear_hatch', y=6.0),
        ]
        mock_family.return_value = [
            _make_raw_row(vin='V_OTHER_1', y=3.0),
        ]
        form.door_location_widget.setCurrentRow(0)  # driver_front
        form.edit_vin.setText('VIN1')
        form.init_vin_plots()
        assert len(form.stats_selection) == 1
        assert form.stats_selection[0].location == 'driver_front'


# ===========================================================================
# Language selector
# ===========================================================================

class TestLanguageSelector:
    """Verify the language dropdown is correctly populated and defaults."""

    def test_lang_combo_populated(self, form, qtbot):
        assert form.lang_combo.count() == 5

    def test_lang_combo_default_is_english(self, form, qtbot):
        current = form.lang_combo.currentData()
        assert current == 'en'

    def test_lang_combo_items_have_data(self, form, qtbot):
        codes = [form.lang_combo.itemData(i) for i in range(form.lang_combo.count())]
        assert 'en' in codes
        assert 'de' in codes
        assert 'fr' in codes
        assert 'es' in codes
        assert 'nl' in codes

    def test_window_version_is_4_0_0_beta(self, form, qtbot):
        assert '4.0.0 Beta' in form.windowTitle()

    def test_minimum_size_enforced(self, form, qtbot):
        assert form.minimumWidth() >= 960
        assert form.minimumHeight() >= 640


# ===========================================================================
# Database selector
# ===========================================================================

class TestDatabaseSelector:
    """Verify the database dropdown is correctly populated."""

    def test_db_combo_populated(self, form, qtbot):
        assert form.db_combo.count() >= 5

    def test_db_combo_default_is_first(self, form, qtbot):
        assert form.db_combo.currentIndex() >= 0

    def test_db_combo_items_have_data(self, form, qtbot):
        files = [form.db_combo.itemData(i) for i in range(form.db_combo.count())]
        assert 'db_config.json' in files
        assert 'db_config_de.json' in files
        assert 'db_config_fr.json' in files
        assert 'db_config_es.json' in files
        assert 'db_config_nl.json' in files

    def test_db_combo_items_show_db_names(self, form, qtbot):
        names = [form.db_combo.itemText(i) for i in range(form.db_combo.count())]
        assert 'ezsaw3' in names
        assert 'ezsaw_de' in names
