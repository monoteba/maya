"""
Search and replace image path in all file nodes.

Place in Maya's script folder and execute in a Python tab:

from replace_file_node_paths import *
replace_file_node_paths.do_replace()

"""

import pymel.core as pm


class replace_file_node_paths:
    @staticmethod
    def do_replace():
        search = ''
        replace = ''
        
        method = pm.confirmDialog(title='Search/replace file textures (file and psdFile)',
                                  message='Auto: replace absolute paths with relative paths based on project location\n\nManual: search and replace with string',
                                  button=['Auto', 'Manual', 'Cancel'],
                                  cancelButton='Cancel', dismissString='Cancel')
        
        if method == 'Cancel':
            return
        elif method == 'Auto':
            r = replace_file_node_paths.auto_mode()
        elif method == 'Manual':
            r = replace_file_node_paths.manual_mode()
        
        if r is None:
            return
        
        search = r[0]
        replace = r[1]
        
        print search
        print replace
        
        # get all file nodes
        fileNodes = pm.ls(exactType='file')
        fileNodes.extend(pm.ls(exactType='psdFileTex'))
        
        # iterate and replace path
        print "\n# Replacing file nodes' file texture name...\n"
        
        with pm.UndoChunk():
            for node in fileNodes:
                old_path = pm.getAttr('%s.fileTextureName' % str(node))
                path = old_path.replace(search, replace)
                
                pm.setAttr('%s.fileTextureName' % str(node), path, type='string', alteredValue=True)
                
                print '# %s old path: %s \n# %s new path: %s\n' % (
                str(node), old_path, str(node), pm.getAttr('%s.fileTextureName' % str(node)))
    
    @staticmethod
    def auto_mode():
        return (pm.workspace.path + '/', '')
    
    @staticmethod
    def manual_mode():
        if 'replace_file_node_paths_search' not in pm.env.optionVars:
            pm.optionVar['replace_file_node_paths_search'] = ''
            pm.optionVar['replace_file_node_paths_replace'] = ''
        
        # get saved search/replace paths
        search = pm.optionVar['replace_file_node_paths_search']
        replace = pm.optionVar['replace_file_node_paths_replace']
        
        # prompt for paths
        search_p = pm.promptDialog(text=search, title='Search/Replace', message='Search for file node paths...',
                                   button=['OK', 'Cancel'], defaultButton='OK', cancelButton='Cancel',
                                   dismissString='Cancel')
        search = pm.promptDialog(q=True, text=True)
        replace_p = pm.promptDialog(text=replace, title='Search/Replace', message='... replace with:',
                                    button=['OK', 'Cancel'], defaultButton='OK', cancelButton='Cancel',
                                    dismissString='Cancel')
        replace = pm.promptDialog(q=True, text=True)
        
        if search_p == 'Cancel' or replace_p == 'Cancel':
            return None
        
        # save new search/replace paths
        pm.optionVar['replace_file_node_paths_search'] = search
        pm.optionVar['replace_file_node_paths_replace'] = replace
        
        return (search, replace)
