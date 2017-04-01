import pymel.core as pm
from mtoo.helpers import main

@main.undoable
def transferReferenceEdits():
    """
    Copies all attributes from nodes of two identical references
    :return:
    """
    selection = pm.ls(sl=True)
    
    if len(selection) > 2:
        print "More than two objects selected!\n"
        return
    
    refNode1 = pm.referenceQuery(selection[0], rfn=True)
    refNode2 = pm.referenceQuery(selection[1], rfn=True)
    
    file1 = pm.referenceQuery(refNode1, filename=True)
    file2 = pm.referenceQuery(refNode2, filename=True)
    
    if file1 is not file2:
        print "The two objects does not share the same reference file.\n"
        return
    
    if refNode1 is refNode2:
        print "The two objects share the same reference.\n"
        return
    
    nodes1 = pm.referenceQuery(refNode1, nodes=True)
    nodes2 = pm.referenceQuery(refNode2, nodes=True)
    
    for i in range(0,len(nodes1)):
        pm.copyAttr(nodes1[i], nodes2[i], values=True)
        

# {
#
#     string $sl[] = `ls - sl`;
#
# string $ref = `referenceQuery - rfn $sl[0]
# `;
# // string $target = `referenceQuery - rfn $sl[1]
# `;
#
# string $edits[] = `referenceQuery - es $ref
# `;
#
# string $nodes[] = `referenceQuery - nodes $ref
# `;
# print($nodes);
# }
