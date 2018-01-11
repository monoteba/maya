"""
### Copies all .mov files in "movies/playblasts" folder to folders in "movies" directory

### IMPORTANT!
    - Playblasted files should have a naming that is something like "Sh0010_ANI", not like "Sh_0010_ANI".
    - The first part of the name before any spaces or underscores is used for the folder for the published file.
    - Published files keep the same name as the playblasted files

### Example inside maya project folder:
    the playblast file                      is copied to                        if a file exists, an archive is made before copying
    -------------------------------------------------------------------------------------------------------------------------------
    movies/playblasts/SH0010_ANI.mov        movies/SH0010/SH0010_ANI.mov        movies/SH0010/_archive/SH0010_ANI_v001.mov
    movies/playblasts/SH0020_ANI.mov        movies/SH0020/SH0020_ANI.mov        movies/SH0020/_archive/SH0020_ANI_v001.mov  
"""

import pymel.core as pm
import glob
import os
import sys
import re
from shutil import copyfile

def playblast_publish():
    answer = pm.confirmDialog(
        title="Publish playblasted movies", 
        message="Copy all files in playblasts folder to corresponding subfolders?", 
        button=["OK", "Cancel"], 
        defaultButton="OK", 
        cancelButton="Cancel", 
        dismissString="Cancel"
        )

    if answer == "Cancel":
        return

    # move to movie folder in current maya project
    movie_dir = pm.workspace(q=True, rootDirectory=True) + pm.workspace.fileRules['movie']
    movie_dir.replace('\\', '/')
    playblast_dir = movie_dir + "/playblasts"

    os.chdir(playblast_dir)

    # get all mov files in movie directory
    source_files = []

    for f in glob.glob("*.mov"):
        source_files.append(f)
        
    source_files = sorted(source_files)

    # create subfolder based on file name
    prog = re.compile("([A-Za-z0-9])*")
    errors = []
    
    for f in source_files:
        base = os.path.splitext(f)[0]
        
        # create folder for file
        result = prog.match(base)
        pub_dir = movie_dir + "/" + result.group(0)

        if not os.path.exists(pub_dir):
            os.makedirs(pub_dir)

        pub_file = ("%s/%s") % (pub_dir, f)
        playblast_file = ("%s/%s") % (playblast_dir, f)

        is_newer = os.path.getmtime(playblast_file) > os.path.getmtime(pub_file)

        # create version in _archive and playblast file is newer
        if os.path.exists(pub_file) and is_newer:
            archive_dir = pub_dir + "/_archive"
            if not os.path.exists(archive_dir):
                os.makedirs(archive_dir)
                
            version = 1
            version_path = ""

            while (True):
                version_path = ("%s/_archive/%s_v%03d.mov") % (pub_dir, base, version)
                if not os.path.exists(version_path):
                    break
                version = version + 1

            copyfile(pub_file, version_path)

        # copy from movie_dir to subfolder if newer
        
        if is_newer:
            try:
                copyfile(playblast_file, pub_file)
            except:
                errors.append(pub_file)
            print("# Copied %s" % (playblast_file))
            print("# --> %s" % (pub_file))
        
    if errors:
        print('\n\n# Failed to copy to the following files:')
        for error in errors:
            print('# %s' % (error))
        pm.warning('Some files were not copied! See script editor for details.')
    else:
        sys.stdout.write('\n\n# Successfully copied all files!\n')


playblast_publish()
