import maya.cmds as cmds


def lockJoints():
    joints = cmds.ls(sl=True, type="joint")

    result = cmds.confirmDialog(title="Lock/Unlock Joints",
                               button=["Lock", "Unlock"],
                               defaultButton="Lock",
                               cancelButton="Unlock",
                               dismissString="Cancel")

    if result == "Lock":
        for joint in joints:
            cmds.setAttr(joint + ".liw", 1)

    elif result == "Unlock":
        for joint in joints:
            cmds.setAttr(joint + ".liw", 0)

    else:
        cmds.warning("Operation cancelled")


lockJoints()
