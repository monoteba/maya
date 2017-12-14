import pymel.core as pm
import maya.mel as mel


def copy_paste_offset():
	offset = pm.promptDialog(button=['OK','Cancel'], defaultButton='OK', dismissString='Cancel', cancelButton='Cancel', title='Copy Offset', message='Copy and paste offset:') 
	
	if offset == 'Cancel':
		return
	
	try:
		offset = float(pm.promptDialog(q=True, text=True))
	except ValueError:
		return
		
	# get time slider range
	aTimeSlider = mel.eval('$tmpVar=$gPlayBackSlider')
	timeRange = []
	if cmds.timeControl(aTimeSlider, q=True, rangeVisible=True):
		timeRange = cmds.timeControl(aTimeSlider, q=True, rangeArray=True)
	else:
		timeRange += 2 * [cmds.currentTime(q=True)]
	
	timeRange = tuple(timeRange)
		
	with pm.UndoChunk():
		for o in pm.ls(sl=True):
			for k in sorted(list(set(pm.keyframe(o, q=True, timeChange=True, time=timeRange)))):
				pm.copyKey(o, time=(k,k))
				pm.pasteKey(o, time=(k,k), timeOffset=offset, option='merge')
			
copy_paste_offset()