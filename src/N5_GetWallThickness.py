# N5: GetWallThickness
# Input:  1 Wall hoặc List<Wall> — output của N4
# Output: wallThickness (double, mm) hoặc List<double>, string log

import clr

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager

doc = DocumentManager.Instance.CurrentDBDocument


def get_thickness(wall):
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
        bb = wall.get_BoundingBox(None)
        if bb is None:
            return None, "Wall has no BoundingBox."
        loc = wall.Location
        if loc is None or not isinstance(loc, LocationCurve):
            return None, "Wall has no LocationCurve."
        curve = loc.Curve
        dir_vec = (curve.GetEndPoint(1) - curve.GetEndPoint(0)).Normalize()
        wall_dir_xy = XYZ(dir_vec.X, dir_vec.Y, 0).Normalize()
        perp_dir = XYZ(-wall_dir_xy.Y, wall_dir_xy.X, 0)
        minp, maxp = bb.Min, bb.Max
        corners = [
            XYZ(minp.X, minp.Y, minp.Z),
            XYZ(maxp.X, minp.Y, minp.Z),
            XYZ(minp.X, maxp.Y, minp.Z),
            XYZ(maxp.X, maxp.Y, minp.Z),
            XYZ(minp.X, minp.Y, maxp.Z),
            XYZ(maxp.X, minp.Y, maxp.Z),
            XYZ(minp.X, maxp.Y, maxp.Z),
            XYZ(maxp.X, maxp.Y, maxp.Z),
        ]
        proj = [c.DotProduct(perp_dir) for c in corners]
        val = (max(proj) - min(proj)) * 304.8
        if val <= 0:
            return None, "Invalid thickness (<= 0)."
        return val, None
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
    val, err = get_thickness(inp)
    results.append(val)
    if err:
        errors.append(f"[{i}]: {err}")

if not is_list:
    results = results[0]

log_parts = []
if not is_list:
    log_parts.append(
        f"Thickness: {results:.1f} mm" if results is not None else "Thickness: null"
    )
else:
    valid = [r for r in results if r is not None]
    log_parts.append(f"Total: {len(inputs)}, Valid: {len(valid)}")
if errors:
    log_parts.append(f"Errors: {'; '.join(errors)}")

OUT = results, "\n".join(log_parts)
