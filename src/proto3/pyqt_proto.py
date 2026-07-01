'''
EZSAW V3.1.0A PYQT Edition
ABANDONING KIVY.
'''
import sys
from PySide6.QtWidgets import (QApplication, QDialog, QLineEdit, 
    QPushButton, QVBoxLayout)
import dataFacilities


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

        self.button.clicked.connect(self.dbg_print_vin_fetch)

    def dbg_print_vin_fetch(self):
        print(vin_fetch(self.edit.text()))

    

if __name__ == '__main__':
    app = QApplication(sys.argv)

    form = intro_form()
    form.show()

    sys.exit(app.exec())