"""
EZSAW V4.0.0 Beta — PyQt5 GUI for door check outlier analysis.

Provides an interactive interface for querying vehicle door measurement
data by VIN or make/model/year, plotting outlier results, and navigating
through stat families with pyqtgraph. Uses a left sidebar (statistical
software pattern) for controls and a main plot area on the right.
"""
import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLineEdit, QListWidget,
    QLabel, QFrame, QComboBox, QSizePolicy,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QProcess
import pyqtgraph as pg
import numpy as np
from src.core.auto_stat_facilities import (
    vin_query, vehicle_query, fetch_stat_family,
    fetch_makes, fetch_models, fetch_years,
    init_test_case_list, matricize_test_cases,
    apply_stat_ordering,
)
from src.core.locale import (
    load_locale_strings, load_db_config_for_locale,
    get_current_locale, set_locale, get_supported_locales,
    get_supported_db_configs, get_current_db_config_file,
    set_current_db_config_file, translate_test_name,
)

# ---------------------------------------------------------------------------
# Paths & module-level state (loaded from user_prefs.json at import time)
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).resolve().parent.parent / 'data' / 'logo'
_LOGO_PATH = _DATA_DIR / 'EZMLogo_Rectangle_BlackBorder_Digital-2207581935.png'

_LOCALE = load_locale_strings()
_APP_CONFIG = load_db_config_for_locale()
DOOR_LOCATIONS = [
    (entry['label'], entry['value'])
    for entry in _APP_CONFIG['EZ_DOOR_LOCATIONS']
]

# ---------------------------------------------------------------------------
# Colour palette (dark theme)
# ---------------------------------------------------------------------------

LIME = '#32cd32'
LIME_DIM = '#228B22'
LIME_DARK = '#1a5c1a'
BG = '#0a0a0a'
BG_WIDGET = '#141414'
BG_INPUT = '#1e1e1e'
TEXT = '#e0e0e0'
TEXT_DIM = '#888888'
BORDER = '#2a2a2a'

# ---------------------------------------------------------------------------
# Qt stylesheet
# ---------------------------------------------------------------------------

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {BG};
    color: {TEXT};
    font-family: "Segoe UI", "SF Pro Text", "Helvetica Neue", "Noto Sans", "Cantarell", sans-serif;
    font-size: 13px;
    font-weight: 400;
}}

QLabel {{
    color: {TEXT};
    background: transparent;
}}

QLabel#title {{
    color: {LIME};
    font-size: 17px;
    font-weight: 600;
    letter-spacing: 0.5px;
    padding: 2px 0;
}}

QLabel#logo {{
    background: transparent;
}}

QLineEdit {{
    background-color: {BG_INPUT};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 7px 12px;
    font-size: 13px;
    font-weight: 400;
    min-width: 180px;
}}

QLineEdit:focus {{
    border: 1px solid {LIME_DIM};
}}

QPushButton {{
    background-color: {BG_WIDGET};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 7px 20px;
    font-size: 13px;
    font-weight: 500;
    min-width: 70px;
}}

QPushButton:hover {{
    background-color: {LIME_DARK};
    border: 1px solid {LIME_DIM};
    color: #ffffff;
}}

QPushButton:pressed {{
    background-color: {LIME_DIM};
}}

QPushButton:disabled {{
    background-color: {BG};
    color: {TEXT_DIM};
    border: 1px solid {BORDER};
}}

QListWidget {{
    background-color: {BG_INPUT};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 4px;
    font-size: 13px;
    font-weight: 400;
    outline: none;
}}

QListWidget::item {{
    padding: 5px 8px;
    border-radius: 3px;
}}

QListWidget::item:selected {{
    background-color: {LIME_DARK};
    color: #ffffff;
}}

QListWidget::item:hover {{
    background-color: {BORDER};
}}

QListWidget::item:disabled {{
    color: {TEXT_DIM};
    background-color: transparent;
}}

