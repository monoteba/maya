import math
import pymel.core as pm
import maya.OpenMaya as OpenMaya
import maya.OpenMayaUI as OpenMayaUI


deg2rad = math.pi / 180.0


def scale_to_camera_frustrum():
	cam = get_camera()
	fov_w = cam.getHorizontalFieldOfView()
	
	objs = pm.ls(sl=True)
	for obj in objs:
		bb = pm.exactWorldBoundingBox(obj, calculateExactly=True)
		z_dist = abs(obj.translateZ.get() - cam.getTransform().translateZ.get())

		frustrum_w = 2.0 * z_dist * math.tan(fov_w * 0.5 * deg2rad)
		# frustrum_h = frustrum_w / cam.getAspectRatio()

		obj_w = abs(bb[0] - bb[3])  # x
		# obj_h = abs(bb[1] - bb[4])  # y
		
		scale_x = obj.scaleX.get() * (frustrum_w / obj_w)
		# scale_y = obj.scaleY.get() * (frustrum_h / obj_h)

		obj.scaleX.set(scale_x)
		obj.scaleY.set(scale_x)

	
def get_camera():
	view = OpenMayaUI.M3dView.active3dView()
	cam = OpenMaya.MDagPath()
	view.getCamera(cam)
	camPath = cam.fullPathName()
	return pm.PyNode(camPath)

	
scale_to_camera_frustrum()