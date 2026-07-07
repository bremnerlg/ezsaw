'''
EZSAW V3.1.0A PYQT Edition
ABANDONING KIVY.
'''
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLineEdit
)
import pyqtgraph as pg
import numpy as np
from autoStatFacilities import (test_case, vin_fetch_outliers, init_test_case, 
    AUTO_STAT_FIELDS, join_stat_with_table, matricize_test_cases)

'''
# Structure to store imperative information for the graphing mechanism
# so user can go backward, forward, can have multiple stat types to analyze, etc.
class stat_cache():
    def __init__(self):
        self.previous
        self.current
        self.next
'''

class intro_form(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EZSAW Version 3.1.0 Alpha")
        self.resize(800, 600)

        central = QWidget()
        self.setCentralWidget(central)


        layout = QVBoxLayout(central)

        top_row = QHBoxLayout()

        self.edit = QLineEdit("Enter a VIN...")
        self.button_enter = QPushButton("Enter")
        self.button_next = QPushButton("Next")
        self.button_prev = QPushButton("Previous")

        top_row.addWidget(self.edit)
        top_row.addWidget(self.button_prev)
        top_row.addWidget(self.button_enter)
        top_row.addWidget(self.button_next)

        layout.addLayout(top_row) # add the row as a layout instead of each individual widget
        self.plot = pg.PlotWidget()
        layout.addWidget(self.plot)
        self.relevant_stats = []

        self.setLayout(layout)

        # self.button_next.clicked.connect(next_stats)
        # self.button_next.clicked.connect(prev_stats)
        self.button_enter.clicked.connect(self.graph_first_outlier_with_related)
        # self.button_next.clicked.connect(self.cache_traverse_graph)

    def cache_relevant_stats(self):
        return list(set(vin_fetch_outliers(self.edit.text(), fields=['auto_door_stat_name'])))

    # find raw data -> convert to test case -> generate graph labels -> matricize stats into np array -> plot
    def graph_first_outlier_with_related(self):
        vin_selected = self.edit.text()
        self.relevant_stats = self.cache_relevant_stats()
        outliers_raw = vin_fetch_outliers(vin_selected)

        stat = init_test_case(outliers_raw[0], vin_selected)
        stat.print()
        # print('related stats confirmation: ')
        # print(join_stat_with_table(outlier_stat))
        # print('[DBG] Joined Stats: ')
        stats_matrix = matricize_test_cases(join_stat_with_table(stat))
        # print('[DBG] graph_next_outlier_with_related() stat matrix: ')
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

    '''
    # DEBUG FUNCTIONS
    def display_failed_graphs(self):
        vin_selected = self.edit.text()
        outliers = vin_fetch_outliers(vin_selected)
        print(f'[DBG] Query Return: ')
        print(outliers)
        for i in outliers:
            test_results = init_test_case(i, vin_selected)
            if test_results.out_of_tolerance == True:
                fetch the full results for that stat name
                graph the full results
                paint vin_selected a different colour than the rest
    '''

    '''
    display_related_stats():
    given a specific stat, display all other stats that are
    within that stat case
    def display_related_stats(self):
        vin_selected = self.edit.text()
        outliers = vin_fetch_outliers(vin_selected)
        for outlier in outliers:
            stat = init_test_case(outlier, vin_selected)    
            related_stats = join_stat_with_table(stat)
            print(related_stats)
        print("\n\n---------TEST_RESULTS----------")
        i_cnt = 0
        for i in tests:
            test_results = init_test_case(i, vin_selected)
            i_cnt = i_cnt + 1

            if test_results.out_of_tolerance == True:
                print(str(i[0]) + ': FAILED.')
            else:
                print(str(i[0]) + ': PASSED')
            print("Set: " + str(i_cnt))
            print("VIN: " + str(test_results.vehicle) + "\n"
                  "y val: " + str(test_results.result_y) + "\n" 
                  "upper_lim: " + str(test_results.result_y_upper) + "\n" 
                  "lower_lim: " + str(test_results.result_y_lower) + "\n")
    
    def plot_stats(self): # given a list of test cases, plot each
        vin_selected = self.edit.text()
        outliers = vin_fetch_outliers(vin_selected)
        stats_graph = pg.plot(title="testgraph1")
        for outlier in outliers:
            stat = init_test_case(outlier, vin_selected) 
            stat_graph(stat)      

    def display_entry_table(self, vin: str):
        vin_selected = self.edit.text()
        outliers = vin_fetch_outliers(vin)
        print("[DBG] Query Return: ")
        print(outliers)
        print("\n\n---------TEST_RESULTS----------")
        i_cnt = 0
        for i in outliers:
            
            test_results = init_test_case(i, vin_selected)
            i_cnt = i_cnt + 1

            if test_results.out_of_tolerance == True:
                print(str(i[0]) + ': FAILED.')
            else:
                print(str(i[0]) + ': PASSED')
            print("Set: " + str(i_cnt))
            print("VIN: " + str(test_results.vehicle) + "\n"
                  "y val: " + str(test_results.result_y) + "\n" 
                  "upper_lim: " + str(test_results.result_y_upper) + "\n" 
                  "lower_lim: " + str(test_results.result_y_lower) + "\n")

    def dbg_print_vin_fetch(self):
        print(vin_fetch_outliers(self.edit.text(), AUTO_STAT_FIELDS, 'auto_door_stats', 'steps'))

   ''' 

if __name__ == '__main__':
    app = QApplication(sys.argv)

    form = intro_form()
    form.show()

    sys.exit(app.exec())