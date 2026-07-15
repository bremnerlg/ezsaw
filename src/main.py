"""
EZSAW V3.1.2A PyQt Edition
"""
import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLineEdit, QListWidget,
    QLabel, QFrame,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import pyqtgraph as pg
import numpy as np
from src.core.auto_stat_facilities import (
    vin_query, fetch_stat_family,
    init_test_case_list, matricize_test_cases,
)

_DATA_DIR = Path(__file__).resolve().parent.parent / 'data' / 'logo'
_LOGO_PATH = _DATA_DIR / 'EZMLogo_Rectangle_BlackBorder_Digital-2207581935.png'

DOOR_LOCATIONS = [
    ('Driver Front', 'driver_front'),
    ('Driver Rear', 'driver_rear'),
    ('Passenger Front', 'passenger_front'),
    ('Passenger Rear', 'passenger_rear'),
    ('Rear Hatch', 'hatch_rear'),
]

LIME = '#32cd32'
LIME_DIM = '#228B22'
LIME_DARK = '#1a5c1a'
BG = '#0a0a0a'
BG_WIDGET = '#141414'
BG_INPUT = '#1e1e1e'
TEXT = '#e0e0e0'
TEXT_DIM = '#888888'
BORDER = '#2a2a2a'

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {BG};
    color: {TEXT};
}}

QLabel {{
    color: {TEXT};
    background: transparent;
}}

QLabel#title {{
    color: {LIME};
    font-size: 18px;
    font-weight: bold;
    padding: 4px 0;
}}

QLabel#logo {{
    background: transparent;
}}

