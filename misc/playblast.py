#
# Playblast using filename and H.264 compression
#

# options
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
    filename = match.group(1) + match.group(2) + '_' + match.group(3)


# assemble full path and filename
filename = movieDir + filename + ".mov"


# get active sound in time slider
aPlayBackSliderPython = maya.mel.eval('$tmpVar=$gPlayBackSlider')
sound = pm.timeControl(aPlayBackSliderPython, q=True, sound=True)


# disable resolution gate
view = OpenMayaUI.M3dView.active3dView()
cam = OpenMaya.MDagPath()
view.getCamera(cam)
camShape = cam.partialPathName()

resGateEnabled = pm.getAttr(camShape + ".displayResolution")
overscan = pm.getAttr(camShape + ".overscan")

pm.setAttr(camShape + ".displayResolution", 1)
pm.setAttr(camShape + ".overscan", 1)


# playblast! 
pm.animation.playblast(filename=filename, format="qt", compression="H.264", forceOverwrite=True, sequenceTime=False, clearCache=True, showOrnaments=False, offScreen=True, viewer=True, percent=100, quality=100, widthHeight=resolution, sound=sound)


# restore gate
pm.setAttr(camShape + ".displayResolution", resGateEnabled)
pm.setAttr(camShape + ".overscan", overscan)
