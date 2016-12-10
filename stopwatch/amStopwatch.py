# -----------------------------------------------------------------------------
# amStopwatch.py
# -----------------------------------------------------------------------------

# Author: Morten Dalgaard Andersen
# Author URI: http://www.amorten.com
#
# License: Attribution-ShareAlike 4.0 International
# License URI: http://creativecommons.org/licenses/by-sa/4.0/
#
# Version: 1.0
# Modified: 2015-10-27
#
# -----------------------------------------------------------------------------
#
# Instructions on how to use:
#
#  1.	Copy the script to the Maya script folder.
#
#  2.	Enter the following two python commands to load the script:
#
#       import amStopwatch as amsw
#       amsw.amStopwatch()


import csv
import json
import timeit
from functools import partial
from os.path import basename, dirname, splitext
from collections import OrderedDict
import logging

import maya.cmds as cmds
from am.maya.amHotkeys import amHotkeys


class Stopwatch(object):
    """ Class for measuring time laps """

    def __init__(self):
        self.startTime = 0
        self.lapTime = 0
        self.deltaTime = 0
        self.addition = 0
        self.running = False
        self.isReset = True

    @staticmethod
    def sysTime():
        """ :return: float of system wall time """
        return timeit.default_timer()

    def start(self):
        self.running = True
        if self.isReset:
            self.isReset = False
            self.startTime = self.sysTime()

            if ui.playbackInMaya:
                self.setAddition(cmds.playbackOptions(q=True, minTime=True) / getSceneFPS())

            return int(0) + self.addition
        else:
            self.deltaTime += self.sysTime() - self.lapTime
            return self.lap()

    def lap(self):
        self.lapTime = self.sysTime()
        return self.lapTime - self.startTime - self.deltaTime + self.addition

    def stop(self):
        self.running = False
        if ui.playbackInMaya:
            playbackManager.stopFrame = cmds.currentTime(q=True)
            stopTime = playbackManager.stopFrame / getSceneFPS()
            self.lapTime += stopTime - (self.lapTime - self.startTime - self.deltaTime + self.addition)
            return stopTime
        else:
            return self.lap()

    def reset(self, clear=False):
        self.isReset = True
        self.running = False
        self.startTime = 0
        self.lapTime = 0
        self.deltaTime = 0
        self.addition = 0

        if clear:
            table.clear()
            ui.reload()
        return int(0)

    def getRunning(self):
        return self.running

    def getLastLap(self):
        return self.lapTime - self.startTime - self.deltaTime + self.addition

    @staticmethod
    def getLeadingZeros(number, digits=2):
        result = ""

        if number < 10 and digits is None:
            result = "0" + str(number)

        else:
            z = len(str(number))
            while z < digits:
                result += "0"
                z += 1
            result += str(number)

        return result

    @staticmethod
    def getFrame(t):
        fps = getSceneFPS()
        return int(t * fps)

    def getTimecode(self, t):
        fps = getSceneFPS()

        ff = int((t % 1) * fps)
        ss = int(t) % 60
        mm = int(t / 60) % 60
        hh = int(t / 60 / 60) % 24

        ff = self.getLeadingZeros(ff, len(str(fps)))
        ss = self.getLeadingZeros(ss)
        mm = self.getLeadingZeros(mm)
        hh = self.getLeadingZeros(hh)

        if int(hh) > 0:
            timecode = "%s:%s:%s:%s" % (hh, mm, ss, ff)
        else:
            timecode = "%s:%s:%s" % (mm, ss, ff)

        return timecode

    @staticmethod
    def getTimeFromFrame(value):
        fps = getSceneFPS()
        return float(value / fps)

    def setAddition(self, t=None):
        if t:
            self.addition = t
        else:
            rows = cmds.scriptTable(ui.table, q=True, rows=True) - 1
            if rows > 0:
                self.addition = float(cmds.scriptTable(ui.table, q=True, cellIndex=(rows, 3), cellValue=True)[0])


