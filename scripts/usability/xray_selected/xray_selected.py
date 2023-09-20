import maya.cmds as cmds

def xray_selected():
    for o in cmds.ls(sl=True):
        val = not bool(cmds.displaySurface(o, q=True, xRay=True)[0])
        cmds.displaySurface(o, xRay=val)
        
xray_selected()