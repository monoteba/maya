"""
Remove duplicate shelf entries from userPrefs.mel. This may fix the "empty shelves on startup" issue.

The issue is discussed at:
https://forums.autodesk.com/t5/maya-forum/shelf-buttons-disappear-upon-restarting-maya/td-p/4357871
https://amorten.com/blog/2017/maya-empty-shelves-after-restart/

Place in Maya's script folder and execute in a Python tab:

from fix_empty_shelves import *
fix_empty_shelves()

Alternatively, copy the entire script into a Python tab in the Script Editor, and add the following line to the end

fix_empty_shelves()
"""

import maya.cmds as cmds
import mmap
import os
import re
import shutil
import sys
from time import gmtime, strftime


def fix_empty_shelves(userprefs_file=None):
    confirm = cmds.confirmDialog(title='Fix empty shelves',
                                 message='This will find duplicate shelf entries in userPrefs.mel.\n\n'
                                         'Maya needs to be closed at the end for the tool to work.\n\n'
                                         'Please save all work before continuing.',
                                 button=['Continue', 'Cancel'],
                                 cancelButton='Cancel',
                                 dismissString='Cancel')
    
    if confirm == 'Cancel':
        return
    
    # if no path is supplied, try to find the default
    if userprefs_file is None:
        prefs_dir = cmds.about(preferences=True)
        userprefs_file = prefs_dir + '/prefs/userPrefs.mel'
        
    # convert path to platform path style
    userprefs_file = os.path.abspath(userprefs_file)
        
    if not os.path.isfile(userprefs_file):
        cmds.warning('Could not find userPrefs.mel at %s' % userprefs_file)
        return
    
    # backup userPrefs.mel
    backup_file = userprefs_file + strftime('.backup-%Y%m%d-%H%M%S', gmtime())
    shutil.copy2(userprefs_file, backup_file)
    
    # find duplicates
    try:
        with open(userprefs_file, 'r+') as f:           
            shelves = []
            indices = []
            names = []

            data = mmap.mmap(f.fileno(), 0)
            matches = re.findall(b'-sv "shelfName([0-9]+)" "(.*?)"', data)
            data.close()
            
            for shelf in matches:
                if shelf[1] not in shelves:
                    shelves.append(shelf[1])
                else:
                    names.append(shelf[1])
                    indices.append(shelf[0])
            
            f.seek(0, 0)
            lines = f.readlines()
    except IOError as e:
        cmds.warning('Could not read from file %s (%s)' % (userprefs_file, str(e)))
        return
    except Exception as e:
        cmds.warning('An unknown error occured when trying to read from %s (%s)' % (userprefs_file, str(e)))
        return
    
    if not indices:
        cmds.confirmDialog(title='No duplicates found',
                           message='No changed were done and you can safely close the tool.',
                           button=['OK'], cancelButton='OK', dismissString='OK')
        os.remove(backup_file)
        return
    
    # remove duplicates
    log = 'Removed %s lines:\n' % str(len(indices))
    try:
        with open(userprefs_file, 'w+') as f:
            for line in lines:
                for i in indices:
                    pattern = re.compile('-.. "shelf(.*?)%s" (".*?"|[0-9+])' % i)
                    new_line = re.sub(pattern, '', line)
                    if line != new_line:
                        log = log + str(line)
                        line = new_line
                        break
                
                f.writelines(line)
    except IOError as e:
        cmds.warning('IOError: Could not write to file %s (%s)' % (userprefs_file, str(e)))
        return
    except Exception as e:
        cmds.warning('An unknown error occured when trying to write to %s (%s)' % (userprefs_file, str(e)))
        return

    # fes_quit(log, len(indices))
    win = cmds.window(title='Fix Empty Shelves', rtf=True, widthHeight=(300, 100))
    form = cmds.formLayout(nd=100)

    m = cmds.iconTextStaticLabel(st="iconAndTextHorizontal", i="info.xpm", align='center', fn='plainLabelFont',
                                 l='Removed %d shelf duplicates in userPrefs.mel.\nPlease quit Maya to apply the changes.' % len(indices))
    b1 = cmds.button('Quit Maya', command=lambda *args: fes_quit(win, True))
    b2 = cmds.button('View Log', command=lambda *args: fes_view_log(log))
    b3 = cmds.button('Cancel', command=lambda *args: fes_quit(win, False))

    cmds.formLayout(form, e=True, numberOfDivisions=100, 
                    attachForm=[
                        (m, 'top', 8), (m, 'left', 8), (m, 'right', 8),
                        (b1, 'left', 8), (b3, 'right', 8),
                        (b1, 'bottom', 8), (b2, 'bottom', 8), (b3, 'bottom', 8)
                        ],
                    attachPosition=[
                        (b1, 'right', 8, 34), (b3, 'left', 8, 66)
                        ],
                    attachControl=[
                        (b2, 'left', 8, b1), (b2, 'right', 8, b3)
                        ]
        )

    cmds.showWindow(win)


def fes_quit(window, quit):
    cmds.deleteUI(window, window=True)    

    save_settings = int(cmds.optionVar(q='saveActionsPreferences'))
    cmds.optionVar(iv=('saveActionsPreferences', 0))
    
    if quit:
        cmds.Quit()
    else:
        cmds.optionVar(iv=('saveActionsPreferences', save_settings))

def fes_view_log(log):
    # show the log
    cmds.window(title='Log', widthHeight=(350,350))
    cmds.paneLayout(configuration='single')
    cmds.scrollField(editable=False, wordWrap=False, text=log)
    cmds.showWindow()
