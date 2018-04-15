"""
For testing and development in Maya use:
import sys
sys.path.append('')  # path to folder that contains this script

import basic_ui
# basic_ui.delete()  # try to delete it before reloading to avoid duplicates, should only be needed when testing
# reload(basic_ui)  # only reload when testing
basic_ui.create()
"""

import maya.OpenMayaUI as omui
import os
from functools import partial

# PySide2 is for Maya 2017+, PySide is for Maya 2016-(2011 ?)
try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
    from shiboken2 import wrapInstance
except ImportError:
    from PySide.QtCore import *
    from PySide.QtGui import *
    from shiboken import wrapInstance

basic_window = None


def get_main_maya_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(ptr), QMainWindow)


def create():
    global basic_window
    
    if basic_window is None:
        basic_window = BasicUI(parent=get_main_maya_window())
        print '// Created %s' % basic_window.objectName()
        
    basic_window.show()  # show the window
    basic_window.raise_()  # raise it on top of others
    basic_window.activateWindow()  # set focus to it


def delete():
    global basic_window
    if basic_window is not None:
        print '// Deleting %s' % basic_window.objectName()
        basic_window.deleteLater()
        basic_window = None


class BasicUI(QMainWindow):
    def __init__(self, parent):
        super(BasicUI, self).__init__(parent)
        
        self.parent = parent
        self.window_name = 'BasicWindowObj'
        
        # Set basic window properties
        self.setWindowTitle('Basic UI')
        self.setObjectName(self.window_name)
        
        if os.name == 'nt':  # windows platform
            self.setWindowFlags(Qt.Window)
        else:
            self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
            
        self.setProperty("saveWindowPref", True)  # maya's automatic window management
        
        # Define window dimensions
        self.setMinimumWidth(200)
        self.setMaximumWidth(400)
        self.setMinimumHeight(42)
        self.setMaximumHeight(200)
        
        # Setup central widget and layout
        self.central_widget = QWidget()
        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.setContentsMargins(8, 8, 8, 8)
        self.setCentralWidget(self.central_widget)
        
        self.example_layout()
    
    def example_layout(self):
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(8)
        
        label = QLabel('Fancy')
        label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(label)
        
        self.button = QPushButton('Button')
        self.button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.connect(self.button, SIGNAL("clicked()"), partial(self.button_clicked, self.button))
        layout.addWidget(self.button)
        
        self.central_layout.addLayout(layout)
    
    def button_clicked(self, obj):
        print '// Clicked on %s' % obj.text()
        self.button.setText('Clicked')
    
    def hideEvent(self, event):
        # Close the window instead of hiding it when clicking on 'x' in the title bar
        if not self.isMinimized():
            self.close()
            delete()
    
    def keyPressEvent(self, event):
        # Prevents keyboard press events from being passed onto Maya
        pass
