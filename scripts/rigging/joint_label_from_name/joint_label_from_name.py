# Set joint label to the name of the object,
# removing L_ and R_ from the name.
#
# Handy for when you need to mirror skin weights exactly.

import pymel.core as pm

for jnt in pm.ls(sl=True, type='joint'):
    label = jnt.name()
    
    label = label.replace('L_', '')
    label = label.replace('R_', '')
    
    jnt.attr('type').set(18)  # other
    jnt.attr('otherType').set(label)
