'''
Rounds key values of selected curves to nearest whole number
'''

import pymel.core as pm

animCurves = pm.keyframe(q=True, name=True)

for c in animCurves:
    keys = pm.keyframe(c, q=True, tc=True, vc=True, sl=True)
    for k in keys:
        val = round(k[1])
        pm.keyframe(c, e=True, t=k[0], vc=val, absolute=True)