class Table(object):
    """ Class for manipulation of table data """

    def __init__(self):
        self.active = None
        self.tables = {}

    def new(self, *args):
        logging.info('table.new')
        # Add a new table to the dict and return the name
        index = 1
        name = "Table %s" % index

        while name in self.tables:
            index += 1
            name = "Table %s" % index

        # Add key, value in tables dictionary
        self.tables[name] = {"frames": [],
                             "laps": [],
                             "times": [],
                             "notes": []
                             }

        # Set new table as active
        self.active = name

        if cmds.window(ui.window, exists=True):
            stopwatch.reset()
            ui.buttonSwitch()
            ui.reload(name)

        return name

    def loadAttr(self):
        logging.info('table.loadAttr')
        # Get JSON data as dictionary from node
        self.active = cmds.getAttr(sceneData.node + ".active")
        self.tables = json.loads(cmds.getAttr(sceneData.node + ".tables"))

    def saveAttr(self):
        logging.info('table.saveAttr')
        # Read data from table and save in tables dict
        rows = cmds.scriptTable(ui.table, q=True, rows=True)
        frames = []
        times = []
        notes = []

        for row in range(1, rows):
            frame = cmds.scriptTable(ui.table, q=True,
                                     excludingHeaders=True,
                                     cellIndex=(row, 1),
                                     cellValue=True)
            t = cmds.scriptTable(ui.table, q=True,
                                 excludingHeaders=True,
                                 cellIndex=(row, 3),
                                 cellValue=True)
            note = cmds.scriptTable(ui.table, q=True,
                                    excludingHeaders=True,
                                    cellIndex=(row, 4),
                                    cellValue=True)
            frames.append(int(frame[0]))
            times.append(float(t[0]))
            notes.append(str(note[0]))

        if rows > 1:
            # cast to int list
            frames = [int(x) for x in frames]

            # sort frames, times and notes
            times, frames, notes = (list(l) for l in zip(*sorted(zip(times, frames, notes))))

        laps = self.getLaps(frames, rows)

        self.tables[self.active] = {"frames": frames,
                                    "laps": laps,
                                    "times": times,
                                    "notes": notes
                                    }

        sceneData.writeNode()

    def delete(self, name=None, *args):
        if not name:
            name = table.active

        # remove table from dict
        self.tables.pop(name)

        # if there are no more tables
        if len(self.tables) == 0:
            # Create a new
            name = self.new()
        else:
            # Find the first in the menu
            tables = []
            for key, value in self.tables.items():
                tables.append(key)

            tables.sort()
            name = tables[0]

        ui.reload(name)

    def deleteAll(self, *args):
        confirm = cmds.confirmDialog(title="Delete All Tables",
                                     message="Are you sure?",
                                     button=["Yes", "No"],
                                     defaultButton="Yes",
                                     cancelButton="No",
                                     dismissString="No"
                                     )

        if confirm == "No":
            return False

        self.tables.clear()
        self.new()
        sceneData.writeNode()
        ui.reload()

    def rename(self, name=None):
        oldName = table.active

        if name == oldName:
            return  # don't do anything if it's the same name

        if name in self.tables:
            confirm = cmds.confirmDialog(title="Overwrite Table?",
                                         message="Name is already in use, would you like to overwrite it?",
                                         button=["Yes", "No"],
                                         defaultButton="Yes",
                                         cancelButton="No",
                                         dismissString="No"
                                         )

            if confirm == "No":
                return False

        # return true to accept changes
        self.overwrite(oldName, name)
        ui.reload()
        return True

    def overwrite(self, oldName, newName):
        self.tables[newName] = self.tables.pop(oldName)
        self.active = newName
        sceneData.writeNode()

    def clear(self):
        # Clear table
        self.tables[self.active] = {"frames": [],
                                    "laps": [],
                                    "times": [],
                                    "notes": []
                                    }
        sceneData.writeNode()

    @staticmethod
    def getLaps(frames, rows):
        laps = [0]  # first lap is always 0

        for row in range(1, rows - 1):
            prevFrame = int(frames[row - 1])
            frame = int(frames[row])
            laps.append(frame - prevFrame)

        return laps

    def convertFrameRate(self, frameRate, *args):
        rows = cmds.scriptTable(ui.table, q=True, rows=True)

        if rows < 1:
            return

        index = 0
        for t in self.tables[self.active]["times"]:
            self.tables[self.active]["frames"][index] = int(round(float(t) * frameRate, 0))
            index += 1

        laps = self.getLaps(self.tables[self.active]["frames"], rows)
        self.tables[self.active]["laps"] = laps

        sceneData.writeNode()
        ui.reload()

    def applyOffset(self, positive=True, *args):
        # Return if there's no offset or no rows
        rows = cmds.scriptTable(ui.table, q=True, rows=True)
        if not rows:
            return

        offset = 1
        userOffset = cmds.textField(ui.tableOffset, q=True, text=True)

        if userOffset:
            try:
                int(userOffset)
            except ValueError:
                cmds.error("Offset must be a whole number.")
                return
            userOffset = abs(int(userOffset))
            offset = userOffset

        frameRate = float(getSceneFPS())
        offset /= frameRate

        if not positive:
            offset *= -1

        # Recalculate time and frame
        index = 0
        for t in self.tables[self.active]["times"]:
            t = float(t) + offset
            self.tables[self.active]["times"][index] = "%f" % t  # prevent scientific notation of float
            self.tables[self.active]["frames"][index] = int(round(t * frameRate, 0))
            index += 1

        # Set laps
        self.tables[self.active]["laps"] = self.getLaps(self.tables[self.active]["frames"], rows)

        # Set user offset to absolute values
        if userOffset:
            cmds.textField(ui.tableOffset, e=True, text=userOffset)

        # Write out and reload
        sceneData.writeNode()
        ui.reload()


