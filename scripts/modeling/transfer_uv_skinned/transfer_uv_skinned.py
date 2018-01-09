"""
Transfer UV from non-skinned to skinned model
"""

import pymel.core as pm


def transfer_uv_skinned():
    # get selection
    selection = pm.ls(sl=True, transforms=True)
    shapes = selection[1].getShapes()

    # find "Orig" object on skinned mesh
    orig = None
    for shape in shapes:
        if shape.attr('intermediateObject').get():
            orig = shape
            orig.attr('intermediateObject').set(False)
            break

    # abort if no intermediate object was found
    if not orig:
        pm.warning("Could not find intermediate object on second transform.")
        return

    # transfer uvs from first object to base shape of the second
    pm.transferAttributes(selection[0], orig, 
        transferPositions=0, 
        transferNormals=0, 
        transferUVs=2, 
        transferColors=0, 
        sampleSpace=5, 
        searchMethod=0, 
        flipUVs=0, 
        colorBorders=1)

    # delete history, so we can safely delete the second object afterwards
    pm.delete(orig, constructionHistory=True)
    orig.attr('intermediateObject').set(True)


transfer_uv_skinned()
