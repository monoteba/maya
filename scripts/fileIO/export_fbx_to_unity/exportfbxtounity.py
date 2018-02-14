"""
## Description
Customized bake process and fbx settings suited for use with Unity and possibly other game engines as well.

## Features
- Simplified export process
- Split animation into clips
- Maintain step tangent for keys (useful for stop-motion style animation)
- Cleanup unchanged keys

## Installation
Save script in Maya's script folder.

## Execute as python
import exportfbxtounity
exportfbxtounity.create()
"""

# todo: save project with maya project?
# todo: option for other export folder (if you often export same character to same folder)
# todo: insert key on every clip start/end frame - ask to save? Can we just undo?
# todo: cleanup curves - animation clips must have keys in them!
# todo: how to bake without saving?
# todo: optimize step tangent process
# todo: add item to "File" menu

import pymel.core as pm
import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om
import os
import json
import sys

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
    try:
        if window is None:
            window = ExportFbxToUnity(parent=get_main_maya_window())
            print '// Created %s' % window.objectName()
        window.show()  # show the window
        window.raise_()  # raise it on top of others
        window.activateWindow()  # set focus to it
    except Exception as e:
        sys.stdout.write(str(e) + '\n')


def delete():
    global window
    try:
        if window is not None:
            print '// Deleting %s' % window.objectName()
            window.delete_instance()
            window = None
    except Exception as e:
        sys.stdout.write(str(e) + '\n')


