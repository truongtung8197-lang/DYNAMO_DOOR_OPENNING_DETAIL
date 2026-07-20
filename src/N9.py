# N9: CreateAnnotation
# Input :
#   IN[0] = N8 output (FamilySymbol ElementId or List<ElementId>)
#   IN[1] = N7 output (Dynamo Point or List<Point>)
#   IN[2] = N6 output (Dynamo Vector or List<Vector>)
#   IN[3] = N3 output (widthValue_mm or List<double>)
#   IN[4] = Extra mm each side (optional — default 20.0)
# Output:
#   OUT[0] = FamilyInstance (annotation) or List<FamilyInstance>
#   OUT[1] = Log
#
# Tạo line-based Detail Component. Length tự động từ Line (không set parameter).
# annotation_length = width_mm + 2 * extra_each_mm

import clr

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

clr.AddReference("RevitNodes")
import Revit

clr.ImportExtensions(Revit.GeometryConversion)

doc = DocumentManager.Instance.CurrentDBDocument


TOL_MM = 1.0  # tolerance khoảng cách midpoint (mm)


def _mid_key(type_id, mid, dx, dy):
    # Chuẩn hóa hướng: đảo dấu nếu dx<0 (hoặc dx==0 và dy<0) để line 2 chiều
    # (dx,dy) và (-dx,-dy) cho cùng 1 key
    if dx < 0 or (dx == 0 and dy < 0):
        dx, dy = -dx, -dy
    return (type_id, round(mid.X, 4), round(mid.Y, 4),
            round(dx, 4), round(dy, 4))


def existing_annotations(view, symbols):
    """Scan ActiveView cho các FamilyInstance cùng FamilySymbol sắp tạo.
    Trả về set của key (TypeId, mid_x, mid_y, dirx, diry)."""
    out = set()
    ids = set(s.Id for s in symbols if s is not None)
    if not ids or view is None:
        return out
    try:
        coll = FilteredElementCollector(doc, view.Id).OfClass(FamilyInstance)
    except Exception:
        return out
    for fi in coll:
        try:
            if fi.Symbol.Id not in ids:
                continue
            loc = fi.Location
            if not isinstance(loc, LocationCurve):
                continue
            c = loc.Curve
            mid = c.Evaluate(0.5, True)
            sp, ep = c.GetEndPoint(0), c.GetEndPoint(1)
            dx, dy = ep.X - sp.X, ep.Y - sp.Y
            out.add(_mid_key(fi.Symbol.Id, mid, dx, dy))
        except Exception:
            continue
    return out


def create_annotation(family_symbol, location_pt, wall_dir_vec, width_mm, extra_each_mm):
    """Tạo 1 annotation. Trả về (FamilyInstance, error_str, dup_key)."""
    dup_key = None
    if family_symbol is None:
        return None, "FamilySymbol is null.", dup_key
    if location_pt is None:
        return None, "Location point is null.", dup_key
    if wall_dir_vec is None:
        return None, "Wall direction is null.", dup_key
    if width_mm is None or width_mm <= 0:
        return None, f"Invalid width: {width_mm}", dup_key

    try:
        annotation_length = width_mm + 2.0 * extra_each_mm  # mm
        half = annotation_length / 2.0 / 304.8  # feet

        view = doc.ActiveView
        elev = view.GenLevel.Elevation if view.GenLevel else 0.0

        # Convert Dynamo Point/Vector → Revit XYZ bằng cách copy tọa độ
        center_xyz = location_pt.ToXyz()
        dir_xyz = wall_dir_vec.ToXyz()

        # Tính 2 điểm đầu/cuối thủ công để tránh lỗi operator overload
        sp = XYZ(
            center_xyz.X - dir_xyz.X * half,
            center_xyz.Y - dir_xyz.Y * half,
            elev
        )
        ep = XYZ(
            center_xyz.X + dir_xyz.X * half,
            center_xyz.Y + dir_xyz.Y * half,
            elev
        )
        line = Line.CreateBound(sp, ep)

        # Khóa duplicate: TypeId + midpoint + direction
        dx = ep.X - sp.X
        dy = ep.Y - sp.Y
        dup_key = _mid_key(family_symbol.Id, center_xyz, dx, dy)

        annotation = doc.Create.NewFamilyInstance(line, family_symbol, view)
        if annotation is None:
            return None, "NewFamilyInstance returned null.", dup_key
        return annotation, None, dup_key
    except Exception as e:
        return None, str(e), dup_key


def is_iterable_list(obj):
    """Check if obj is a list/tuple (not FamilySymbol, not str, not ElementId)."""
    if obj is None:
        return False
    if isinstance(obj, (FamilySymbol, ElementId, str)):
        return False
    return hasattr(obj, "__iter__")


def unwrap_deep(obj):
    """Unwrap nested lists đến khi ra object thực tế."""
    if obj is None:
        return None
    if isinstance(obj, (FamilySymbol, ElementId, str)):
        return obj
    while hasattr(obj, "__iter__"):
        if len(obj) > 0:
            obj = obj[0]
            if isinstance(obj, (FamilySymbol, ElementId, str)):
                return obj
        else:
            return None
    return obj


