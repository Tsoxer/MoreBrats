Scriptname MB_Recovery extends ReferenceAlias
; Existing watchdog quest; no population or actor state belongs to this script.
MB_Controller Property Controller Auto
Bool loadedPending = True
Bool reportedMissing = False
Bool reportedStartup = False

Function WatchEvent(Int code)
    GlobalVariable marker = Game.GetFormFromFile(0x85F, "MoreBrats.esp") as GlobalVariable
    If marker != None
        marker.SetValue(code as Float)
    EndIf
EndFunction
Event OnInit()
    Debug.Trace("[MoreBrats] v1.0.0 recovery alias initialized; startup detected")
    WatchEvent(6)
    loadedPending = True
    RegisterForSingleUpdate(3.0)
EndEvent
Event OnPlayerLoadGame()
    Debug.Trace("[MoreBrats] v1.0.0 recovery alias received OnPlayerLoadGame")
    WatchEvent(7)
    loadedPending = True
    RegisterForSingleUpdate(3.0)
EndEvent
Event OnUpdate()
    RegisterForSingleUpdate(60.0)
    WatchEvent(8)
    If Controller == None
        Controller = Game.GetFormFromFile(0x800, "MoreBrats.esp") as MB_Controller
    EndIf
    If Controller == None
        If !reportedMissing
            reportedMissing = True
            Debug.Trace("[MoreBrats] v1.0.0 recovery error: controller script cast unresolved")
        EndIf
        Return
    EndIf
    reportedMissing = False
    If !Controller.IsRunning()
        Bool started = Controller.Start()
        Debug.Trace("[MoreBrats] v1.0.0 recovery quest startup requested; result=" + started)
        If !started
            Return
        EndIf
    EndIf
    If !reportedStartup
        reportedStartup = True
        Debug.Trace("[MoreBrats] v1.0.0 recovery found running controller quest")
    EndIf
    If loadedPending
        loadedPending = False
        Controller.Loaded()
    Else
        Controller.RecoveryPulse()
    EndIf
EndEvent
