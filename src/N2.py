# N2: PickDetailComponent
# Input :
#   IN[0] = Detail Component instance (select in model)
# Output:
#   OUT[0] = FamilySymbol
#   OUT[1] = Dynamo Point (Location)
#   OUT[2] = Log

import clr

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager

clr.AddReference("RevitNodes")
import Revit
clr.ImportExtensions(Revit.GeometryConversion)

doc = DocumentManager.Instance.CurrentDBDocument

# ------------------------------------------------------
# Input
# ------------------------------------------------------

element = UnwrapElement(IN[0])

family_symbol = None
location = None
errors = []

# ------------------------------------------------------
# Check input
# ------------------------------------------------------

if element is None:
    errors.append("Input is null.")

else:

    try:
        # Lấy FamilySymbol bằng GetTypeId() (ổn định hơn .Symbol)
        type_id = element.GetTypeId()

        if type_id == ElementId.InvalidElementId:
            errors.append("Element has no valid TypeId.")
        else:
            family_symbol = doc.GetElement(type_id)

            if not isinstance(family_symbol, FamilySymbol):
                errors.append(
                    "Type is {}, not FamilySymbol.".format(
                        family_symbol.GetType().Name
                    )
                )

    except Exception as ex:
        errors.append("Cannot get FamilySymbol: {}".format(ex))

    # --------------------------------------------------
    # Location
    # --------------------------------------------------

    try:

        loc = element.Location

        if loc is None:

            errors.append("Element has no Location.")

        elif isinstance(loc, LocationPoint):

            location = loc.Point.ToPoint()

        elif isinstance(loc, LocationCurve):

            curve = loc.Curve

            mid = curve.Evaluate(0.5, True)

            location = mid.ToPoint()

        else:

            errors.append(
                "Unsupported Location type: {}".format(
                    loc.GetType().Name
                )
            )

    except Exception as ex:

        errors.append("Cannot get Location: {}".format(ex))

# ------------------------------------------------------
# Log
# ------------------------------------------------------

log = []

if family_symbol is not None:

    try:
        fam_name = family_symbol.Family.Name
    except:
        fam_name = "<Unknown Family>"

    try:
        type_name = family_symbol.get_Parameter(
            BuiltInParameter.SYMBOL_NAME_PARAM
        ).AsString()
    except:
        type_name = "<Unknown Type>"

    log.append(
        "Family: {} | Type: {}".format(
            fam_name,
            type_name
        )
    )

if location is not None:

    log.append(
        "Location: ({:.1f}, {:.1f}, {:.1f})".format(
            location.X,
            location.Y,
            location.Z
        )
    )

if errors:

    log.append("Errors: " + "; ".join(errors))

OUT = family_symbol, location, "\n".join(log)