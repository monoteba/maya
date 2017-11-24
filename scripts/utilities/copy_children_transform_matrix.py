'''
Copies the transform matrix of children in one group to the children of another group.

Example, selecting groupA and then groupB, will make sphere1 have the same transform as cube1, sphere2 the same as cube2 etc.

groupA			groupB
-cube1		=>	-sphere1
-cube2		=>	-sphere2
-cube3		=>	-sphere3

'''

import pymel.core as pm

def copy_children_transform_matrix():
	sl = pm.ls(orderedSelection=True)

	if len(sl) != 2:
		print "Must select exactly two groups"
		
	else:
		sources = pm.listRelatives(sl[0], children=True, typ="transform")
		targets = pm.listRelatives(sl[1], children=True, typ="transform")
			
		transforms = []
		for o in sources:
			transforms.append(pm.xform(o, q=True, matrix=True))
		
		
		for o, t in zip(targets, transforms):
			pm.xform(o, matrix=t)
		
copy_children_transform_matrix()