class UI(object):
    """ Class for maintaining UI """

    def __init__(self):
        # Window
        self.window = "amsw_window"

        # Dynamic menus
        self.menu = "amsw_menu"
        self.menuFile = "amsw_menuFile"
        self.menuOptions = "amsw_menuOptions"
        self.menuTables = "amsw_menuTables"
        self.menuOptionsPlayBack = "amsw_menuOptionsPlayBack"
        self.menuOptionsUpdateViewport = "amsw_menuOptionsUpdateViewport"

        # Options
        self.playbackInMaya = False
        self.updateViewport = False

        # Dynamic buttons
        self.buttonA = "amsw_buttonA"
        self.buttonB = "amsw_buttonB"

        # Dynamic info text
        self.timecode = "amsw_timecode"
        self.frame = "amsw_frame"

        # Dynamic script table
        self.table = "amsw_table"
        self.tableName = "amsw_tableName"
        self.tableOffset = "amsw_tableOffset"

        # Script job
        self.scriptjob = None

    def createWindow(self):
        windowWidth = 400
        windowHeight = 500
        stdHeight = 20
        buttonWidth = 50
        buttonHeight = 23

        # Load options
        self.getOptionVar()

        # Window definition
        cmds.window(self.window,
                    title="amStopwatch",
                    sizeable=True,
                    width=windowWidth,
                    height=windowHeight)

        # Form definition (layout container)
        form = cmds.formLayout(numberOfDivisions=100)

        # Menu items
        cmds.menuBarLayout(self.menu, height=stdHeight, width=windowWidth)

        cmds.menu(self.menuFile, label="File")
        cmds.menuItem(label="Import Set...", command=fileManager.importFile)
        cmds.menuItem(label="Export Set...", command=fileManager.exportFile)
        cmds.menuItem(label="Export as csv...", command=fileManager.exportCSVFile)
        cmds.setParent(self.menuFile, menu=True)

        cmds.menu(self.menuOptions, label="Options")
        cmds.menuItem(self.menuOptionsPlayBack,
                      label="Playback in Maya",
                      checkBox=self.playbackInMaya,
                      command=self.setOptionPlayBack
                      )
        cmds.menuItem(self.menuOptionsUpdateViewport,
                      label="Update Viewport",
                      checkBox=self.updateViewport,
                      command=self.setOptionsUpdateViewport
                      )
        cmds.menuItem(label="Convert Frame Rate to...", subMenu=True)
        cmds.menuItem(label="Scene Frame Rate", command=partial(table.convertFrameRate, getSceneFPS()))
        cmds.menuItem(label="Custom Frame Rate", command=partial(self.customFrameRate))
        cmds.setParent("..", menu=True)
        cmds.menuItem(label="Hotkeys", command=self.hotkey)

        cmds.setParent("|")

        # Menu bar bottom border
        menuBorder = cmds.separator(style="none", h=1, w=200, bgc=[0.2, 0.2, 0.2])

        timerArea = cmds.rowLayout(numberOfColumns=5,
                                   adjustableColumn=4,
                                   columnAttach=[(1, "left", 0),
                                                 (2, "left", 8),
                                                 (3, "both", 0),
                                                 (4, "right", 0)],
                                   h=40,
                                   )

        # Title
        cmds.text(label="amStopwatch", align="left", font="boldLabelFont", h=stdHeight)

        # Start/Reset Buttons
        cmds.button(self.buttonA, label="Start", w=buttonWidth, h=buttonHeight, c=self.buttonStart)
        cmds.button(self.buttonB, label="Reset", w=buttonWidth, h=buttonHeight, c=self.buttonReset)

        # Time
        cmds.separator(visible=False)
        cmds.rowColumnLayout(numberOfColumns=1, columnAlign=[1, "right"], columnAttach=[1, "right", 0])
        cmds.text(self.timecode, label="", font="smallPlainLabelFont", recomputeSize=True)
        cmds.text(self.frame, label="", font="boldLabelFont", recomputeSize=True)

        cmds.setParent("|")

        # Table
        tableLabel = cmds.rowLayout(numberOfColumns=6,
                                    h=buttonHeight,
                                    adjustableColumn=1,
                                    columnAttach=[(1, "left", 0),
                                                  (2, "left", 4),
                                                  (3, "left", 2),
                                                  (4, "left", 4),
                                                  (5, "both", 2),
                                                  (6, "right", 0)],
                                    )
        cmds.textField(self.tableName,
                       h=buttonHeight,
                       text="",
                       changeCommand=table.rename
                       )
        cmds.button(label="New", w=buttonWidth, h=buttonHeight, command=table.new)
        cmds.button(label="Delete", w=buttonWidth, h=buttonHeight, command=table.delete)
        cmds.textField(self.tableOffset, w=buttonWidth, height=buttonHeight, placeholderText="Offset")
        cmds.button(label="<", w=buttonHeight, h=buttonHeight, command=partial(table.applyOffset, False))
        cmds.button(label=">", w=buttonHeight, h=buttonHeight, command=partial(table.applyOffset, True))

        cmds.setParent("|")

        # Time Chart script table
        cmds.scriptTable(self.table,
                         rows=1,
                         columns=4,
                         label=[(1, "Frame"), (2, "Lap"), (3, "Sec"), (4, "Note")],
                         columnWidth=[(1, 60), (2, 60), (3, 60), (4, 196)],
                         clearTable=True,
                         useDoubleClickEdit=True,
                         cellChangedCmd=self.tableChange,
                         afterCellChangedCmd=self.tableAfterChange,
                         rowsToBeRemovedCmd=self.tableRemoveRows
                         )

        # Edit form layout to desired, must be done after all elements are declared
        cmds.formLayout(form, e=True,
                        attachForm=[
                            (self.menu, "top", 0),
                            (self.menu, "left", 0),
                            (self.menu, "right", 0),

                            (menuBorder, "left", 0),
                            (menuBorder, "right", 0),

                            (timerArea, "left", 10),
                            (timerArea, "right", 10),

                            (tableLabel, "left", 10),
                            (tableLabel, "right", 10),

                            (self.table, "left", 0),
                            (self.table, "right", 0),
                            (self.table, "bottom", 0),
                        ],
                        attachControl=[
                            (menuBorder, "top", 0, self.menu),
                            (timerArea, "top", 10, menuBorder),
                            (tableLabel, "top", 20, timerArea),
                            (self.table, "top", 8, tableLabel),
                        ],
                        )

        # Load options
        self.setOptionVar()

        # Attach script job to window to automatically close window when a scene is closed
        self.scriptjob = cmds.scriptJob(event=["NewSceneOpened", sceneData.reboot], runOnce=True, parent=self.window)
        cmds.scriptJob(event=["PostSceneRead", partial(sceneData.reboot, False)], runOnce=True)

    def show(self):
        if cmds.window(self.window, exists=True):
            self.reload()
            cmds.showWindow(self.window)
        else:
            self.createWindow()
            self.show()

    def delete(self):  # redudant?
        if cmds.window(self.window, exists=True):
            cmds.deleteUI(self.window)

    def load(self, name=None, *args):
        logging.info('ui.load')
        if not name:
            name = table.active

        # Load data from the table object
        data = table.tables[name]

        # Important to clear selection
        ui.tableClearSelection()

        rows = int(len(data["frames"]))
        cmds.scriptTable(self.table, e=True, rows=rows)

        # Apply to script table
        self.tableAllowChanges(True)
        cmds.textField(self.tableName, e=True, text=name)

        for i in range(0, rows):
            cmds.scriptTable(self.table, e=True, cellIndex=(i+1, 1), cellValue=data["frames"][i])
            cmds.scriptTable(self.table, e=True, cellIndex=(i+1, 2), cellValue=data["laps"][i])
            cmds.scriptTable(self.table, e=True, cellIndex=(i+1, 3), cellValue=data["times"][i])
            cmds.scriptTable(self.table, e=True, cellIndex=(i+1, 4), cellValue=data["notes"][i])

        self.tableAllowChanges(False)

        table.active = str(name)
        sceneData.writeNode()

    def reload(self, name=None, *args):
        self.load(name)
        # if name:
        #     stopwatch.setAddition()
        self.refreshTablesMenu()
        if not stopwatch.getRunning():
            self.refreshDisplay(stopwatch.getLastLap())

    def loadNew(self, name, *args):
        table.saveAttr()
        stopwatch.reset()
        self.buttonSwitch()
        self.reload(name)

    def refreshTablesMenu(self):
        logging.info('ui.refreshTablesMenu')
        # Re-create tables menu
        cmds.setParent(ui.menu)
        if cmds.menu(self.menuTables, q=True, exists=True):
            cmds.deleteUI(self.menuTables, menu=True)
        cmds.menu(self.menuTables, label="Tables")

        tables = []
        for key, value in table.tables.items():
            tables.append(key)

        tables.sort()

        for item in tables:
            cmds.menuItem(label=item, subMenu=True)
            cmds.menuItem(label="Load", command=partial(self.loadNew, item))
            cmds.menuItem(label="Delete", command=partial(table.delete, item))
            cmds.setParent(self.menuTables, menu=True)

        # Delete all
        cmds.menuItem(label="Delete All", command=table.deleteAll)

        cmds.setParent("|")

    def refreshDisplay(self, t):
        logging.info('ui.refreshDisplay')
        frame = stopwatch.getFrame(t)
        timecode = stopwatch.getTimecode(t)

        frame = "%s frames" % frame
        fps = getSceneFPS()
        timecode = "%s @ %sfps" % (timecode, fps)

        cmds.text(self.frame, e=True, label=frame)
        cmds.text(self.timecode, e=True, label=timecode)

    def addRow(self, t, note=None):
        self.tableAllowChanges(True)

        rows = cmds.scriptTable(self.table, q=True, rows=True)

        frame = stopwatch.getFrame(t)
        round(t, 6)

        cmds.scriptTable(self.table, e=True, insertRow=rows)
        cmds.scriptTable(self.table, e=True, cellIndex=(rows, 1), cellValue=frame)
        cmds.scriptTable(self.table, e=True, cellIndex=(rows, 3), cellValue=t)
        cmds.scriptTable(self.table, e=True, cellIndex=(rows, 4), cellValue=note)

        self.tableAllowChanges(False)
        table.saveAttr()
        self.load()

    def tableAllowChanges(self, allow):
        # Allow or disallow changes to the script table in the UI
        if allow:
            # Change callback of cell changes to allow all changes to cells
            cmds.scriptTable(self.table, e=True, cellChangedCmd=self.tablePassChanges)
            cmds.scriptTable(self.table, e=True, afterCellChangedCmd="")
        else:
            # Change callback of cell changes to more limited
            cmds.scriptTable(self.table, e=True, cellChangedCmd=self.tableChange)
            cmds.scriptTable(self.table, e=True, afterCellChangedCmd=self.tableAfterChange)

    def tableChange(self, row, column, value):
        self.tableClearSelection()
        # Update changes to time chart if valid
        # Verify frame change is a float
        if column == 1:
            try:
                float(value)
            except ValueError:
                return False

        # Disallow editing of laps
        if column == 2 or column == 3:
            cmds.warning("Laps and seconds are read-only.")
            return False

        return True

    def tableAfterChange(self, row, column, value):
        if column == 1:
            try:
                float(value)
            except ValueError:
                return False

            # Calculate new time
            t = stopwatch.getTimeFromFrame(float(value))
            self.tableAllowChanges(True)
            cmds.scriptTable(self.table, e=True, cellIndex=(row, 3), cellValue=t)
            self.tableAllowChanges(False)

        table.saveAttr()
        ui.reload()
        return True

    @staticmethod
    def tablePassChanges(row, column, value):
        # Allow all changes (used when adding data to the UI table through script)
        return True

    @staticmethod
    def tableRemoveRows(rows):
        return True  # Remove selected rows

    def tableClearSelection(self):
        # Workaround for a bug in Maya where all edits are put in the
        # selected cells
        cmds.scriptTable(self.table, e=True, selectedCells=[1, 999])

    def buttonStart(self, *args):
        if self.playbackInMaya:
            if cmds.currentTime(q=True) == cmds.playbackOptions(q=True, maxTime=True):
                stopwatch.reset(True)
            playbackManager.play()

        # Save reset status for later...
        startNew = not bool(len(table.tables[table.active]["frames"]))

        t = stopwatch.start()
        self.refreshDisplay(t)
        self.buttonSwitch()

        if startNew:
            note = "Start @ %sfps" % getSceneFPS()
            self.addRow(t, note)

    def buttonLap(self, *args):
        t = stopwatch.lap()
        self.refreshDisplay(t)
        self.addRow(t)

    def buttonStop(self, *args):
        t = stopwatch.stop()
        self.refreshDisplay(t)
        self.buttonSwitch()
        self.addRow(t, "Stop")

        if self.playbackInMaya:
            playbackManager.stop()

    def buttonReset(self, *args):
        t = stopwatch.reset(True)
        self.refreshDisplay(t)

    def buttonSwitch(self):
        if stopwatch.getRunning():
            cmds.button(self.buttonA, e=True, label="Lap", c=self.buttonLap)
            cmds.button(self.buttonB, e=True, label="Stop", c=self.buttonStop)
        else:
            cmds.button(self.buttonA, e=True, label="Start", c=self.buttonStart)
            cmds.button(self.buttonB, e=True, label="Reset", c=self.buttonReset)

    def buttonHotkeyA(self):
        if cmds.window(self.window, exists=True):
            if stopwatch.getRunning():
                self.buttonLap()
            else:
                self.buttonStart()
        else:
            cmds.warning("amStopwatch must be open.")

    def buttonHotkeyB(self):
        if cmds.window(self.window, exists=True):
            if stopwatch.getRunning():
                self.buttonStop()
            else:
                self.buttonReset()
        else:
            cmds.warning("amStopwatch must be open.")

    def setOptionPlayBack(self, value):
        self.playbackInMaya = value
        self.setOptionVar()

    def setOptionsUpdateViewport(self, value):
        self.updateViewport = value
        self.setOptionVar()

    def getOptionVar(self):
        if cmds.optionVar(exists="amsw_playbackInMaya"):
            self.playbackInMaya = cmds.optionVar(q="amsw_playbackInMaya")
            self.updateViewport = cmds.optionVar(q="amsw_updateViewport")

    def setOptionVar(self):
        cmds.optionVar(iv=("amsw_playbackInMaya", self.playbackInMaya))
        cmds.optionVar(iv=("amsw_updateViewport", self.updateViewport))

    @staticmethod
    def customFrameRate(*args):
        result = cmds.promptDialog(title="Convert to Frame Rate",
                                   message="Enter frame rate",
                                   button=["Convert", "Cancel"],
                                   defaultButton="Convert",
                                   cancelButton="Cancel",
                                   dismissString="Cancel"
                                   )

        if result == "Convert":
            value = cmds.promptDialog(q=True, text=True)
            try:
                float(value)
            except ValueError:
                cmds.error("Frame rate must be a number.")
                return

            table.convertFrameRate(float(value))

    @staticmethod
    def hotkey(*args):
        dictCommands = OrderedDict()
        dictCommands["amStopwatchStartLap"] = {"command":    'python("amsw.ui.buttonHotkeyA()")',
                                               "annotation": "amStopwatch Start/Lap",
                                               "type":       "python"}
        dictCommands["amStopwatchStopReset"] = {"command":    'python("amsw.ui.buttonHotkeyB()")',
                                                "annotation": "amStopwatch Stop/Reset",
                                                "type":       "python"}

        hotkeyManager.dialog(dictCommands)


