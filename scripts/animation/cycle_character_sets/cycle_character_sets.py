"""
Cycles character sets either forwards or backwards. It cycles alphabetically, NOT in the order shown in Maya.
"""

import pymel.core as pm

def cycle_character_set(backwards=False):
    characters = pm.ls(type="character")
    active = pm.selectionConnection("highlightList", q=True, object=True)
    
    if not characters:
        return
    
    if active is None:
        index = 0
        
        if backwards:
            pm.mel.eval('setCurrentCharacters({"%s"})' % (characters[-1]))
        else:
            pm.mel.eval('setCurrentCharacters({"%s"})' % (characters[0]))
            
        return
    
    
    index = characters.index(active[0])
    new_index = 0
    
    new_index = (index + 1) if not backwards else (index - 1)
    
    if  new_index < 0 or new_index > (len(characters)-1):
        pm.mel.eval('setCurrentCharacters({})')
    else:
        pm.mel.eval('setCurrentCharacters({"%s"})' % (characters[new_index]))
    

cycle_character_set(backwards=False)
