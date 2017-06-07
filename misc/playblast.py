#
# Playblast using filename
#

import maya.cmds as cmds
import maya.mel
import pymel.core as pm
import re
import os

# playblast resolution
resolution=[1920,1080]

# Filename in the format "/my/path/sh_0010_ANI_workshop_0010.ma"
# is converted to "sh_0010_ANI"

name = os.path.basename(pm.system.sceneName())
pattern = re.compile('(?!\/)(.*?_.*?_.*?_)')
match = re.match(pattern, name)
movieDir = pm.workspace.fileRules['movie'] + "/"
movieDir.replace('\\', '/')

filename = match.group(1)
filename = movieDir + filename[:-1] + ".mov"

aPlayBackSliderPython = maya.mel.eval('$tmpVar=$gPlayBackSlider')
sound = pm.timeControl(aPlayBackSliderPython, q=True, sound=True)

pm.animation.playblast(filename=filename, format="qt", compression="H.264", forceOverwrite=True, sequenceTime=False, clearCache=True, showOrnaments=False, offScreen=True, viewer=True, percent=100, quality=100, widthHeight=resolution, sound=sound)