class SceneData(object):
    """ Class for maintaining data structure in node and file info """

    def __init__(self):
        self.node = None
        self.fileInfo = "amStopwatch"

    def read(self):
        self.node = cmds.fileInfo(self.fileInfo, q=True)

        if len(self.node) < 1:
            self.node = None
        else:
            self.node = self.node[0]

        if not self.node:
            self.make()  # make a new node
            table.new()  # make new content
            self.writeNode()  # write new content to node attr
            table.loadAttr()  # read content from node into dict
        elif not cmds.objExists(self.node):
            self.reboot()
        else:
            table.loadAttr()

    def make(self):
        # Create a new node for storing data
        self.node = cmds.createNode("transform", name="amStopwatch", skipSelect=True)
        cmds.fileInfo(self.fileInfo, self.node)

        # Add data attribute to our node
        cmds.addAttr(self.node,
                     longName="active",
                     dataType="string"
                     )
        cmds.addAttr(self.node,
                     longName="tables",
                     dataType="string"
                     )

    def writeNode(self):
        self.lock(False)
        cmds.setAttr(self.node + ".active", table.active, type="string")
        cmds.setAttr(self.node + ".tables", json.dumps(table.tables), type="string")
        self.lock(True)

    def clean(self):
        # remove node
        if self.node:
            if cmds.objExists(self.node):
                sceneData.lock(False)
                cmds.delete(self.node)

        # remove file info
        if cmds.fileInfo(self.fileInfo, q=True):
            cmds.fileInfo(remove=self.fileInfo)

        # re-instantiate variables
        stopwatch.__init__()
        table.__init__()
        ui.__init__()
        sceneData.__init__()

    def reboot(self, clean=True, *args):
        # Remove and re-create node and fileinfo
        if clean:
            self.clean()

        self.read()
        ui.delete()
        ui.show()

    def lock(self, lock):
        # Lock node and attributes to prevent accidental user changes
        if not lock:
            cmds.lockNode(self.node, lock=lock)

        cmds.setAttr(self.node + ".active", lock=lock)
        cmds.setAttr(self.node + ".tables", lock=lock)

        if lock:
            cmds.lockNode(self.node, lock=lock)