class ExportFbxToUnity(QMainWindow):
    def __init__(self, parent):
        super(ExportFbxToUnity, self).__init__(parent)
        self.parent = parent
        
        self.setWindowTitle('Export FBX to Unity')
        self.window_name = 'ExportFbxToUnityObj'
        self.setObjectName(self.window_name)
        
        self.setMinimumWidth(350)
        # self.setMaximumWidth(1000)
        
        # we need both of these to make the window order behave correctly
        if os.name == 'nt':  # windows platform
            self.setWindowFlags(Qt.Window)
        else:
            self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)

        self.setProperty("saveWindowPref", True)
        
        self.original_selection = None
        self.transform_attributes = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'visibility']
        
        # qt widgets
        self.file_input = QLineEdit()
        self.file_input.setToolTip('Tip: Save to subfolders using forward slashes like\nsubfolder/my_file.fbx')
        self.set_folder_path_label = ElidedLabel()
        
        self.time_slider_radio = QRadioButton('Time slider')
        self.start_end_radio = QRadioButton('Start/end')
        self.start_end_label = self.create_label('Start/end:')
        self.start_input = QLineEdit()
        self.end_input = QLineEdit()
        
        self.animation_only_layout = QHBoxLayout()
        self.animation_only_label = self.create_label('Animation only:')
        self.animation_only_checkbox = QCheckBox()
        
        self.bake_animation_layout = QGridLayout()
        self.bake_animation_label = self.create_label('Bake animation:')
        self.bake_animation_checkbox = QCheckBox()
        self.euler_filter_label = self.create_label('Apply euler filter')
        self.euler_filter_checkbox = QCheckBox()
        self.has_stepped_label = self.create_label('Has stepped tangents')
        self.has_stepped_checkbox = QCheckBox()
        
        self.animation_clip_layout = QHBoxLayout()
        self.animation_clip_label = self.create_label('Animation clips:')
        self.animation_clip_checkbox = QCheckBox()
        
        self.clip_data = [["Take 001", pm.playbackOptions(q=True, min=True), pm.playbackOptions(q=True, max=True)]]
        header = ["Clip name", "Start", "End"]
        self.table_model = AnimationClipTableModel(self, self.clip_data, header)
        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)
        self.add_clip_button = QPushButton('Add Clip')
        self.remove_clip_button = QPushButton('Remove Selected Clips')
        
        # folder path for export
        self.export_dir = None
        
        # maya callbacks
        self.open_callback = om.MSceneMessage.addCallback(om.MSceneMessage.kAfterOpen, self.after_open_file)
        self.new_callback = om.MSceneMessage.addCallback(om.MSceneMessage.kAfterNew, self.after_open_file)
        
        # create and open the ui
        self.create_menu()
        self.create_window()
    
    def keyPressEvent(self, event):
        pass  # Prevent key press events to propagate to Maya
    
    def hideEvent(self, event):
        try:
            if not self.isMinimized():
                self.close_window()
        except Exception as e:
            sys.stdout.write(str(e) + '\n')
    
    def delete_instance(self):
        self.remove_callbacks()
        self.deleteLater()
    
    def after_open_file(self, *args):
        self.load_options()
    
    def remove_callbacks(self):
        om.MSceneMessage.removeCallback(self.open_callback)
        om.MSceneMessage.removeCallback(self.new_callback)
        
    def create_menu(self):
        # add item to File menu - disabled for now
        return
        
        file_menu = pm.language.melGlobals['gMainFileMenu']
        pm.mel.eval('buildFileMenu()')
        
        if pm.menuItem('exportfbxtounity', exists=True):
            pm.deleteUI('exportfbxtounity', menuItem=True)
        
        pm.menuItem('exportfbxtounity', label='Export FBX', command=self.show_window, parent=file_menu)

    def show_window(self, *args):
        self.show()
        self.raise_()
        self.activateWindow()
    
    def create_window(self, *args):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        main_vertical_layout = QVBoxLayout(main_widget)
        main_vertical_layout.setContentsMargins(6, 6, 6, 6)
        
        # style widgets
        button_small_height = 22
        button_large_height = 26
        input_height = 20
        
        self.setStyleSheet(
            'QLineEdit { padding: 0 3px; border-radius: 2px; }'
            'QLineEdit:disabled { color: rgb(128,128,128); background-color: rgb(64,64,64); }'
            'QLabel:disabled { background-color: none; }'
            'QPushButton { padding: 0 6px; border-radius: 0px; background-color: rgb(93,93,93); }'
            'QPushButton:hover { background-color: rgb(112,112,112); }'
            'QPushButton:pressed { background-color: rgb(29,29,29); }'
        )
        
        # create and arrange elements
        inner_vertical_layout = QVBoxLayout()
        
        # file layout
        file_layout = QHBoxLayout()
        
        file_label = self.create_label('File name:')
        
        self.file_input.setPlaceholderText('e.g. Model@Animation')
        self.file_input.setFixedHeight(input_height)
        self.file_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        file_regex = QRegExp("^[\w\d\.,-=@\(\)\[\]]+$")
        file_validator = QRegExpValidator(file_regex, self.file_input)
        self.file_input.setValidator(file_validator)
        
        file_layout.addWidget(file_label)
        file_layout.addWidget(self.file_input)
        file_layout.setAlignment(Qt.AlignVCenter)
        
        # set project layout
        set_folder_layout = QHBoxLayout()
        
        set_folder_label = self.create_label('Export folder:')
        
        set_folder_button = QPushButton('Set Export Folder')
        set_folder_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        set_folder_button.setFixedHeight(button_small_height)
        self.connect(set_folder_button, SIGNAL("clicked()"), self.set_export_folder)
        
        self.set_folder_path_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.set_folder_path_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.set_folder_path_label.setMinimumWidth(1)
        
        set_folder_layout.addWidget(set_folder_label)
        set_folder_layout.addWidget(set_folder_button)
        set_folder_layout.addWidget(self.set_folder_path_label)
        
        # time slider and start/end
        time_layout = QHBoxLayout()
        time_label = self.create_label('Time range:')
        self.time_slider_radio.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.start_end_radio.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        
        self.connect(self.time_slider_radio, SIGNAL("toggled(bool)"), self.toggle_start_end)
        self.connect(self.start_end_radio, SIGNAL("toggled(bool)"), self.toggle_start_end)
        
        time_layout.addWidget(time_label)
        time_layout.addWidget(self.time_slider_radio)
        time_layout.addWidget(self.start_end_radio)
        
        # start/end input
        start_end_layout = QHBoxLayout()
        
        number_validator = QDoubleValidator()
        number_validator.setNotation(QDoubleValidator.StandardNotation)
        number_validator.setDecimals(4)
        
        self.start_input.setFixedHeight(input_height)
        self.start_input.setValidator(number_validator)
        self.end_input.setFixedHeight(input_height)
        self.end_input.setValidator(number_validator)
        
        start_end_layout.addWidget(self.start_end_label)
        start_end_layout.addWidget(self.start_input)
        start_end_layout.addWidget(self.end_input)
        
        # options
        self.animation_only_checkbox.setToolTip('Only export animation without geometry. '
                                                'Useful for character animation.')
        self.bake_animation_checkbox.setToolTip('Use a customized bake method. '
                                                'For safety, this requires saving the file before.')
        self.euler_filter_checkbox.setToolTip('Apply euler filter to rotation after baking.')
        self.has_stepped_checkbox.setToolTip('After baking animation, attempt to set tangents to step.\n\n'
                                             'IMPORTANT: Untick "Resample Curves" in Unity to keep the stepped '
                                             'tangents.')
        
        self.connect(self.bake_animation_checkbox, SIGNAL('toggled(bool)'), self.toggle_bake_animation)
        self.connect(self.animation_clip_checkbox, SIGNAL('toggled(bool)'), self.toggle_animation_clip)
        
        self.animation_only_layout.addWidget(self.animation_only_label)
        self.animation_only_layout.addWidget(self.animation_only_checkbox)
        
        self.bake_animation_layout.addWidget(self.bake_animation_label, 0, 0)
        self.bake_animation_layout.addWidget(self.bake_animation_checkbox, 0, 1)
        self.bake_animation_layout.addWidget(self.euler_filter_label, 1, 0)
        self.bake_animation_layout.addWidget(self.euler_filter_checkbox, 1, 1)
        self.bake_animation_layout.addWidget(self.has_stepped_label, 2, 0)
        self.bake_animation_layout.addWidget(self.has_stepped_checkbox, 2, 1)
        
        self.animation_clip_layout.addWidget(self.animation_clip_label)
        self.animation_clip_layout.addWidget(self.animation_clip_checkbox)
        
        # animation clip table
        table_layout = QVBoxLayout()
        
        self.table_view.setEditTriggers(QAbstractItemView.DoubleClicked |
                                        QAbstractItemView.EditKeyPressed |
                                        QAbstractItemView.AnyKeyPressed)
        self.table_view.verticalHeader().setVisible(False)
        
        if qt_version == 5:
            self.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        else:
            self.table_view.horizontalHeader().setResizeMode(0, QHeaderView.Stretch)
        
        self.table_view.setColumnWidth(1, 80)  # fixed width for start
        self.table_view.setColumnWidth(2, 80)  # fixed width for end
        table_layout.addWidget(self.table_view)
        
        # table add/remove buttons
        table_button_layout = QHBoxLayout()
        
        self.add_clip_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.add_clip_button.setFixedHeight(button_small_height)
        self.connect(self.add_clip_button, SIGNAL('clicked()'), self.add_clip)
        self.remove_clip_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.remove_clip_button.setFixedHeight(button_small_height)
        self.connect(self.remove_clip_button, SIGNAL('clicked()'), self.remove_clip)
        
        table_button_layout.addWidget(self.add_clip_button)
        table_button_layout.addWidget(self.remove_clip_button)
        
        # export and close buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(4)
        export_button = QPushButton('Export Selected')
        export_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        export_button.setFixedHeight(button_large_height)
        self.connect(export_button, SIGNAL('clicked()'), self.export)
        
        button_layout.addWidget(export_button)
        
        # add widgets to inner layout
        inner_vertical_layout.addLayout(file_layout)
        inner_vertical_layout.addLayout(set_folder_layout)
        inner_vertical_layout.addLayout(self.create_separator_layout())
        inner_vertical_layout.addLayout(time_layout)
        inner_vertical_layout.addLayout(start_end_layout)
        inner_vertical_layout.addLayout(self.create_separator_layout())
        inner_vertical_layout.addLayout(self.animation_only_layout)
        inner_vertical_layout.addLayout(self.create_separator_layout())
        inner_vertical_layout.addLayout(self.bake_animation_layout)
        inner_vertical_layout.addLayout(self.create_separator_layout())
        inner_vertical_layout.addLayout(self.animation_clip_layout)
        inner_vertical_layout.addLayout(table_layout)
        inner_vertical_layout.addLayout(table_button_layout)
        inner_vertical_layout.addSpacerItem(self.create_spacer_item(16))
        inner_vertical_layout.addLayout(button_layout)
        
        main_vertical_layout.addLayout(inner_vertical_layout)
        
        self.load_options()
        self.toggle_start_end()
        self.update_export_folder_path()
        self.toggle_bake_animation()
        self.toggle_animation_clip(self.animation_clip_checkbox.isChecked())
    
    @staticmethod
    def create_label(text):
        label = QLabel(text)
        label.setFixedWidth(140)
        label.setFixedHeight(16)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return label
    
    @staticmethod
    def create_spacer_item(height=8):
        return QSpacerItem(1, height, QSizePolicy.Maximum, QSizePolicy.Fixed)
    
    @staticmethod
    def create_separator_layout():
        layout = QHBoxLayout()
        frame = QFrame()
        frame.setFrameShape(QFrame.HLine)
        layout.addWidget(frame)
        return layout
    
    def toggle_start_end(self, checked=False):
        checked = self.start_end_radio.isChecked()
        self.start_end_label.setEnabled(checked)
        self.start_input.setEnabled(checked)
        self.end_input.setEnabled(checked)
    
    def toggle_bake_animation(self, checked=None):
        if checked is None:
            checked = self.bake_animation_checkbox.isChecked()
        self.euler_filter_label.setEnabled(checked)
        self.euler_filter_checkbox.setEnabled(checked)
        self.has_stepped_label.setEnabled(checked)
        self.has_stepped_checkbox.setEnabled(checked)
    
    def toggle_animation_clip(self, checked):
        self.table_view.setEnabled(checked)
        self.add_clip_button.setEnabled(checked)
        self.remove_clip_button.setEnabled(checked)
    
    def update_export_folder_path(self):
        if self.export_dir:
            self.set_folder_path_label.setText(self.export_dir)
        else:
            self.set_folder_path_label.setText('(not set)')
    
    def set_export_folder(self):
        if not self.export_dir or self.export_dir == 'None':
            dialog_dir = pm.fileDialog2(caption='Set FBX Export Folder',
                                        dialogStyle=2,
                                        fileMode=3,
                                        fileFilter='.',
                                        okCaption='Set Folder')
        else:
            dialog_dir = pm.fileDialog2(caption='Set FBX Export Folder',
                                        dialogStyle=2,
                                        fileMode=3,
                                        fileFilter='.',
                                        okCaption='Set Folder',
                                        dir=self.export_dir)
        
        if dialog_dir is None:
            return
        
        self.export_dir = dialog_dir[0]
        self.set_folder_path_label.setText(self.export_dir)
    
    def add_clip(self):
        name = "Take %03d" % (len(self.clip_data) + 1)
        self.clip_data.append([name, pm.playbackOptions(q=True, min=True), pm.playbackOptions(q=True, max=True)])
        self.table_view.model().layoutChanged.emit()
    
    def remove_clip(self):
        selected_rows = sorted(set(index.row() for index in self.table_view.selectedIndexes()))
        i = 0
        
        for row in selected_rows:
            if len(self.clip_data) > 1:
                del self.clip_data[row - i]
                i += 1
            elif len(self.clip_data) == 1:
                self.clip_data.append(
                    ["Take 001", pm.playbackOptions(q=True, min=True), pm.playbackOptions(q=True, max=True)])
                del self.clip_data[0]
        
        self.table_view.model().layoutChanged.emit()
    
    def export(self):
        if self.export_dir is None:
            pm.warning('No folder has been set for export')
            return
        
        time_range = self.get_time_range()
        
        if time_range is None:
            pm.error('Could not determine time range.')
            return
        
        self.save_options()
        
        # if "bake animation" is checked
        if self.bake_animation_checkbox.isChecked():
            self.bake(time_range)
        else:
            self.export_fbx(time_range)
    
    def bake(self, time_range):
        # if file has never been saved
        if pm.system.sceneName() == '':
            pm.confirmDialog(title='Scene never saved',
                             message='Your scene has never been saved.\n\n'
                                     'Please save your scene and try again.',
                             button=['OK'])
            return
        
        # if asked to skip confirmation message (0 is default)
        confirm = pm.confirmDialog(title='Bake animation is NOT undoable!',
                                   message='Do you want to save before baking the animation and re-open the file after '
                                           'it is done? This action cannot be undone!',
                                   button=['Save, bake and re-open', "Bake without saving", 'Cancel'],
                                   cancelButton='Cancel',
                                   dismissString='Cancel')
        
        if confirm == 'Cancel':
            return
            
        # save original file
        if confirm == 'Save, bake and re-open':
            original_file = pm.saveFile(force=True)
        
        self.original_selection = pm.ls(sl=True)
        
        # set playback range (appears that fbx uses it for the range when exporting)
        pm.playbackOptions(min=time_range[0], max=time_range[1])
        
        try:
            # bake keys
            self.custom_bake(time_range)
            self.remove_non_transform_curves()
            self.export_fbx(time_range)
        except Exception as e:
            pm.warning('An unknown error occured.')
            print str(e)
        
        # open original file
        if confirm == 'Save, bake and re-open':
            pm.openFile(original_file, force=True)
    
    def get_time_range(self):
        if self.time_slider_radio.isChecked():
            return pm.playbackOptions(q=True, min=True), pm.playbackOptions(q=True, max=True)
        elif self.start_end_radio.isChecked():
            if self.start_input.text() == '' or self.end_input.text() == '':
                pm.warning('You need to set start and end frame.')
                return None
            return sorted((float(self.start_input.text()), float(self.end_input.text())))
        return None
    
    def custom_bake(self, time_range):
        stepped_limit = 0.0001
        
        # get objects to bake
        baked_objects = self.original_selection
        joints = pm.listRelatives(self.original_selection, allDescendents=True, type='joint')
        baked_objects.extend(pm.listRelatives(self.original_selection, allDescendents=True, type='transform'))
        
        pm.select(baked_objects, r=True)
        obj_list = om.MGlobal.getActiveSelectionList()
        iterator = om.MItSelectionList(obj_list, om.MFn.kDagNode)
        
        to_bake = []
        while not iterator.isDone():
            node = iterator.getDependNode()
            nodeFn = om.MFnDependencyNode(node)
            
            if nodeFn.findPlug('tx', True).connectedTo(True, False) or \
                    nodeFn.findPlug('tx', True).connectedTo(True, False) or \
                    nodeFn.findPlug('ty', True).connectedTo(True, False) or \
                    nodeFn.findPlug('tz', True).connectedTo(True, False) or \
                    nodeFn.findPlug('rx', True).connectedTo(True, False) or \
                    nodeFn.findPlug('ry', True).connectedTo(True, False) or \
                    nodeFn.findPlug('rz', True).connectedTo(True, False) or \
                    nodeFn.findPlug('sx', True).connectedTo(True, False) or \
                    nodeFn.findPlug('sy', True).connectedTo(True, False) or \
                    nodeFn.findPlug('sz', True).connectedTo(True, False) or \
                    nodeFn.findPlug('visibility', True).connectedTo(True, False):
                to_bake.append(str(iterator.getDagPath().fullPathName()))
            iterator.next()
        
        samples = 1
        has_stepped = self.has_stepped_checkbox.isChecked()
        if has_stepped:
            samples = 0.5
        
        # bake selected transforms and children with half step
        pm.bakeResults(to_bake,
                       time=time_range,
                       sampleBy=samples,
                       hierarchy='none',
                       disableImplicitControl=True,
                       preserveOutsideKeys=False,
                       simulation=True,
                       minimizeRotation=True)
        
        # remove static channels to speed up analysis
        to_bake.extend(joints)
        pm.select(to_bake, r=True)
        pm.delete(staticChannels=True)
        
        muted_curves = []
        for obj in to_bake:
            for curve in pm.keyframe(obj, q=True, name=True):
                # find muted curves
                connection = pm.listConnections(curve, d=True, s=False)[0]
                if pm.nodeType(connection) == 'mute':
                    if pm.getAttr('%s.mute' % connection):
                        muted_curves.append(curve)
                        continue
                
                # analyse half frames to determine which are stepped
                if has_stepped:
                    for key in range(int(time_range[0]), int(time_range[1])):
                        try:
                            epsilon_half = abs(pm.keyframe(curve, q=True, valueChange=True, time=(key,))[0]
                                               - pm.keyframe(curve, q=True, valueChange=True, time=(key + 0.5,))[0])
                            epsilon_full = abs(pm.keyframe(curve, q=True, valueChange=True, time=(key,))[0]
                                               - pm.keyframe(curve, q=True, valueChange=True, time=(key + 1))[0])
                            if epsilon_half < stepped_limit < epsilon_full:
                                pm.keyTangent(curve, time=(key,), ott='step')
                        except IndexError:
                            continue
        
        pm.delete(muted_curves)
        
        # remove unsnapped keys
        if has_stepped:
            pm.selectKey(to_bake, unsnappedKeys=True)
            pm.cutKey(animation='keys', clear=True)
        
        # apply euler filter
        if self.euler_filter_checkbox.isChecked():
            self.apply_euler_filter(to_bake)
        
        pm.currentTime(time_range[0])
        pm.setKeyframe(to_bake, attribute=self.transform_attributes, t=time_range[0], insertBlend=False)
        
        # re-select original selection, so that we export the right thing
        pm.select(self.original_selection, r=True)
    
    def remove_non_transform_curves(self):
        objs = self.original_selection
        objs.extend(pm.listRelatives(pm.ls(sl=True), allDescendents=True, type='transform'))
        all_curves = set(pm.keyframe(objs, q=True, name=True))
        transform_curves = set(pm.keyframe(objs, q=True, name=True, attribute=self.transform_attributes))
        
        for curve in all_curves:
            if curve not in transform_curves:
                pm.delete(curve)
    
    def apply_euler_filter(self, objs):
        curves = pm.keyframe(objs, q=True, name=True, attribute=['rx', 'ry', 'rz'])
        pm.filterCurve(curves, filter='euler')
    
    def export_fbx(self, time_range):
        # get window properties
        if self.file_input.text() == '':
            pm.warning('You need to write a file name"')
            return False
        
        # set fbx options
        pm.mel.eval('FBXResetExport')  # reset any user preferences so we start clean
        pm.mel.eval('FBXExportAnimationOnly -v %d' % int(self.animation_only_checkbox.isChecked()))
        pm.mel.eval('FBXExportBakeComplexAnimation -v 0')
        pm.mel.eval('FBXExportBakeComplexStart -v %d' % time_range[0])
        pm.mel.eval('FBXExportBakeComplexEnd -v %d' % time_range[1])
        pm.mel.eval('FBXExportBakeResampleAnimation -v 0')
        pm.mel.eval('FBXExportCameras -v 0')
        pm.mel.eval('FBXExportConstraints -v 0')
        pm.mel.eval('FBXExportLights -v 0')
        pm.mel.eval('FBXExportQuaternion -v quaternion')
        pm.mel.eval('FBXExportAxisConversionMethod none')
        pm.mel.eval('FBXExportSmoothMesh -v 0')  # do not export subdivision version
        pm.mel.eval('FBXExportShapes -v 1')  # needed for skins and blend shapes
        pm.mel.eval('FBXExportSkins -v 1')
        pm.mel.eval('FBXExportSkeletonDefinitions -v 1')
        pm.mel.eval('FBXExportEmbeddedTextures -v 0')
        pm.mel.eval('FBXExportInputConnections -v 1')
        pm.mel.eval('FBXExportInstances -v 1')  # preserve instances by sharing same mesh
        pm.mel.eval('FBXExportUseSceneName -v 1')
        pm.mel.eval('FBXExportSplitAnimationIntoTakes -c')  # clear previous clips
        
        if self.animation_clip_checkbox.isChecked():
            for row in self.clip_data:
                pm.mel.eval('FBXExportSplitAnimationIntoTakes -v \"%s\" %d %d' %
                            (str(row[0]), int(row[1]), int(row[2])))
        
        pm.mel.eval('FBXExportGenerateLog -v 0')
        pm.mel.eval('FBXExportInAscii -v 0')
        
        # save the fbx
        f = "%s/%s.fbx" % (self.export_dir, self.file_input.text())
        pm.mel.eval('FBXExport -f "%s" -s' % f)
        sys.stdout.write('# Saved fbx to: %s\n' % f)
    
    def close_window(self):
        self.save_options()
        self.close()
    
    def save_options(self):
        # save settings with file
        pm.system.fileInfo['exportfbxtounity_file_name'] = self.file_input.text()
        pm.system.fileInfo['exportfbxtounity_time_slider_radio'] = int(self.time_slider_radio.isChecked())
        pm.system.fileInfo['exportfbxtounity_start_end_radio'] = int(self.start_end_radio.isChecked())
        pm.system.fileInfo['exportfbxtounity_start'] = self.start_input.text()
        pm.system.fileInfo['exportfbxtounity_end'] = self.end_input.text()
        pm.system.fileInfo['exportfbxtounity_animation_only'] = int(self.animation_only_checkbox.isChecked())
        pm.system.fileInfo['exportfbxtounity_bake_animation'] = int(self.bake_animation_checkbox.isChecked())
        pm.system.fileInfo['exportfbxtounity_euler_filter'] = int(self.euler_filter_checkbox.isChecked())
        pm.system.fileInfo['exportfbxtounity_has_stepped'] = int(self.has_stepped_checkbox.isChecked())
        pm.system.fileInfo['exportfbxtounity_animation_clip'] = int(self.animation_clip_checkbox.isChecked())
        pm.system.fileInfo['exportfbxtounity_clips'] = json.dumps(self.clip_data)
        
        # save "export_dir" with preferences
        if self.export_dir is not None:
            pm.optionVar['exportfbxtounity_save_dir'] = self.export_dir
        else:
            pm.optionVar['exportfbxtounity_save_dir'] = ''
    
    def load_options(self):
        # try to load settings from file
        try:
            self.file_input.setText(pm.system.fileInfo['exportfbxtounity_file_name'])
        except (RuntimeError, KeyError):
            self.file_input.setText(os.path.splitext(os.path.basename(pm.system.sceneName()))[0])
        
        try:
            self.time_slider_radio.setChecked(int(pm.system.fileInfo['exportfbxtounity_time_slider_radio']))
        except (RuntimeError, KeyError):
            self.time_slider_radio.setChecked(True)
        
        try:
            self.start_end_radio.setChecked(int(pm.system.fileInfo['exportfbxtounity_start_end_radio']))
        except (RuntimeError, KeyError):
            self.start_end_radio.setChecked(False)
        
        try:
            self.start_input.setText(pm.system.fileInfo['exportfbxtounity_start'])
        except (RuntimeError, KeyError):
            self.start_input.setText('')
        
        try:
            self.end_input.setText(pm.system.fileInfo['exportfbxtounity_end'])
        except (RuntimeError, KeyError):
            self.end_input.setText('')
        
        try:
            self.animation_only_checkbox.setChecked(int(pm.system.fileInfo['exportfbxtounity_animation_only']))
        except (RuntimeError, KeyError):
            self.animation_only_checkbox.setChecked(False)
        
        try:
            self.bake_animation_checkbox.setChecked(int(pm.system.fileInfo['exportfbxtounity_bake_animation']))
        except (RuntimeError, KeyError):
            self.bake_animation_checkbox.setChecked(False)
        
        try:
            self.euler_filter_checkbox.setChecked(int(pm.system.fileInfo['exportfbxtounity_euler_filter']))
        except (RuntimeError, KeyError):
            self.euler_filter_checkbox.setChecked(False)
        
        try:
            self.has_stepped_checkbox.setChecked(int(pm.system.fileInfo['exportfbxtounity_has_stepped']))
        except (RuntimeError, KeyError):
            self.has_stepped_checkbox.setChecked(False)
        
        try:
            self.animation_clip_checkbox.setChecked(int(pm.system.fileInfo['exportfbxtounity_animation_clip']))
        except (RuntimeError, KeyError):
            self.animation_clip_checkbox.setChecked(False)
        
        # animation clips
        self.load_clips()
        
        # load "export_dir" from preferences
        try:
            self.export_dir = pm.optionVar['exportfbxtounity_save_dir']
        except (RuntimeError, KeyError):
            self.export_dir = None
    
    def load_clips(self):
        try:
            read_clips = pm.system.fileInfo['exportfbxtounity_clips']
            if read_clips:
                read_clips = read_clips.replace('\\"', '"')
                self.clip_data = json.loads(read_clips)
        except (RuntimeError, KeyError, ValueError):
            pass
        
        # we have to re-assign the table model data with the clip data, otherwise the reference is lost!!
        self.table_model.table_data = self.clip_data
        self.table_view.model().layoutChanged.emit()


