"""
Scales an object on XZ (default) based on the width/height of its UV bounding box
"""

import pymel.core as pm


def scale_to_uv_bounding_box(xy=False, xz=True, yz=False):
    if xy:
        w_attr = 'scaleX'
        h_attr = 'scaleY'
    elif xz:
        w_attr = 'scaleX'
        h_attr = 'scaleZ'
    elif yz:
        w_attr = 'scaleZ'
        h_attr = 'scaleY'
    else:
        pm.warning('You need to specify which axis to scale in.')
        return
    
    objs = pm.ls(sl=True, transforms=True)
    
    for obj in objs:
        uv_bounds = pm.polyEvaluate(obj, boundingBox2d=True)
        uv_w = abs(uv_bounds[0][0] - uv_bounds[0][1])
        uv_h = abs(uv_bounds[1][0] - uv_bounds[1][1])
        ratio = uv_w / uv_h
        
        if uv_w < uv_h:
            # change the width
            obj_w = obj.attr(h_attr).get() * ratio
            obj.attr(w_attr).set(obj_w)
        else:
            # change the height
            obj_h = obj.attr(w_attr).get() / ratio
            obj.attr(h_attr).set(obj_h)


scale_to_uv_bounding_box()