class PlaybackManager(object):
    """ Class for managing playback in Maya """

    def __init__(self):
        self.startFrame = None
        self.endFrame = None
        self.stopFrame = None
        self.eventPlaybackEnded = None

        # Settings saved for restoring playbackOptions
        self.playbackSpeed = None
        self.loop = None

    def play(self):
        self.startFrame = cmds.playbackOptions(q=True, minTime=True)
        self.endFrame = cmds.playbackOptions(q=True, maxTime=True)

        # Save user settings
        self.playbackSpeed = cmds.playbackOptions(q=True, playbackSpeed=True)
        self.loop = cmds.playbackOptions(q=True, loop=True)

        if not ui.updateViewport:
            cmds.refresh(suspend=True)

        startNew = not bool(len(table.tables[table.active]["frames"]))
        if startNew:
            cmds.currentTime(self.startFrame)
        else:
            cmds.currentTime(stopwatch.getFrame(table.tables[table.active]["times"][-1]))
            if self.startFrame > self.stopFrame:
                cmds.playbackOptions(minTime=self.stopFrame)

        cmds.playbackOptions(playbackSpeed=1, loop="once")
        cmds.play(forward=True, state=True)

        # Setup scriptjob to know when it has ended
        self.eventPlaybackEnded = cmds.scriptJob(cf=["playingBack", partial(ui.buttonStop)], runOnce=True)

    def stop(self):
        cmds.play(state=False)

        # Kill scriptjob to make sure only one exists
        if self.eventPlaybackEnded:
            if cmds.scriptJob(exists=self.eventPlaybackEnded):
                cmds.scriptJob(kill=self.eventPlaybackEnded)

        # Restore scene
        cmds.refresh(suspend=False)


