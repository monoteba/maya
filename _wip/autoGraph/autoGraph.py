import maya.cmds as cmds
from functools import partial


class autoGrapher(object):
    def __init__(self):
        self.jobNum = None

    def goToKey(arg):
        print("Go to key")
        keyframes = cmds.keyframe(q=True, selected=True)

        if keyframes is not None:
            animCurves = cmds.keyframe(q=True, timeChange=True)
            frame = animCurves[0]

            if frame != cmds.currentTime(q=True):
                cmds.currentTime(time=frame)

    def startScriptJob(self):
        if self.jobNum is not None:
            self.stopScriptJob()

        self.jobNum = cmds.scriptJob(event=["SelectionChanged", partial(self.goToKey)],
                                     killWithScene=True)

    def stopScriptJob(self):
        cmds.scriptJob(kill=self.jobNum)


def autoGraph():
    k = autoGrapher()
    k.startScriptJob()