QStatusBar {{
    background-color: {BG_WIDGET};
    color: {TEXT_DIM};
    border-top: 1px solid {BORDER};
    font-size: 12px;
    font-weight: 400;
    padding: 3px 10px;
}}

QComboBox {{
    background-color: {BG_INPUT};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 7px 12px;
    font-size: 13px;
    font-weight: 400;
    min-width: 140px;
}}

QComboBox:focus {{
    border: 1px solid {LIME_DIM};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}

QComboBox::down-arrow {{
    border: none;
}}

QComboBox QAbstractItemView {{
    background-color: {BG_INPUT};
    color: {TEXT};
    border: 1px solid {BORDER};
    selection-background-color: {LIME_DARK};
    selection-color: #ffffff;
    padding: 4px;
    font-size: 13px;
}}

QFrame#separator {{
    background-color: {LIME_DARK};
    max-height: 1px;
    min-height: 1px;
}}
"""


# ===========================================================================
# Main window
# ===========================================================================

class intro_form(QMainWindow):
    """Primary application window: VIN/vehicle query, outlier plotting,
    door filtering, and stat family navigation."""

    def __init__(self, locale_strings=None, db_config=None):
        super().__init__()
        if locale_strings is None:
            locale_strings = _LOCALE
        if db_config is None:
            db_config = _APP_CONFIG
        self.locale = locale_strings
        self.db_config = db_config

        self.setWindowTitle(self.locale['EZ_WINDOW_TITLE'])
        self.resize(1100, 750)
        self.setMinimumSize(960, 640)

        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(16, 12, 16, 8)
        root.setSpacing(10)

        # --- header: logo + title ---
        header = QHBoxLayout()
        header.setSpacing(12)

        self.logo_label = QLabel()
        self.logo_label.setObjectName('logo')
        if _LOGO_PATH.exists():
            pixmap = QPixmap(str(_LOGO_PATH))
            scaled = pixmap.scaledToHeight(48, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled)
        header.addWidget(self.logo_label)

        self.title = QLabel(self.locale['EZ_APP_TITLE'])
        self.title.setObjectName('title')
        header.addWidget(self.title)
        header.addStretch()

        lang_label = QLabel(self.locale['EZ_LABEL_LANGUAGE'])
        lang_label.setStyleSheet(
            f'color: {TEXT_DIM}; font-size: 12px; font-weight: 500;'
        )
        header.addWidget(lang_label)

        self.lang_combo = QComboBox()
        self.lang_combo.setFixedWidth(120)
        current_locale = get_current_locale()
        for code, name in get_supported_locales():
            self.lang_combo.addItem(name, code)
        for i in range(self.lang_combo.count()):
            if self.lang_combo.itemData(i) == current_locale:
                self.lang_combo.setCurrentIndex(i)
                break
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        header.addWidget(self.lang_combo)

        db_label = QLabel(self.locale['EZ_LABEL_DATABASE'])
        db_label.setStyleSheet(
            f'color: {TEXT_DIM}; font-size: 12px; font-weight: 500;'
        )
        header.addWidget(db_label)

        self.db_combo = QComboBox()
        self.db_combo.setFixedWidth(140)
        current_db_file = get_current_db_config_file()
        current_db_idx = 0
        for i, (db_name, config_file) in enumerate(get_supported_db_configs()):
            self.db_combo.addItem(db_name, config_file)
            if current_db_file and config_file == current_db_file:
                current_db_idx = i
            elif not current_db_file and i == 0:
                current_db_idx = i
        self.db_combo.setCurrentIndex(current_db_idx)
        self.db_combo.currentIndexChanged.connect(self._on_db_changed)
        header.addWidget(self.db_combo)

        sep = QFrame()
        sep.setObjectName('separator')
        sep.setFrameShape(QFrame.HLine)

        # --- body: sidebar controls + right panel (nav + plot) ---
        body = QHBoxLayout()
        body.setSpacing(0)

        # Left sidebar (statistical software pattern: controls panel)
        sidebar = QWidget()
        sidebar.setObjectName('sidebar')
        sidebar.setStyleSheet(
            f'#sidebar {{ background-color: {BG_WIDGET}; border: 1px solid {BORDER}; border-radius: 6px; }}'
        )
        sidebar.setFixedWidth(270)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(12, 10, 12, 10)
        side.setSpacing(8)

        # VIN section
        vin_lbl = QLabel('VIN')
        vin_lbl.setStyleSheet(
            f'color: {TEXT_DIM}; font-size: 11px; font-weight: 500; letter-spacing: 0.5px;'
        )
        side.addWidget(vin_lbl)
        self.edit_vin = QLineEdit()
        self.edit_vin.setPlaceholderText(self.locale['EZ_VIN_PLACEHOLDER'])
        self.edit_vin.returnPressed.connect(self.init_vin_plots)
        side.addWidget(self.edit_vin)
        self.button_vin_query = QPushButton(self.locale['EZ_BTN_QUERY'])
        self.button_vin_query.clicked.connect(self.init_vin_plots)
        self.button_vin_query.setEnabled(False)
        side.addWidget(self.button_vin_query)

        # OR horizontal divider
        or_hdiv = QFrame()
        or_hdiv.setFrameShape(QFrame.HLine)
        or_hdiv.setStyleSheet(f'color: {BORDER};')
        or_lbl2 = QLabel('OR')
        or_lbl2.setAlignment(Qt.AlignCenter)
        or_lbl2.setStyleSheet(
            f'color: {TEXT_DIM}; font-size: 10px; font-weight: 600; background: transparent; padding: 0;'
        )
        or_box = QWidget()
        or_box.setFixedHeight(26)
        or_lo = QVBoxLayout(or_box)
        or_lo.setContentsMargins(0, 0, 0, 0)
        or_lo.setSpacing(2)
        or_lo.addWidget(or_hdiv)
        or_lo.addWidget(or_lbl2)
        side.addWidget(or_box)

        # Vehicle section
        veh_lbl = QLabel(self.locale['EZ_LABEL_VEHICLE'])
        veh_lbl.setStyleSheet(
            f'color: {TEXT_DIM}; font-size: 11px; font-weight: 500; letter-spacing: 0.5px;'
        )
        side.addWidget(veh_lbl)
        self.make_combo = QComboBox()
        self.make_combo.setPlaceholderText(self.locale['EZ_LABEL_MAKE'])
        side.addWidget(self.make_combo)
        self.model_combo = QComboBox()
        self.model_combo.setPlaceholderText(self.locale['EZ_LABEL_MODEL'])
        self.model_combo.setEnabled(False)
        side.addWidget(self.model_combo)
        self.year_combo = QComboBox()
        self.year_combo.setPlaceholderText(self.locale['EZ_LABEL_YEAR'])
        self.year_combo.setEnabled(False)
        side.addWidget(self.year_combo)
        self.button_enter = QPushButton(self.locale['EZ_BTN_ENTER'])
        self.button_enter.clicked.connect(self.init_vehicle_plots)
        self.button_enter.setEnabled(False)
        side.addWidget(self.button_enter)

        # Separator
        sep2 = QFrame()
        sep2.setObjectName('separator')
        sep2.setFrameShape(QFrame.HLine)
        side.addWidget(sep2)

        # Door section
        dr_lbl = QLabel(self.locale['EZ_LABEL_DOOR'])
        dr_lbl.setStyleSheet(
            f'color: {TEXT_DIM}; font-size: 11px; font-weight: 500; letter-spacing: 0.5px;'
        )
        side.addWidget(dr_lbl)
        self.door_location_widget = QListWidget()
        for label, _ in DOOR_LOCATIONS:
            self.door_location_widget.addItem(label)
        row_h = self.door_location_widget.sizeHintForRow(0)
        self.door_location_widget.setMinimumHeight(
            row_h * self.door_location_widget.count() + 8  # 4px padding top/bottom from stylesheet
            if row_h > 0 else 180
        )
        self.door_location_widget.setCurrentRow(0)
        side.addWidget(self.door_location_widget)
        side.addStretch()

        body.addWidget(sidebar)

        # Right panel: nav + plot
        right = QVBoxLayout()
        right.setSpacing(6)
        right.setContentsMargins(10, 0, 0, 0)

        nav = QHBoxLayout()
        nav.setSpacing(10)
        self.button_prev = QPushButton(self.locale['EZ_BTN_PREV'])
        self.button_next = QPushButton(self.locale['EZ_BTN_NEXT'])
        self.button_next.setEnabled(False)
        self.button_prev.setEnabled(False)
        self.label_status = QLabel('')
        self.label_status.setStyleSheet(
            f'color: {TEXT_DIM}; font-size: 12px; font-weight: 400;'
        )
        self.label_status.setAlignment(Qt.AlignCenter)
        nav.addWidget(self.button_prev)
        nav.addStretch()
        nav.addWidget(self.label_status)
        nav.addStretch()
        nav.addWidget(self.button_next)
        right.addLayout(nav)

        self.plot = pg.PlotWidget()
        self.plot.setBackground(BG_WIDGET)
        self.plot.showGrid(x=True, y=True, alpha=0.15)
        self.plot.getAxis('bottom').setPen(pg.mkPen(color=TEXT_DIM, width=1))
        self.plot.getAxis('left').setPen(pg.mkPen(color=TEXT_DIM, width=1))
        self.plot.getAxis('bottom').setTextPen(TEXT)
        self.plot.getAxis('left').setTextPen(TEXT)
        self.plot.setTitle('', color=LIME, size='13pt')
        self.plot.setLabel('bottom', '', color=TEXT)
        self.plot.setLabel('left', '', color=TEXT)
        self.plot.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right.addWidget(self.plot, stretch=1)

        body.addLayout(right, stretch=1)

        # --- assemble layout ---
        root.addLayout(header)
        root.addWidget(sep)
        root.addLayout(body)

        # --- application state ---
        self.test_cases = []
        self.current_stat = 0
        self.all_outliers = []

        # --- connect signals ---
        self.button_next.clicked.connect(self.show_next)
        self.button_prev.clicked.connect(self.show_prev)

        self.make_combo.currentIndexChanged.connect(self._on_make_changed)
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        self.door_location_widget.currentRowChanged.connect(self._on_door_changed)

        self._update_action_buttons()
        self.statusBar().showMessage(self.locale['EZ_STATUS_READY'])
        self._populate_makes()

    # -----------------------------------------------------------------------
    # Language & database selection (restart app on change)
    # -----------------------------------------------------------------------

    def _on_language_changed(self, index):
        new_locale = self.lang_combo.itemData(index)
        if new_locale and new_locale != get_current_locale():
            set_locale(new_locale)
            self._restart_app()

    def _on_db_changed(self, index):
        new_db_file = self.db_combo.itemData(index)
        if new_db_file and new_db_file != get_current_db_config_file():
            set_current_db_config_file(new_db_file)
            self._restart_app()

    def _restart_app(self):
        QProcess.startDetached(sys.executable, sys.argv)
        QApplication.instance().quit()

    # -----------------------------------------------------------------------
    # Door selection
    # -----------------------------------------------------------------------

    def _selected_door_key(self):
        row = self.door_location_widget.currentRow()
        if row < 0 or row >= len(DOOR_LOCATIONS):
            return None
        return DOOR_LOCATIONS[row][1]

    def _update_door_availability(self, raw_outliers):
        available = set(r.get('door_location', '') for r in raw_outliers)
        current_row = self.door_location_widget.currentRow()
        for i in range(self.door_location_widget.count()):
            item = self.door_location_widget.item(i)
            _, key = DOOR_LOCATIONS[i]
            if key in available:
                item.setFlags(item.flags() | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                item.setForeground(Qt.white)
            else:
                item.setFlags(item.flags() & ~(Qt.ItemIsEnabled | Qt.ItemIsSelectable))
                item.setForeground(Qt.gray)
        if current_row >= 0:
            self.door_location_widget.setCurrentRow(current_row)

    def _update_action_buttons(self):
        """Enable query/enter buttons only when a door is selected and enabled."""
        has_door = self._selected_door_key() is not None
        current_item = self.door_location_widget.currentItem()
        enabled = has_door and (
            current_item is None
            or bool(current_item.flags() & Qt.ItemIsEnabled)
        )
        self.button_vin_query.setEnabled(enabled)
        self.button_enter.setEnabled(enabled)

    def _on_door_changed(self, row):
        self._update_action_buttons()
        if not self.all_outliers or not self.test_cases:
            return
        door_key = self._selected_door_key()
        if door_key:
            filtered = [r for r in self.all_outliers if r['door_location'] == door_key]
        else:
            filtered = self.all_outliers
        self._dedupe_stats_selection(filtered)
        self.current_stat = 0
        if self.test_cases:
            self._display_current_stat()
        else:
            self._clear_plot()
            self._update_nav_buttons()
            self.statusBar().showMessage(
                self.locale['EZ_STATUS_NO_DOOR_OUTLIERS']
            )

    # -----------------------------------------------------------------------
    # Vehicle cascading dropdowns (make → model → year)
    # -----------------------------------------------------------------------

    def _populate_makes(self):
        self.make_combo.blockSignals(True)
        self.make_combo.clear()
        self.make_combo.addItem("")
        try:
            makes = fetch_makes(self.db_config)
            self.make_combo.addItems(makes)
        except Exception as e:
            self.statusBar().showMessage(f'Failed to load makes: {e}')
        self.make_combo.blockSignals(False)

    def _on_make_changed(self, index):
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        self.model_combo.addItem("")
        self.year_combo.blockSignals(True)
        self.year_combo.clear()
        self.year_combo.addItem("")
        self.year_combo.setEnabled(False)
        if index > 0:
            make = self.make_combo.currentText()
            try:
                models = fetch_models(make, self.db_config)
                self.model_combo.addItems(models)
            except Exception as e:
                self.statusBar().showMessage(f'Failed to load models: {e}')
            self.model_combo.setEnabled(True)
        else:
            self.model_combo.setEnabled(False)
        self.model_combo.blockSignals(False)
        self.year_combo.blockSignals(False)

    def _on_model_changed(self, index):
        self.year_combo.blockSignals(True)
        self.year_combo.clear()
        self.year_combo.addItem("")
        if index > 0:
            make = self.make_combo.currentText()
            model = self.model_combo.currentText()
            try:
                years = fetch_years(make, model, self.db_config)
                self.year_combo.addItems([str(y) for y in years])
            except Exception as e:
                self.statusBar().showMessage(f'Failed to load years: {e}')
            self.year_combo.setEnabled(True)
        else:
            self.year_combo.setEnabled(False)
        self.year_combo.blockSignals(False)

    # -----------------------------------------------------------------------
    # Plot rendering
    # -----------------------------------------------------------------------

    def _clear_plot(self):
        self.plot.clear()
        self.plot.setTitle('')

    def plot_selection(self, stat, family):
        """Render the outlier plot: family scatter (green), highlighted
        point (red), tolerance bound lines (dashed green), and a
        branch-style annotation label on the outlier point."""
        try:
            self._clear_plot()

            translated_name = translate_test_name(stat.name, self.locale)
            self.plot.setTitle(translated_name, color=LIME, size='13pt')
            self.plot.setLabel('bottom', stat.result_x_unit, color=TEXT)
            self.plot.setLabel('left', stat.result_y_unit, color=TEXT)

            if family:
                family_matrix = matricize_test_cases(family)
                if family_matrix.shape[1] > 0:
                    self.plot.plot(
                        family_matrix[0], family_matrix[1],
                        pen=None, symbol='o', symbolBrush=LIME_DIM, symbolSize=6,
                    )

            x_val = float(stat.result_x)
            y_val = float(stat.result_y)
            self.plot.plot(
                np.array([x_val]),
                np.array([y_val]),
                pen=None, symbol='o', symbolBrush='#ff4444', symbolSize=10,
            )

            self.plot.addLine(
                y=stat.result_y_lower,
                pen=pg.mkPen(LIME, width=1.5, style=pg.QtCore.Qt.DashLine),
            )
            self.plot.addLine(
                y=stat.result_y_upper,
                pen=pg.mkPen(LIME, width=1.5, style=pg.QtCore.Qt.DashLine),
            )

            margin_x = max(abs(float(stat.result_x)) * 0.3, 5.0)
            margin_y = max(abs(float(stat.result_y)) * 0.3, 5.0)
            self.plot.setXRange(
                float(stat.result_x) - margin_x,
                float(stat.result_x) + margin_x,
            )
            self.plot.setYRange(
                float(stat.result_y) - margin_y,
                float(stat.result_y) + margin_y,
            )

            # Branch-style annotation label on the graph
            deviation = ''
            if stat.out_of_tolerance:
                if stat.result_y < stat.result_y_lower:
                    deviation = f'{abs(stat.result_y_lower - stat.result_y):.2f} {stat.result_y_unit} below lower limit'
                else:
                    deviation = f'{abs(stat.result_y_upper - stat.result_y):.2f} {stat.result_y_unit} above upper limit'

            make_str = stat.make or ''
            model_str = stat.model or ''
            mandate_str = str(stat.mandate) if stat.mandate else ''

            vehicle_info = f'{stat.vehicle}'
            if make_str or model_str:
                vehicle_info += f'  |  {make_str} {model_str}'
            if mandate_str:
                vehicle_info += f'  |  Man: {mandate_str}'

            label_text = (
                f'<span style="color: #ff4444; font-weight: bold; font-size: 13px;">'
                f'{translated_name}</span><br>'
                f'<span style="color: #e0e0e0; font-size: 11px;">'
                f'VIN: {vehicle_info}</span><br>'
                f'<span style="color: #e0e0e0; font-size: 11px;">'
                f'result_y: {stat.result_y} {stat.result_y_unit}</span><br>'
                f'<span style="color: #e0e0e0; font-size: 11px;">'
                f'Tolerance: [{stat.result_y_lower} \u2013 {stat.result_y_upper}] {stat.result_y_unit}</span>'
            )
            if deviation:
                label_text += (
                    f'<br><span style="color: #ff8888; font-size: 11px; font-weight: bold;">'
                    f'\u2191 {deviation}</span>'
                )

            annotation = pg.TextItem(
                html=label_text,
                anchor=(0, 1),
                border=pg.mkPen(LIME_DIM, width=1),
                fill=pg.mkColor(20, 20, 20, 220),
            )
            annotation.setPos(x_val, y_val)
            self.plot.addItem(annotation)

            line = pg.PlotDataItem(
                [x_val, x_val + margin_x * 0.4],
                [y_val, y_val],
                pen=pg.mkPen(LIME_DIM, width=1, style=pg.QtCore.Qt.DashLine),
            )
            self.plot.addItem(line)
        except Exception as e:
            self._clear_plot()
            self.plot.setTitle(f'Error: {e}', color='#ff4444', size='13pt')
            self.statusBar().showMessage(f'Plot error: {e}')

    # -----------------------------------------------------------------------
    # Navigation (prev / next through outlier list)
    # -----------------------------------------------------------------------

    def _update_nav_buttons(self):
        """Enable/disable prev/next buttons based on current position."""
        has_items = len(self.test_cases) > 0
        self.button_next.setEnabled(
            has_items and self.current_stat < len(self.test_cases) - 1
        )
        self.button_prev.setEnabled(has_items and self.current_stat > 0)
        if has_items:
            self.label_status.setText(
                f'{self.current_stat + 1} / {len(self.test_cases)}'
            )
        else:
            self.label_status.setText('')

    def show_next(self):
        if self.current_stat < len(self.test_cases) - 1:
            self.current_stat += 1
            self._display_current_stat()

    def show_prev(self):
        if self.current_stat > 0:
            self.current_stat -= 1
            self._display_current_stat()

    def _display_current_stat(self):
        if not self.test_cases:
            return
        stat = self.test_cases[self.current_stat]
        try:
            family_raw = fetch_stat_family(
                stat.name, stat.location, self.db_config
            )
        except Exception as e:
            self.statusBar().showMessage(f'Failed to load family: {e}')
            return
        family = init_test_case_list(family_raw)
        try:
            self.plot_selection(stat, family)
        except Exception as e:
            self._clear_plot()
            self.statusBar().showMessage(f'Plot error: {e}')
        self._update_nav_buttons()
        translated_name = translate_test_name(stat.name, self.locale)
        self.statusBar().showMessage(
            self.locale['EZ_STATUS_VIN_FORMAT'].format(
                vin=stat.vehicle, name=translated_name, location=stat.location
            )
        )

    # -----------------------------------------------------------------------
    # Query result processing
    # -----------------------------------------------------------------------

    def _dedupe_stats_selection(self, raw_entries):
        """Convert raw query rows to test_case objects, removing duplicates
        by (name, location) key, then apply stat ordering."""
        seen = set()
        deduped = []
        for tc in init_test_case_list(raw_entries):
            key = (tc.name, tc.location)
            if key not in seen:
                seen.add(key)
                deduped.append(tc)
        self.test_cases = apply_stat_ordering(deduped)

    def _apply_query_results(self, raw_outliers, label):
        """Process raw query results: filter by door, dedupe, and display."""
        self._update_door_availability(raw_outliers)

        if not raw_outliers:
            self._clear_plot()
            self._update_nav_buttons()
            self.all_outliers = []
            self.test_cases = []
            self.statusBar().showMessage(
                self.locale['EZ_STATUS_NO_OUTLIERS'].format(label=label)
            )
            return

        self.all_outliers = raw_outliers

        door_key = self._selected_door_key()
        if door_key:
            raw_outliers = [r for r in raw_outliers if r['door_location'] == door_key]

        self._dedupe_stats_selection(raw_outliers)
        self.current_stat = 0
        self.statusBar().showMessage(
            self.locale['EZ_STATUS_FOUND_OUTLIERS'].format(
                count=len(self.test_cases), label=label
            )
        )
        self._display_current_stat()

    # -----------------------------------------------------------------------
    # Entry points (called by buttons / Enter key)
    # -----------------------------------------------------------------------

    def init_vehicle_plots(self):
        if not self.button_enter.isEnabled():
            self.statusBar().showMessage('Select a door first.')
            return
        make = self.make_combo.currentText()
        model = self.model_combo.currentText()
        year = self.year_combo.currentText()

        if not make or not model or not year:
            self.statusBar().showMessage(
                self.locale['EZ_STATUS_SELECT_VEHICLE']
            )
            return

        try:
            raw_outliers = vehicle_query(make, model, year, self.db_config)
        except Exception as e:
            self.statusBar().showMessage(f'Query failed: {e}')
            return
        self._apply_query_results(raw_outliers, f'{make} {model} {year}')

    def init_vin_plots(self):
        if not self.button_vin_query.isEnabled():
            self.statusBar().showMessage('Select a door first.')
            return
        vin = self.edit_vin.text().strip()
        if not vin:
            self.statusBar().showMessage(self.locale['EZ_STATUS_ENTER_VIN'])
            return

        try:
            raw_outliers = vin_query(vin, self.db_config)
        except Exception as e:
            self.statusBar().showMessage(f'Query failed: {e}')
            return
        self._apply_query_results(raw_outliers, f'VIN {vin}')


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    form = intro_form()
    form.show()

    sys.exit(app.exec())