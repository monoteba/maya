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
    
    # replace backslashes with forward slashes
    userprefs_file = userprefs_file.replace('\\', '/')
    
    if not os.path.isfile(userprefs_file):
        cmds.warning('Could not find userPrefs.mel at %s' % userprefs_file)
        return
    
    # backup userPrefs.mel
    backup_file = userprefs_file + strftime('.backup-%Y%m%d-%H%M%S', gmtime())
    shutil.copy2(userprefs_file, backup_file)
    
    # find duplicates
    if os.access(userprefs_file, os.R_OK):
        try:
            with open(userprefs_file, 'r+') as f:
                data = mmap.mmap(f.fileno(), 0)
                matches = re.findall(b'-sv "shelfName([0-9]+)" "(.*?)"', data)
                
                shelves = []
                indices = []
                names = []
                
                for shelf in matches:
                    if shelf[1] not in shelves:
                        shelves.append(shelf[1])
                    else:
                        names.append(shelf[1])
                        indices.append(shelf[0])
                
                f.seek(0)
                lines = f.readlines()
        except IOError as e:
            cmds.warning('Could not read from file %s (%s)' % (userprefs_file, str(e)))
            return
        except Exception as e:
            cmds.warning('An unknown error occured when trying to read from %s (%s)' % (userprefs_file, str(e)))
            return
    else:
        cmds.warning('Failed! Does not have permission to read file %s' % userprefs_file)
        return
    
    if not indices:
        cmds.confirmDialog(title='No duplicates found :/',
                           message='No changed were done and you can safely close the tool.',
                           button=['OK'], cancelButton='OK', dismissString='OK')
        os.remove(backup_file)
        return
    
    # remove duplicates
    if os.access(userprefs_file, os.W_OK):
        try:
            with open(userprefs_file, 'w+') as f:
                for line in lines:
                    for i in indices:
                        pattern = re.compile('-.. "shelf(.*?)%s" (".*?"|[0-9+])' % i)
                        new_line = re.sub(pattern, '', line)
                        if line != new_line:
                            line = new_line
                            break
                    
                    f.writelines(line)
        except IOError as e:
            cmds.warning('IOError: Could not write to file %s (%s)' % (userprefs_file, str(e)))
            return
        except Exception as e:
            cmds.warning('An unknown error occured when trying to write to %s (%s)' % (userprefs_file, str(e)))
            return
    else:
        cmds.warning('Failed: Does not have permission to write to file %s' % userprefs_file)
        return
    
    # restart maya
    restart = cmds.confirmDialog(title='Complete!',
                                 message='Removed %d shelf duplicates in userPrefs.mel.\n'
                                         'Please restart Maya for the changes to take effect.' % len(indices),
                                 button=['Quit Maya', 'Cancel'],
                                 cancelButton='Cancel',
                                 dismissString='Cancel')
    
    save_settings = int(cmds.optionVar(q='saveActionsPreferences'))
    cmds.optionVar(iv=('saveActionsPreferences', 0))
    
    if restart == 'Quit Maya':
        cmds.Quit()
    else:
        cmds.optionVar(iv=('saveActionsPreferences', save_settings))
