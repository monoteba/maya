'''
Removes redundant keys on animation curves.

For example, if the keyframes at time {1, 5, 9} have the same value, but at time {13} the value changes. The keyframe at time {5} will be removed. 

stepped=True
Then both keys {5, 9} will be removed in the example above, since it would visually be identical.

keepLast=False
Will remove the last keyframe if it is identical the the previous keyframe.

tolerance=0.001
How large the difference needs to be for two keyframes to be considered equal. Setting the value to 0 may not produce expected results.
'''

def isclose(a, b, epsilon=1e-09):
    """
    Compare two numbers for equality with supplied epsilon
    :param a: First value
    :param b: Second value
    :param epsilon: Max. allowed difference
    :return: True if difference between a and b is less than epsilon
    """
    return abs(a - b) < epsilon
	

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
	
cleanupCurves(False, True, 0.001)
