# N10: SanityCheck
# Input:  Annotation (FamilyInstance hoặc List<FamilyInstance> — từ N9),
#         widthValue_mm (từ N3), wallThickness_mm (từ N5)
# Output: bool (Pass/Fail) hoặc List<bool>, string log
#
# Kiểm tra độc lập: đo Width (Type) và Length (hình học) của annotation.

import clr

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager

doc = DocumentManager.Instance.CurrentDBDocument


def check_annotation(annotation, expected_width, expected_length):
    """Kiểm tra 1 annotation. Trả về (passed: bool, detail: str)."""
    if annotation is None:
        return False, "Annotation is null."
    try:
        # Check 1: Width (Type) = wall thickness
        sym = annotation.Symbol
        if sym is None:
            return False, "Annotation has no Symbol."
        width_param = sym.LookupParameter("Width")
        if width_param is None:
            return False, "Cannot find 'Width' (Type) parameter."
        actual_width_mm = width_param.AsDouble() * 304.8
        if abs(actual_width_mm - expected_width) > 1.0:
            return (
                False,
                f"Width mismatch: expected {expected_width:.1f}, got {actual_width_mm:.1f}",
            )

        # Check 2: Length (hình học) = width cửa + 40mm
        loc = annotation.Location
        if loc is None:
            return False, "Annotation has no Location."
        if not isinstance(loc, LocationCurve):
            return False, f"Location is {loc.GetType().Name}, not LocationCurve."
        actual_length_mm = loc.Curve.Length * 304.8
        if abs(actual_length_mm - expected_length) > 1.0:
            return (
                False,
                f"Length mismatch: expected {expected_length:.1f}, got {actual_length_mm:.1f}",
            )

        return True, "OK"
    except Exception as e:
        return False, f"Error: {str(e)}"


def unwrap_deep(obj):
    """Unwrap nested lists đến khi ra object thực tế."""
    if obj is None:
        return None
    while hasattr(obj, "__iter__") and not isinstance(obj, str):
        if len(obj) > 0:
            obj = obj[0]
        else:
            return None
    return obj


def extract_list_from_output(raw):
    """Extract list từ output [list, log_string] của các node."""
    if raw is None:
        return []
    # Nếu là list, lấy phần tử đầu tiên là list
    if hasattr(raw, "__iter__") and not isinstance(raw, str):
        if len(raw) > 0:
            first = raw[0]
            # Nếu first là list → đó là list values
            if hasattr(first, "__iter__") and not isinstance(first, str):
                return first
            # Nếu first là string → log, tìm phần tử là list
            elif isinstance(first, str):
                for item in raw:
                    if hasattr(item, "__iter__") and not isinstance(item, str):
                        return item
    # Nếu là list đơn thuần
    if hasattr(raw, "__iter__") and not isinstance(raw, str):
        return raw
    # Nếu là single value
    return [raw]


# --- INPUT ---
raw_anno = extract_list_from_output(IN[0])
annos = [unwrap_deep(a) for a in raw_anno] if raw_anno else []

raw_width = extract_list_from_output(IN[1])
widths = [unwrap_deep(w) for w in raw_width] if raw_width else []

raw_thickness = extract_list_from_output(IN[2])
thicknesses = [unwrap_deep(t) for t in raw_thickness] if raw_thickness else []

is_list = len(annos) > 1 or len(widths) > 1 or len(thicknesses) > 1
count = max(len(annos), len(widths), len(thicknesses))

results = []
errors = []

for i in range(count):
    anno = annos[i] if i < len(annos) else None
    w = widths[i] if i < len(widths) else None
    t = thicknesses[i] if i < len(thicknesses) else None

    if anno is None:
        results.append(False)
        errors.append(f"[{i}]: Annotation is null.")
        continue
    if w is None or w <= 0:
        results.append(False)
        errors.append(f"[{i}]: Invalid width.")
        continue
    if t is None or t <= 0:
        results.append(False)
        errors.append(f"[{i}]: Invalid thickness.")
        continue

    expected_length = w + 40.0
    passed, detail = check_annotation(anno, t, expected_length)
    results.append(passed)
    if not passed:
        errors.append(f"[{i}]: {detail}")

if not is_list:
    results = results[0] if results else False

log_parts = []
if not is_list:
    log_parts.append("PASSED" if results else "FAILED")
else:
    passed_count = sum(1 for r in results if r)
    log_parts.append(f"Total: {count}, Passed: {passed_count}, Failed: {len(errors)}")
if errors:
    log_parts.append(f"Errors: {'; '.join(errors[:5])}")

OUT = results, "\n".join(log_parts)
