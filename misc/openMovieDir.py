#
# Open the "movie" directory of the current project
#

import pymel.core as pm
import webbrowser
import platform

movieDir = pm.workspace(q=True, rootDirectory=True) + pm.workspace.fileRules['movie']
movieDir.replace('\\', '/')


if platform.system() == 'darwin':
    webbrowser.open('file://' + movieDir) # MacOS
else:
    webbrowser.open(movieDir) # Windows, Linux
