"""
Set an object scale to fit the ratio of a file texture. Scales on XZ by default.

Optionally renames the file texture node to match the image file.
"""

import os
import pymel.core as pm


def scale_to_image_dimensions(xy=False, xz=True, yz=False, rename=False):
    objs = pm.ls(orderedSelection=True, transforms=True)
    sgs = get_shading_groups(objects=objs)

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
    
    for obj, sg in zip(objs, sgs):
        mat = sg.attr('surfaceShader').inputs()[0]
        tex = mat.attr('color').inputs()[0]
        
        w = None
        h = None
        
        if tex.nodeType() == 'file':
            w = tex.attr('outSizeX').get()
            h = tex.attr('outSizeY').get()
        else:
            return
        
        if rename:
            name = os.path.splitext(os.path.basename(tex.attr('fileTextureName').get()))[0]
            pm.rename(tex, name)
        
        r = w / h
        
        if w < h:
            # change the width
            obj_w = obj.attr(h_attr).get() * r
            obj.attr(w_attr).set(obj_w)
        else:
            # change the height
            obj_h = obj.attr(w_attr).get() * r
            obj.attr(h_attr).set(obj_h)


def get_shading_groups(objects=None):
    if not objects:
        return None
    
    # find shading groups in objects
    shading_groups = []
    for obj in objects:
        for shape in obj.getShapes():
            for node in shape.outputs():
                if node.nodeType() == 'shadingEngine':
                    shading_groups.append(node)
    
    return shading_groups


scale_to_image_dimensions(rename=True)
