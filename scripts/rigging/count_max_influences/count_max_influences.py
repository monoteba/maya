import pymel.core as pm
import sys


def count_max_influences():
    for obj in pm.ls(sl=True, type="transform"):
        skins = obj.getShape().inputs(type="skinCluster")
        
        for skin in skins:
            max = 0
            
            for mesh in pm.skinCluster(skin, q=True, geometry=True):
                verts = pm.polyListComponentConversion(mesh, toVertex=True)
                verts = pm.filterExpand(verts, selectionMask=31)
                
                for vert in verts:
                    joints = pm.skinPercent(skin, vert, q=True, ignoreBelow=0.000001, transform=None)
                    
                    if len(joints) > max:
                        max = len(joints)
            
            sys.stdout.write("# %s max influences is %d\n" % (obj.shortName(), max))    


count_max_influences()