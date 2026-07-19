# N4: GetHostWall
# Input :
#   IN[0] = N1 output (Element or List<Element>)
# Output:
#   OUT[0] = Wall (host wall) or List<Wall>
#   OUT[1] = Log

import clr

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager

doc = DocumentManager.Instance.CurrentDBDocument


def get_host_wall(el):
    if el is None:
        return None, "Element is null."
    try:
        host = el.Host
        if host is None:
            return None, "Unhosted element."
        host_el = doc.GetElement(host.Id)
        if host_el is None:
            return None, "Host element not found."
        if not isinstance(host_el, Wall):
            return None, f"Host is {host_el.GetType().Name}, not a Wall."
        return host_el, None
    except Exception as e:
        return None, str(e)


raw = IN[0]
if hasattr(raw, "__iter__") and not isinstance(raw, str):
    if len(raw) > 0 and hasattr(raw[0], "__iter__") and not isinstance(raw[0], str):
        raw = raw[0]
is_list = hasattr(raw, "__iter__") and not isinstance(raw, str)
inputs = raw if is_list else [raw]
results = []
errors = []

for i, inp in enumerate(inputs):
    el = UnwrapElement(inp)
    val, err = get_host_wall(el)
    results.append(val)
    if err:
        errors.append(f"[{i}]: {err}")

if not is_list:
    results = results[0]

log_parts = []
if not is_list:
    log_parts.append(f"Host Wall: {'ID ' + str(results.Id) if results else 'null'}")
else:
    valid = [r for r in results if r is not None]
    log_parts.append(f"Total: {len(inputs)}, Valid: {len(valid)}")
if errors:
    log_parts.append(f"Errors: {'; '.join(errors)}")

OUT = results, "\n".join(log_parts)