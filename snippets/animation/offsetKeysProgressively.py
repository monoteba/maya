import pymel.core as pm
from random import randint


def offsetKeys(offsetMin, offsetMax, moveFirst=False):
	"""
	Offsets each object in the selection progressively in selected order, meaning the first object is offset a little, the second more, and third even more. Offset is randomized between offsetMin and offsetMax.
	:param offsetMin: minimum offset
	:param offsetMax: maximum offset
	"""
	sl = pm.ls(orderedSelection=True)
	lastOffset = 0

	# remove first item
	if moveFirst is False:
		del sl[0]

	for o in sl:
		offset = randint(offsetMin, offsetMax) + lastOffset
		lastOffset = offset
		pm.keyframe(o, e=True, time=(":"), relative=True, timeChange=offset)


offsetKeys(0, 2, False) 

