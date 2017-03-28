import pymel.core as pm
from mtoo.helpers import main, math


@main.undoable
def cleanupCurves(stepped=False, keepLast=True, tolerance=0.001):
    """
    Remove redundant keys on animation curves.
    :param stepped: Applied on stepped curves.
    :param keepLast: Always keep the last keyframe.
    :param tolerance: Max. allowed difference before key is removed.
    :return: Total number of keys removed.
    """
    
    # return value
    totalKeys = 0
    
    selection = pm.ls(sl=True)
    for obj in selection:
        curves = pm.listConnections(obj, type="animCurve")
        
        for curve in curves:
            keys = pm.keyframe(curve, q=True, timeChange=True, valueChange=True)
            
            toRemove = []
            count = len(keys)
            
            for i, (time, value) in enumerate(keys):
                if i < count - 2:
                    nextValue = keys[i + 1][1]
                    
                    if stepped and math.isclose(value, nextValue, tolerance):
                        toRemove.append(keys[i + 1][0])
                    elif math.isclose(value, nextValue, tolerance) \
                            and math.isclose(nextValue, keys[i + 2][1], tolerance):
                        toRemove.append(keys[i + 1][0])
            
            if not keepLast and count > 1:
                if math.isclose(keys[count - 1][1], keys[count - 2][1], tolerance):
                    toRemove.append(keys[count - 1][0])
            
            if toRemove:
                for t in toRemove:
                    pm.cutKey(curve, time=t)
                    totalKeys += 1
    
    print "// {0} keys removed on ".format(totalKeys) + str([obj.name().encode() for obj in selection])
    return int(totalKeys)


def graphEditorFramePlaybackRange():
    """
    Frame the current playback range in the Graph Editor
    """
    
    start = pm.playbackOptions(q=True, minTime=True)
    end = pm.playbackOptions(q=True, maxTime=True) + 1
    pm.animView('graphView', startTime=start, endTime=end)
