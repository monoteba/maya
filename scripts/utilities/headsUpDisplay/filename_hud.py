import pymel.core as pm
import maya.api.OpenMaya as om
import os

# hud screen position
# top:      0   1   2   3   4
# bottom:   5   6   7   8   9
hud_filename_section = 9

hud_filename_save_callback = None
hud_filename_open_callback = None

def hud_file_object(*args):
    try:
        filename = os.path.basename(pm.system.sceneName())
        if not filename:
            return "(not set)"
        return filename
    except:
        return ""
        

def toggle_file_hud():
    if pm.headsUpDisplay('HUDFilename', exists=True):
        pm.headsUpDisplay('HUDFilename', rem=True)
    else:
        create_file_hud()
    
 
def create_file_hud(event=None):
    if pm.headsUpDisplay('HUDFilename', exists=True):
        pm.headsUpDisplay('HUDFilename', rem=True)
    
    block = 0
    
    while block < 20:
        try:
            pm.headsUpDisplay('HUDFilename', 
                section=hud_filename_section, 
                block=block,
                blockSize='medium',
                label='Filename:',
                labelFontSize='small',
                command=hud_file_object,
                event='NewSceneOpened')
        except RuntimeError:
            block = block + 1
            continue
        
        break
        
    global hud_filename_save_callback
    global hud_filename_open_callback
    
    try:
        om.MSceneMessage.removeCallback(hud_filename_save_callback)
        om.MSceneMessage.removeCallback(hud_filename_open_callback)
    except:
        pass

    hud_filename_save_callback = om.MSceneMessage.addCallback(om.MSceneMessage.kAfterSave, create_file_hud)
    hud_filename_open_callback = om.MSceneMessage.addCallback(om.MSceneMessage.kAfterOpen, create_file_hud)
        

toggle_file_hud()
