'''
Playblast using filename and H.264 compression

Default regex replacement pattern is: (?!\/)(.*?)_?([0-9]+)_(.*?)_
'''

# OPTIONS
resolution = [1920,1080] # playblast resolution
modFileName = True # do a regex search to replace filename, see example below


import maya.mel
import pymel.core as pm
import maya.OpenMaya as OpenMaya
import maya.OpenMayaUI as OpenMayaUI
import re
import os


 # default paths
filename = os.path.splitext(os.path.basename(pm.system.sceneName()))[0]
movieDir = pm.workspace.fileRules['movie'] + "/"
movieDir.replace('\\', '/')

if modFileName:
    # Regex example:
    # Filename in the format "/my/path/sh_0010_ANI_workshop_0010.ma"
    # is converted to "sh0010_ANI"
    pattern = re.compile('(?!\/)(.*?)_?([0-9]+)_(.*?)_')
    match = re.match(pattern, filename)
    filename = match.group(1) + match.group(2)


# get camera name
view = OpenMayaUI.M3dView.active3dView()
camPath = OpenMaya.MDagPath()
view.getCamera(camPath)  # returns camera shape node
camShapeName = camPath.partialPathName()

cam = camPath.transform()  # returns MObject
OpenMaya.MDagPath.getAPathTo(cam, camPath)
camName = camPath.partialPathName()


# prompt for postfix
message = "Playblast camera:\n" + camName + "\n\nOutput name:\n" + filename + "\n\nFilename postfix (optional):"

postfix = ""
try:
    postfix = pm.system.fileInfo['playblastPostfix']
except:
    pass

result = pm.promptDialog(title="Playblast", message=message, button=["Playblast","Cancel"], defaultButton="Playblast", cancelButton="Cancel", dismissString="Cancel", text=postfix)


if result == "Playblast":
    postfix = pm.promptDialog(q=True, text=True)
    pm.system.fileInfo['playblastPostfix'] = postfix

    # get active sound in time slider
    aPlayBackSliderPython = maya.mel.eval('$tmpVar=$gPlayBackSlider')
    sound = pm.timeControl(aPlayBackSliderPython, q=True, sound=True)


    # assemble full path and filename
    filename = movieDir + filename + postfix + ".mov"

    # disable resolution gate
    resGateEnabled = pm.getAttr(camShapeName + ".displayResolution")
    overscan = pm.getAttr(camShapeName + ".overscan")
    pm.setAttr(camShapeName + ".displayResolution", 1)
    pm.setAttr(camShapeName + ".overscan", 1)


    # playblast! 
    pm.animation.playblast(filename=filename, format="qt", compression="H.264", forceOverwrite=True, sequenceTime=False, clearCache=True, showOrnaments=False, offScreen=True, viewer=True, percent=100, quality=100, widthHeight=resolution, sound=sound)


    # restore gate
    pm.setAttr(camShapeName + ".displayResolution", resGateEnabled)
    pm.setAttr(camShapeName + ".overscan", overscan)
