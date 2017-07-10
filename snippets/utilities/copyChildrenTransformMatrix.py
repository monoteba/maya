'''
Copies the transform matrix of children in one group to the children of another group.

Example, selecting groupA and then groupB, will make sphere1 have the same transform as cube1, sphere2 the same as cube2 etc.
groupA
	- cube1
	- cube2
	- cube3

groupB
	- sphere1
	- sphere2
	- sphere3
'''

import pymel.core as pm


sl = pm.ls(orderedSelection=True)

if len(sl) != 2:
    print "Must select exactly two groups"
    
else:
    listA = listA = pm.listRelatives(sl[0], children=True, typ="transform")
    listB = listA = pm.listRelatives(sl[1], children=True, typ="transform")
        
    transforms = []
    for o in listA:
        transforms.append(pm.xform(o, q=True, matrix=True))
    
    
    for o, t in zip(listB, transforms):
        pm.xform(o, matrix=t)
	
