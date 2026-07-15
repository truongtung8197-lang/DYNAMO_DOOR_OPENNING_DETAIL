# N7: GetLocationPoint
# Input:  1 Element hoặc List<Element> — output của N1
# Output: Point (Dynamo Point) hoặc List<Point>, string log

import clr

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference("RevitNodes")
import Revit

clr.ImportExtensions(Revit.GeometryConversion)


def get_loc_point(el):
    if el is None:
        return None, "Element is null."
    try:
        loc = el.Location
        if loc is None:
            return None, "Element has no Location."
        if not isinstance(loc, LocationPoint):
            return None, f"Location is {loc.GetType().Name}, not LocationPoint."
        return loc.Point.ToPoint(), None
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
    el = UnwrapElement(inp)
    val, err = get_loc_point(el)
    results.append(val)
    if err:
        errors.append(f"[{i}]: {err}")

if not is_list:
    results = results[0]

log_parts = []
if not is_list:
    log_parts.append(f"Point: OK" if results is not None else "Point: null")
else:
    valid = [r for r in results if r is not None]
    log_parts.append(f"Total: {len(inputs)}, Valid: {len(valid)}")
if errors:
    log_parts.append(f"Errors: {'; '.join(errors)}")

OUT = results, "\n".join(log_parts)
