# Animation Modules

## Cleanup Curves

`(mortentoo.animation.utils)
`
### Description

Finds consecutive identical keys are removes the superflous ones. Currently works best on tangents set to auto, linear or stepped.

_Note: Does currently **not** take tangent direction into consideration._

### Usage

```python 
import mortentoo.animation.utils as too
too.cleanupCurves(stepped=False, tolerance=0.001)
```