class ElidedLabel(QLabel):
    def paintEvent(self, *args, **kwargs):
        painter = QPainter(self)
        metrics = QFontMetrics(self.font())
        elided = metrics.elidedText(self.text(), Qt.ElideLeft, self.width())
        painter.drawText(self.rect(), self.alignment(), elided)


class AnimationClipTableModel(QAbstractTableModel):
    def __init__(self, parent, datain, header, *args):
        try:
            QAbstractTableModel.__init__(self, parent, *args)
            self.table_data = datain
            self.header = header
        except Exception as e:
            sys.stdout.write(str(e) + '\n')
    
    def rowCount(self, parent):
        return len(self.table_data)
    
    def columnCount(self, parent):
        col = 0
        
        if self.table_data[0]:
            col = len(self.table_data[0])
        
        return col
    
    def data(self, index, role):
        if role == Qt.DisplayRole or role == Qt.EditRole:
            try:
                row = index.row()
                col = index.column()
                return self.table_data[row][col]
            except Exception as e:
                sys.stdout.write(str(e) + '\n')
        
        return None
    
    def headerData(self, col, orientation, role):
        try:
            if orientation == Qt.Horizontal and role == Qt.DisplayRole:
                return self.header[col]
            return None
        except Exception as e:
            sys.stdout.write(str(e) + '\n')
    
    def setData(self, index, value, role=Qt.EditRole):
        try:
            row = index.row()
            col = index.column()
            self.table_data[row][col] = value
            self.emit(SIGNAL("dataChanged()"))
        except Exception as e:
            sys.stdout.write(str(e) + '\n')
            return False
        
        return True
    
    def flags(self, index):
        try:
            flags = super(self.__class__, self).flags(index)
            
            flags |= Qt.ItemIsEditable
            flags |= Qt.ItemIsSelectable
            flags |= Qt.ItemIsEnabled
            flags |= Qt.ItemIsDragEnabled
            flags |= Qt.ItemIsDropEnabled
            
            return flags
        except Exception as e:
            sys.stdout.write(str(e) + '\n')
