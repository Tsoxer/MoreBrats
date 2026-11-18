Scriptname ObjectReference extends Form Hidden
Cell Function GetParentCell() Native
WorldSpace Function GetWorldSpace() Native
Bool Function IsDisabled() Native
Bool Function Is3DLoaded() Native
Bool Function IsInInterior()
    Cell currentCell = GetParentCell()
    If currentCell == None
        Return False
    EndIf
    Return currentCell.IsInterior()
EndFunction
Float Function GetDistance(ObjectReference akOther) Native
Function MoveTo(ObjectReference akTarget, Float afXOffset = 0.0, Float afYOffset = 0.0, Float afZOffset = 0.0, Bool abMatchRotation = True) Native
Function DisableNoWait(Bool abFadeOut = False) Native
Function Enable(Bool abFadeIn = False) Native
Function EnableNoWait(Bool abFadeIn = False) Native

Float Function GetPositionX() Native
Float Function GetPositionY() Native
Float Function GetPositionZ() Native

Location Function GetCurrentLocation() Native
