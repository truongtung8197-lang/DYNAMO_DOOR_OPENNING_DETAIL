# N9Check: VerifyAnnotationPlacement
# Input :
#   IN[0] = N9 OUT[0] (FamilyInstance hoặc List<FamilyInstance>, có thể lẫn None do skip)
#   IN[1] = N1 OUT[0] (List<Element> cửa, cùng thứ tự với N9)
#   IN[2] = N4 OUT[0] (List<Wall> host, cùng thứ tự)
#   IN[3] = extra_mm mỗi bên (number, default 20) — khớp IN[4] N9
# Output:
#   OUT[0] = List<bool> (pass/fail từng phần tử, None nếu skip/null)
#   OUT[1] = List<string> (deviation: "OK" hoặc "pos +Xmm, len +Xmm, dir")
#   OUT[2] = Log
#
# Sanity check ĐỘC LẬP: đọc lại annotation (LocationCurve) và so với giá trị kỳ vọng
# lấy từ geometry cửa (BoundingBox) + wall curve. KHÔNG dùng output N7/N3/N6.

import clr

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager

doc = DocumentManager.Instance.CurrentDBDocument

MM = 304.8
POS_TOL_MM = 1.0
LEN_TOL_MM = 1.0
DIR_TOL = 0.999


def to_float_mm(v, default):
    try:
        f = float(v)
        return f if f >= 0 else default
    except (TypeError, ValueError):
        return default


def is_iter(o):
    if o is None:
        return False
    if isinstance(o, (str, ElementId)):
        return False
    return hasattr(o, "__iter__")


def as_list(o):
    if o is None:
        return []
    if is_iter(o):
        # flatten 1 level [list, log] style
        if len(o) > 0 and is_iter(o[0]):
            return list(o[0])
        return list(o)
    return [o]


def unwrap_deep(o):
    while is_iter(o):
        if len(o) > 0:
            o = o[0]
        else:
            return None
    return o


def wall_dir_xy(wall):
    """Hướng wall (XY) từ LocationCurve. Trả về (dx, dy) normalized hoặc None."""
    if wall is None:
        return None
    wall = UnwrapElement(wall)
    if not isinstance(wall, Wall):
        return None
    loc = wall.Location
    if not isinstance(loc, LocationCurve):
        return None
    c = loc.Curve
    p0, p1 = c.GetEndPoint(0), c.GetEndPoint(1)
    dx, dy = p1.X - p0.X, p1.Y - p0.Y
    m = (dx * dx + dy * dy) ** 0.5
    if m < 1e-9:
        return None
    return (dx / m, dy / m)


def expected_from_door(el, wall, extra_mm):
    """Trả về (center_xy, door_extent_mm, dir_xy) từ BoundingBox + wall curve."""
    el = UnwrapElement(el)
    view = doc.ActiveView
    bb = el.get_BoundingBox(view)
    if bb is None:
        raise Exception("BoundingBox is null (element not visible in view?)")
    minx, miny = bb.Min.X, bb.Min.Y
    maxx, maxy = bb.Max.X, bb.Max.Y
    cx, cy = (minx + maxx) / 2.0, (miny + maxy) / 2.0

    d = wall_dir_xy(wall)
    if d is None:
        # fallback: đo extent theo trục X
        d = (1.0, 0.0)
    # chiếu 4 đỉnh bbox lên trục wall
    corners = [(minx, miny), (maxx, miny), (minx, maxy), (maxx, maxy)]
    projs = [cx_ * d[0] + cy_ * d[1] for cx_, cy_ in corners]
    door_extent_mm = (max(projs) - min(projs)) * MM

    return (cx, cy), door_extent_mm, d


def read_annotation(anno):
    """Trả về (mid_xy, len_mm, dir_xy) từ LocationCurve của annotation."""
    anno = UnwrapElement(anno)
    loc = anno.Location
    if not isinstance(loc, LocationCurve):
        raise Exception("Annotation has no LocationCurve")
    c = loc.Curve
    mid = c.Evaluate(0.5, True)
    sp, ep = c.GetEndPoint(0), c.GetEndPoint(1)
    dx, dy = ep.X - sp.X, ep.Y - sp.Y
    m = (dx * dx + dy * dy) ** 0.5
    if m < 1e-9:
        raise Exception("Annotation length = 0")
    return (mid.X, mid.Y), c.Length * MM, (dx / m, dy / m)


def dir_diff(a, b):
    # abs dot, bất kể chiều
    return abs(a[0] * b[0] + a[1] * b[1])


# --- INPUT ---
annos_raw = as_list(IN[0])
doors_raw = as_list(IN[1])
walls_raw = as_list(IN[2])
extra_mm = to_float_mm(IN[3] if len(IN) > 3 else None, 20.0)

annos = [unwrap_deep(a) for a in annos_raw]
doors = [unwrap_deep(d) for d in doors_raw]
walls = [unwrap_deep(w) for w in walls_raw]

count = max(len(annos), len(doors))
passes = []
deviations = []
errors = []

for i in range(count):
    anno = annos[i] if i < len(annos) else None
    door = doors[i] if i < len(doors) else None
    wall = walls[i] if i < len(walls) else None

    if anno is None:
        passes.append(None)
        deviations.append("Skipped (no annotation)")
        continue

    try:
        mid_a, len_a, dir_a = read_annotation(anno)
        (cx, cy), extent_mm, dir_e = expected_from_door(door, wall, extra_mm)
    except Exception as e:
        passes.append(False)
        deviations.append("ERR: {}".format(e))
        errors.append("[{}]: {}".format(i, e))
        continue

    pos_err = (((mid_a[0] - cx) ** 2 + (mid_a[1] - cy) ** 2) ** 0.5) * MM
    len_err = len_a - (extent_mm + 2.0 * extra_mm)
    dir_ok = dir_diff(dir_a, dir_e) > DIR_TOL

    parts = []
    if pos_err > POS_TOL_MM:
        parts.append("pos +{:.2f}mm".format(pos_err))
    if abs(len_err) > LEN_TOL_MM:
        parts.append("len {:+.2f}mm".format(len_err))
    if not dir_ok:
        parts.append("dir")

    ok = (pos_err <= POS_TOL_MM) and (abs(len_err) <= LEN_TOL_MM) and dir_ok
    passes.append(ok)
    deviations.append("OK" if ok else ", ".join(parts))

valid = [p for p in passes if p is True]
failed = [p for p in passes if p is False]

log_parts = []
log_parts.append("Total: {}, Pass: {}, Fail: {}, Skipped: {}".format(
    count, len(valid), len(failed), count - len(valid) - len(failed)))
if errors:
    log_parts.append("Errors: {}".format("; ".join(errors[:5])))

OUT = passes, deviations, "\n".join(log_parts)