class FileManager(object):
    """ Class with functions for importing and exporting files """

    @staticmethod
    def fileDialog(title, action="Open", ext="amsw"):
        directory = cmds.workspace(q=True, dir=True)
        fileFilter = ".%s (*.%s)" % (ext, ext)

        if action == "Open":
            fileMode = 1
        elif action == "Save":
            fileMode = 0
        else:
            return None

        filePath = cmds.fileDialog2(caption=title,
                                    dialogStyle=2,
                                    dir=directory,
                                    fileMode=fileMode,
                                    fileFilter=fileFilter,
                                    okCaption=action
                                    )

        if not filePath:
            return

        # Remove any ext and add our ext
        if action == "Save":
            dirName = dirname(filePath[0])
            fileNameExt = splitext(basename(filePath[0]))
            fileName = fileNameExt[0]
            if fileNameExt[1] != "." + ext:
                fileName += fileNameExt[1]
            fullPath = "%s/%s.%s" % (dirName, fileName, ext)

            return fullPath
        else:
            return filePath[0]

    @staticmethod
    def importFile(*args):
        filePath = fileManager.fileDialog("Import File", "Open", "amsw")

        if not filePath:
            cmds.warning("No file specified.")
            return

        contents = open(filePath, "r")
        data = json.loads(contents.read())

        for key, value in data.items():
            if key in table.tables:
                while key in table.tables:
                    key += " (conflict)"

            table.tables[key] = {"frames": [],
                                 "laps":   [],
                                 "times":  [],
                                 "notes":  []
                                 }

            frames = [int(x) for x in value["frames"]]
            laps = [int(x) for x in value["laps"]]
            times = [float(x) for x in value["times"]]

            table.tables[key]["frames"] = frames
            table.tables[key]["laps"] = laps
            table.tables[key]["times"] = times
            table.tables[key]["notes"] = value["notes"]

        sceneData.writeNode()
        ui.reload()

        print("// Import successful!")

    @staticmethod
    def exportFile(*args):
        filePath = fileManager.fileDialog("Export File", "Save", "amsw")
        if not filePath:
            cmds.warning("No file specified.")
            return

        exportFile = open(filePath, "w")
        contents = json.dumps(table.tables)
        exportFile.write(contents)
        exportFile.close()

        print("// Exported file at %s successfully!" % filePath)

    @staticmethod
    def exportCSVFile(*args):
        filePath = fileManager.fileDialog("Export as CSV File", "Save", "csv")

        if not filePath:
            cmds.warning("No file specified.")
            return

        exportFile = open(filePath, "w")
        writer = csv.writer(exportFile, delimiter=";", quotechar='"', quoting=csv.QUOTE_NONNUMERIC)

        heading = ["Frame", "Lap", "Sec", "Notes"]
        writer.writerow(heading)

        frames = [int(x) for x in table.tables[table.active]["frames"]]
        laps = [int(x) for x in table.tables[table.active]["laps"]]
        times = [float(x) for x in table.tables[table.active]["times"]]
        notes = table.tables[table.active]["notes"]

        for i in range(0, len(frames)):
            row = [frames[i], laps[i], times[i], notes[i]]
            writer.writerow(row)

        exportFile.close()
        print("// Exported file at %s successfully!" % filePath)


