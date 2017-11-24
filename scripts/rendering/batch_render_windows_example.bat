# Modify the example below to your installation and file output and input
#
# Leave out a flag to use the scene settings.
#
# Flags
# -r  Renderer (sw = software, hw = hardware, hw2 = hardware 2.0, vr = vector)
# -v  Verbose level
# -s  Start frame
# -e  End frame
# -rd Render Directory
#
# Simple example:
# "C:\Program Files\Autodesk\Maya2016\bin\Render.exe" "C:\path\to\file.ma"

"C:\Program Files\Autodesk\Maya2016\bin\Render.exe" -r sw -v 5 -s 1 -e 50 -rd "C:\path\to\output.exr" "C:\path\to\file.ma"
"C:\Program Files\Autodesk\Maya2016\bin\Render.exe" -r sw -v 5 -s 1 -e 50 -rd "C:\path\to\other\output2.exr" "C:\path\to\file2.ma"
