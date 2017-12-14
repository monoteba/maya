'''
Playblast using filename and H.264 compression
'''

import maya.mel
import pymel.core as pm
import maya.OpenMaya as OpenMaya
import maya.OpenMayaUI as OpenMayaUI
import re
import os


def custom_playblast():
    # default paths
    filename = os.path.splitext(os.path.basename(pm.system.sceneName()))[0]
    movieDir = pm.workspace.fileRules['movie'] + "/"
    movieDir.replace('\\', '/')
    
    # get camera name
    view = OpenMayaUI.M3dView.active3dView()
    camPath = OpenMaya.MDagPath()
    view.getCamera(camPath)  # returns camera shape node
    camShapeName = camPath.partialPathName()
    
    cam = camPath.transform()  # returns MObject
    OpenMaya.MDagPath.getAPathTo(cam, camPath)
    camName = camPath.partialPathName()
    
    # get render resolution
    resolution = [int(pm.getAttr("defaultResolution.width")), int(pm.getAttr("defaultResolution.height"))]
    
    # prompt for postfix
    message = "Camera: %s\n\nResolution: %dx%d\n\nFilename:" % (camName, resolution[0], resolution[1])
    
    filename = None
    try:
        filename = pm.system.fileInfo['playblastFilename']
    except:
        pass
    
    if filename is None:
        # Regex example:
        # Filename in the format "/my/path/sh_0010_ANI_workshop_0010.ma"
        # is converted to "sh_0010_ANI_workshop"
        filename = os.path.splitext(os.path.basename(pm.system.sceneName()))[0]
        pattern = re.compile('(.*?)_[0-9+]')
        match = re.match(pattern, filename)
        
        if match is not None:
            filename = match.group(1)
    
    result = pm.promptDialog(title="Playblast", message=message, button=["Playblast", "Cancel"],
                             defaultButton="Playblast", cancelButton="Cancel", dismissString="Cancel", text=filename)
    
    if result == "Playblast":
        newName = pm.promptDialog(q=True, text=True)
        
        if newName is not "":
            filename = newName
        
        pm.system.fileInfo['playblastFilename'] = filename
        
        # get active sound in time slider
        aPlayBackSliderPython = maya.mel.eval('$tmpVar=$gPlayBackSlider')
        sound = pm.timeControl(aPlayBackSliderPython, q=True, sound=True)
        
        # assemble full path and filename
        filename = movieDir + filename + ".mov"
        
        # disable resolution gate
        resGateEnabled = pm.getAttr(camShapeName + ".displayResolution")
        overscan = pm.getAttr(camShapeName + ".overscan")
        pm.setAttr(camShapeName + ".displayResolution", 1)
        pm.setAttr(camShapeName + ".overscan", 1)
        
        # playblast!
        pm.animation.playblast(filename=filename, format="qt", compression="H.264", forceOverwrite=True,
                               sequenceTime=False, clearCache=True, showOrnaments=False, offScreen=True, viewer=True,
                               percent=100, quality=100, widthHeight=resolution, sound=sound)
        
        # restore gate
        pm.setAttr(camShapeName + ".displayResolution", resGateEnabled)
        pm.setAttr(camShapeName + ".overscan", overscan)


custom_playblast()
