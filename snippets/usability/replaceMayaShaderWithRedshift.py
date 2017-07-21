'''
Takes selected materials and replaces them with Redshift materials imported from file dialog window.

Finds the gammaCorrect node attached to the Redshift material's "diffuse_color" attribute, and assigns it the color value of the selected material(s). If it does not find a gammaCorrect node, it simply assign the color of the material to the diffuse color of the Redshift material.

Finally, it assigns the Redshift material to the  objects the material was assigned to.
'''


# import packages
import pymel.core as pm
import os

shaderFilePath = pm.fileDialog2(caption='Import Redshift shader', dialogStyle=2, fileMode=1, fileFilter='Maya Files (*.ma *.mb);;Maya ASCII (*.ma);;Maya Binary (*.mb)')[0]

# use filename as namespace
filename = os.path.basename(shaderFilePath)
namespace = os.path.splitext(filename)[0]	


# get selected materials
selectedMaterials = pm.ls(orderedSelection=True, materials=True)

redshiftNodes = []

# for each material...
for material in selectedMaterials:
	# import shader
	nodes = pm.system.importFile(shaderFilePath, returnNewNodes=True, defaultNamespace=False, namespace=namespace)

	# find RedshiftMaterial node in imported nodes
	redshiftNode = None
	for node in nodes:
		if pm.nodeType(node) == 'RedshiftMaterial':
			redshiftNode = node
			redshiftNodes.append(redshiftNode)
			break

	# get color from original material and assign it to the gammeCorrect node - or diffuse color if no gamma correct node is attached
	colorValue = pm.getAttr(material + '.color')

	# get connected node, the gammaCorrect node
	gammaCorrectNode = pm.listConnections(redshiftNode + '.diffuse_color', destination=False, source=True)[0]

	if gammaCorrectNode:
		if pm.nodeType(gammaCorrectNode) == 'gammaCorrect':
			pm.setAttr(gammaCorrectNode + '.value', colorValue, type='double3')
	else:
		pm.setAttr(redshiftNode + '.diffuse_color', colorValue, type='double3')

	# get objects with material and assign redshift material to them
	sg = material.shadingGroups()
	setMembers = pm.sets(sg, q=True)
	pm.select(setMembers, r=True)
	pm.hyperShade(assign=redshiftNode)

	# select the imported redshift nodes
	pm.select(redshiftNodes, r=True)
    
