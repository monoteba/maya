import pymel.core as pm

panel = pm.getPanel(withFocus=True)

if panel is not None:
	panelType = pm.getPanel(typeOf=panel)

	# modelPanel is cameras
	if panelType == "modelPanel" and panel:
		nc = not pm.modelEditor(panel, q=True, nc=True)
		pm.modelEditor(panel, e=True, nurbsCurves=nc)
		
