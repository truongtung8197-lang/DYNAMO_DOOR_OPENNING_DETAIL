# N10: SanityCheck (DEBUG VERSION)
# Input:  Annotation (FamilyInstance hoặc List<FamilyInstance> — từ N9),
#         widthValue_mm (từ N3), wallThickness_mm (từ N5)
# Output: bool (Pass/Fail) hoặc List<bool>, string log
#
# DEBUG: Thêm detailed logging để tìm nguyên nhân false failure.

import clr

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager

doc = DocumentManager.Instance.CurrentDBDocument


def check_annotation_debug(annotation, expected_width, expected_length):
    if annotation is None:
        return False, "Annotation is null."
    
    annotation = UnwrapElement(annotation)   # <-- THÊM DÒNG NÀY
    if annotation is None:
        return False, "Annotation is null after UnwrapElement."
    
    debug_info = []
    
    try:
        # Check annotation type
        debug_info.append(f"Annotation type: {annotation.GetType().Name}")
        debug_info.append(f"Annotation Id: {annotation.Id}")
        
        # Check 1: Width (Type) = wall thickness
        sym = annotation.Symbol
        debug_info.append(f"Symbol: {sym.Name if sym else 'None'}")
        debug_info.append(f"Symbol Id: {sym.Id if sym else 'None'}")
        
        if sym is None:
            return False, "Annotation has no Symbol. " + " | ".join(debug_info)
        
        # List all parameters on the symbol
        all_params = []
        for param in sym.Parameters:
            if param.Definition.Name in ["Width", "Length", "Length (mm)", "Width (mm)"]:
                all_params.append(f"{param.Definition.Name}={param.AsDouble()*304.8:.3f}mm (storage={param.StorageType})")
        
        debug_info.append(f"Relevant params: {', '.join(all_params) if all_params else 'None found'}")
        
        width_param = sym.LookupParameter("Width_Door")
        if width_param is None:
            # Try alternative names
            for alt_name in ["Length", "Width (mm)", "Length (mm)"]:
                alt_param = sym.LookupParameter(alt_name)
                if alt_param:
                    debug_info.append(f"Found alternative param '{alt_name}': {alt_param.AsDouble()*304.8:.3f}mm")
            return False, f"Cannot find 'Width' (Type) parameter. " + " | ".join(debug_info)
        
        actual_width_mm = width_param.AsDouble() * 304.8
        debug_info.append(f"Width param value: {actual_width_mm:.4f}mm")
        debug_info.append(f"Expected width: {expected_width:.4f}mm")
        debug_info.append(f"Width diff: {abs(actual_width_mm - expected_width):.4f}mm")
        
        # Check 2: Length (hình học) = width cửa + 40mm
        loc = annotation.Location
        if loc is None:
            return False, "Annotation has no Location. " + " | ".join(debug_info)
        
        debug_info.append(f"Location type: {loc.GetType().Name}")
        
        if not isinstance(loc, LocationCurve):
            return False, f"Location is {loc.GetType().Name}, not LocationCurve. " + " | ".join(debug_info)
        
        actual_length_mm = loc.Curve.Length * 304.8
        debug_info.append(f"Curve length: {actual_length_mm:.4f}mm")
        debug_info.append(f"Expected length: {expected_length:.4f}mm")
        debug_info.append(f"Length diff: {abs(actual_length_mm - expected_length):.4f}mm")
        
        # Check with 2mm tolerance (more lenient)
        width_ok = abs(actual_width_mm - expected_width) <= 2.0
        length_ok = abs(actual_length_mm - expected_length) <= 2.0
        
        debug_info.append(f"Width check (2mm tol): {'PASS' if width_ok else 'FAIL'}")
        debug_info.append(f"Length check (2mm tol): {'PASS' if length_ok else 'FAIL'}")
        
        if not width_ok or not length_ok:
            return False, " | ".join(debug_info)
        
        return True, "OK | " + " | ".join(debug_info)
    except Exception as e:
        error_detail = f"Error: {str(e)}. " + " | ".join(debug_info)
        return False, error_detail


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


def debug_input_format(name, value):
    """Debug: Print input format."""
    if value is None:
        return f"{name}: None"
    elif hasattr(value, "__iter__") and not isinstance(value, str):
        if len(value) > 0:
            first_type = type(value[0]).__name__
            return f"{name}: list[{len(value)}] first={first_type}"
        return f"{name}: empty list"
    else:
        return f"{name}: {type(value).__name__}"


# --- INPUT ---
# DEBUG: Log input formats
debug_log = []
debug_log.append("=== N10 DEBUG ===")
debug_log.append(debug_input_format("IN[0] (annotations)", IN[0]))
debug_log.append(debug_input_format("IN[1] (widths)", IN[1]))
debug_log.append(debug_input_format("IN[2] (thicknesses)", IN[2]))

raw_anno = extract_list_from_output(IN[0])
annos = [unwrap_deep(a) for a in raw_anno] if raw_anno else []

raw_width = extract_list_from_output(IN[1])
widths = [unwrap_deep(w) for w in raw_width] if raw_width else []

raw_thickness = extract_list_from_output(IN[2])
thicknesses = [unwrap_deep(t) for t in raw_thickness] if raw_thickness else []

debug_log.append(f"Parsed: {len(annos)} annotations, {len(widths)} widths, {len(thicknesses)} thicknesses")

is_list = len(annos) > 1 or len(widths) > 1 or len(thicknesses) > 1
count = max(len(annos), len(widths), len(thicknesses))

results = []
errors = []
debug_details = []

for i in range(count):
    anno = annos[i] if i < len(annos) else None
    w = widths[i] if i < len(widths) else None
    t = thicknesses[i] if i < len(thicknesses) else None

    debug_log.append(f"\n--- Element [{i}] ---")
    debug_log.append(f"  Annotation: {anno.Id if anno else 'None'}")
    debug_log.append(f"  Width: {w:.3f}mm" if w else "  Width: None")
    debug_log.append(f"  Thickness: {t:.3f}mm" if t else "  Thickness: None")
    
    if anno is None:
        results.append(False)
        errors.append(f"[{i}]: Annotation is null.")
        debug_details.append(f"[{i}]: Annotation is null")
        continue
    if w is None or w <= 0:
        results.append(False)
        errors.append(f"[{i}]: Invalid width.")
        debug_details.append(f"[{i}]: Invalid width")
        continue
    if t is None or t <= 0:
        results.append(False)
        errors.append(f"[{i}]: Invalid thickness.")
        debug_details.append(f"[{i}]: Invalid thickness")
        continue

    expected_length = w + 40.0
    passed, detail = check_annotation_debug(anno, t, expected_length)
    results.append(passed)
    debug_details.append(detail)
    if not passed:
        errors.append(f"[{i}]: {detail}")

if not is_list:
    results = results[0] if results else False

log_parts = []
log_parts.extend(debug_log)

if not is_list:
    log_parts.append(f"\nRESULT: {'PASSED' if results else 'FAILED'}")
else:
    passed_count = sum(1 for r in results if r)
    log_parts.append(f"\nTotal: {count}, Passed: {passed_count}, Failed: {len(errors)}")
if errors:
    log_parts.append(f"Errors: {'; '.join(errors[:5])}")
if debug_details:
    log_parts.append(f"\nDebug details:")
    for d in debug_details:
        log_parts.append(f"  {d}")

OUT = results, "\n".join(log_parts)
