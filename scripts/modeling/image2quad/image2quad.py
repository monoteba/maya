import pymel.core as pm


def image2quad(pixels_per_unit=100):
	pixels_per_unit = float(pixels_per_unit)

	filter = 'Images (*.jpg *.jpeg *.png *.gif *.tiff *tif *.bmp *.exr *.tex *.iff)'
	f = pm.fileDialog2(fileFilter=filter, fm=4, ds=2)

	if f is None:
		return

	for path in f:
		material = pm.shadingNode('lambert', asShader=True)
		sg = pm.sets(renderable=True, noSurfaceShader=True, empty=True, name=material.name() + 'SG')
		material.attr('outColor') >> sg.attr('surfaceShader')
		
		tex = pm.shadingNode('file', asTexture=True, isColorManaged=True)
		tex.attr('outColor') >> material.attr('color')
		tex.attr('outTransparency') >> material.attr('transparency')
		tex.attr('fileTextureName').set(path)

		uv = pm.shadingNode('place2dTexture', asUtility=True)
		uv.attr('outUV') >> tex.attr('uvCoord')
		uv.attr('outUvFilterSize') >> tex.attr('uvFilterSize')
		uv.attr('coverage') >> tex.attr('coverage')
		uv.attr('translateFrame') >> tex.attr('translateFrame')
		uv.attr('rotateFrame') >> tex.attr('rotateFrame')
		uv.attr('mirrorU') >> tex.attr('mirrorU')
		uv.attr('mirrorV') >> tex.attr('mirrorV')
		uv.attr('stagger') >> tex.attr('stagger')
		uv.attr('wrapU') >> tex.attr('wrapU')
		uv.attr('wrapV') >> tex.attr('wrapV')
		uv.attr('repeatUV') >> tex.attr('repeatUV')
		uv.attr('vertexUvOne') >> tex.attr('vertexUvOne')
		uv.attr('vertexUvTwo') >> tex.attr('vertexUvTwo')
		uv.attr('vertexUvThree') >> tex.attr('vertexUvThree')
		uv.attr('vertexCameraOne') >> tex.attr('vertexCameraOne')
		uv.attr('noiseUV') >> tex.attr('noiseUV')
		uv.attr('offset') >> tex.attr('offset')
		uv.attr('rotateUV') >> tex.attr('rotateUV')

		width = tex.attr('outSizeX').get() / float(pixels_per_unit)
		height = tex.attr('outSizeY').get() / float(pixels_per_unit)
		quad = pm.polyPlane(width=width, height=height, sw=1, sh=1, ch=False)

		pm.select(quad, r=True)
		pm.sets(sg, e=True, forceElement=True)


image2quad()