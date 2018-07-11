"""
"Unfreezes" translation values in local space for better compatibility with Unity.

The way Maya handles pivots when "freezing" translation is not the same as when viewed in Unity.

For example, if you move an object to -5 in X and then freeze transformations, X will be 0. However, when imported into
Unity, X will be -5.
"""

import pymel.core as pm


def unity_pivot():
    sl = pm.ls(sl=True, transforms=True)
    
    for obj in sl:
        # rotate pivot seems to be the same as translate pivot
        p = pm.xform(obj, q=True, objectSpace=True, rotatePivot=True)
        
        # get original translation
        tx = obj.tx.get()
        ty = obj.ty.get()
        tz = obj.tz.get()
        
        # negative local pivot
        ox = float(p[0]) * -1
        oy = float(p[1]) * -1
        oz = float(p[2]) * -1
        
        # set object negative local pivot
        obj.tx.set(ox)
        obj.ty.set(oy)
        obj.tz.set(oz)
        
        # freeze translate
        pm.makeIdentity(obj, apply=True, t=True, n=True, pn=True)
        
        # set object back to original position
        obj.tx.set(float(tx) + float(p[0]))
        obj.ty.set(float(ty) + float(p[1]))
        obj.tz.set(float(tz) + float(p[2]))


unity_pivot()
