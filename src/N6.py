# N6: GetWallOrientation
# Input :
#   IN[0] = N4 output (Wall or List<Wall>)
# Output:
#   OUT[0] = Dynamo Vector or List<Vector>
#   OUT[1] = Log

import clr

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager

clr.AddReference("RevitNodes")
import Revit
clr.ImportExtensions(Revit.GeometryConversion)

doc = DocumentManager.Instance.CurrentDBDocument


def get_orientation(wall):
    if wall is None:
        return None, "Wall is null."

    # Unwrap Dynamo element
    wall = UnwrapElement(wall)

    if wall is None:
        return None, "Unwrap failed."

    if not isinstance(wall, Wall):
        try:
            t = wall.GetType().Name
        except:
            t = str(type(wall))
        return None, "Input is {}, not Wall.".format(t)

    try:
        loc = wall.Location

        if loc is None:
            return None, "Wall has no Location."

        if not isinstance(loc, LocationCurve):
            return None, "Wall has no LocationCurve."

        curve = loc.Curve

        p0 = curve.GetEndPoint(0)
        p1 = curve.GetEndPoint(1)

        # IronPython không hỗ trợ XYZ - XYZ
        vec = p1.Subtract(p0)

        if vec.GetLength() == 0:
            return None, "Wall direction length = 0."

        vec = vec.Normalize()

        # Chỉ lấy hướng trên mặt phẳng XY
        vec_xy = XYZ(vec.X, vec.Y, 0)

        if vec_xy.GetLength() == 0:
            return None, "Wall direction in XY is zero."

        vec_xy = vec_xy.Normalize()

        return vec_xy.ToVector(), None

    except Exception as e:
        return None, str(e)


# -----------------------------
# Handle single/list input
# -----------------------------

raw = IN[0]

# unwrap [[list]] -> [list]
if hasattr(raw, "__iter__") and not isinstance(raw, str):
    if len(raw) > 0 and hasattr(raw[0], "__iter__") and not isinstance(raw[0], str):
        raw = raw[0]

is_list = hasattr(raw, "__iter__") and not isinstance(raw, str)

inputs = raw if is_list else [raw]

results = []
errors = []

for i, item in enumerate(inputs):
    value, err = get_orientation(item)
    results.append(value)

    if err:
        errors.append("[{}]: {}".format(i, err))

if not is_list:
    results = results[0]

# -----------------------------
# Log
# -----------------------------

log = []

if is_list:
    valid = len([x for x in results if x is not None])
    log.append("Total: {}, Valid: {}".format(len(inputs), valid))
else:
    if results is None:
        log.append("Dir: null")
    else:
        log.append("Dir: OK")

if errors:
    log.append("Errors: " + "; ".join(errors))

OUT = results, "\n".join(log)