QLineEdit {{
    background-color: {BG_INPUT};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 13px;
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
    padding: 6px 18px;
    font-size: 13px;
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

QStatusBar {{
    background-color: {BG_WIDGET};
    color: {TEXT_DIM};
    border-top: 1px solid {BORDER};
    font-size: 12px;
    padding: 2px 8px;
}}

QFrame#separator {{
    background-color: {LIME_DARK};
    max-height: 1px;
    min-height: 1px;
}}
"""


class intro_form(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EZSAW Version 3.1.2 Alpha")
        self.resize(960, 680)
        self.setMinimumSize(720, 480)

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

        self.title = QLabel('Statistical Analysis Wizard')
        self.title.setObjectName('title')
        header.addWidget(self.title)
        header.addStretch()

        # --- separator ---
        sep = QFrame()
        sep.setObjectName('separator')
        sep.setFrameShape(QFrame.HLine)

        # --- controls row ---
        controls = QHBoxLayout()
        controls.setSpacing(10)

        self.edit_vin = QLineEdit()
        self.edit_vin.setPlaceholderText("Enter a VIN...")
        self.edit_vin.setFixedWidth(200)
        self.edit_vin.returnPressed.connect(self.init_plots)
        controls.addWidget(self.edit_vin)

        self.button_enter = QPushButton("Query")
        controls.addWidget(self.button_enter)

        controls.addSpacing(12)

        door_label = QLabel('Door:')
        door_label.setStyleSheet(f'color: {TEXT_DIM}; font-size: 12px;')
        controls.addWidget(door_label)

        self.door_location_widget = QListWidget()
        self.door_location_widget.setFixedWidth(160)
        self.door_location_widget.setFixedHeight(130)
        for label, _ in DOOR_LOCATIONS:
            self.door_location_widget.addItem(label)
        self.door_location_widget.setCurrentRow(0)
        controls.addWidget(self.door_location_widget)

        controls.addStretch()

        # --- nav row ---
        nav = QHBoxLayout()
        nav.setSpacing(10)

        self.button_prev = QPushButton("\u25C0  Prev")
        self.button_next = QPushButton("Next  \u25B6")
        self.button_next.setEnabled(False)
        self.button_prev.setEnabled(False)

        self.label_status = QLabel('')
        self.label_status.setStyleSheet(f'color: {TEXT_DIM}; font-size: 12px;')
        self.label_status.setAlignment(Qt.AlignCenter)

        nav.addWidget(self.button_prev)
        nav.addStretch()
        nav.addWidget(self.label_status)
        nav.addStretch()
        nav.addWidget(self.button_next)

        # --- plot ---
        self.plot = pg.PlotWidget()
        self.plot.setBackground(BG_WIDGET)
        self.plot.showGrid(x=True, y=True, alpha=0.15)
        self.plot.getAxis('bottom').setPen(pg.mkPen(color=TEXT_DIM, width=1))
        self.plot.getAxis('left').setPen(pg.mkPen(color=TEXT_DIM, width=1))
        self.plot.getAxis('bottom').setTextPen(TEXT)
        self.plot.getAxis('left').setTextPen(TEXT)
        self.plot.setTitle('', color=LIME, size='14pt')
        self.plot.setLabel('bottom', '', color=TEXT)
        self.plot.setLabel('left', '', color=TEXT)

        # --- assemble ---
        root.addLayout(header)
        root.addWidget(sep)
        root.addLayout(controls)
        root.addLayout(nav)
        root.addWidget(self.plot, stretch=1)

        self.stats_selection = []
        self.current_stat = 0

        self.button_enter.clicked.connect(self.init_plots)
        self.button_next.clicked.connect(self.show_next)
        self.button_prev.clicked.connect(self.show_prev)

        self.statusBar().showMessage('Ready')

    def _selected_door_key(self):
        row = self.door_location_widget.currentRow()
        if row < 0 or row >= len(DOOR_LOCATIONS):
            return None
        return DOOR_LOCATIONS[row][1]

    def _clear_plot(self):
        self.plot.clear()
        self.plot.setTitle('')

    def _validate_vin(self):
        vin = self.edit_vin.text().strip()
        if not vin:
            self.statusBar().showMessage('Please enter a VIN.')
            return None
        return vin

    def cache_relevant_stats(self, vin):
        door_key = self._selected_door_key()
        raw_outliers = vin_query(vin)
        if not raw_outliers:
            return []

        if door_key:
            raw_outliers = [r for r in raw_outliers if r['door_location'] == door_key]

        return init_test_case_list(raw_outliers)

    def plot_selection(self, stat, family):
        self._clear_plot()

        self.plot.setTitle(stat.name, color=LIME, size='14pt')
        self.plot.setLabel('bottom', stat.result_x_unit, color=TEXT)
        self.plot.setLabel('left', stat.result_y_unit, color=TEXT)

        if family:
            family_matrix = matricize_test_cases(family)
            if family_matrix.shape[1] > 0:
                self.plot.plot(
                    family_matrix[0], family_matrix[1],
                    pen=None, symbol='o', symbolBrush=LIME_DIM, symbolSize=6,
                )

        self.plot.plot(
            np.array([float(stat.result_x)]),
            np.array([float(stat.result_y)]),
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

    def _update_nav_buttons(self):
        has_items = len(self.stats_selection) > 0
        self.button_next.setEnabled(has_items and self.current_stat < len(self.stats_selection) - 1)
        self.button_prev.setEnabled(has_items and self.current_stat > 0)
        if has_items:
            self.label_status.setText(
                f'{self.current_stat + 1} / {len(self.stats_selection)}'
            )
        else:
            self.label_status.setText('')

    def show_next(self):
        if self.current_stat < len(self.stats_selection) - 1:
            self.current_stat += 1
            self._display_current_stat()

    def show_prev(self):
        if self.current_stat > 0:
            self.current_stat -= 1
            self._display_current_stat()

    def _display_current_stat(self):
        if not self.stats_selection:
            return
        stat = self.stats_selection[self.current_stat]
        family_raw = fetch_stat_family(stat.name, stat.location)
        family = init_test_case_list(family_raw)
        self.plot_selection(stat, family)
        self._update_nav_buttons()
        self.statusBar().showMessage(
            f'VIN: {stat.vehicle}  |  {stat.name}  @  {stat.location}'
        )

    def init_plots(self):
        vin = self._validate_vin()
        if vin is None:
            return

        self.stats_selection = self.cache_relevant_stats(vin)
        self.current_stat = 0

        if not self.stats_selection:
            self._clear_plot()
            self._update_nav_buttons()
            self.statusBar().showMessage(f'No outlier results found for VIN: {vin}')
            return

        self.statusBar().showMessage(f'Found {len(self.stats_selection)} outlier(s) for VIN {vin}')
        self._display_current_stat()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    form = intro_form()
    form.show()

    sys.exit(app.exec())
