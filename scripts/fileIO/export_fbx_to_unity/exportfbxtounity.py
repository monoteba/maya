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

# todo: support multiple clips
# todo: save project with maya project?
# todo: cleanup curves
# todo: consider if it's possible to set keys on fewer objects

import pymel.core as pm
import maya.OpenMayaUI as omui
import maya.OpenMaya as om
import os

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


def get_main_maya_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(ptr), QMainWindow)


def create():
    global window
    if window is None:
        window = ExportFbxToUnity(parent=get_main_maya_window())
        print '// Created %s' % window.objectName()
    window.show()  # show the window
    window.raise_()  # raise it on top of others
    window.activateWindow()  # set focus to it


def delete():
    global window
    if window is not None:
        print '// Deleting %s' % window.objectName()
        window.delete_instance()
        window = None


class ExportFbxToUnity(QMainWindow):
    def __init__(self, parent):
        super(ExportFbxToUnity, self).__init__(parent)
        
        self.setWindowTitle('Export FBX to Unity')
        self.window_name = 'ExportFbxToUnityObj'
        self.setObjectName(self.window_name)
        
        self.setMinimumWidth(500)
        self.setMaximumWidth(1000)
        
        # we need both of these to make the window order behave correctly
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setProperty("saveWindowPref", True)
        
        self.original_selection = None
        self.transform_attributes = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'visibility']
        
        # qt widgets
        self.file_input = QLineEdit()
        self.set_folder_path_label = ElidedLabel()
        
        self.time_slider_radio = QRadioButton('Time slider')
        self.start_end_radio = QRadioButton('Start/end')
        self.start_end_label = self.create_label('Start/end:')
        self.start_input = QLineEdit()
        self.end_input = QLineEdit()
        
        self.options_layout = QGridLayout()
        self.animation_only_checkbox = QCheckBox()
        self.bake_animation_checkbox = QCheckBox()
        self.euler_filter_checkbox = QCheckBox()
        self.has_stepped_checkbox = QCheckBox()
        
        # folder path for export
        self.export_dir = None
        
        # maya callbacks
        self.open_callback = om.MSceneMessage.addCallback(om.MSceneMessage.kAfterOpen, self.after_open_file)
        self.new_callback = om.MSceneMessage.addCallback(om.MSceneMessage.kAfterNew, self.after_open_file)
        
        # create and open the ui
        self.create_window()
    
    def keyPressEvent(self, event):
        # Prevent key press events to propagate to Maya
        pass
    
    def hideEvent(self, event):
        if not self.isMinimized():
            self.close_window()
            
    def delete_instance(self):
        self.remove_callbacks()
        self.deleteLater()
            
    def after_open_file(self, *args):
        self.load_options()
        
    def remove_callbacks(self):
        om.MSceneMessage.removeCallback(self.open_callback)
        om.MSceneMessage.removeCallback(self.new_callback)
    
    def create_window(self):
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
        set_folder_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        set_folder_button.setFixedHeight(button_small_height)
        self.connect(set_folder_button, SIGNAL("clicked()"), self.set_export_folder)
        
        self.set_folder_path_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.set_folder_path_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
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
        self.has_stepped_checkbox.setToolTip('After baking animation, attempt to set tangents to step. '
                                             'IMPORTANT: Untick "Resample Curves" in Unity to keep the stepped '
                                             'tangents.')
        
        self.connect(self.bake_animation_checkbox, SIGNAL('toggled(bool)'), self.toggle_bake_animation)
        
        self.options_layout.addWidget(self.create_label('Animation only:'), 0, 0)
        self.options_layout.addWidget(self.animation_only_checkbox, 0, 1)
        self.options_layout.addWidget(self.create_label('Bake Animation:'), 1, 0)
        self.options_layout.addWidget(self.bake_animation_checkbox, 1, 1)
        self.options_layout.addWidget(self.create_label('Apply euler filter:'), 2, 0)
        self.options_layout.addWidget(self.euler_filter_checkbox, 2, 1)
        self.options_layout.addWidget(self.create_label('Has stepped tangents:'), 3, 0)
        self.options_layout.addWidget(self.has_stepped_checkbox, 3, 1)
        
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
        inner_vertical_layout.addSpacerItem(QSpacerItem(1, 8, QSizePolicy.Maximum, QSizePolicy.Minimum))
        inner_vertical_layout.addLayout(time_layout)
        inner_vertical_layout.addLayout(start_end_layout)
        inner_vertical_layout.addSpacerItem(QSpacerItem(1, 8, QSizePolicy.Maximum, QSizePolicy.Minimum))
        inner_vertical_layout.addLayout(self.options_layout)
        inner_vertical_layout.addStretch()
        inner_vertical_layout.addLayout(button_layout)
        
        main_vertical_layout.addLayout(inner_vertical_layout)
        
        self.load_options()
        self.toggle_start_end()
        self.update_export_folder_path()
        self.toggle_bake_animation()
    
    @staticmethod
    def create_label(text):
        label = QLabel(text)
        label.setFixedWidth(140)
        label.setFixedHeight(16)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return label
    
    def toggle_start_end(self, checked=False):
        start_end_checked = self.start_end_radio.isChecked()
        self.start_end_label.setEnabled(start_end_checked)
        self.start_input.setEnabled(start_end_checked)
        self.end_input.setEnabled(start_end_checked)
    
    def toggle_bake_animation(self, checked=None):
        if checked is None:
            checked = self.bake_animation_checkbox.isChecked()
        for row in range(2, 4):
            for col in range(2):
                self.options_layout.itemAtPosition(row, col).widget().setEnabled(checked)
    
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
        if pm.optionVar.get('exportfbxtounity_skip_save_confirm', 0) == 0:
            confirm = pm.confirmDialog(title='Save file and continue?',
                                       message='This will save the current file and re-open it when done. Are you sure '
                                               'you want to continue?',
                                       button=['Yes', "Yes (never ask again)", 'No'],
                                       cancelButton='No',
                                       dismissString='No')
            
            if confirm == 'No':
                return
            elif confirm == "Yes (don't ask again)":
                pm.optionVar['exportfbxtounity_skip_save_confirm'] = 1
        
        # save original file
        original_file = pm.saveFile(force=True)
        
        self.original_selection = pm.ls(sl=True)
        
        # set playback range (appears that fbx uses it for the range when exporting)
        pm.playbackOptions(min=time_range[0], max=time_range[1])
        
        try:
            # bake keys
            self.custom_bake(time_range)
            self.remove_non_transform_curves()
            self.export_fbx(time_range)
        except:
            pm.warning('An unknown error occured.')
        
        # open original file
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
        # todo: only meshes, joints, constrained objects and animated transforms
        baked_objects = pm.listRelatives(self.original_selection, allDescendents=True, type='transform')
        
        samples = 1
        has_stepped = self.has_stepped_checkbox.isChecked()
        if has_stepped:
            samples = 0.5
        
        # bake selected transforms and children with half step
        pm.bakeResults(baked_objects,
                       time=time_range,
                       sampleBy=samples,
                       hierarchy='none',
                       disableImplicitControl=True,
                       preserveOutsideKeys=False,
                       simulation=True,
                       minimizeRotation=True)
        
        # remove static channels to speed up analysis
        pm.select(baked_objects, r=True)
        pm.delete(staticChannels=True)
        
        muted_curves = []
        for obj in baked_objects:
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
            pm.selectKey(baked_objects, unsnappedKeys=True)
            pm.cutKey(animation='keys', clear=True)
        
        # apply euler filter
        if self.euler_filter_checkbox.isChecked():
            self.apply_euler_filter(baked_objects)
        
        pm.currentTime(time_range[0])
        pm.setKeyframe(baked_objects, attribute=self.transform_attributes, t=time_range[0], insertBlend=False)
    
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
        pm.mel.eval('FBXExportAnimationOnly -v %d' % self.animation_only_checkbox.isChecked())
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
        # pm.mel.eval('FBXExportSplitAnimationIntoTakes -v \"%s\" %d %d'
        #             % (clip_name, time_range[0], time_range[1]))
        pm.mel.eval('FBXExportGenerateLog -v 0')
        pm.mel.eval('FBXExportInAscii -v 0')
        
        # save the fbx
        f = "%s/%s.fbx" % (self.export_dir, self.file_input.text())
        pm.mel.eval('FBXExport -f "%s" -s' % f)
    
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
        
        # save "export_dir" with preferences
        if self.export_dir is not None:
            pm.optionVar['exportfbxtounity_save_dir'] = self.export_dir
        else:
            pm.optionVar['exportfbxtounity_save_dir'] = ''
    
    def load_options(self):
        # load settings from file
        try:
            self.file_input.setText(pm.system.fileInfo['exportfbxtounity_file_name'])
            self.time_slider_radio.setChecked(int(pm.system.fileInfo['exportfbxtounity_time_slider_radio']))
            self.start_end_radio.setChecked(int(pm.system.fileInfo['exportfbxtounity_start_end_radio']))
            self.start_input.setText(pm.system.fileInfo['exportfbxtounity_start'])
            self.end_input.setText(pm.system.fileInfo['exportfbxtounity_end'])
            self.animation_only_checkbox.setChecked(int(pm.system.fileInfo['exportfbxtounity_animation_only']))
            self.bake_animation_checkbox.setChecked(int(pm.system.fileInfo['exportfbxtounity_bake_animation']))
            self.euler_filter_checkbox.setChecked(int(pm.system.fileInfo['exportfbxtounity_euler_filter']))
            self.has_stepped_checkbox.setChecked(int(pm.system.fileInfo['exportfbxtounity_has_stepped']))
        except (RuntimeError, KeyError):
            # defaults
            self.file_input.setText(os.path.splitext(os.path.basename(pm.system.sceneName()))[0])
            self.time_slider_radio.setChecked(True)
            self.start_end_radio.setChecked(False)
            self.start_input.setText('')
            self.end_input.setText('')
            self.animation_only_checkbox.setChecked(False)
            self.bake_animation_checkbox.setChecked(False)
            self.euler_filter_checkbox.setChecked(False)
            self.has_stepped_checkbox.setChecked(False)
        
        # load "export_dir" from preferences
        try:
            self.export_dir = pm.optionVar['exportfbxtounity_save_dir']
        except (RuntimeError, KeyError):
            self.export_dir = None


class ElidedLabel(QLabel):
    def paintEvent(self, event):
        painter = QPainter(self)
        metrics = QFontMetrics(self.font())
        elided = metrics.elidedText(self.text(), Qt.ElideLeft, self.width())
        painter.drawText(self.rect(), self.alignment(), elided)
