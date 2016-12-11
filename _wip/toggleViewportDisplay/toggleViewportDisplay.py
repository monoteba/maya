import maya.cmds as cm


def getActiveModelPanel():
    # get focused panel
    activePanel = cm.getPanel(wf=True)
    
    # if the panel is a type of modelPanel, return it
    if 'modelPanel' == cm.getPanel(typeOf=activePanel):
        return activePanel
    
    return None


def toggleViewportDisplay():
    activePanel = getActiveModelPanel()
    
    if getActiveModelPanel() is not None:
        cm.modelEditor(activePanel, e=True,
                       # allObjects=False,
        
                       nurbsCurves=True,
                       nurbsSurfaces=True,
                       controlVertices=True,
                       hulls=True,
                       polymeshes=True,
                       subdivSurfaces=True,
                       planes=True,
                       lights=True,
                       cameras=True,
                       imagePlane=True,
                       joints=True,
                       ikHandles=True,
                       deformers=True,
                       dynamics=True,
                       particleInstancers=True,
                       fluids=True,
                       hairSystems=True,
                       follicles=True,
                       nCloths=True,
                       nParticles=True,
                       nRigids=True,
                       dynamicConstraints=True,
                       locators=True,
                       dimensions=True,
                       pivots=True,
                       handles=True,
                       textures=True,
                       strokes=True,
                       motionTrails=True,
                       pluginShapes=True,
                       clipGhosts=True,
                       greasePencils=True,
                       pluginObjects=["gpuCacheDisplayFilter", True],
        
                       manipulators=True,
                       grid=True,
                       hud=True,
                       hos=True,
                       selectionHiliteDisplay=True
                       )


toggleViewportDisplay()
