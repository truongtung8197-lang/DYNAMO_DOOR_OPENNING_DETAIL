# N3: GetWidth
# Input :
#   IN[0] = N1 output (Element or List<Element>)
# Output:
#   OUT[0] = widthValue (double, mm) or List<double>
#   OUT[1] = Log

import clr

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager

doc = DocumentManager.Instance.CurrentDBDocument


def get_width(el):
    """Lấy Width (Type parameter) từ 1 element. Trả về (value_mm, error_str)."""
    if el is None:
        return None, "Element is null."
    try:
        sym = el.Symbol
        if sym is None:
            return None, "Element has no Symbol."
        param = sym.LookupParameter("Width")
        if param is None:
            return None, "Cannot find 'Width' parameter on Symbol."
        return param.AsDouble() * 304.8, None
    except Exception as e:
        return None, str(e)


# --- INPUT ---
raw = IN[0]

# N1 output có thể là [list_elements, log] → lấy phần tử đầu
if hasattr(raw, "__iter__") and not isinstance(raw, str):
    if len(raw) > 0 and hasattr(raw[0], "__iter__") and not isinstance(raw[0], str):
        raw = raw[0]

is_list = hasattr(raw, "__iter__") and not isinstance(raw, str)
inputs = raw if is_list else [raw]
results = []
errors = []

for i, inp in enumerate(inputs):
    el = UnwrapElement(inp)
    val, err = get_width(el)
    results.append(val)
    if err:
        errors.append(f"[{i}]: {err}")

if not is_list:
    results = results[0]

# --- OUTPUT ---
log_parts = []
if not is_list:
    log_parts.append(
        f"Width: {results:.1f} mm" if results is not None else "Width: null"
    )
else:
    valid = [r for r in results if r is not None]
    log_parts.append(f"Total: {len(inputs)}, Valid: {len(valid)}")
if errors:
    log_parts.append(f"Errors: {'; '.join(errors)}")

OUT = results, "\n".join(log_parts)