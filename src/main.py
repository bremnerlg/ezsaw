'''
EZSAW V3.1.0A PYQT Edition
ABANDONING KIVY.
'''
import sys
import pyqtgraph as pg
from PySide6.QtWidgets import (QApplication, QDialog, QLineEdit, 
    QPushButton, QVBoxLayout)
from autoStatFacilities import vin_fetch_outliers, init_test_case, AUTO_STAT_FIELDS


class intro_form(QDialog):

    def __init__(self, parent=None):
        super(intro_form, self).__init__(parent)
        self.setWindowTitle("EZSAW Version 3.1.0 Alpha")

        self.edit = QLineEdit("Enter a VIN...")
        self.button = QPushButton("Enter")

        layout = QVBoxLayout()
        layout.addWidget(self.edit)
        layout.addWidget(self.button)

        self.setLayout(layout)

        self.button.clicked.connect(self.display_entry_table)


    def display_entry_table(self, vin: str):
        vin_selected = self.edit.text()
        outliers = vin_fetch_outliers(vin_selected, AUTO_STAT_FIELDS, 'auto_door_stats', 'steps')
        print("[DBG] Query Return: ")
        print(outliers)
        print("\n\n---------TEST_RESULTS----------")
        for i in outliers:
            test_results = init_test_case(i, vin_selected)
            i_cnt = i_cnt + 1

            print(str(i[0]) + ': FAILED.')
            print("Set: " + str(i_cnt))
            print("VIN: " + str(test_results.vin) + "\n"
                  "y val: " + str(test_results.result) + "\n" 
                  "upper_lim: " + str(test_results.upper_limit) + "\n" 
                  "lower_lim: " + str(test_results.lower_limit) + "\n")

    def dbg_print_vin_fetch(self):
        print(vin_fetch_outliers(self.edit.text(), AUTO_STAT_FIELDS, 'auto_door_stats', 'steps'))

    

if __name__ == '__main__':
    app = QApplication(sys.argv)

    form = intro_form()
    form.show()

    sys.exit(app.exec())