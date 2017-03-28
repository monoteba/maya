# Animation Modules

## Functions

- `cleanupCurves(*args)`
- `graphEditorFramePlaybackRange()`



## Cleanup Curves

`(mtoo.animation.utils)`

### Description

Finds consecutive identical keys on selected objects and removes the superflous ones. Currently works best on tangents set to auto, linear or stepped.

_Note: Does currently **not** take tangent direction into consideration._

### Usage

```python 
import mtoo.animation.utils as mtoo
mtoo.cleanupCurves(stepped=False, keepLast=True, tolerance=0.001)
```


##### stepped `=False`
Remove all consecutive identical keys. If `False` it will only remove identical keys in between two matches.

##### keepLast `=True`
Will keep the last keyframe even if it is identical to the previous.

##### tolerance `=0.001`
If the difference between two keys is less than the tolerance, they will be removed.



## Graph Editor: Frame Playback Range
Simple command that does the same as _View > Frame > Frame Playback Range_ in the _Graph Editor_, but can be assigned to a hotkey.

### Usage

```python 
import mtoo.animation.utils as mtoo
mtoo.graphEditorFramePlaybackRange()
```
