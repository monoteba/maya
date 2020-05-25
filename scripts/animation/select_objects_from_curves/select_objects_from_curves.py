"""
Select the objects affected by the select animation curves.
"""

import pymel.core as pm

def select_object_from_curve():
    curves = pm.keyframe(q=True, name=True)
    
    objs = []
    for c in curves:
        c = pm.PyNode(c)
        objs = objs + c.attr('output').outputs()
    
    pm.select(objs, r=True)
    pm.selectKey(curves, add=True, k=True)
    
select_object_from_curve()