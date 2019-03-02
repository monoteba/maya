"""
For testing and development in Maya use:
import sys
sys.path.append('')  # path to folder that contains this script

import slider
# slider.delete()  # try to delete it before reloading to avoid duplicates, should only be needed when testing
# reload(slider)  # only reload when testing
slider.create()
"""

import maya.OpenMayaUI as omui
import maya.cmds as cmds
import os

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

lazytween_window = None


def get_main_maya_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(ptr), QMainWindow)


def create():
    global lazytween_window
    
    if slider_window is None:
        slider_window = SliderUI(parent=get_main_maya_window())
        print '// Created %s' % slider_window.objectName()
    
    slider_window.show()  # show the window
    slider_window.raise_()  # raise it on top of others
    slider_window.activateWindow()  # set focus to it


def delete():
    global lazytween_window
    if slider_window is not None:
        print '// Deleting %s' % slider_window.objectName()
        slider_window.deleteLater()
        slider_window = None


class SliderUI(QMainWindow):
    def __init__(self, parent):
        super(SliderUI, self).__init__(parent)
        
        self.parent = parent
        self.window_name = 'SliderWindowObj'
        
        # Set slider window properties
        self.setWindowTitle('Slider UI')
        self.setObjectName(self.window_name)
        
        if os.name == 'nt':  # windows platform
            self.setWindowFlags(Qt.Window)
        else:
            self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        
        self.setProperty("saveWindowPref", True)  # maya's automatic window management
        
        # Define window dimensions
        self.setMinimumWidth(200)
        self.setMaximumWidth(400)
        self.setMinimumHeight(80)
        self.setMaximumHeight(200)
        
        # Setup central widget and layout
        self.central_widget = QWidget()
        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.setContentsMargins(8, 8, 8, 8)
        self.setCentralWidget(self.central_widget)
        
        self.slider_layout()
    
    def slider_layout(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        self.slider_label = QLabel()
        self.slider_label.setFixedHeight(20)
        self.slider_label.setAlignment(Qt.AlignCenter)
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setFixedHeight(40)
        self.slider.setMinimum(0)
        self.slider.setMaximum(10)
        self.slider.setValue(5)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(1)
        
        self.slider.valueChanged.connect(self.slider_changed)
        self.slider.sliderReleased.connect(self.slider_released)
        
        self.slider_label.setText(str(self.slider.value()))
        
        layout.addWidget(self.slider_label)
        layout.addWidget(self.slider)
        
        self.central_layout.addLayout(layout)
        
    def slider_changed(self):
        self.slider_label.setText(str(self.slider.value()))
        
    def slider_released(self):
        cmds.warning('Value is %d' % self.slider.value())
    
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
