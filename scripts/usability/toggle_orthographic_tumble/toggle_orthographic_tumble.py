"""
Toggles the orthographic locked state of the Tumble Tool
"""

import maya.cmds as cmds


def toggle_orthographic_tumble(stepped=False):
    val = not (cmds.tumbleCtx('tumbleContext', q=True, orthoLock=True))
    cmds.tumbleCtx('tumbleContext', e=True, orthoLock=val)
    cmds.tumbleCtx('tumbleContext', e=True, autoOrthoConstrain=stepped)


toggle_orthographic_tumble()
