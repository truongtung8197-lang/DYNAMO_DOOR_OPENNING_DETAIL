# N2: PickDetailComponent
# Input:  1 Detail Component instance (FamilyInstance) được chọn từ model
# Output: FamilySymbol (để dùng cho placement), Point (location), string log
#
# Trích xuất FamilySymbol và Location Point từ 1 Detail Component instance.
# Detail Component là annotation element trong model.

import clr

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager

clr.AddReference("RevitNodes")
import Revit

clr.ImportExtensions(Revit.GeometryConversion)

doc = DocumentManager.Instance.CurrentDBDocument

# --- INPUT ---
detail_instance = UnwrapElement(IN[0])

# --- XỬ LÝ ---
errors = []
family_symbol = None
location_point = None

if detail_instance is None:
    errors.append("Input is null. Please select a Detail Component instance.")
elif not isinstance(detail_instance, FamilyInstance):
    errors.append(
        f"Input is {detail_instance.GetType().Name}, not a FamilyInstance. "
        "Please select a Detail Component instance."
    )
else:
    try:
        # Lấy FamilySymbol
        family_symbol = detail_instance.Symbol  # FamilySymbol
        symbol_name = family_symbol.Name if family_symbol else "null"
    except Exception as e:
        errors.append(f"Cannot get FamilySymbol: {str(e)}")

    try:
        # Lấy Location — có thể là LocationPoint hoặc LocationCurve
        loc = detail_instance.Location
        if loc is None:
            errors.append("Element has no Location.")
        elif isinstance(loc, LocationPoint):
            location_point = loc.Point.ToPoint()
        elif isinstance(loc, LocationCurve):
            # Detail Component có LocationCurve → lấy StartPoint (gốc family)
            curve = loc.Curve
            start = curve.GetEndPoint(0)
            # Đổi sang Dynamo Point
            location_point = start.ToPoint()
        else:
            errors.append(f"Location is {loc.GetType().Name}, unexpected type.")
    except Exception as e:
        errors.append(f"Cannot get Location: {str(e)}")

# --- OUTPUT ---
log_parts = []
if family_symbol:
    log_parts.append(f"FamilySymbol: {family_symbol.FamilyName} / {symbol_name}")
if location_point:
    log_parts.append(
        f"Location: ({location_point.X}, {location_point.Y}, {location_point.Z})"
    )
if errors:
    log_parts.append(f"Errors: {'; '.join(errors)}")

OUT = family_symbol, location_point, "\n".join(log_parts)
