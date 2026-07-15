"""
EZSAW V3.1.2A PyQt Edition
"""
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLineEdit, QListWidget,
    QLabel
)
import pyqtgraph as pg
import numpy as np
from src.core.auto_stat_facilities import (
    test_case, vin_query, init_test_case, matricize_test_cases
)


class intro_form(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EZSAW Version 3.1.0 Alpha")
        self.resize(800, 600)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        header = QHBoxLayout()
        top_row = QHBoxLayout()

        door_locations = [
            'Driver Front', 'Driver Rear',
            'Passenger Front', 'Passenger Rear', 'Rear Hatch'
        ]

        self.title = QLabel('EZMetrology Statistical Analysis Wizard Alpha')
        self.edit_vin = QLineEdit("Enter a VIN...")
        self.button_enter = QPushButton("Enter")
        self.button_next = QPushButton("Next")
        self.button_prev = QPushButton("Previous")
        self.door_location_widget = QListWidget()
        self.door_location_widget.addItems(door_locations)

        header.addWidget(self.title)

        top_row.addWidget(self.edit_vin)
        top_row.addWidget(self.button_prev)
        top_row.addWidget(self.button_enter)
        top_row.addWidget(self.button_next)
        top_row.addWidget(self.door_location_widget)

        layout.addLayout(header)
        layout.addLayout(top_row)
        self.plot = pg.PlotWidget()
        layout.addWidget(self.plot)

        self.stats_selection = []
        self.current_stat = 0

        self.setLayout(layout)

        self.button_enter.clicked.connect(self.init_plots)

    def cache_relevant_stats(self):
        vin_selected = self.edit_vin.text()
        outliers = vin_fetch_outliers(vin_selected)
        for outlier in outliers:
            self.stats_selection.append(init_test_case(outlier, vin_selected))

    def plot_selection(stat: test_case):
        stats_matrix = matricize_test_cases(join_stat_with_table(stat))
        self.plot.setLabel('top', stat.name)
        self.plot.setLabel('bottom', stat.result_x_unit)
        self.plot.setLabel('left', stat.result_y_unit)

        self.plot.plot(stats_matrix[0], stats_matrix[1], pen=None, symbol='o')
        self.plot.plot(
            np.array([float(stat.result_x)]),
            np.array([float(stat.result_y)]),
            pen=None,
            symbol='o',
            symbolBrush='r',
        )

        self.plot.addLine(y=stat.result_y_lower, pen=pg.mkPen('b', width=2, style=pg.QtCore.Qt.DashLine))
        self.plot.addLine(y=stat.result_y_upper, pen=pg.mkPen('b', width=2, style=pg.QtCore.Qt.DashLine))

    def init_plots(self):
        vin_selected = self.edit_vin.text()
        self.cache_relevant_stats()

        self.stats_selection = self.relevant_stats[current]
        outliers_raw = vin_fetch_outliers(vin_selected)

        init_stat = init_test_case(outliers_raw[current], vin_selected)
        stat.print()
        stats_matrix = matricize_test_cases(join_stat_with_table(stat))
        self.plot.setLabel('top', stat.name)
        self.plot.setLabel('bottom', stat.result_x_unit)
        self.plot.setLabel('left', stat.result_y_unit)

        self.plot.plot(stats_matrix[0], stats_matrix[1], pen=None, symbol='o')
        self.plot.plot(
            np.array([float(stat.result_x)]),
            np.array([float(stat.result_y)]),
            pen=None,
            symbol='o',
            symbolBrush='r',
        )

        self.plot.addLine(y=stat.result_y_lower, pen=pg.mkPen('b', width=2, style=pg.QtCore.Qt.DashLine))
        self.plot.addLine(y=stat.result_y_upper, pen=pg.mkPen('b', width=2, style=pg.QtCore.Qt.DashLine))


if __name__ == '__main__':
    app = QApplication(sys.argv)

    form = intro_form()
    form.show()

    sys.exit(app.exec())