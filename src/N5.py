# N5: GetWallThickness
# Input :
#   IN[0] = N4 output (Wall or List<Wall>)
# Output:
#   OUT[0] = thickness_mm (double) or List<double>
#   OUT[1] = Log
#
# Lấy độ dày tường từ WallType.Width (Revit API).

import clr

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager

doc = DocumentManager.Instance.CurrentDBDocument


def get_wall_thickness(wall):
    """Lấy wall thickness từ WallType.Width. Trả về (thickness_mm, error_str)."""
    if wall is None:
        return None, "Wall is null."
    try:
        # Unwrap wall nếu cần
        wall_el = UnwrapElement(wall)
        if not isinstance(wall_el, Wall):
            return None, f"Input is {type(wall_el).__name__}, not Wall."
        
        # Lấy WallType, từ đó lấy Width (feet)
        wall_type = wall_el.WallType
        if wall_type is None:
            return None, "Wall has no WallType."
        
        # WallType.Width trả về độ dày thực tế của tường (feet)
        thickness_ft = wall_type.Width
        
        if thickness_ft <= 0:
            return None, f"Invalid WallType.Width: {thickness_ft}"
        
        # Chuyển feet → mm
        thickness_mm = thickness_ft * 304.8
        
        return thickness_mm, None
    except Exception as e:
        return None, str(e)


# --- INPUT ---
raw = IN[0]

# N4 output có thể là [list, log] → extract list
if hasattr(raw, "__iter__") and not isinstance(raw, str):
    if len(raw) > 0 and hasattr(raw[0], "__iter__") and not isinstance(raw[0], str):
        raw = raw[0]

is_list = hasattr(raw, "__iter__") and not isinstance(raw, str)
inputs = raw if is_list else [raw]
results = []
errors = []

for i, inp in enumerate(inputs):
    wall = UnwrapElement(inp)
    val, err = get_wall_thickness(wall)
    results.append(val)
    if err:
        errors.append(f"[{i}]: {err}")

if not is_list:
    results = results[0]

# --- OUTPUT ---
log_parts = []
if not is_list:
    log_parts.append(f"Thickness: {results:.1f} mm" if results is not None else "Thickness: null")
else:
    valid = [r for r in results if r is not None]
    log_parts.append(f"Total: {len(inputs)}, Valid: {len(valid)}")
if errors:
    log_parts.append(f"Errors: {'; '.join(errors)}")

OUT = results, "\n".join(log_parts)