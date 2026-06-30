'''
EZSAW V3.1.0A PYQT Edition
ABANDONING KIVY.
'''

import sys
import numpy as numpy
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QLabel
)

class MplCanvas(FigureCanvasQTAgg):
    """Canvas Widget Utilizing MPL"""
    def __init__(self, parent=None)