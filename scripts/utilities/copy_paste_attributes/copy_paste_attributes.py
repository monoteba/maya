"""
## WORK IN PROGRESS

## Installation
Save script in Maya's script folder.

## Execute as python
import copy_paste_attributes
copy_paste_attributes.create()
"""

import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om
import pymel.core as pm
import collections
import json
import sys
import os

qt_version = 5
try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
    from shiboken2 import wrapInstance
except ImportError:
    from PySide.QtCore import *
    from PySide.QtGui import *
    from shiboken import wrapInstance
    qt_version = 4

window = None

def get_main_maya_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(ptr), QMainWindow)


def create():
    global window
    if window is None:
        window = CopyPasteAttributes(parent=get_main_maya_window())
    window.show()  # show the window
    window.raise_()  # raise it on top of others
    window.activateWindow()  # set focus to it


def delete():
    global window
    if window is not None:
        sys.stdout.write('# Deleting %s' % window.objectName())
        window.delete_instance()
        window = None


class CopyPasteAttributes(QMainWindow):
    def __init__(self, parent):
        super(CopyPasteAttributes, self).__init__(parent)
        
        # setup window
        self.parent = parent
        
        self.setWindowTitle('Copy/Paste Attributes')
        self.window_name = 'CopyPasteAttributesObj'
        self.setObjectName(self.window_name)
        
        self.setMinimumWidth(350)
        self.setMaximumWidth(1000)
                
        if os.name == 'nt':  # windows platform
            self.setWindowFlags(Qt.Window)
        else:
            self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        
        self.setProperty("saveWindowPref", True)
        
        self.clipboard = None
        self.json_data = ""
        
        self.create_window()
        
    def keyPressEvent(self, event):
        pass  # prevent key press events to propagate to maya
        
    def hideEvent(self, event):
        if not self.isMinimized():
            self.close_window()
    
    def close_window(self):
        self.close()
        
    def show_window(self, *args):
        self.show()
        self.raise_()
        self.activateWindow()
    
    def create_window(self, *args):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(6, 6, 6, 6)
        
        self.setStyleSheet(
            'QLabel { min-width: 100px; min-height: 20px; }'
            'QLabel:disabled { background-color: none; }'
            'QLineEdit { min-height: 20px; padding: 0 3px; border-radius: 2px; }'
            'QLineEdit:disabled { color: rgb(128,128,128); background-color: rgb(64,64,64); }'
            'QPushButton { padding: 0 6px; border-radius: 0px; background-color: rgb(93,93,93); height: 26px }'
            'QPushButton:hover { background-color: rgb(112,112,112); }'
            'QPushButton:pressed { background-color: rgb(29,29,29); }'
        )
                       
        # copy button layout
        self.copy_layout = QHBoxLayout()
        self.copy_button = QPushButton('Copy Selected Attributes')
        self.copy_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.connect(self.copy_button, SIGNAL('clicked()'), self.copy_button_clicked)
        self.copy_layout.addWidget(self.copy_button)
        
        # paste buttons layout
        self.paste_layout = QHBoxLayout()
        self.paste_name_button = QPushButton('Paste by Name')
        self.paste_name_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.connect(self.paste_name_button, SIGNAL('clicked()'), self.paste_name_button_clicked)
        self.paste_order_button = QPushButton('Paste by Selected Order')
        self.paste_order_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.connect(self.paste_order_button, SIGNAL('clicked()'), self.paste_order_button_clicked)
        self.paste_layout.addWidget(self.paste_name_button)
        self.paste_layout.addWidget(self.paste_order_button)
        
        # data layout
        self.data_layout = QHBoxLayout()
        self.data_label = QLabel('Copy Data:')
        self.data_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.data_line = QLineEdit()
        self.data_line.setText(self.json_data)
        self.data_line.setReadOnly(True)
        self.data_line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.data_layout.addWidget(self.data_label)
        self.data_layout.addWidget(self.data_line)
        
        # paste data layout
        self.paste_data_layout = QHBoxLayout()
        self.paste_data_label = QLabel('Optional Data:')
        self.paste_data_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.paste_data_line = QLineEdit()
        self.paste_data_line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.paste_data_line.setPlaceholderText('Paste text from "Copy Data"')
        self.paste_data_layout.addWidget(self.paste_data_label)
        self.paste_data_layout.addWidget(self.paste_data_line)
        
        # add layouts to inner layout, and inner layout to main layout
        inner_layout = QVBoxLayout()
        inner_layout.addLayout(self.copy_layout)
        inner_layout.addLayout(self.data_layout)
        inner_layout.addLayout(self.create_separator_layout())
        inner_layout.addLayout(self.paste_layout)
        inner_layout.addLayout(self.paste_data_layout)
        inner_layout.addStretch()
        
        main_layout.addLayout(inner_layout)
        
    def copy_button_clicked(self):
        clipboard = self.copy_channelbox_attributes()
        
        if clipboard:
            self.clipboard = clipboard
            self.json_data = json.dumps(self.clipboard)
            self.data_line.setText(self.json_data)
        
    def paste_name_button_clicked(self):
        pass
        
    def paste_order_button_clicked(self):
        pass
        
            
    @staticmethod
    def copy_channelbox_attributes():
        # copy values from selected main and shape attributes
        main_channels = pm.channelBox('mainChannelBox', q=True, selectedMainAttributes=True)
        shape_channels = pm.channelBox('mainChannelBox', q=True, selectedShapeAttributes=True)
        # input_attr = pm.channelBox('mainChannelBox', q=True, selectedHistoryAttributes=True)
        # output_attr = pm.channelBox('mainChannelBox', q=True, selectedOutputAttributes=True)
        
        clipboard = collections.OrderedDict()
        for obj in pm.ls(orderedSelection=True):
            main_attr = {}
            shape_attr = {}
            
            if main_channels:
                for at in main_channels:
                    if pm.hasAttr(obj, at):
                        main_attr[str(at)] = pm.getAttr(obj + '.' + at)
                    
            shape_node = obj.getShape()
            if shape_channels:
                for at in shape_channels:
                    if pm.hasAttr(obj, at):
                        shape_attr[str(at)] = pm.getAttr(shape_node + '.' + at)
            
            clipboard[str(obj.fullPath())] = {'main_attributes': main_attr, 'shape_attributes': shape_attr}
        
        return clipboard
    
    @staticmethod
    def paste_channelbox_attributes(data=None, objects=None):
        if not data:
            pm.warning('Nothing to paste from.')
            return
        
        for obj in objects:
            for k, cat in data.iteritems():
                for at, value in cat['main_attributes'].iteritems():
                    if pm.hasAttr(obj, at):
                        pm.setAttr(obj + '.' + at, float(value))
                
                shape_node = obj.getShape()
                if shape_node:
                    for at, value in cat['shape_attributes'].iteritems():
                        if pm.hasAttr(shape_node, at):
                            pm.setAttr(shape_node + '.' + at, float(value))
    
    @staticmethod
    def create_separator_layout():
        layout = QHBoxLayout()
        frame = QFrame()
        frame.setFrameShape(QFrame.HLine)
        layout.addWidget(frame)
        return layout
