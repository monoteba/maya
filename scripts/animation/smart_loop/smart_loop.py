import pymel.core as pm


def smart_loop():
	with pm.UndoChunk():
		for obj in pm.ls(sl=True):
			for curve in pm.keyframe(obj, q=True, name=True):
				first = pm.findKeyframe(curve, which='first')
				last = pm.findKeyframe(curve, which='last')
				t = (first, last)
				pm.copyKey(curve)
				pm.pasteKey(curve, time=last, option='insert', connect=True)

smart_loop()