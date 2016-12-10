# -----------------------------------------------------------------------------
# amHotkeys.py
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
# Custom Python module for easily assigning hotkeys in Maya.
#


import maya.cmds as cmds
from functools import partial


class amHotkeys():
    def __init__(self):
        # UI elements
        self.window = "amHotkeys_window"
        self.scrollList = "amHotkeys_scrollList"
        self.keyField = "amHotkeys_keyField"
        self.buttonAssign = "amHotkeys_buttonAssign"
        self.radioPress = "amHotkeys_radioPress"
        self.radioRelease = "amHotkeys_radioRelease"
        self.checkCtrl = "amHotkeys_checkCtrl"
        self.checkCmd = "amHotkeys_checkCmd"
        self.checkAlt = "amHotkeys_checkAlt"
        self.checkShift = "amHotkeys_checkShift"

        # Internal values
        self.commandName = None
        self.key = None
        self.modCtrl = False
        self.modCmd = False
        self.modAlt = False
        self.modShift = False
        self.press = True
        self.release = False
        self.assignedHotkey = None
        self.dictCommands = {}

    @staticmethod
    def _editableSet():
        """
        :return: True or False depending on the current set is editable (not default).
        """

        # Maya versions prior to 2016 does not support hotkey sets
        if int(cmds.about(version=True)) < 2016:
            return True

        # If the set exists, change to it, otherwise create a new
        if cmds.hotkeySet(q=True, current=True) == "Maya_Default":
            cmds.confirmDialog(title="Default Hotkey Set",
                               message="Hotkeys cannot be assigned to the default hotkey set.\n\n"
                                       "Please choose a different in Window > Settings / Preferences "
                                       "> Hotkey Editor.",
                               button=["OK"],
                               defaultButton="OK"
                               )
            return False

        return True

    def _assign(self):

        #   Up, Down, Right, Left,
        #   Home, End, Page_Up, Page_Down, Insert
        #   Return, Space
        #   F1 to F12
        #   Tab (Will only work when modifiers are specified)
        #   Delete, Backspace (Will only work when modifiers are specified)

        annotation = self.dictCommands[self.commandName]["annotation"]
        command = self.dictCommands[self.commandName]["command"]
        sourceType = self.dictCommands[self.commandName]["type"]

        # Setup name command
        cmds.nameCommand(self.commandName,
                         annotation=annotation,
                         command=command,
                         sourceType=sourceType,
                         )

        # Lower case single characters
        if len(self.key) == 1:
                self.key = self.key.lower()

        # Assign hotkey to the name command
        if self.press:
            # Check if it already exists
            current = cmds.hotkey(self.key, q=True,
                                  name=True,
                                  alt=self.modAlt,
                                  cmd=self.modCmd,
                                  ctl=self.modCtrl,
                                  sht=self.modShift)

            if current:
                confirm = cmds.confirmDialog(title="Overwrite Hotkey",
                                             message="The hotkey is already assigned to %s.\n\n"
                                                     "Would you like to overwrite it?" % current,
                                             button=["Yes", "No"],
                                             defaultButton="Yes",
                                             cancelButton="No",
                                             dismissString="No"
                                             )

                if confirm == "No":
                    return

            # Assign hotkey
            cmds.hotkey(name=self.commandName,
                        k=self.key,
                        alt=self.modAlt,
                        cmd=self.modCmd,
                        ctl=self.modCtrl,
                        sht=self.modShift,
                        )

        elif self.release:
            # Check if it already exists
            current = cmds.hotkey(self.key, q=True,
                                  releaseName=True,
                                  alt=self.modAlt,
                                  cmd=self.modCmd,
                                  ctl=self.modCtrl,
                                  sht=self.modShift)

            if current:
                confirm = cmds.confirmDialog(title="Overwrite Hotkey",
                                             message="The hotkey is already assigned to %s.\n\n"
                                                     "Would you like to overwrite it?" % current,
                                             button=["Yes", "No"],
                                             defaultButton="Yes",
                                             cancelButton="No",
                                             dismissString="No"
                                             )

                if confirm == "No":
                    return

            # Assign hotkey
            cmds.hotkey(releaseName=self.commandName,
                        k=self.key.lower(),
                        alt=self.modAlt,
                        cmd=self.modCmd,
                        ctl=self.modCtrl,
                        sht=self.modShift,
                        )

        return True

    @staticmethod
    def _delete():
        pass

    def _scrollListSelection(self):
        self.commandName = cmds.textScrollList(self.scrollList, q=True, selectUniqueTagItem=True)[0]
        self._resetInput()
        self._showCurrentHotkey()

    def _keyValidate(self, text=None):

        if text is None:
            self.key = None
            return

        if len(text) == 0:
            # Neutral color
            cmds.textField(self.keyField, e=True, bgc=[0.169, 0.169, 0.169], ebg=False)
            self.key = None
            return

        specialKeys = ["Up", "Down", "Right", "Left", "Home", "End", "Page_Up", "Page_Down", "Insert", "Return",
                       "Space",
                       "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"]

        modSpecialKeys = ["Tab", "Delete", "Backspace"]

        # Validate
        valid = False

        if len(text) == 1:
            valid = True
            text = text.lower()
        if text in specialKeys:
            valid = True
        elif text in modSpecialKeys:
            valid = True

        if valid:
            # Green
            cmds.textField(self.keyField, e=True, bgc=[0.463, 0.729, 0.631], ebg=False)
            self.key = text
        else:
            # Neutral
            cmds.textField(self.keyField, e=True, bgc=[0.169, 0.169, 0.169], ebg=False)
            self.key = None

        self._validHotkeyCombo()

    def _modifierChange(self, modifier, value):
        if modifier == "Ctrl":
            self.modCtrl = value
        elif modifier == "Cmd":
            self.modCmd = value
        elif modifier == "Alt":
            self.modAlt = value
        elif modifier == "Shift":
            self.modShift = value

        # validate key after change
        self._validHotkeyCombo()

    def _pressReleaseChange(self, state, *args):
        if state == "Press":
            self.press = True
            self.release = False
        else:
            self.press = False
            self.release = True

    def _validHotkeyCombo(self):
        # Can we assign this key combination?
        enable = False

        modSpecialKeys = ["Tab", "Delete", "Backspace"]

        # Only 3 modifiers can be used at a time
        if self.modCtrl + self.modCmd + self.modAlt + self.modShift >= 3:
            if not self.modCtrl:
                cmds.checkBox(self.checkCtrl, e=True, enable=False)
            elif not self.modCmd:
                cmds.checkBox(self.checkCmd, e=True, enable=False)
            elif not self.modAlt:
                cmds.checkBox(self.checkAlt, e=True, enable=False)
            elif not self.modShift:
                cmds.checkBox(self.checkShift, e=True, enable=False)
        else:
            cmds.checkBox(self.checkCtrl, e=True, enable=True)
            cmds.checkBox(self.checkCmd, e=True, enable=True)
            cmds.checkBox(self.checkAlt, e=True, enable=True)
            cmds.checkBox(self.checkShift, e=True, enable=True)

        if self.key in modSpecialKeys:
            if self.modAlt or self.modCtrl or self.modCmd or self.modShift:
                enable = True
            else:
                enable = False

        elif self.key:
            enable = True

        print(self.key)

        cmds.button(self.buttonAssign, e=True, enable=enable)

    def _getHotkey(self):
        keySet = {"key":   [],
                  "ctrl":  [],
                  "cmd":   [],
                  "alt":   [],
                  "shift": [],
                  "release": [],
                  "index": [],
                  }

        # First figure out which buttons the command is assigned to
        count = cmds.assignCommand(query=True, numElements=True)

        for index in xrange(count + 1, 1, -1):
            # If the command matches the name of our command name
            name = cmds.assignCommand(index, query=True, name=True)
            if name == self.commandName:
                keyString = cmds.assignCommand(index, query=True, keyString=True)

                key = keyString[0]
                if key == "NONE":
                    key = None

                # Determine if it has only is a assigned a key without modifier
                onlyKey = False

                specialKeys = {"Up":     "Up",
                               "Down":   "Down",
                               "Right":  "Right",
                               "Left":   "Left",
                               "Home":   "Home",
                               "End":    "End",
                               "PgUp":   "Page_Up",
                               "PgDown": "Page_Down",
                               "Ins":    "Insert",
                               "Return": "Return",
                               "Space":  "Space",
                               "F1":     "F1",
                               "F2":     "F2",
                               "F3":     "F3",
                               "F4":     "F4",
                               "F5":     "F5",
                               "F6":     "F6",
                               "F7":     "F7",
                               "F8":     "F8",
                               "F9":     "F9",
                               "F10":    "F10",
                               "F11":    "F11",
                               "F12":    "F12"}

                modSpecialKeys = {"Tab":       "Tab",
                                  "Delete":    "Del",
                                  "Backspace": "Backspace"}

                # Validate
                if len(key) == 1:
                    onlyKey = True
                    key = key.lower()

                # Translate assignCommand to hotkey
                if key in specialKeys:
                    key = specialKeys[key]
                elif key in modSpecialKeys:
                    key = modSpecialKeys[key]

                # Append the key to the list
                keySet["key"].append(key)

                # The documented way of determining modifiers
                keySet["ctrl"].append(bool(int(keyString[2])))
                keySet["cmd"].append(bool(int(keyString[4])))
                keySet["alt"].append(bool(int(keyString[1])))
                keySet["shift"].append(bool(int(keyString[5])))
                keySet["release"].append(bool(int(keyString[3])))

                if not onlyKey:
                    # BEGINNING OF HORRIBLE REQUIRED HACK
                    # The actual way (at least in Maya 2016 SP4, and apparently also 2015 SP6)
                    keyResult = keyString[0]
                    # If not Windows system
                    if not cmds.about(windows=True) or not cmds.about(ntOS=True) or not cmds.about(win64=True):
                        if "Meta+" in keyResult:
                            keyResult.replace("Meta+", "")
                            keySet["ctrl"].pop()
                            keySet["ctrl"].append(True)

                    # For all systems
                    if "Ctrl+" in keyResult:
                        keyResult.replace("Ctrl+", "")
                        # If Windows system
                        if cmds.about(windows=True) or cmds.about(ntOS=True) or cmds.about(win64=True):
                            keySet["ctrl"].pop()
                            keySet["ctrl"].append(True)
                        else:
                            keySet["cmd"].pop()
                            keySet["cmd"].append(True)
                    if "Alt+" in keyResult:
                        keyResult.replace("Alt+", "")
                        keySet["alt"].pop()
                        keySet["alt"].append(True)
                    if "Shift+" in keyResult:
                        keyResult.replace("Shift+", "")
                        keySet["shift"].pop()
                        keySet["shift"].append(True)
                    # END OF HORRIBLE REQUIRED HACK

                keySet["index"].append(index)

        if keySet["index"]:
            return keySet
        else:
            return False

    def _resetInput(self):
        cmds.textField(self.keyField, e=True, text="")
        cmds.radioButton(self.radioPress, e=True, select=True)
        cmds.radioButton(self.radioRelease, e=True, select=False)
        cmds.checkBox(self.checkCtrl, e=True, value=False)
        cmds.checkBox(self.checkCmd, e=True, value=False)
        cmds.checkBox(self.checkAlt, e=True, value=False)
        cmds.checkBox(self.checkShift, e=True, value=False)

        self.key = ""
        self.modCtrl = False
        self.modCmd = False
        self.modAlt = False
        self.modShift = False
        self.press = True
        self.release = False

        self._validHotkeyCombo()

    def _showCurrentHotkey(self):
        # Show hotkey settings for selected command if it has any
        keySet = self._getHotkey()

        if not keySet:
            return

        cmds.textField(self.keyField, e=True, text=keySet["key"][0])
        cmds.checkBox(self.checkCtrl, e=True, value=keySet["ctrl"][0])
        cmds.checkBox(self.checkCmd, e=True, value=keySet["cmd"][0])
        cmds.checkBox(self.checkAlt, e=True, value=keySet["alt"][0])
        cmds.checkBox(self.checkShift, e=True, value=keySet["shift"][0])

        if keySet["release"][0]:
            cmds.radioButton(self.radioRelease, e=True, select=True)
            cmds.radioButton(self.radioPress, e=True, select=False)
        else:
            cmds.radioButton(self.radioRelease, e=True, select=False)
            cmds.radioButton(self.radioPress, e=True, select=True)

    def _assignButton(self, *args):
        # Make sure to unassign it first
        # self._unassignButton()

        if not self._assign():
            cmds.error("The hotkey was not assigned properly :/")

    def _unassignButton(self, *args):
        keySet = self._getHotkey()

        if not keySet:
            return

        # Unassign all returned name commands
        count = len(keySet["index"])
        for i in range(0, count):
            # Unset the hotkey for both lower and uppercase

            # Need to validate that we actually have a key to prevent Maya crashing,
            # because we may have a namecommand without a key assigned.
            if keySet["key"][i]:
                cmds.hotkey(k=keySet["key"][i],
                            ctl=keySet["ctrl"][i],
                            cmd=keySet["cmd"][i],
                            alt=keySet["alt"][i],
                            sht=keySet["shift"][i],
                            name="",
                            releaseName="")

            # And remove the namecommand
            cmds.assignCommand(e=True, index=True, delete=keySet["index"][i])

    def _closeButton(self, *args):
        if cmds.window(self.window, exists=True):
            cmds.deleteUI(self.window)

    def dialog(self, dictCommands):
        """
        Window for assigning hotkeys from a dictionary of commands to a specified hotkey set.

        :param dictCommands:    Dictionary (preferably OrderedDict) of commands with nice name and annotation
                                in the format:

                                dictCommands = OrderedDict()
                                dictCommands["myCommandName"] = {{"command": 'python("myFunction()")',
                                                                  "annotation": "My Annotation",
                                                                  "type": "python"}
        """

        self.dictCommands = dictCommands

        # Check that the current hotkey set can be used
        if self._editableSet():
            # Delete existing window to prevent duplicates
            if cmds.window(self.window, exists=True):
                cmds.deleteUI(self.window)

            # Window definition
            window = cmds.window(self.window, title="Hotkey Manager", sizeable=True)

            buttonWidth = 80
            baseHeight = 23

            # Form definition (layout container)
            form = cmds.formLayout(numberOfDivisions=100)

            # Scroll list container
            scrollLabel = cmds.text(label="Commands", align="left", height=baseHeight, font="boldLabelFont", width=225)
            scrollList = cmds.textScrollList(self.scrollList,
                                             allowMultiSelection=False,
                                             selectCommand=self._scrollListSelection,
                                             width=225)

            # Add commands to scroll list
            for key, value in self.dictCommands.items():
                cmds.textScrollList(scrollList, e=True,
                                    append=value["annotation"],
                                    uniqueTag=key)

            # Select first scroll list item
            cmds.textScrollList(scrollList, e=True, selectIndexedItem=1)
            self.commandName = cmds.textScrollList(self.scrollList, q=True, selectUniqueTagItem=True)[0]

            cmds.setParent("|")

            # Hotkey layout
            hotkeyLayout = cmds.rowColumnLayout(numberOfColumns=2, columnAttach=([1, "left", 16], [2, "left", 16]))

            # Key assignment area (left hotkey layout)
            hotkeyLayoutLeft = cmds.rowColumnLayout(numberOfColumns=1)

            # Hotkey header
            cmds.rowColumnLayout(numberOfColumns=1, columnAttach=([1, "left", 0]))
            cmds.text(label="Hotkey", align="left", font="boldLabelFont", height=baseHeight)
            cmds.setParent(hotkeyLayoutLeft)

            # Row 1: Key
            cmds.rowColumnLayout(numberOfColumns=1, columnAttach=([1, "left", 0]), rowOffset=[1, "bottom", 8])
            cmds.textField(self.keyField, width=124, height=baseHeight, textChangedCommand=self._keyValidate,
                           font="boldLabelFont")
            cmds.setParent(hotkeyLayoutLeft)

            # Row 2: Press/Release
            cmds.rowColumnLayout(numberOfColumns=2, columnAttach=([1, "left", 0], [2, "left", 4]),
                                 rowOffset=[1, "bottom", 8])
            cmds.radioCollection()
            cmds.radioButton(self.radioPress,
                             label="Press",
                             width=60,
                             height=baseHeight,
                             onCommand=partial(self._pressReleaseChange, "Press"),
                             select=True)
            cmds.radioButton(self.radioRelease,
                             label="Release",
                             width=60,
                             height=baseHeight,
                             onCommand=partial(self._pressReleaseChange, "Release"))
            cmds.setParent(hotkeyLayoutLeft)

            # Row 3: Modifiers label
            cmds.rowColumnLayout(numberOfColumns=1, rowOffset=[1, "bottom", 0])
            cmds.text(label="Modifiers", height=baseHeight, width=124, font="boldLabelFont", align="left")
            cmds.setParent(hotkeyLayoutLeft)

            # Row 4: Ctrl, Cmd checkbox
            cmds.rowColumnLayout(numberOfColumns=2, columnAttach=([1, "left", 0], [2, "left", 4]),
                                 rowOffset=[1, "bottom", 0])
            cmds.checkBox(self.checkCtrl,
                          label="Ctrl",
                          width=60,
                          height=baseHeight,
                          changeCommand=partial(self._modifierChange, "Ctrl"))
            cmds.checkBox(self.checkCmd,
                          label="Cmd",
                          width=60,
                          height=baseHeight,
                          changeCommand=partial(self._modifierChange, "Cmd"))
            cmds.setParent(hotkeyLayoutLeft)

            # Row 5: Alt, Shift checkbox
            cmds.rowColumnLayout(numberOfColumns=2, columnAttach=([1, "left", 0], [2, "left", 4]),
                                 rowOffset=[1, "bottom", 8])
            cmds.checkBox(self.checkAlt,
                          label="Alt",
                          width=60,
                          height=baseHeight,
                          changeCommand=partial(self._modifierChange, "Alt"))
            cmds.checkBox(self.checkShift,
                          label="Shift",
                          width=60,
                          height=baseHeight,
                          changeCommand=partial(self._modifierChange, "Shift"))
            cmds.setParent(hotkeyLayout)

            # Hotkey info text layout (right side)
            cmds.rowColumnLayout(numberOfColumns=1, rowOffset=[1, "top", 23])
            cmds.text(label="Any single key or any of the following words:\n"
                            "'Up', 'Down', 'Right', 'Left', 'Home', 'End', 'Page_Up', 'Page_Down', "
                            "'Insert', 'Return', 'Space', or 'F1' to 'F12'.\n\n"
                            "'Tab', 'Delete' or 'Backspace' only work when modifiers are specified.\n\n"
                            "* Words are case sensitive, single letters are not.",
                      align="left", width=216, wordWrap=True)
            cmds.setParent("|")

            buttonLayout = cmds.rowColumnLayout(numberOfColumns=3,
                                                columnAttach=([1, "right", 2], [2, "right", 2], [3, "right", 0]),
                                                rowOffset=[1, "top", 4])
            cmds.button(self.buttonAssign, label="Assign", width=buttonWidth, height=baseHeight,
                        command=self._assignButton)
            cmds.button(label="Unassign", width=buttonWidth, height=baseHeight, command=self._unassignButton)
            cmds.button(label="Close", width=buttonWidth, height=baseHeight, command=self._closeButton)
            cmds.setParent("|")

            # Setup form layout
            cmds.formLayout(form, e=True,
                            attachForm=[
                                (scrollLabel, "top", 8),
                                (scrollLabel, "left", 8),
                                (scrollList, "left", 8),
                                (scrollList, "bottom", 8),

                                (hotkeyLayout, "top", 8),
                                (hotkeyLayout, "right", 8),

                                (buttonLayout, "bottom", 8),
                                (buttonLayout, "right", 8)
                            ],
                            attachControl=[
                                (scrollList, "top", 4, scrollLabel),
                                (scrollList, "right", 0, hotkeyLayout),
                            ])

            # Reset and validate input
            self._resetInput()

            # Show hotkey of first command if it has one
            self._showCurrentHotkey()

            # Show the window
            cmds.showWindow(window)
