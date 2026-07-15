# N1: GetSelectedElements
# Input:  List<Element> từ Dynamo selection (Select Model Elements)
# Output: List<Element> (chỉ Doors & Windows), string log
#
# Lọc danh sách element được chọn, chỉ giữ lại Doors và Windows.
# Bỏ qua element null hoặc không thuộc category phù hợp.

import clr

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager

doc = DocumentManager.Instance.CurrentDBDocument

# --- INPUT ---
elements = UnwrapElement(IN[0])

# Đảm bảo elements là list
if not hasattr(elements, "__iter__"):
    elements = [elements]

# --- XỬ LÝ ---
result = []
errors = []
count_skipped = 0

for i, el in enumerate(elements):
    if el is None:
        count_skipped += 1
        continue
    try:
        cat = el.Category
        if cat is None:
            count_skipped += 1
            continue

        # So sánh BuiltInCategory trực tiếp (an toàn hơn IntegerValue)
        bic = cat.BuiltInCategory
        if bic == BuiltInCategory.OST_Doors or bic == BuiltInCategory.OST_Windows:
            result.append(el)
        else:
            count_skipped += 1
    except Exception as e:
        errors.append(f"Element #{i}: {str(e)}")
        count_skipped += 1

# --- OUTPUT ---
log_parts = []
log_parts.append(f"Total input: {len(elements)}")
log_parts.append(f"Doors+Windows found: {len(result)}")
log_parts.append(f"Skipped: {count_skipped}")
if errors:
    log_parts.append(f"Errors: {'; '.join(errors)}")

OUT = result, "\n".join(log_parts)
