'''
Select the handles of the currently selected keys in the Graph Editor.

Useful for quickly selecting and changing curve tangents on multiple keys.
'''

# OPTIONS
# which tangent handles to select?
inTangent = False
outTangent = True


# THE SCRIPT
import pymel.core as pm

def select_curve_tangets():
	animCurves = pm.keyframe(q=True, name=True)

	for c in animCurves:
		keys = pm.keyframe(c, q=True, tc=True, sl=True)
		
		if inTangent:
			for k in keys:
				pm.selectKey(c, add=True, inTangent=True, t=k)
		
		if outTangent:
			for k in keys:
				pm.selectKey(c, add=True, outTangent=True, t=k)


select_curve_tangets()