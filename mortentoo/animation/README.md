# Animation Modules

## Cleanup Curves

`(mortentoo.animation.utils)`

### Description

Finds consecutive identical keys are removes the superflous ones. Currently works best on tangents set to auto, linear or stepped.

_Note: Does currently **not** take tangent direction into consideration._

### Usage

```python 
import mortentoo.animation.utils as too
too.cleanupCurves(stepped=False, keepLast=True, tolerance=0.001)
```


#### stepped `=False`
Remove all consecutive identical keys. If `False` it will only remove identical keys in between two matches.

#### keepLast `=True`
(Only valid with `stepped=True`). Will keep the last keyframe even if it is identical to the previous.

#### tolerance `=0.001`
If the difference between two keys is less than the tolerance, they will be removed.
