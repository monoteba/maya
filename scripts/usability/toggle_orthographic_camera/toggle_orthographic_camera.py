"""
Toggles the orthographic option of the current camera
"""

import pymel.core as pm


def toggle_orthographic_camera():
    # get camera name
    panel = pm.getPanel(withFocus=True)
    
    if panel is not None:
        panelType = pm.getPanel(typeOf=panel)
        
        # modelPanel is camera
        if panelType == "modelPanel" and panel:
            cam = pm.modelEditor(panel, q=True, camera=True)
            cam_shape = cam.getShape()
            cam_shape.attr('orthographic').set(not (cam_shape.attr('orthographic').get()))


toggle_orthographic_camera()
