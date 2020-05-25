import pymel.core as pm


def smart_offset(offset = 0):
    with pm.UndoChunk():
        for obj in pm.ls(sl=True):
            for curve in pm.keyframe(obj, q=True, name=True):
                old_keys = pm.keyframe(curve, q=True, timeChange=True)
                pm.keyframe(curve, timeChange=offset, relative=True)

                keys = old_keys + pm.keyframe(curve, q=True, timeChange=True)
                keys = list(set(keys))
                
                for t in old_keys:
                    pm.setKeyframe(curve, time=t, insert=True)
                
                for t in keys:
                    if t > old_keys[-1] or t < old_keys[0]:
                        pm.cutKey(curve, time=t, clear=True)

smart_offset(2)