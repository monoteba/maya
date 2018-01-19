"""
Opens the Resource Browser in Maya (to find what icons are available inside Maya)
"""

import maya.app.general.resourceBrowser as resourceBrowser
resBrowser = resourceBrowser.resourceBrowser()
path = resBrowser.run()
