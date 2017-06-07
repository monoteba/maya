#
# Playblast using filename and H.264 compression
#

# options
resolution = [1920,1080] # playblast resolution
modFileName = False # do a regex search to replace filename, see example below

import maya.cmds as cmds
import maya.mel
import pymel.core as pm
import re
import os

# default paths
filename = os.path.basename(pm.system.sceneName())
movieDir = pm.workspace.fileRules['movie'] + "/"
movieDir.replace('\\', '/')

if modFileName:
# Regex example:
# Filename in the format "/my/path/sh_0010_ANI_workshop_0010.ma"
# is converted to "sh_0010_ANI"
pattern = re.compile('(?!\/)(.*?_.*?_.*?_)')
match = re.match(pattern, name)
filename = match.group(1)

# assemble full path and filename
filename = movieDir + filename[:-1] + ".mov"

# get active sound in time slider
aPlayBackSliderPython = maya.mel.eval('$tmpVar=$gPlayBackSlider')
sound = pm.timeControl(aPlayBackSliderPython, q=True, sound=True)

# playblast! 
pm.animation.playblast(filename=filename, format="qt", compression="H.264", forceOverwrite=True, sequenceTime=False, clearCache=True, showOrnaments=False, offScreen=True, viewer=True, percent=100, quality=100, widthHeight=resolution, sound=sound)
