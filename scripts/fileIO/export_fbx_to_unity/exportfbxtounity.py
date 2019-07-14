"""
## Description
Customized bake process and fbx settings suited for use with Unity and possibly other game engines as well.


## Features
- Simplified export process
- Split animation into clips
- Maintain step tangent for keys (useful for stop-motion style animation)


## Installation
Save script in Maya's scripts folder.


## Execute as Python in Maya
import exportfbxtounity
exportfbxtounity.create()
"""

import pymel.core as pm
import maya.cmds as cmds
import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om
import maya.utils
import maya.mel
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
            sys.stdout.write('// Created %s\n' % window.objectName())
        window.show()  # show the window
        window.raise_()  # raise it on top of others
        window.activateWindow()  # set focus to it
    except Exception as e:
        sys.stdout.write(str(e) + '\n')


def delete():
    global window
    try:
        if window is not None:
            sys.stdout.write('// Deleting %s \n' % window.objectName())
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
        
        self.setMinimumWidth(apply_dpi_scaling(350))
        
        # we need both of these to make the window order behave correctly
        if os.name == 'nt':  # windows platform
            self.setWindowFlags(Qt.Window)
        else:
            self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        
        self.setProperty("saveWindowPref", True)
        
        self.original_selection = None
        self.transform_attributes = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'visibility']
        
        # qt widgets
        self.input_connections_layout = QHBoxLayout()
        self.input_connections_label = self.create_label('Input connections:')
        self.input_connections_checkbox = QCheckBox()
        self.input_connections_checkbox.clicked.connect(self.save_input_connections_option)
        
        self.constraints_layout = QHBoxLayout()
        self.constraints_label = self.create_label('Constraints:')
        self.constraints_checkbox = QCheckBox()
        self.constraints_checkbox.clicked.connect(self.save_constraints_option)
        
        self.animation_only_layout = QHBoxLayout()
        self.animation_only_label = self.create_label('Animation only:')
        self.animation_only_checkbox = QCheckBox()
        self.animation_only_checkbox.clicked.connect(self.save_animation_only_option)
        self.animation_only_description = QLabel('Blendshapes are not exported')
        self.animation_only_description.setStyleSheet('color: rgb(128, 128, 128);')
        self.animation_only_description.setFixedHeight(16)
        self.animation_only_description.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.animation_only_description.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        self.bake_animation_layout = QGridLayout()
        self.bake_animation_label = self.create_label('Bake animation:')
        self.bake_animation_checkbox = QCheckBox()
        self.bake_animation_checkbox.clicked.connect(self.save_bake_animation_option)
        self.euler_filter_label = self.create_label('Apply euler filter')
        self.euler_filter_checkbox = QCheckBox()
        self.euler_filter_checkbox.clicked.connect(self.save_euler_filter_option)
        self.has_stepped_label = self.create_label('Has stepped tangents')
        self.has_stepped_checkbox = QCheckBox()
        self.has_stepped_checkbox.clicked.connect(self.save_has_stepped_option)
        
        self.time_slider_radio = QRadioButton('Time slider')
        self.start_end_radio = QRadioButton('Start/end')
        self.start_end_label = self.create_label('Start/end:')
        self.start_input = QLineEdit()
        self.end_input = QLineEdit()
        
        self.time_slider_radio.clicked.connect(self.save_time_range_option)
        self.start_end_radio.clicked.connect(self.save_time_range_option)
        self.start_input.editingFinished.connect(self.save_time_range_option)
        self.end_input.editingFinished.connect(self.save_time_range_option)
        
        self.animation_clip_layout = QHBoxLayout()
        self.animation_clip_label = self.create_label('Animation clips:')
        self.animation_clip_checkbox = QCheckBox()
        self.animation_clip_checkbox.clicked.connect(self.save_animation_clip_option)
        
        self.clip_data = [
            ["Take 001", int(pm.playbackOptions(q=True, min=True)), int(pm.playbackOptions(q=True, max=True))]]
        
        self.header_labels = ["Clip name", "Start", "End"]
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels(self.header_labels)
        self.table_widget.cellChanged.connect(self.table_cell_changed)
        self.table_is_being_edited = False
        
        self.add_clip_button = QPushButton('Add Clip')
        self.remove_clip_button = QPushButton('Remove Selected Clips')
        
        # folder path for export
        self.save_dir = None
        self.file_name = None
        
        # maya callbacks
        self.open_callback = om.MSceneMessage.addCallback(om.MSceneMessage.kAfterOpen, self.after_open_file)
        self.new_callback = om.MSceneMessage.addCallback(om.MSceneMessage.kAfterNew, self.after_open_file)
        
        # try to load fbx plugin
        if not pm.pluginInfo('fbxmaya.bundle', q=True, loaded=True):
            try:
                pm.loadPlugin('fbxmaya.bundle')
            except:
                pm.warning('# Could not load FBX plugin.')
        
        # create and open the ui
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
    
    def show_window(self, *args):
        self.show()
        self.raise_()
        self.activateWindow()
    
    def create_window(self, *args):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        main_vertical_layout = QVBoxLayout(main_widget)
        margin = apply_dpi_scaling(6)
        main_vertical_layout.setContentsMargins(margin, margin, margin, margin)
        
        # style widgets
        button_small_height = apply_dpi_scaling(22)
        button_large_height = apply_dpi_scaling(26)
        input_height = apply_dpi_scaling(20)
        
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
        
        # options
        self.input_connections_checkbox.setToolTip('Include input connections when exporting.')
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
        
        self.input_connections_layout.addWidget(self.input_connections_label)
        self.input_connections_layout.addWidget(self.input_connections_checkbox)
        
        self.constraints_layout.addWidget(self.constraints_label)
        self.constraints_layout.addWidget(self.constraints_checkbox)
        
        self.animation_only_layout.addWidget(self.animation_only_label)
        self.animation_only_layout.addWidget(self.animation_only_checkbox)
        self.animation_only_layout.addWidget(self.animation_only_description)
        
        self.bake_animation_layout.addWidget(self.bake_animation_label, 0, 0)
        self.bake_animation_layout.addWidget(self.bake_animation_checkbox, 0, 1)
        self.bake_animation_layout.addWidget(self.euler_filter_label, 1, 0)
        self.bake_animation_layout.addWidget(self.euler_filter_checkbox, 1, 1)
        self.bake_animation_layout.addWidget(self.has_stepped_label, 2, 0)
        self.bake_animation_layout.addWidget(self.has_stepped_checkbox, 2, 1)
        
        self.animation_clip_layout.addWidget(self.animation_clip_label)
        self.animation_clip_layout.addWidget(self.animation_clip_checkbox)
        
        # time slider and start/end
        self.time_layout = QHBoxLayout()
        time_label = self.create_label('Time range:')
        self.time_slider_radio.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.start_end_radio.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        
        self.connect(self.time_slider_radio, SIGNAL("toggled(bool)"), self.toggle_start_end)
        self.connect(self.start_end_radio, SIGNAL("toggled(bool)"), self.toggle_start_end)
        
        self.time_layout.addWidget(time_label)
        self.time_layout.addWidget(self.time_slider_radio)
        self.time_layout.addWidget(self.start_end_radio)
        
        # start/end input
        self.start_end_layout = QHBoxLayout()
        
        number_validator = QIntValidator()
        locale = QLocale()
        locale.setNumberOptions(QLocale.OmitGroupSeparator | QLocale.RejectGroupSeparator)
        number_validator.setLocale(locale)
        
        self.start_input.setFixedHeight(input_height)
        self.start_input.setValidator(number_validator)
        self.end_input.setFixedHeight(input_height)
        self.end_input.setValidator(number_validator)
        
        self.start_end_layout.addWidget(self.start_end_label)
        self.start_end_layout.addWidget(self.start_input)
        self.start_end_layout.addWidget(self.end_input)
        
        # animation clip table
        table_layout = QVBoxLayout()
        
        if qt_version == 5:
            self.table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        else:
            self.table_widget.horizontalHeader().setResizeMode(0, QHeaderView.Stretch)
        
        self.table_widget.setColumnWidth(1, apply_dpi_scaling(80))
        self.table_widget.setColumnWidth(2, apply_dpi_scaling(80))
        table_layout.addWidget(self.table_widget)
        
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
        button_layout.setSpacing(apply_dpi_scaling(4))
        export_button = QPushButton('Export Selected')
        export_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        export_button.setFixedHeight(button_large_height)
        self.connect(export_button, SIGNAL('clicked()'), self.export)
        
        button_layout.addWidget(export_button)
        
        # add widgets to inner layout
        inner_vertical_layout.addLayout(self.animation_only_layout)
        inner_vertical_layout.addLayout(self.constraints_layout)
        inner_vertical_layout.addLayout(self.input_connections_layout)
        inner_vertical_layout.addLayout(self.create_separator_layout())
        inner_vertical_layout.addLayout(self.bake_animation_layout)
        inner_vertical_layout.addLayout(self.create_separator_layout())
        inner_vertical_layout.addLayout(self.time_layout)
        inner_vertical_layout.addLayout(self.start_end_layout)
        inner_vertical_layout.addLayout(self.animation_clip_layout)
        inner_vertical_layout.addLayout(table_layout)
        inner_vertical_layout.addLayout(table_button_layout)
        inner_vertical_layout.addSpacerItem(self.create_spacer_item(16))
        inner_vertical_layout.addLayout(button_layout)
        
        main_vertical_layout.addLayout(inner_vertical_layout)
        
        self.load_options()
        self.toggle_start_end()
        self.toggle_bake_animation()
        self.toggle_animation_clip(self.animation_clip_checkbox.isChecked())
    
    @staticmethod
    def create_label(text):
        label = QLabel(text)
        label.setFixedWidth(apply_dpi_scaling(140))
        label.setFixedHeight(apply_dpi_scaling(16))
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return label
    
    @staticmethod
    def create_spacer_item(height=8):
        return QSpacerItem(1, apply_dpi_scaling(height), QSizePolicy.Maximum, QSizePolicy.Fixed)
    
    @staticmethod
    def create_separator_layout():
        layout = QHBoxLayout()
        frame = QFrame()
        frame.setFrameShape(QFrame.HLine)
        layout.addWidget(frame)
        return layout
    
    def toggle_start_end(self):
        if self.animation_clip_checkbox.isChecked():
            checked = False
        else:
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
        self.table_widget.setEnabled(checked)
        self.add_clip_button.setEnabled(checked)
        self.remove_clip_button.setEnabled(checked)
        
        widgets = (self.time_layout.itemAt(i) for i in range(self.time_layout.count()))
        
        for w in widgets:
            w.widget().setEnabled(not checked)
        
        widgets = (self.start_end_layout.itemAt(i) for i in range(self.start_end_layout.count()))
        
        for w in widgets:
            w.widget().setEnabled(not checked)
        
        self.toggle_start_end()
    
    def add_clip(self):
        self.table_is_being_edited = True
        
        name = "Take %03d" % (len(self.clip_data) + 1)
        start = str(int(pm.playbackOptions(q=True, min=True)))
        end = str(int(pm.playbackOptions(q=True, max=True)))
        data = [name, start, end]
        row = self.table_widget.rowCount()
        
        self.table_widget.insertRow(row)
        self.table_widget.setItem(row, 0, QTableWidgetItem(name))
        self.table_widget.setItem(row, 1, QTableWidgetItem(start))
        self.table_widget.setItem(row, 2, QTableWidgetItem(end))
        
        self.clip_data.append(data)
        
        self.table_is_being_edited = False
        
        self.save_animation_clip_data()
    
    def remove_clip(self):
        self.table_is_being_edited = True
        
        rows = set()
        for item in self.table_widget.selectedIndexes():
            rows.add(item.row())
        
        for i, row in enumerate(rows):
            self.table_widget.removeRow(row - i)
            del self.clip_data[row - i]
        
        self.table_widget.clearSelection()
        
        self.table_is_being_edited = False
        
        if len(self.clip_data) == 0:
            self.add_clip()
        
        self.save_animation_clip_data()
    
    def table_cell_changed(self, row, col):
        if self.table_is_being_edited:
            return
        
        self.table_is_being_edited = True
        
        val = self.table_widget.item(row, col).text()
        
        if col > 0:
            try:
                val = str(int(float(val)))
            except ValueError:
                pm.warning('"%s" is not a valid number.' % val)
                val = '0.0'
        
        data = self.clip_data[row]
        data[col] = val
        self.clip_data[row] = data
        
        self.table_widget.setItem(row, col, QTableWidgetItem(val))
        self.table_is_being_edited = False
        
        self.save_animation_clip_data()
    
    def set_export_path(self):
        # resolve last file path
        if self.save_dir:
            path = self.save_dir
        else:
            path = pm.workspace(q=True, rd=True)
        
        if self.file_name:
            path = path + '/' + self.file_name
        
        # show dialog
        result = pm.fileDialog2(caption='Export FBX File',
                                dialogStyle=2,
                                fileMode=0,
                                fileFilter='FBX Export (*.fbx)',
                                okCaption='Export',
                                dir=path)
        
        if result is None:
            return False
        
        # set new export directory
        path = os.path.split(result[0])
        self.save_dir = path[0]
        self.file_name = path[1]
        
        self.save_file_option()
        
        return True
    
    def export(self):
        # where to save file?
        if not self.set_export_path():
            return
        
        # verify if anything is selected
        selection = pm.ls(sl=True)
        if not selection:
            pm.confirmDialog(title='No objects selected', message='Please select one or more object(s) to export.',
                             button=['OK'], defaultButton='OK')
            self.original_selection = None
            return
        
        self.original_selection = pm.ls(sl=True)
        
        time_range = self.get_time_range()
        
        if time_range is None:
            pm.error('Could not determine time range.')
            return
        
        try:
            cycle_check = pm.cycleCheck(q=True, evaluation=True)
            pm.cycleCheck(evaluation=False)
            
            # if "bake animation" is checked
            if self.bake_animation_checkbox.isChecked():
                self.bake(time_range)
            else:
                self.export_fbx(time_range)
            
            pm.cycleCheck(evaluation=cycle_check)
        except Exception as e:
            sys.stdout.write(str(e) + '\n')
    
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
                                           'it is done? This action cannot be undone!\n\n'
                                           'Baking also removes animation layers.',
                                   button=['Save and Bake Animation', 'Bake Without Saving', 'Cancel'],
                                   cancelButton='Cancel',
                                   dismissString='Cancel')
        
        if confirm == 'Cancel':
            return
        
        # save original file
        if confirm == 'Save and Bake Animation':
            original_file = pm.saveFile(force=True)
            qApp.processEvents()
        
        # disable viewport
        maya.mel.eval("paneLayout -e -manage false $gMainPane")
        
        # set playback range (appears that fbx uses it for the range when exporting)
        pm.playbackOptions(min=time_range[0], max=time_range[1])
        
        try:
            # bake keys
            self.custom_bake(time_range)
            self.remove_non_transform_curves()
        except Exception as e:
            sys.stdout.write(str(e) + '\n')
        
        try:
            self.export_fbx(time_range)
        except Exception as e:
            sys.stdout.write(str(e) + '\n')
        
        # enable viewport
        maya.mel.eval("paneLayout -e -manage true $gMainPane")
        
        # open original file
        if confirm == 'Save and Bake Animation':
            try:
                maya.utils.processIdleEvents()
                qApp.processEvents()
                confirmOpen = pm.confirmDialog(title='Open File',
                                               message='The FBX file was saved. The original file will now be opened.',
                                               button=['Open', 'Cancel'],
                                               defaultButton='Open', cancelButton='Cancel', dismissString='Cancel')
                
                if confirmOpen == 'Open':
                    pm.openFile(original_file, force=True)
            except Exception as e:
                sys.stdout.write(str(e) + '\n')
    
    def get_time_range(self):
        if self.animation_clip_checkbox.isChecked() and self.clip_data:
            s = []
            e = []
            for row in self.clip_data:
                s.append(int(row[1]))
                e.append(int(row[2]))
            s.sort()
            e.sort()
            return (s[0], e[-1])
        elif self.time_slider_radio.isChecked():
            return pm.playbackOptions(q=True, min=True), pm.playbackOptions(q=True, max=True)
        elif self.start_end_radio.isChecked():
            if self.start_input.text() == '' or self.end_input.text() == '':
                pm.warning('You need to set a start and end frame.')
                return None
            return sorted((int(float(self.start_input.text())), int(float(self.end_input.text()))))
        return None
    
    def custom_bake(self, time_range):
        stepped_limit = 0.0001
        
        # get objects to bake
        # baked_objects = list(self.original_selection)  # copy the list
        # joints = pm.listRelatives(self.original_selection, allDescendents=True, type='joint')
        # baked_objects.extend(pm.listRelatives(self.original_selection, allDescendents=True, type='transform'))
        
        # pm.select(baked_objects, r=True)
        
        # obj_list = om.MGlobal.getActiveSelectionList()
        # iterator = om.MItSelectionList(obj_list, om.MFn.kDagNode)
        try:
            to_bake = pm.ls(self.original_selection, type='transform')
            to_bake += pm.listRelatives(self.original_selection, allDescendents=True, type='transform')
            
            # create a set, and add all joints to the set
            filtered = set(pm.ls(self.original_selection, type='joint'))
            filtered |= set(pm.listRelatives(self.original_selection, allDescendents=True, type='joint'))  # union op.
        except Exception as e:
            sys.stdout.write("error 1: %s\n" % e)
        
        # add blendshapes and animated transforms to the set
        blendshapes = set()
        for node in to_bake:
            # blendshape?
            try:
                for shape in node.getShapes():
                    shape_inputs = shape.inputs()
                    # shape_inputs.extend(shape.attr('inMesh').inputs())  # maybe not needed
                    
                    # this should perhaps be rewritten as a recursive function,
                    # that keeps traversing down the hierarchy
                    for shape_input in shape_inputs:
                        if pm.nodeType(shape_input) == 'blendShape':
                            blendshapes.add(shape_input)
                        elif pm.nodeType(shape_input) in ('skinCluster', 'objectSet'):
                            for inp in shape_input.inputs():
                                if pm.nodeType(inp) == 'blendShape':
                                    blendshapes.add(inp)
            except Exception as e:
                pm.warning("Could not determine blendshape: %s" % e)
            
            # any inputs to transform attributes? i.e. any animation?
            for at in self.transform_attributes:
                if pm.hasAttr(node, at) and len(node.attr(at).inputs()) > 0:
                    filtered.add(node)
                    break
        
        to_bake = list(filtered.union(blendshapes))
        
        samples = 1
        has_stepped = self.has_stepped_checkbox.isChecked()
        if has_stepped:
            samples = 0.5
        
        maya.utils.processIdleEvents()
        qApp.processEvents()
        
        if len(to_bake) == 0:
            pm.select(self.original_selection, r=True)
            return
        
        # set key tangent to auto when baking
        itt = pm.keyTangent(q=True, g=True, itt=True)
        ott = pm.keyTangent(q=True, g=True, ott=True)
        pm.keyTangent(g=True, itt='auto', ott='auto')
        
        # bake selected transforms and children with half step
        pm.bakeResults(to_bake,
                       time=time_range,
                       sampleBy=samples,
                       hierarchy='none',
                       disableImplicitControl=True,
                       preserveOutsideKeys=False,
                       sparseAnimCurveBake=False,
                       simulation=True,
                       minimizeRotation=False,
                       removeBakedAnimFromLayer=True)
        
        # set key tangent back to default
        pm.keyTangent(g=True, itt=itt, ott=ott)
        
        pm.flushUndo()
        # maya.utils.processIdleEvents()
        # qApp.processEvents()
        
        # remove static channels to speed up analysis
        # to_bake.extend(joints)
        try:
            pm.select(to_bake, r=True)
            pm.delete(staticChannels=True)
        except Exception as e:
            sys.stdout.write(str(e) + '\n')
        
        muted_curves = []
        
        # progress bar
        try:
            gMainProgressBar = maya.mel.eval('$tmp = $gMainProgressBar')
            pm.progressBar(gMainProgressBar,
                           e=True,
                           beginProgress=True,
                           isInterruptable=True,
                           status='Working...',
                           maxValue=len(to_bake))
        except Exception as e:
            sys.stdout.write(str(e) + '\n')
        
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
            
            # update progress
            pm.progressBar(gMainProgressBar, e=True, step=1)
            if pm.progressBar(gMainProgressBar, q=True, isCancelled=True):
                break
        
        # end progressbar
        pm.progressBar(gMainProgressBar, e=True, endProgress=True)
        
        qApp.processEvents()
        
        pm.delete(muted_curves)
        
        # remove unsnapped keys
        if has_stepped:
            pm.selectKey(to_bake, unsnappedKeys=True)
            pm.cutKey(animation='keys', clear=True)
        
        # apply euler filter
        if self.euler_filter_checkbox.isChecked():
            self.apply_euler_filter(to_bake)
        
        pm.currentTime(time_range[0])
        
        # set a key on the first frame
        # todo: when doing stepped animation, all rotations needs to be either stepped or not, because of the way unity interpolates
        try:
            if has_stepped:
                tangent_type = 'step'
            else:
                tangent_type = 'auto'
            
            if to_bake:
                pm.setKeyframe(to_bake, attribute=self.transform_attributes, t=time_range[0], insertBlend=False,
                               ott=tangent_type)
            if blendshapes:
                pm.setKeyframe(blendshapes, t=time_range[0], insertBlend=False, ott=tangent_type)
        except Exception as e:
            sys.stdout.write(str(e) + '\n')
        
        # re-select original selection, so that we export the right thing
        pm.select(self.original_selection, r=True)
        
        # select all child constraints if enabled
        if self.constraints_checkbox.isChecked():
            constraints = pm.listRelatives(pm.ls(sl=True), allDescendents=True, type='constraint')
            pm.select(constraints, add=True)
    
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
        sys.stdout.write('# Preparing to write FBX file...\n')
        
        # maybe autokeyframe messes up something
        autoKeyState = bool(pm.autoKeyframe(q=True, state=True))
        pm.autoKeyframe(state=False)
        
        # set fbx options
        try:
            pm.mel.eval('FBXResetExport')  # reset any user preferences so we start clean
            pm.mel.eval('FBXExportAnimationOnly -v %d' % int(self.animation_only_checkbox.isChecked()))
            pm.mel.eval('FBXExportBakeComplexAnimation -v 0')
            pm.mel.eval('FBXExportBakeComplexStart -v %d' % time_range[0])
            pm.mel.eval('FBXExportBakeComplexEnd -v %d' % time_range[1])
            pm.mel.eval('FBXExportBakeResampleAnimation -v 0')
            pm.mel.eval('FBXExportCameras -v 1')
            pm.mel.eval('FBXExportConstraints -v %d' % int(self.constraints_checkbox.isChecked()))
            pm.mel.eval('FBXExportLights -v 1')
            pm.mel.eval('FBXExportQuaternion -v quaternion')
            pm.mel.eval('FBXExportAxisConversionMethod none')
            pm.mel.eval('FBXExportApplyConstantKeyReducer -v 0')
            pm.mel.eval('FBXExportSmoothMesh -v 0')  # do not export subdivision version
            pm.mel.eval('FBXExportShapes -v 1')  # needed for skins and blend shapes
            pm.mel.eval('FBXExportSkins -v 1')
            pm.mel.eval('FBXExportSkeletonDefinitions -v 1')
            pm.mel.eval('FBXExportEmbeddedTextures -v 0')
            pm.mel.eval('FBXExportInputConnections -v %d' % int(self.input_connections_checkbox.isChecked()))
            pm.mel.eval('FBXExportInstances -v 1')  # preserve instances by sharing same mesh
            pm.mel.eval('FBXExportUseSceneName -v 1')
            pm.mel.eval('FBXExportSplitAnimationIntoTakes -c')  # clear previous clips
            
            if self.animation_clip_checkbox.isChecked():
                for row in self.clip_data:
                    pm.mel.eval('FBXExportSplitAnimationIntoTakes -v \"%s\" %f %f' %
                                (str(row[0]), int(float(row[1])), int(float(row[2]))))
            
            pm.mel.eval('FBXExportGenerateLog -v 0')
            pm.mel.eval('FBXExportInAscii -v 0')
        except Exception as e:
            sys.stdout.write(str(e) + '\n')
        
        # save the fbx
        f = self.save_dir + '/' + self.file_name
        
        d = os.path.dirname(f)
        if not os.path.isdir(d):
            try:
                os.makedirs(d)
            except Exception as e:
                sys.stdout.write(str(e) + '\n')
                return
        
        # maya.utils.processIdleEvents()
        
        try:
            pm.mel.eval('FBXExport -f "%s" -s' % f)
        except Exception as e:
            sys.stdout.write(str(e) + '\n')
        
        maya.utils.processIdleEvents()
        
        sys.stdout.write('# Saved fbx to: %s\n' % f)
        pm.autoKeyframe(state=autoKeyState)
    
    def close_window(self):
        self.close()
    
    def save_file_option(self):
        pm.system.fileInfo['exportfbxtounity_save_dir'] = self.save_dir
        pm.system.fileInfo['exportfbxtounity_file_name'] = self.file_name
    
    def save_time_range_option(self):
        pm.system.fileInfo['exportfbxtounity_time_slider_radio'] = int(self.time_slider_radio.isChecked())
        pm.system.fileInfo['exportfbxtounity_start_end_radio'] = int(self.start_end_radio.isChecked())
        pm.system.fileInfo['exportfbxtounity_start'] = self.start_input.text()
        pm.system.fileInfo['exportfbxtounity_end'] = self.end_input.text()
    
    def save_input_connections_option(self):
        pm.system.fileInfo['exportfbxtounity_input_connections'] = int(self.input_connections_checkbox.isChecked())
    
    def save_constraints_option(self):
        pm.system.fileInfo['exportfbxtounity_constraints'] = int(self.constraints_checkbox.isChecked())
    
    def save_animation_only_option(self):
        pm.system.fileInfo['exportfbxtounity_animation_only'] = int(self.animation_only_checkbox.isChecked())
    
    def save_bake_animation_option(self):
        pm.system.fileInfo['exportfbxtounity_bake_animation'] = int(self.bake_animation_checkbox.isChecked())
    
    def save_euler_filter_option(self):
        pm.system.fileInfo['exportfbxtounity_euler_filter'] = int(self.euler_filter_checkbox.isChecked())
    
    def save_has_stepped_option(self):
        pm.system.fileInfo['exportfbxtounity_has_stepped'] = int(self.has_stepped_checkbox.isChecked())
    
    def save_animation_clip_option(self):
        pm.system.fileInfo['exportfbxtounity_animation_clip'] = int(self.animation_clip_checkbox.isChecked())
    
    def save_animation_clip_data(self):
        pm.system.fileInfo['exportfbxtounity_clips'] = json.dumps(self.clip_data)
    
    def load_options(self):
        # try to load export_dir from local file
        try:
            self.save_dir = pm.system.fileInfo['exportfbxtounity_save_dir']
        except (RuntimeError, KeyError):
            self.save_dir = None
        
        if self.save_dir is None:
            # try load "export_dir" from global settings instead
            try:
                self.save_dir = pm.optionVar['exportfbxtounity_save_dir']
            except (RuntimeError, KeyError):
                self.save_dir = None
        
        # try to load all other settings from file
        try:
            self.file_name = pm.system.fileInfo['exportfbxtounity_file_name']
        except (RuntimeError, KeyError):
            self.file_name = None
        
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
            self.start_input.setText(str(int(pm.playbackOptions(q=True, ast=True))))
        
        try:
            self.end_input.setText(pm.system.fileInfo['exportfbxtounity_end'])
        except (RuntimeError, KeyError):
            self.end_input.setText(str(int(pm.playbackOptions(q=True, aet=True))))
        
        try:
            self.input_connections_checkbox.setChecked(int(pm.system.fileInfo['exportfbxtounity_input_connections']))
        except (RuntimeError, KeyError):
            self.input_connections_checkbox.setChecked(False)
        
        try:
            self.constraints_checkbox.setChecked(int(pm.system.fileInfo['exportfbxtounity_constraints']))
        except (RuntimeError, KeyError):
            self.constraints_checkbox.setChecked(False)
        
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
    
    def load_clips(self):
        self.clip_data = self.clip_data = self.clip_data = [
            ["Take 001", pm.playbackOptions(q=True, min=True), pm.playbackOptions(q=True, max=True)]]
        try:
            read_clips = pm.system.fileInfo['exportfbxtounity_clips']
            if read_clips:
                read_clips = read_clips.replace('\\"', '"')
                self.clip_data = json.loads(read_clips)
        except (RuntimeError, KeyError, ValueError):
            pass
        
        self.table_is_being_edited = True
        self.table_widget.clearContents()
        self.table_widget.setRowCount(0)
        
        for i, row_data in enumerate(self.clip_data):
            self.table_widget.insertRow(i)
            self.table_widget.setItem(i, 0, QTableWidgetItem(row_data[0]))
            self.table_widget.setItem(i, 1, QTableWidgetItem(str(int(float(row_data[1])))))
            self.table_widget.setItem(i, 2, QTableWidgetItem(str(int(float(row_data[2])))))
        
        self.table_is_being_edited = False


def apply_dpi_scaling(value):
    if hasattr(cmds, 'mayaDpiSetting'):
        scale = cmds.mayaDpiSetting(q=True, realScaleValue=True)
        return int(scale * value)
    else:
        return int(value)
