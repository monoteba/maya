import maya.cmds as cmds


class alignObjects(object):
    def __init__(self):
        self.selection = []
        self.alignTranslation = True
        self.alignRotation = True

    def align(self):
        # Translation
        target = self.selection.pop()
        t = cmds.xform(target, q=True, ws=True, t=True)
        rp = cmds.xform(target, q=True, rp=True)
        print(t)

        for obj in self.selection:
            rp2 = cmds.xform(obj, q=True, rp=True)
            cmds.xform(obj, ws=True, t=(t[0] + rp[0] - rp2[0],
                                        t[1] + rp[1] - rp2[1],
                                        t[2] + rp[2] - rp2[2]))

        # Rotation

    def main(self):
        self.selection = cmds.ls(sl=True, transforms=True)

        if len(self.selection) < 2:
            cmds.warning("Select at least 2 objects to align them.")
        else:
            self.align()


def alignToPivot():
    align = alignObjects()
    align.main()

alignToPivot()
