import pymel.core as pm
from random import randint


def offsetKeys(offsetMin, offsetMax):
	"""
	Offsets each object in the selection progressively, meaning the first object is offset a little, the second more, and third even more. Offset is randomized between offsetMin and offsetMax.
	:param offsetMin: minimum offset
	:param offsetMax: maximum offset
	"""
	sl = pm.ls(orderedSelection=True)
	lastOffset = 0

	for o in sl:
		offset = randint(offsetMin, offsetMax) + lastOffset
		lastOffset += offset
		pm.keyframe(o, e=True, animation='objects', time=(":"), relative=True, timeChange=offset)


offsetKeys(1,6)
