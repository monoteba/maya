import pymel.core as pm

def create_center_joint():
    x = y = z = 0.0
    c = pm.ls(sl=True, flatten=True)
    
    for v in c:
        pos = v.getPosition(space='world')
        x += pos[0]
        y += pos[1]
        z += pos[2]
        
    x /= len(c)
    y /= len(c)
    z /= len(c)
    pm.select(cl=True)
    pm.joint(p=[x,y,z], sc=False, radius=5)
    pm.select(c, r=True)

create_center_joint()