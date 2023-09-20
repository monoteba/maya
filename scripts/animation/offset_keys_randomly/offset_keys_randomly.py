import pymel.core as pm
import random
import maya.mel


def offset_keys_randomly(max_offset):
    gPlayBackSlider = maya.mel.eval('$tmpVar=$gPlayBackSlider')
    range = cmds.timeControl(gPlayBackSlider, q=True, rangeArray=True)
    
    for o in pm.ls(os=True):
        offset = random.randrange(0, max_offset)
        pm.keyframe(o, e=True, time=range, r=True, o="over", tc=offset)
    

offset_keys_randomly(6)