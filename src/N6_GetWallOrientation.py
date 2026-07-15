# N6: GetWallOrientation
# Input:  1 Wall hoặc List<Wall> — output của N4
# Output: Vector (Dynamo Vector) hoặc List<Vector>, string log

import clr

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference("RevitNodes")
import Revit

clr.ImportExtensions(Revit.GeometryConversion)


def get_orientation(wall):
    if wall is None:
        return None, "Wall is null."
    # Unwrap nếu là Dynamo wrapper
    unwrapped = UnwrapElement(wall)
    if not isinstance(unwrapped, Wall):
        return (
            None,
            f"Input is {unwrapped.GetType().Name if unwrapped else 'None'}, not Wall.",
        )
    wall = unwrapped
    try:
        loc = wall.Location
        if loc is None or not isinstance(loc, LocationCurve):
            return None, "Wall has no LocationCurve."
        curve = loc.Curve
        p0 = curve.GetEndPoint(0)
        p1 = curve.GetEndPoint(1)
        vec = (p1 - p0).Normalize()
        result = XYZ(vec.X, vec.Y, 0).Normalize().ToVector()
        return result, None
    except Exception as e:
        return None, str(e)


raw = IN[0]
if hasattr(raw, "__iter__") and not isinstance(raw, str):
    if len(raw) > 0 and hasattr(raw[0], "__iter__") and not isinstance(raw[0], str):
        raw = raw[0]
is_list = hasattr(raw, "__iter__") and not isinstance(raw, str)
inputs = raw if is_list else [raw]
results = []
errors = []

for i, inp in enumerate(inputs):
    val, err = get_orientation(inp)
    results.append(val)
    if err:
        errors.append(f"[{i}]: {err}")

if not is_list:
    results = results[0]

log_parts = []
if not is_list:
    log_parts.append(f"Dir: OK" if results is not None else "Dir: null")
else:
    valid = [r for r in results if r is not None]
    log_parts.append(f"Total: {len(inputs)}, Valid: {len(valid)}")
if errors:
    log_parts.append(f"Errors: {'; '.join(errors)}")

OUT = results, "\n".join(log_parts)
