# N8: GetOrCreateType
# Input:  FamilySymbol (original — từ N2), wallThickness_mm (double hoặc List<double> — từ N5)
# Output: ElementId (FamilySymbol) hoặc List<ElementId>, string log
#
# Width (Type parameter) của Detail = độ dày tường.
# Nếu type với Width này đã tồn tại → trả về ElementId của nó.
# Nếu chưa → duplicate, đặt tên `<Gốc>_T<wallThickness>`, set Width = wall thickness.

import clr

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument

# --- INPUT ---
raw_orig = IN[0]
if hasattr(raw_orig, "__iter__") and not isinstance(raw_orig, str):
    raw_orig = raw_orig[0] if len(raw_orig) > 0 else None
if isinstance(raw_orig, ElementId):
    orig_sym = doc.GetElement(raw_orig)
else:
    orig_sym = UnwrapElement(raw_orig)

raw_thick = IN[1]

# N5/N6/N7 output là [list_values, log_string] → extract list_values
if hasattr(raw_thick, "__iter__") and not isinstance(raw_thick, str):
    if len(raw_thick) > 0:
        first = raw_thick[0]
        # Nếu first là list → đó là [values, log]
        if hasattr(first, "__iter__") and not isinstance(first, str):
            raw_thick = first
        # Nếu first là string → đó là log, cần tìm phần tử số
        elif isinstance(first, str):
            for item in raw_thick:
                if not isinstance(item, str):
                    raw_thick = item
                    break
            else:
                raw_thick = None

is_list = hasattr(raw_thick, "__iter__") and not isinstance(raw_thick, str)
thicknesses = raw_thick if is_list else [raw_thick]

results = []
errors = []

if orig_sym is None:
    errors.append("Original FamilySymbol is null.")
    results = [None] * len(thicknesses)
else:
    cache = {}
    TransactionManager.Instance.EnsureInTransaction(doc)

    for i, t in enumerate(thicknesses):
        try:
            wt = float(t)
            if wt <= 0:
                errors.append(f"[{i}]: Invalid thickness {wt}")
                results.append(None)
                continue

            key = round(wt, 1)
            if key in cache:
                results.append(cache[key])
                continue

            tn = f"{orig_sym.Name}_T{wt:.0f}"
            existing = None
            for sid in orig_sym.Family.GetFamilySymbolIds():
                s = doc.GetElement(sid)
                if s is not None and s.Name == tn:
                    existing = s
                    break

            if existing is not None:
                cache[key] = existing.Id
                results.append(existing.Id)
            else:
                new_sym = orig_sym.Duplicate(tn)
                if new_sym is None:
                    errors.append(f"[{i}]: Duplicate returned null.")
                    results.append(None)
                else:
                    wp = new_sym.LookupParameter("Width")
                    if wp is not None:
                        wp.Set(wt / 304.8)
                    cache[key] = new_sym.Id
                    results.append(new_sym.Id)
        except Exception as ex:
            errors.append(f"[{i}]: {str(ex)}")
            results.append(None)

    TransactionManager.Instance.TransactionTaskDone()

if not is_list:
    results = results[0]

log_parts = []
if not is_list:
    log_parts.append(
        f"Type: {orig_sym.Name}_T{float(raw_thick):.0f}" if results else "Type: null"
    )
else:
    valid = [r for r in results if r is not None]
    log_parts.append(f"Total: {len(thicknesses)}, Created/Found: {len(valid)}")
if errors:
    log_parts.append(f"Errors: {'; '.join(errors[:3])}")

OUT = results, "\n".join(log_parts)
