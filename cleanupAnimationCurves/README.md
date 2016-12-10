# Cleanup Animation Curves

### Description

Finds consecutive identical keys are removes the superflous ones. Currently works best on tangents set to auto, linear or stepped.

_Note: Does currently **not** take tangent direction into consideration._

### Instructions

1. Copy the script to Maya's script folder.
2. Enter the following python command

    ``` python 
    import cleanupAnimationCurves as cac
    cac.cleanupCurves(False, 0.001)
    ```


``` python 
cleanupCurves(stepped=False, tolerance=0.001)
```