# --- INPUT ---
raw_sym = IN[0]

# IN[4] = extra mm each side (optional, default 20.0)
try:
    raw_extra = IN[4]
except IndexError:
    raw_extra = None


def to_float_mm(v):
    if v is None:
        return 20.0
    try:
        f = float(v)
    except (TypeError, ValueError):
        return 20.0
    return f if f >= 0 else 20.0


EXTRA_MM = to_float_mm(raw_extra)

# N8 output là [list_ElementId, log_string] → extract list_ElementId
if is_iterable_list(raw_sym):
    if len(raw_sym) > 0:
        first = raw_sym[0]
        if is_iterable_list(first):
            raw_sym = first
        elif isinstance(first, str):
            for item in raw_sym:
                if isinstance(item, ElementId) or is_iterable_list(item):
                    raw_sym = item
                    break
            else:
                raw_sym = None

# Convert sang list of FamilySymbol
family_symbols = []
if isinstance(raw_sym, ElementId):
    family_symbols = [doc.GetElement(raw_sym)]
elif is_iterable_list(raw_sym):
    for item in raw_sym:
        # Unwrap nested lists đến khi ra ElementId
        while is_iterable_list(item):
            if len(item) > 0:
                item = item[0]
            else:
                item = None
                break
        if isinstance(item, ElementId):
            family_symbols.append(doc.GetElement(item))
        else:
            family_symbols.append(UnwrapElement(item))
else:
    family_symbols = [UnwrapElement(raw_sym)]


# Helper: unwrap N1-style output [list, log]
def unwrap_n1_output(raw):
    if is_iterable_list(raw):
        if len(raw) > 0 and is_iterable_list(raw[0]):
            return raw[0]
    return raw


raw_pt = unwrap_n1_output(IN[1])
raw_vec = unwrap_n1_output(IN[2])
raw_width = unwrap_n1_output(IN[3])

is_list_pt = is_iterable_list(raw_pt)
pts = raw_pt if is_list_pt else [raw_pt]

is_list_vec = is_iterable_list(raw_vec)
vecs = raw_vec if is_list_vec else [raw_vec]

is_list_w = is_iterable_list(raw_width)
widths = raw_width if is_list_w else [raw_width]

is_list = is_list_pt or is_list_vec or is_list_w
count = max(len(pts), len(vecs), len(widths))

# Scan existing annotations trong Active View để skip duplicate
existing = existing_annotations(doc.ActiveView, family_symbols)

results = []
errors = []
skipped = 0

TransactionManager.Instance.EnsureInTransaction(doc)

for i in range(count):
    pt = pts[i] if i < len(pts) else None
    vec = vecs[i] if i < len(vecs) else None
    w = widths[i] if i < len(widths) else None

    # Nếu width vẫn là list (từ N3), unwrap sâu
    if w is not None and is_iterable_list(w):
        while is_iterable_list(w):
            if len(w) > 0:
                w = w[0]
            else:
                w = None
                break

    # Lấy FamilySymbol cho element thứ i
    sym_i = family_symbols[i] if i < len(family_symbols) else None

    # Đảm bảo sym_i là FamilySymbol, không phải list
    if sym_i is not None:
        sym_i = unwrap_deep(sym_i)
        if isinstance(sym_i, ElementId):
            sym_i = doc.GetElement(sym_i)

    extra_i = EXTRA_MM
    if is_iterable_list(raw_extra):
        extra_i = to_float_mm(raw_extra[i]) if i < len(raw_extra) else 20.0

    if sym_i is None:
        results.append(None)
        errors.append(f"[{i}]: FamilySymbol is null.")
        continue

    # Kiểm tra duplicate bằng khóa (TypeId, midpoint, direction)
    # Tính trước dup_key mà không tạo instance
    try:
        annotation_length = w + 2.0 * extra_i  # mm
        half = annotation_length / 2.0 / 304.8
        center_xyz = pt.ToXyz()
        dir_xyz = vec.ToXyz()
        dx = dir_xyz.X * 2.0 * half
        dy = dir_xyz.Y * 2.0 * half
        dup_key = _mid_key(sym_i.Id, center_xyz, dx, dy)
    except Exception:
        dup_key = None

    if dup_key is not None and dup_key in existing:
        results.append(None)
        skipped += 1
        errors.append(f"[{i}]: Skipped (duplicate)")
        continue

    anno, err, _ = create_annotation(sym_i, pt, vec, w, extra_i)
    results.append(anno)
    if err:
        errors.append(f"[{i}]: {err}")

TransactionManager.Instance.TransactionTaskDone()

if not is_list:
    results = results[0] if results else None

log_parts = []
log_parts.append(f"Extra each side: {EXTRA_MM} mm")
if not is_list:
    log_parts.append(f"Created: {results.Id}" if results else "Failed")
else:
    valid = [r for r in results if r is not None]
    log_parts.append(f"Total: {count}, Created: {len(valid)}, Skipped: {skipped}")
if errors:
    log_parts.append(f"Errors: {'; '.join(errors[:5])}")

OUT = results, "\n".join(log_parts)