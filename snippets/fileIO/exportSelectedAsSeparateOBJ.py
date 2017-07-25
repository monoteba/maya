'''
Exports all selected meshes as separate .obj files
'''

import maya.cmds as cmds

def exportSelectedAsSeparateOBJ():
	path = cmds.fileDialog2(caption='Select Export Folder', dialogStyle=2, fileMode=2)
	
	if not path:
		return

	path = path[0]
	
	prompt = cmds.promptDialog(button=['Save', 'Cancel'], cancelButton='Cancel', defaultButton='Save', dismissString='Cancel', message='Optional file prefix', title='OBJ File Prefix')
	
	if prompt == 'Cancel':
		return
	
	selection = cmds.ls(sl=True, transforms=True)
	
	print '\n// Exporting files...'
	
	for obj in selection:
		cmds.select(obj, r=True)
		filename = cmds.promptDialog(q=True, text=True) + obj.replace('|', '_') + '.obj'
		exportPath = path + '/' + filename
		print '// ' + exportPath
		cmds.file(exportPath, force=True, options="groups=1;ptgroups=1;materials=0;smoothing=1;normals=1", typ='OBJexport', preserveReferences=False, exportSelected=True)
	
	print '\n// Exported ' + str(len(selection)) + ' objects!',
	
	cmds.select(selection, r=True)


exportSelectedAsSeparateOBJ()
