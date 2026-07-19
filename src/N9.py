# N9: CreateAnnotation
# Input :
#   IN[0] = N8 output (FamilySymbol ElementId or List<ElementId>)
#   IN[1] = N7 output (Dynamo Point or List<Point>)
#   IN[2] = N6 output (Dynamo Vector or List<Vector>)
#   IN[3] = N3 output (widthValue_mm or List<double>)
# Output:
#   OUT[0] = FamilyInstance (annotation) or List<FamilyInstance>
#   OUT[1] = Log
#
# Tạo line-based Detail Component. Length tự động từ Line (không set parameter).

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


def create_annotation(family_symbol, location_pt, wall_dir_vec, width_mm):
    """Tạo 1 annotation. Trả về (FamilyInstance, error_str)."""
    if family_symbol is None:
        return None, "FamilySymbol is null."
    if location_pt is None:
        return None, "Location point is null."
    if wall_dir_vec is None:
        return None, "Wall direction is null."
    if width_mm is None or width_mm <= 0:
        return None, f"Invalid width: {width_mm}"

    try:
        annotation_length = width_mm + 40.0  # mm
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

        annotation = doc.Create.NewFamilyInstance(line, family_symbol, view)
        if annotation is None:
            return None, "NewFamilyInstance returned null."
        return annotation, None
    except Exception as e:
        return None, str(e)


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

results = []
errors = []

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

    anno, err = create_annotation(sym_i, pt, vec, w)
    results.append(anno)
    if err:
        errors.append(f"[{i}]: {err}")

TransactionManager.Instance.TransactionTaskDone()

if not is_list:
    results = results[0] if results else None

log_parts = []
if not is_list:
    log_parts.append(f"Created: {results.Id}" if results else "Failed")
else:
    valid = [r for r in results if r is not None]
    log_parts.append(f"Total: {count}, Created: {len(valid)}")
if errors:
    log_parts.append(f"Errors: {'; '.join(errors[:5])}")

OUT = results, "\n".join(log_parts)