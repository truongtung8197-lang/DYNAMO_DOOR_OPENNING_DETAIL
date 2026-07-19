# N8: GetOrCreateType
# Input :
#   IN[0] = N2 output (FamilySymbol)
#   IN[1] = N5 output (wallThickness_mm or List<double>)
#   IN[2] = Parameter name (string, optional — default "Width_Door")
# Output:
#   OUT[0] = ElementId or List<ElementId>
#   OUT[1] = Log
#
# Duplicate type với Width = wall thickness. Tên type mới = `<Tên gốc>_T<wallThickness>`
# Parameter name configurable qua IN[2]. Mặc định: "Width_Door"

import clr

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

clr.AddReference("RevitNodes")
import Revit

doc = DocumentManager.Instance.CurrentDBDocument

# --- CONSTANTS ---
DEFAULT_PARAM_NAME = "Width_Door"


def get_or_create_type(family_symbol, thickness_mm, param_name):
    """Duplicate type với Width = thickness_mm. Trả về (ElementId, error_str)."""
    if family_symbol is None:
        return None, "FamilySymbol is null."
    if thickness_mm is None or thickness_mm <= 0:
        return None, "Invalid thickness: {} mm".format(thickness_mm)
    
    try:
        # Unwrap FamilySymbol nếu cần
        fam_sym = UnwrapElement(family_symbol)
        if not isinstance(fam_sym, FamilySymbol):
            return None, "Input is {}, not FamilySymbol.".format(type(fam_sym).__name__)
        
        # Lấy tên type gốc
        orig_name = fam_sym.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
        if orig_name is None:
            orig_name = "Unknown"
        
        # Tên type mới
        new_name = "{}_T{:.0f}".format(orig_name, thickness_mm)
        
        # Kiểm tra xem type đã tồn tại chưa
        family = fam_sym.Family
        existing_symbol = None
        for sym_id in family.GetFamilySymbolIds():
            sym = doc.GetElement(sym_id)
            if sym.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString() == new_name:
                existing_symbol = sym
                break
        
        if existing_symbol is not None:
            # Type đã tồn tại, trả về luôn
            return existing_symbol.Id, None
        
        # Duplicate type mới
        new_symbol = fam_sym.Duplicate(new_name)
        if new_symbol is None:
            return None, "Duplicate() returned null."
        
        # Set Width parameter (mm → feet)
        width_param = new_symbol.LookupParameter(param_name)
        if width_param is None:
            return None, "Cannot find '{}' parameter on new type.".format(param_name)
        
        width_param.Set(thickness_mm / 304.8)
        
        return new_symbol.Id, None
        
    except Exception as e:
        return None, str(e)


# --- INPUT ---
raw_symbol = IN[0]
raw_thickness = IN[1]

# IN[2] = parameter name (configurable), mặc định "Width_Door"
try:
    raw_param_name = IN[2]
except IndexError:
    raw_param_name = None

if raw_param_name is None or not isinstance(raw_param_name, str) or raw_param_name.strip() == "":
    param_name = DEFAULT_PARAM_NAME
else:
    param_name = raw_param_name.strip()

# Unwrap N2 output: N2 trả về (FamilySymbol, location, log)
# Nếu là tuple/list 3 phần tử, lấy phần tử đầu (FamilySymbol)
if isinstance(raw_symbol, (list, tuple)):
    if len(raw_symbol) >= 1:
        raw_symbol = raw_symbol[0]

# N5 output có thể là [list, log] → extract list
if isinstance(raw_thickness, (list, tuple)):
    if len(raw_thickness) > 0 and isinstance(raw_thickness[0], (list, tuple)):
        raw_thickness = raw_thickness[0]

# Đảm bảo thicknesses là list
if isinstance(raw_thickness, (list, tuple)):
    thicknesses = list(raw_thickness)
    is_list_thick = True
elif isinstance(raw_thickness, (int, float)):
    thicknesses = [raw_thickness]
    is_list_thick = False
else:
    thicknesses = [raw_thickness]
    is_list_thick = False

# Lấy FamilySymbol từ raw_symbol (bỏ qua batch vì N2 chỉ có 1 symbol)
if isinstance(raw_symbol, (list, tuple)):
    # Unwrap nested list nếu cần
    temp = raw_symbol
    while isinstance(temp, (list, tuple)):
        if len(temp) > 0:
            temp = temp[0]
        else:
            temp = None
            break
    base_symbol = temp
elif isinstance(raw_symbol, FamilySymbol):
    base_symbol = raw_symbol
else:
    base_symbol = raw_symbol

# Dùng 1 symbol cho tất cả các thickness
symbol = UnwrapElement(base_symbol)

# is_list: true nếu thicknesses > 1
is_list = len(thicknesses) > 1
count = len(thicknesses)

results = []
errors = []

TransactionManager.Instance.EnsureInTransaction(doc)

for i in range(count):
    thick = thicknesses[i]
    type_id, err = get_or_create_type(symbol, thick, param_name)
    results.append(type_id)
    if err:
        errors.append("[{}]: {}".format(i, err))

TransactionManager.Instance.TransactionTaskDone()

if not is_list:
    if results and len(results) > 0:
        results = results[0]
    else:
        results = None

# --- OUTPUT ---
log_parts = []
if not is_list:
    if results is not None:
        log_parts.append("Type ID: {}".format(results.IntegerValue))
    else:
        log_parts.append("Failed to create type.")
else:
    valid = [r for r in results if r is not None]
    log_parts.append("Total: {}, Created: {}".format(count, len(valid)))
if errors:
    log_parts.append("Errors: {}".format("; ".join(errors[:5])))

OUT = results, "\n".join(log_parts)