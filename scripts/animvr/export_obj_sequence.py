import pymel.core as pm


class ExportObjSequence:
    def __init__(self):
        self.objects = []
        self.start_frame = None
        self.end_frame = None
    
    def export(self):
        if not pm.ls(sl=True):
            pm.warning("No objects selected")
            return
        
        path = pm.fileDialog2(fileFilter="*.obj", dialogStyle=2, fileMode=0,
                              dir=pm.workspace.path)
        
        if not path:
            return
        
        path = path[0]
        
        for f in range(self.start_frame, self.end_frame + 1):
            frame_path = ('%s_%04d.obj' % (path[:-4], f))
            print frame_path
            pm.currentTime(f)
            pm.exportSelected(frame_path, force=True, options="groups=1;ptgroups=1;materials=0;smoothing=1;normals=1",
                              typ="OBJexport", preserveReferences=False, exportSelected=True)


if __name__ == '__main__':
    eos = ExportObjSequence()
    
    eos.start_frame = 1
    eos.end_frame = 72
    eos.export()
