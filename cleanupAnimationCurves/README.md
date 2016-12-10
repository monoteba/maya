# Cleanup Animation Curves

### Description

Finds consecutive identical keys are removes the superflous ones. Currently works best on tangents set to auto, linear or stepped.

_Note: Does currently **not** take tangent direction into consideration._

### Instructions

1. Copy the script to Maya's script folder.
2. Enter the following python command


    import cleanAnimationCurves as cac
    cac.cleanupCurves()