def getSceneFPS():
    """
    :return: int or float of Maya's current frame setting
    """
    fpsUnit = cmds.currentUnit(q=True, time=True)
    fps = 1

    if fpsUnit == "game":
        fps = 15
    elif fpsUnit == "film":
        fps = 24
    elif fpsUnit == "pal":
        fps = 25
    elif fpsUnit == "ntsc":
        fps = 30
    elif fpsUnit == "show":
        fps = 48
    elif fpsUnit == "palf":
        fps = 50
    elif fpsUnit == "ntscf":
        fps = 60
    elif fpsUnit == "millisec":
        fps = 100
    elif fpsUnit == "sec":
        fps = 1
    elif fpsUnit == "min":
        fps = 1 / 60
    elif fpsUnit == "hour":
        fps = 1 / 60 / 60
    elif fpsUnit == "2fps":
        fps = 2
    elif fpsUnit == "3fps":
        fps = 3
    elif fpsUnit == "4fps":
        fps = 4
    elif fpsUnit == "5fps":
        fps = 5
    elif fpsUnit == "6fps":
        fps = 6
    elif fpsUnit == "8fps":
        fps = 8
    elif fpsUnit == "10fps":
        fps = 10
    elif fpsUnit == "12fps":
        fps = 12
    elif fpsUnit == "16fps":
        fps = 16
    elif fpsUnit == "20fps":
        fps = 20
    elif fpsUnit == "40fps":
        fps = 40
    elif fpsUnit == "75fps":
        fps = 75
    elif fpsUnit == "80fps":
        fps = 80
    elif fpsUnit == "100fps":
        fps = 100
    elif fpsUnit == "125fps":
        fps = 125
    elif fpsUnit == "150fps":
        fps = 150
    elif fpsUnit == "200fps":
        fps = 200
    elif fpsUnit == "240fps":
        fps = 240
    elif fpsUnit == "250fps":
        fps = 250
    elif fpsUnit == "300fps":
        fps = 300
    elif fpsUnit == "375fps":
        fps = 375
    elif fpsUnit == "400fps":
        fps = 400
    elif fpsUnit == "500fps":
        fps = 500
    elif fpsUnit == "600fps":
        fps = 600
    elif fpsUnit == "750fps":
        fps = 750
    elif fpsUnit == "1200fps":
        fps = 1200
    elif fpsUnit == "1500fps":
        fps = 1500
    elif fpsUnit == "2000fps":
        fps = 2000
    elif fpsUnit == "3000fps":
        fps = 3000
    elif fpsUnit == "6000fps":
        fps = 600

    if fps == 1:
        cmds.warning("The scenes frame-rate was not read properly.")

    return fps


# Instantiate classes
stopwatch = Stopwatch()
table = Table()
ui = UI()
sceneData = SceneData()
playbackManager = PlaybackManager()
fileManager = FileManager()
hotkeyManager = amHotkeys()


def amStopwatch():
    # Read or create new node to ensure we have something to work with
    sceneData.read()

    # Show the UI
    ui.show()

    # Setup logging
    logging.basicConfig(filename='/Users/Morten/Desktop/amstopwatch.log', level=logging.DEBUG)
