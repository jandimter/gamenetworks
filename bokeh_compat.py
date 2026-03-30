"""Compatibility helpers for older Bokeh versions on modern NumPy."""

import numpy as np


# Bokeh 2.x references `np.bool8`, which was removed in recent NumPy releases.
# Keep backward compatibility without pinning/downgrading dependencies.
if not hasattr(np, "bool8"):
    np.bool8 = np.bool_
