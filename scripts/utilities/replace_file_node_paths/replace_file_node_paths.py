"""
Search and replace image path in all file nodes.

### HOW TO USE ###
Copy the script to Maya's script folder. Then execute this Python code or add to shelf:

import replace_file_node_paths
replace_file_node_paths.open()

"""

import pymel.core as pm
import maya.OpenMayaUI as omui
import re, sys, os
from functools import partial


try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
    from shiboken2 import wrapInstance
except ImportError:
    from PySide.QtCore import *
    from PySide.QtGui import *
    from shiboken import wrapInstance
    

window = None


def open():
    create()
    

def get_main_maya_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(ptr), QMainWindow)


def create():
    global window
    if window is None:
        window = ReplaceFileNodePathsUI(parent=get_main_maya_window())
    window.show()  # show the window
    window.raise_()  # raise it on top of others
    window.activateWindow()  # set focus to it


def delete():
    global window
    if window is not None:
        sys.stdout.write('# Deleting %s' % window.objectName())
        window.delete_instance()
        window = None


class ReplaceFileNodePathsUI(QMainWindow):
    def __init__(self, parent):
        super(ReplaceFileNodePathsUI, self).__init__(parent)
        self.parent = parent

        self.setWindowTitle('Replace File Texture Paths')
        self.window_name = 'ReplaceFileTexturePathsObj'
        self.setObjectName(self.window_name)

        if os.name == 'nt':  # windows platform
            self.setWindowFlags(Qt.Window)
        else:
            self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        
        self.setProperty("saveWindowPref", True)

        self.setMinimumWidth(350)

        self.create_window()
        self.setAttribute(Qt.WA_DeleteOnClose)


    def keyPressEvent(self, event):
        pass  # prevent key press events to propagate to maya
        
        
    def hideEvent(self, event):
        if not self.isMinimized():
            self.close_window()
    
    
    def close_window(self):
        self.close()
        global window
        window = None
        
        
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
            'QLabel { min-width: 110px; min-height: 20px; }'
            'QLabel:disabled { background-color: none; }'
            'QLineEdit { min-height: 20px; padding: 0 3px; border-radius: 2px; }'
            'QLineEdit:disabled { color: rgb(128,128,128); background-color: rgb(64,64,64); }'
            'QPushButton { padding: 0 6px; border-radius: 0px; background-color: rgb(93,93,93); height: 26px }'
            'QPushButton:hover { background-color: rgb(112,112,112); }'
            'QPushButton:pressed { background-color: rgb(29,29,29); }'
        )

        # fonts
        font_bold = QFont()
        font_bold.setBold(True)

        # description
        self.desc_layout = QHBoxLayout()
        self.desc_label = QLabel('Replace the image path of "file" and "psdFileTex" textures')
        self.desc_label.setFont(font_bold)
        self.desc_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.desc_label.setWordWrap(True)
        self.desc_layout.addWidget(self.desc_label)

        # missing only layout
        self.missing_layout = QHBoxLayout()
        self.missing_label = self.create_label('Missing Files Only')
        self.missing_checkbox = QCheckBox()
        self.missing_checkbox.setToolTip("Only replace for file nodes, where the image file cannot be found or doesn't exists.")
        self.missing_layout.addWidget(self.missing_label)
        self.missing_layout.addWidget(self.missing_checkbox)

        # input layout
        self.input_layout = QGridLayout()
        self.input_layout.setHorizontalSpacing(6)
        self.input_layout.setVerticalSpacing(6)

        self.before_label = self.create_label('Insert Before:')
        self.before_line_edit = self.create_line_edit()
        self.connect(self.before_line_edit, SIGNAL('editingFinished()'), self.save_options)
        self.after_label = self.create_label('Insert After:')
        self.after_line_edit = self.create_line_edit()
        self.connect(self.after_line_edit, SIGNAL('editingFinished()'), self.save_options)
        self.search_label = self.create_label('Search:')
        self.search_line_edit = self.create_line_edit()
        self.connect(self.search_line_edit, SIGNAL('editingFinished()'), self.save_options)
        self.connect(self.search_line_edit, SIGNAL('textEdited(QString)'), self.search_edit_changed)
        self.replace_label = self.create_label('Replace:')
        self.replace_line_edit = self.create_line_edit()
        self.connect(self.replace_line_edit, SIGNAL('editingFinished()'), self.save_options)
        self.clear_btn = QPushButton('Clear')
        self.connect(self.clear_btn, SIGNAL('clicked()'), self.clear_btn_clicked)

        self.input_layout.addWidget(self.before_label, 0, 0)
        self.input_layout.addWidget(self.before_line_edit, 0, 1)
        self.input_layout.addWidget(self.after_label, 1, 0)
        self.input_layout.addWidget(self.after_line_edit, 1, 1)
        self.input_layout.addWidget(self.search_label, 2, 0)
        self.input_layout.addWidget(self.search_line_edit, 2, 1)
        self.input_layout.addWidget(self.replace_label, 3, 0)
        self.input_layout.addWidget(self.replace_line_edit, 3, 1)
        self.input_layout.addWidget(self.clear_btn, 4, 1)

        # buttons
        self.btn_layout = QHBoxLayout()
        self.selected_btn = QPushButton('Replace Selected')
        self.selected_btn.setToolTip('Replace image path in selected file nodes.')
        self.connect(self.selected_btn, SIGNAL('clicked()'), partial(self.btn_clicked, True))
        self.all_btn = QPushButton('Replace All')
        self.all_btn.setToolTip('Replace image path in all file nodes.')
        self.connect(self.all_btn, SIGNAL('clicked()'), partial(self.btn_clicked, False))
        self.btn_layout.addWidget(self.selected_btn)
        self.btn_layout.addWidget(self.all_btn)

        # layout
        inner_layout = QVBoxLayout()
        inner_layout.setSpacing(6)
        inner_layout.addLayout(self.desc_layout)
        inner_layout.addLayout(self.separator_layout())
        inner_layout.addLayout(self.missing_layout)
        inner_layout.addSpacerItem(self.create_spacer_item(12))
        inner_layout.addLayout(self.input_layout)
        inner_layout.addStretch()
        inner_layout.addSpacerItem(self.create_spacer_item(24))
        inner_layout.addLayout(self.btn_layout)

        main_layout.addLayout(inner_layout)

        self.load_options()


    def btn_clicked(self, selected=True):
        ReplaceFileNodePaths.replace(
            before=self.before_line_edit.text(),
            after=self.after_line_edit.text(),
            search=self.search_line_edit.text(), 
            replace=self.replace_line_edit.text(), 
            selected=selected,
            missing_only=self.missing_checkbox.isChecked()
            )

    def clear_btn_clicked(self):
        self.before_line_edit.setText('')
        self.after_line_edit.setText('')
        self.search_line_edit.setText('')
        self.replace_line_edit.setText('')

    def search_edit_changed(self):
        if not self.search_line_edit.text():
            self.replace_line_edit.setEnabled(False)
        else:
            self.replace_line_edit.setEnabled(True)


    def save_options(self):
        pm.optionVar['replacefilenodepaths_missing'] = int(self.missing_checkbox.isChecked())
        pm.optionVar['replacefilenodepaths_before'] = self.before_line_edit.text()
        pm.optionVar['replacefilenodepaths_after'] = self.after_line_edit.text()
        pm.optionVar['replacefilenodepaths_search'] = self.search_line_edit.text()
        pm.optionVar['replacefilenodepaths_replace'] = self.replace_line_edit.text()


    def load_options(self):
        try:
            self.missing_checkbox.setChecked(int(pm.optionVar['replacefilenodepaths_missing']))
        except:
            pass

        try:
            self.before_line_edit.setText(pm.optionVar['replacefilenodepaths_before'])
        except:
            pass

        try:
            self.after_line_edit.setText(pm.optionVar['replacefilenodepaths_after'])
        except:
            pass

        try:
            self.search_line_edit.setText(pm.optionVar['replacefilenodepaths_search'])
        except:
            pass

        try:
            self.replace_line_edit.setText(pm.optionVar['replacefilenodepaths_replace'])
        except:
            pass

        self.search_edit_changed()


    @staticmethod
    def create_label(text=""):
        label = QLabel(text)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        return label


    @staticmethod
    def create_line_edit():
        line_edit = QLineEdit()
        line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        return line_edit


    @staticmethod
    def create_spacer_item(height=8):
        return QSpacerItem(1, height, QSizePolicy.Maximum, QSizePolicy.Fixed)

    @staticmethod
    def separator_layout():
        layout = QHBoxLayout()
        frame = QFrame()
        frame.setFrameShape(QFrame.HLine)
        layout.addWidget(frame)
        return layout


class ReplaceFileNodePaths():
    @staticmethod
    def replace(before="", after="", search="", replace="", selected=True, missing_only=False):

        file_nodes = pm.ls(sl=selected, exactType='file')
        file_nodes.extend(pm.ls(sl=selected, exactType='psdFileTex'))

        if not file_nodes:
            pm.warning('No file nodes found!')
            return
        
        before = before.replace('\\', '/')
        after = after.replace('\\', '/')
        search = search.replace('\\', '/')
        replace = replace.replace('\\', '/')

        # filter missing files
        if missing_only:
            missing_files = []
            for node in file_nodes:
                f = node.attr('fileTextureName').get()
                if not os.path.isfile(f):
                    missing_files.append(node)

            file_nodes = missing_files


        with pm.UndoChunk():
            for node in file_nodes:
                old_path = node.attr('fileTextureName').get()
                old_path = old_path.replace('\\', '/')
                new_path = old_path

                if search:
                    new_path = old_path.replace(search, replace)

                try:
                    node.attr('fileTextureName').set(before + new_path + after)
                except Exception as e:
                    pm.warning(str(e))

        sys.stdout.write('# Replaced %d image name(s)\n' % len(file_nodes))
