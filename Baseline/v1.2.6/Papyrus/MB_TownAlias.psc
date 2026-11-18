Scriptname MB_TownAlias extends ReferenceAlias
MB_TownController Property Controller Auto

Bool Function BindController()
    If Controller == None
        Controller = GetOwningQuest() as MB_TownController
    EndIf
    Return Controller != None
EndFunction
Event OnInit()
    Debug.Trace("[MoreBrats] v1.1.0 player alias initialized")
    RegisterForSingleUpdate(1.0)
EndEvent
Event OnUpdate()
    If BindController()
        Controller.RecordEvent(2)
        Controller.Transition()
    Else
        Debug.Trace("[MoreBrats] v1.1.0 player alias: main controller unresolved; retrying")
        RegisterForSingleUpdate(30.0)
    EndIf
EndEvent
Event OnPlayerLoadGame()
    Debug.Trace("[MoreBrats] v1.1.0 player alias received OnPlayerLoadGame")
    If BindController()
        Controller.RecordEvent(3)
        Controller.Loaded()
    Else
        RegisterForSingleUpdate(1.0)
    EndIf
EndEvent
Event OnCellLoad()
    If BindController()
        Controller.RecordEvent(4)
        Controller.Transition()
    Else
        RegisterForSingleUpdate(1.0)
    EndIf
EndEvent
Event OnLocationChange(Location oldLocation, Location newLocation)
    If BindController()
        Controller.RecordEvent(5)
        Controller.Transition()
    Else
        RegisterForSingleUpdate(1.0)
    EndIf
EndEvent
