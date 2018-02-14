"""
Selects the transform objects based on component selection
"""

import pymel.core as pm


def select_object_from_component():
    components = pm.ls(sl=True)
    
    objs = set()
    for c in components:
        objs.add(c.node())
    
    pm.select(objs, r=True)


select_object_from_component()
