import pymel.core as pm


def toggle_viewport_nurbs_curves():
    panel = pm.getPanel(withFocus=True)
    
    if panel is not None:
        panelType = pm.getPanel(typeOf=panel)
        
        # panel is model panel
        if panelType == "modelPanel" and panel:
            nc = not pm.modelEditor(panel, q=True, nc=True)
            pm.modelEditor(panel, e=True, nurbsCurves=nc)


toggle_viewport_nurbs_curves()
