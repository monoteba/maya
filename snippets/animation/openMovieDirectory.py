'''
Open the "movie" directory of the current project
'''

import pymel.core as pm
import webbrowser
import subprocess
import platform

movieDir = pm.workspace(q=True, rootDirectory=True) + pm.workspace.fileRules['movie']
movieDir.replace('\\', '/')

if platform.system() == 'Darwin':
    subprocess.call(['open', movieDir])  # MacOS
else:
    webbrowser.open(movieDir)  # Windows, Linux
    
