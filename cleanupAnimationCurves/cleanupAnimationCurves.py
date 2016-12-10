import pymel.core as pm


def undoable(function):
    def undoFunction(*args, **kwargs):
        pm.undoInfo(openChunk=True)
        functionReturn = None
        try:
            functionReturn = function(*args, **kwargs)
        
        except:
            print pm.sys.exc_info()[1]
        
        finally:
            pm.undoInfo(closeChunk=True)
            return functionReturn
    
    return undoFunction


@undoable
def cleanupCurves(tolerance=0.001):
    totalKeys = 0
    
    def isclose(a, b):
        return abs(a - b) < tolerance
    
    def clean(curves, totalKeys):
        for curve in curves:
            keys = pm.keyframe(curve, q=True, timeChange=True, valueChange=True)
            
            toRemove = []
            count = len(keys)
            
            for i, (time, value) in enumerate(keys):
                if i < count - 2:
                    nextValue = keys[i + 1][1]
                    if isclose(value, nextValue) and isclose(nextValue, keys[i + 2][1]):
                        toRemove.append(keys[i + 1][0])
            
            if toRemove:
                for t in toRemove:
                    pm.cutKey(curve, time=t)
                    totalKeys += 1
        
        return totalKeys
    
    # start the job!
    selection = pm.ls(sl=True)
    for obj in selection:
        totalKeys = clean(pm.listConnections(obj, type="animCurve"), totalKeys)
    
    print "// CleanupCurves ({0} keys removed on )".format(totalKeys)
