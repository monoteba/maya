import maya.cmds as cmds


def toggle_viewport_nurbs_curves():
    panel = cmds.getPanel(withFocus=True)
    
    if panel is not None:
        panelType = cmds.getPanel(typeOf=panel)
        
        # panel is model panel
        if panelType == "modelPanel" and panel:
            nc = not cmds.modelEditor(panel, q=True, nc=True)
            cmds.modelEditor(panel, e=True, nurbsCurves=nc)


toggle_viewport_nurbs_curves()
