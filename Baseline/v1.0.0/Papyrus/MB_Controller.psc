Scriptname MB_Controller extends Quest
; More Brats 0.2.5 - Tsoxer. Stable v0.1/v0.2 instance and FormID migration.
; Old properties and saved variable names/types remain for v0.1 migration.
Actor[] Property Children Auto
ObjectReference[] Property ArrivalPoints Auto
ObjectReference Property TavernPoint Auto
Cell Property TavernCell Auto
WorldSpace Property CityWorld Auto
GlobalVariable Property NightMode Auto
GlobalVariable Property DayArea Auto
FormList Property PoolForms Auto
FormList Property RoadForms Auto
FormList Property TargetForms Auto
Faction Property RoamFaction Auto
; v0.1-style direct VMAD bindings. Old FLST properties stay for saved instances.
Actor[] Property PoolRefs Auto
ObjectReference[] Property RoadRefs Auto
ObjectReference[] Property TargetRefs Auto
GlobalVariable[] Property DiagnosticGlobals Auto

Int activeIndex = -1
Int activeCycle = -100000
Int lastSpawnCycle = -100000
Bool retiring = False
Bool disablePending = False
Bool processing = False
Int hiddenSamples = 0
Float nextAreaTime = 0.0

Int schemaVersion = 0
Int todayCycle = -100000
Int dailyPopulation = 0
Actor[] pool
ObjectReference[] roads
ObjectReference[] targets
Actor[] residents
Int[] residentCycle
Int[] lastArrivalCycle
Int[] phase
Int[] destination
Int[] priorDestination
Int[] arrivalIndex
Int[] selectedVariant
Int[] hiddenCount
Int[] stallCount
Bool[] retireSlot
Bool[] disablingSlot
Bool[] safeRoads
Float[] deadline
Float[] runUntil
Float[] progressAt
Float[] lastX
Float[] lastY
Float[] lastZ

; Additive saved fields. Never change the types of fields from an older release.
Int workEpoch = 0
Bool leaseArmed = False
Float leaseStart = 0.0
Float leaseUntil = 0.0
Bool repairRequested = True
Bool announced = False
Bool setupWarning = False
Bool orphanPresent = False
Int[] orphanHidden
Float[] enableUntil
Bool bindingsPending = True
Int diagStage = 0
Int diagReason = 0
Int diagTicks = 0
Int diagResolved = 0
Int diagRoads = 0
Int[] deferredReason
Actor diagSelectedActor
ObjectReference diagSelectedPoint
; Additive diagnostics; legacy target fields retain their exact saved types.
Form[] dayPackageForms
Form[] targetRawForms
Int[] targetLookupState
Bool[] targetBoundArray
Bool[] targetBoundValue
Int diagLegacyTargets = 0
Int diagSlot = -1
Int diagGoal = -1
Int diagLookupResult = 0
Int diagExpectedID = 0
Form diagRawLookup
String diagTargetContext = ""
String diagLookupFile = "MoreBrats.esp"
; Additive diagnostics only; all earlier saved names/types are unchanged.
Bool diagStorageReady = False
String diagStorageFailure = ""
Int diagPoolInputs = 0
Int diagRoadInputs = 0

; One pending cell/location notification; saved field is additive.
Bool transitionPending = False
Int lastWorkerStage = 0

Event OnInit()
    RecordEvent(1)
    Status(1)
    Log("controller OnInit; quest running=" + IsRunning())
    Wake()
EndEvent
Function Loaded()
    ; Do not clear a saved busy flag while a suspended stack may still resume.
    repairRequested = True
    Log("load recovery/migration requested; saved schema=" + schemaVersion)
    Wake()
EndFunction
Function RecoveryPulse()
    ; Called by the separate startup watchdog, which never owns child state.
    Wake()
EndFunction
Function Wake()
    UnregisterForUpdate()
    UnregisterForUpdateGameTime()
    RegisterForSingleUpdate(2.0)
EndFunction
Function Transition()
    transitionPending = True
    ; The interior opportunity is serviced now, not two seconds after the
    ; player could already have left. Same serialized worker as normal updates.
    Service()
EndFunction
Event OnUpdateGameTime()
    Service()
EndEvent
Event OnUpdate()
    Service()
EndEvent
Function Service()
    InitDiagnostics()
    If !DiagnosticGlobals || DiagnosticGlobals.Length != 17
        StorageFailure("DiagnosticGlobals", 17)
        RegisterForSingleUpdate(30.0)
        Return
    EndIf
    Int request = 0
    If DiagnosticGlobals[0] != None
        request = DiagnosticGlobals[0].GetValue() as Int
        If request >= 2
            DiagnosticGlobals[0].SetValue(0.0)
            If request == 3
                repairRequested = True
                Log("optional console recovery requested; actor state retained")
            EndIf
        EndIf
    EndIf
    Float now = Utility.GetCurrentRealTime()
    If processing
        ; A saved v0.1/v0.2 stack gets time to finish. A stuck flag cannot veto
        ; updates forever. Real-time values may restart on a new game process.
        If !leaseArmed || now < leaseStart
            leaseStart = now
            leaseUntil = now + 120.0
            leaseArmed = True
        EndIf
        If now < leaseUntil
            Status(16, 1)
            If request == 2
                ShowStatus()
            EndIf
            RegisterForSingleUpdate(5.0)
            Return
        EndIf
        workEpoch += 1
        processing = False
        repairRequested = True
        Debug.Trace("[MoreBrats] v1.0.0: expired update lease; reconciling saved references.")
    EndIf
    processing = True
    transitionPending = False
    leaseArmed = True
    leaseStart = now
    leaseUntil = now + 120.0
    Int ticket = workEpoch
    Status(2)
    ; Maintain the legacy fallback even if new pool metadata is not ready yet.
    If NightMode != None
        If Daylight(HourAt(Utility.GetCurrentGameTime()))
            NightMode.SetValue(0.0)
        Else
            NightMode.SetValue(1.0)
        EndIf
    EndIf
    If EnsureSetup() && ticket == workEpoch
        Tick()
    EndIf
    If ticket == workEpoch
        diagTicks += 1
        PublishSnapshot()
        If ticket != workEpoch
            Return
        EndIf
        PlanNext()
        If ticket == workEpoch
            processing = False
            leaseArmed = False
            If transitionPending
                RegisterForSingleUpdate(0.1)
            EndIf
        EndIf
        If request == 2
            ShowStatus()
        EndIf
    EndIf
EndFunction
Float Function HourAt(Float stamp)
    Return (stamp - (stamp as Int)) * 24.0
EndFunction
Int Function CycleAt(Float stamp)
    Float shifted = stamp - (8.0 / 24.0)
    Int result = shifted as Int
    If shifted < (result as Float)
        result -= 1
    EndIf
    Return result
EndFunction
Bool Function InWindow(Float hour)
    Return hour >= 8.0 || hour < 3.0
EndFunction
Bool Function Daylight(Float hour)
    Return hour >= 8.0 && hour < 19.0
EndFunction

Bool Function EnsureSetup()
    Int ticket = workEpoch
    diagStorageReady = False
    ; Use boolean array tests, never array == None. Verify every new array
    ; before any element access; preserve each existing correctly sized array.
    ; Local IDs resolve in the current load order. No saved property is assumed
    ; to have acquired an editor value merely because the plugin was upgraded.
    If NightMode == None
        NightMode = Game.GetFormFromFile(0x801, "MoreBrats.esp") as GlobalVariable
    EndIf
    If DayArea == None
        DayArea = Game.GetFormFromFile(0x802, "MoreBrats.esp") as GlobalVariable
    EndIf
    If CityWorld == None
        CityWorld = Game.GetFormFromFile(0x1A26F, "Skyrim.esm") as WorldSpace
    EndIf
    If RoamFaction == None
        RoamFaction = Game.GetFormFromFile(0x814, "MoreBrats.esp") as Faction
    EndIf
    If PoolForms == None
        PoolForms = Game.GetFormFromFile(0x815, "MoreBrats.esp") as FormList
    EndIf
    If RoadForms == None
        RoadForms = Game.GetFormFromFile(0x816, "MoreBrats.esp") as FormList
    EndIf
    If TargetForms == None
        TargetForms = Game.GetFormFromFile(0x817, "MoreBrats.esp") as FormList
    EndIf
    Status(3)
    If RoamFaction == None || CityWorld == None || NightMode == None
        SetupFailure()
        Return False
    EndIf
    If !pool || pool.Length != 60
        Actor[] previousPool = pool
        pool = new Actor[60]
        If !pool || pool.Length != 60
            StorageFailure("pool", 60)
            Return False
        EndIf
        Int copyActor = 0
        While (previousPool as Bool) && copyActor < previousPool.Length && copyActor < 60
            pool[copyActor] = previousPool[copyActor]
            copyActor += 1
        EndWhile
        repairRequested = True
    EndIf
    If !roads || roads.Length != 18
        roads = new ObjectReference[18]
        If !roads || roads.Length != 18
            StorageFailure("roads", 18)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !targets || targets.Length != 6
        targets = new ObjectReference[6]
        If !targets || targets.Length != 6
            StorageFailure("targets", 6)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !dayPackageForms || dayPackageForms.Length != 37
        dayPackageForms = new Form[37]
        If !dayPackageForms || dayPackageForms.Length != 37
            StorageFailure("dayPackageForms", 37)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !targetRawForms || targetRawForms.Length != 6
        targetRawForms = new Form[6]
        If !targetRawForms || targetRawForms.Length != 6
            StorageFailure("targetRawForms", 6)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !targetLookupState || targetLookupState.Length != 6
        targetLookupState = new Int[6]
        If !targetLookupState || targetLookupState.Length != 6
            StorageFailure("targetLookupState", 6)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !targetBoundArray || targetBoundArray.Length != 6
        targetBoundArray = new Bool[6]
        If !targetBoundArray || targetBoundArray.Length != 6
            StorageFailure("targetBoundArray", 6)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !targetBoundValue || targetBoundValue.Length != 6
        targetBoundValue = new Bool[6]
        If !targetBoundValue || targetBoundValue.Length != 6
            StorageFailure("targetBoundValue", 6)
            Return False
        EndIf
        repairRequested = True
    EndIf
    Int n = 0
    If !deferredReason || deferredReason.Length != 6
        deferredReason = new Int[6]
        If !deferredReason || deferredReason.Length != 6
            StorageFailure("deferredReason", 6)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !enableUntil || enableUntil.Length != 6
        enableUntil = new Float[6]
        If !enableUntil || enableUntil.Length != 6
            StorageFailure("enableUntil", 6)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !residents || residents.Length != 6
        residents = new Actor[6]
        If !residents || residents.Length != 6
            StorageFailure("residents", 6)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !residentCycle || residentCycle.Length != 6
        residentCycle = new Int[6]
        If !residentCycle || residentCycle.Length != 6
            StorageFailure("residentCycle", 6)
            Return False
        EndIf
        repairRequested = True
        n = 0
        While n < 6
            residentCycle[n] = -100000
            n += 1
        EndWhile
        repairRequested = True
    EndIf
    If !lastArrivalCycle || lastArrivalCycle.Length != 6
        lastArrivalCycle = new Int[6]
        If !lastArrivalCycle || lastArrivalCycle.Length != 6
            StorageFailure("lastArrivalCycle", 6)
            Return False
        EndIf
        repairRequested = True
        n = 0
        While n < 6
            lastArrivalCycle[n] = -100000
            n += 1
        EndWhile
        repairRequested = True
    EndIf
    If !phase || phase.Length != 6
        phase = new Int[6]
        If !phase || phase.Length != 6
            StorageFailure("phase", 6)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !destination || destination.Length != 6
        destination = new Int[6]
        If !destination || destination.Length != 6
            StorageFailure("destination", 6)
            Return False
        EndIf
        repairRequested = True
        n = 0
        While n < 6
            destination[n] = -1
            n += 1
        EndWhile
        repairRequested = True
    EndIf
    If !priorDestination || priorDestination.Length != 6
        priorDestination = new Int[6]
        If !priorDestination || priorDestination.Length != 6
            StorageFailure("priorDestination", 6)
            Return False
        EndIf
        repairRequested = True
        n = 0
        While n < 6
            priorDestination[n] = -1
            n += 1
        EndWhile
        repairRequested = True
    EndIf
    If !arrivalIndex || arrivalIndex.Length != 6
        arrivalIndex = new Int[6]
        If !arrivalIndex || arrivalIndex.Length != 6
            StorageFailure("arrivalIndex", 6)
            Return False
        EndIf
        repairRequested = True
        n = 0
        While n < 6
            arrivalIndex[n] = -1
            n += 1
        EndWhile
        repairRequested = True
    EndIf
    If !selectedVariant || selectedVariant.Length != 6
        selectedVariant = new Int[6]
        If !selectedVariant || selectedVariant.Length != 6
            StorageFailure("selectedVariant", 6)
            Return False
        EndIf
        repairRequested = True
        n = 0
        While n < 6
            selectedVariant[n] = -1
            n += 1
        EndWhile
        repairRequested = True
    EndIf
    If !hiddenCount || hiddenCount.Length != 6
        hiddenCount = new Int[6]
        If !hiddenCount || hiddenCount.Length != 6
            StorageFailure("hiddenCount", 6)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !stallCount || stallCount.Length != 6
        stallCount = new Int[6]
        If !stallCount || stallCount.Length != 6
            StorageFailure("stallCount", 6)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !retireSlot || retireSlot.Length != 6
        retireSlot = new Bool[6]
        If !retireSlot || retireSlot.Length != 6
            StorageFailure("retireSlot", 6)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !disablingSlot || disablingSlot.Length != 6
        disablingSlot = new Bool[6]
        If !disablingSlot || disablingSlot.Length != 6
            StorageFailure("disablingSlot", 6)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !safeRoads || safeRoads.Length != 18
        safeRoads = new Bool[18]
        If !safeRoads || safeRoads.Length != 18
            StorageFailure("safeRoads", 18)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !deadline || deadline.Length != 6
        deadline = new Float[6]
        If !deadline || deadline.Length != 6
            StorageFailure("deadline", 6)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !runUntil || runUntil.Length != 6
        runUntil = new Float[6]
        If !runUntil || runUntil.Length != 6
            StorageFailure("runUntil", 6)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !progressAt || progressAt.Length != 6
        progressAt = new Float[6]
        If !progressAt || progressAt.Length != 6
            StorageFailure("progressAt", 6)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !lastX || lastX.Length != 6
        lastX = new Float[6]
        If !lastX || lastX.Length != 6
            StorageFailure("lastX", 6)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !lastY || lastY.Length != 6
        lastY = new Float[6]
        If !lastY || lastY.Length != 6
            StorageFailure("lastY", 6)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !lastZ || lastZ.Length != 6
        lastZ = new Float[6]
        If !lastZ || lastZ.Length != 6
            StorageFailure("lastZ", 6)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !orphanHidden || orphanHidden.Length != 60
        Int[] previousOrphanHidden = orphanHidden
        orphanHidden = new Int[60]
        If !orphanHidden || orphanHidden.Length != 60
            StorageFailure("orphanHidden", 60)
            Return False
        EndIf
        Int copyHidden = 0
        While (previousOrphanHidden as Bool) && copyHidden < previousOrphanHidden.Length && copyHidden < 60
            orphanHidden[copyHidden] = previousOrphanHidden[copyHidden]
            copyHidden += 1
        EndWhile
        repairRequested = True
    EndIf
    If repairRequested || bindingsPending || schemaVersion < 6
        diagResolved = 0
        diagRoads = 0
        diagPoolInputs = 0
        diagRoadInputs = 0
        bindingsPending = False
        n = 0
        While n < 60
            Actor candidate = None
            If (PoolRefs as Bool) && n < PoolRefs.Length
                candidate = PoolRefs[n]
            EndIf
            If candidate == None && n < 6 && (Children as Bool) && Children.Length == 6
                candidate = Children[n]
            EndIf
            If candidate == None
                Int localID = 0x818 + n - 6
                If n < 6
                    localID = 0x809 + n * 2
                ElseIf n >= 36
                    localID = 0x890 + n - 36
                EndIf
                candidate = Game.GetFormFromFile(localID, "MoreBrats.esp") as Actor
            EndIf
            If candidate != None
                If pool[n] == None && !candidate.IsDisabled()
                    repairRequested = True
                EndIf
                diagPoolInputs += 1
                pool[n] = candidate
                If pool[n] != candidate
                    StorageFailure("pool binding index " + n, 60, 31)
                    Return False
                EndIf
            Else
                bindingsPending = True
            EndIf
            If pool[n] != None
                diagResolved += 1
            EndIf
            n += 1
        EndWhile
        n = 0
        While n < 18
            ObjectReference road = None
            If (RoadRefs as Bool) && RoadRefs.Length == 18
                road = RoadRefs[n]
            EndIf
            If road == None
                Int roadID = 0x2C934 + n
                If n == 17
                    roadID = 0x2D3CE
                EndIf
                road = Game.GetFormFromFile(roadID, "Skyrim.esm") as ObjectReference
            EndIf
            If road != None
                diagRoadInputs += 1
                roads[n] = road
                If roads[n] != road
                    StorageFailure("roads binding index " + n, 18, 31)
                    Return False
                EndIf
            Else
                bindingsPending = True
                ; Last-resort v0.1 arrival anchors; explicit properties, no
                ; guessed coordinates. Multiple indices can share an anchor;
                ; physical spacing checks still prevent coincident arrivals.
                If (ArrivalPoints as Bool) && ArrivalPoints.Length == 3
                    roads[n] = ArrivalPoints[n % 3]
                    If roads[n] != ArrivalPoints[n % 3]
                        StorageFailure("roads fallback index " + n, 18, 31)
                        Return False
                    EndIf
                EndIf
            EndIf
            If roads[n] != None
                diagRoads += 1
            EndIf
            n += 1
        EndWhile
        n = 0
        diagLegacyTargets = 0
        While n < 6
            ; These old markers are retained for save identity and diagnosis.
            ; They are no longer an arrival/travel dependency in v0.2.5.
            ObjectReference target = None
            targetBoundArray[n] = (TargetRefs as Bool) && TargetRefs.Length == 6
            targetBoundValue[n] = False
            targetLookupState[n] = 1
            targetRawForms[n] = None
            If targetBoundArray[n]
                target = TargetRefs[n]
                targetBoundValue[n] = target != None
                targetLookupState[n] = 2
            EndIf
            If target != None
                targetLookupState[n] = 3
            Else
                targetRawForms[n] = Game.GetFormFromFile(0x836 + n, "MoreBrats.esp")
                target = targetRawForms[n] as ObjectReference
                If targetRawForms[n] != None && target == None
                    targetLookupState[n] = 4
                ElseIf target != None
                    targetLookupState[n] = 5
                EndIf
            EndIf
            If target != None
                targets[n] = target
            ElseIf targets[n] != None
                targetLookupState[n] = 6
            EndIf
            If targets[n] != None
                diagLegacyTargets += 1
            EndIf
            n += 1
        EndWhile
    EndIf
    ; Every required array passed its presence/length checks above. Binding
    ; counts now come from runtime storage, not merely resolved input forms.
    diagStorageReady = True
    diagStorageFailure = ""
    If ticket != workEpoch
        Return False
    EndIf
    If repairRequested || schemaVersion < 6
        Status(4)
        Log("reconciling saved references; schema=" + schemaVersion + "; pool resolved=" + diagResolved)
        Reconcile()
        If ticket != workEpoch
            Return False
        EndIf
        ; Commit only after caches, per-slot state and adoption are complete.
        schemaVersion = 6
        repairRequested = False
        setupWarning = False
        activeIndex = -1
        If !announced
            announced = True
            Log("controller initialized; v1.0.0 schema 6; pool=" + diagResolved + "/60; roads=" + diagRoads + "/18")
        EndIf
        Log("migration complete; schema 6; legacy private targets=" + diagLegacyTargets + "/6 (not required); direct road packages selected per actor")
    EndIf
    Status(5)
    Return True
EndFunction

Function StorageFailure(String name, Int expectedLength, Int reason = 30)
    diagStorageReady = False
    repairRequested = True
    Status(91, reason)
    ; Do not advertise old successful counters while current storage failed.
    diagResolved = 0
    diagRoads = 0
    If diagStorageFailure != name
        Log("runtime storage failure; array=" + name + "; expected length=" + expectedLength + "; reason=" + reason)
    EndIf
    diagStorageFailure = name
EndFunction

Function SetupFailure()
    Status(90, 10)
    repairRequested = True
    If !setupWarning
        setupWarning = True
        Debug.Trace("[MoreBrats] v1.0.0: runtime form bindings unavailable; retrying. Existing actors retained.")
        Log("missing core property: faction=" + RoamFaction + "; city world=" + CityWorld + "; night global=" + NightMode)
    EndIf
EndFunction

Function Reconcile()
    Float stamp = Utility.GetCurrentGameTime()
    Int cycle = CycleAt(stamp)
    Int s = 0
    ; Keep each valid saved resident and its cycle/retirement state. Dedupe
    ; bookkeeping, never disable an actor just because two slots refer to it.
    While s < 6
        Actor saved = residents[s]
        If saved != None
            Bool found = False
            Int n = 0
            While n < 60
                If pool[n] == saved
                    found = True
                EndIf
                n += 1
            EndWhile
            n = 0
            While n < s
                If residents[n] == saved
                    found = False
                EndIf
                n += 1
            EndWhile
            If !found
                residents[s] = None
            Else
                If residentCycle[s] < -99999
                    residentCycle[s] = cycle
                    lastArrivalCycle[s] = cycle
                EndIf
                If residentCycle[s] != cycle || !InWindow(HourAt(stamp))
                    retireSlot[s] = True
                EndIf
                RefreshResident(s, stamp)
            EndIf
        EndIf
        s += 1
    EndWhile
    ; Scan ALL 60 stable references, not just v0.1's first six. A VM stack may
    ; have enabled a child before its saved array assignment was completed.
    Int i = 0
    While i < 60
        Actor child = pool[i]
        If child != None && !child.IsDisabled() && !ReferenceInUse(child)
            Int slot = SlotFromPoolIndex(i)
            If residents[slot] != None
                slot = 0
                While slot < 6 && residents[slot] != None
                    slot += 1
                EndWhile
            EndIf
            If slot < 6
                residents[slot] = child
                residentCycle[slot] = cycle
                lastArrivalCycle[slot] = cycle
                retireSlot[slot] = !InWindow(HourAt(stamp))
                disablingSlot[slot] = False
                hiddenCount[slot] = 0
                destination[slot] = -1
                priorDestination[slot] = -1
                arrivalIndex[slot] = -1
                If schemaVersion < 2 && i < 6
                    If activeCycle > -99999
                        residentCycle[slot] = activeCycle
                        lastArrivalCycle[slot] = activeCycle
                    EndIf
                    retireSlot[slot] = retiring || residentCycle[slot] != cycle || !InWindow(HourAt(stamp))
                    disablingSlot[slot] = disablePending && i == activeIndex
                ElseIf todayCycle > -99999 && todayCycle != cycle
                    retireSlot[slot] = True
                EndIf
                RefreshResident(slot, stamp)
                Debug.Trace("[MoreBrats] v1.0.0: adopted saved enabled pool index " + i)
            EndIf
        EndIf
        i += 1
    EndWhile
    RecoverOrphans()
EndFunction

Function RefreshResident(Int s, Float stamp)
    If retireSlot[s] || !Daylight(HourAt(stamp))
        SetPhase(s, 3, True)
    Else
        ; Restart procedures after an upgrade/load without moving the child.
        If !RequiredDayPackage(s, 0, "RefreshResident.pause")
            SetPhase(s, 3, True)
            Return
        EndIf
        SetPhase(s, 0, True)
        deferredReason[s] = 0
        deadline[s] = stamp + Utility.RandomFloat(2.0, 5.0) / 1440.0
        destination[s] = -1
        priorDestination[s] = -1
    EndIf
EndFunction

Function RecoverOrphans()
    ; Normally empty. If saved bookkeeping contained more than six enabled
    ; refs, route extras indoors and retire each ONLY under the visibility rule.
    orphanPresent = False
    Int i = 0
    While i < 60
        Actor child = pool[i]
        If child != None && !child.IsDisabled() && !ReferenceInUse(child)
            orphanPresent = True
            If child.GetFactionRank(RoamFaction) != 3
                child.SetFactionRank(RoamFaction, 3)
                child.EvaluatePackage()
            EndIf
            orphanHidden[i] = RemovalObservation(child, orphanHidden[i])
            If orphanHidden[i] >= 2 && !Game.GetPlayer().HasLOS(child)
                child.DisableNoWait(False)
            EndIf
        Else
            orphanHidden[i] = 0
        EndIf
        i += 1
    EndWhile
EndFunction

Int Function ResidentCount()
    Int count = 0
    Int s = 0
    While s < 6
        If residents[s] != None
            count += 1
        EndIf
        s += 1
    EndWhile
    Return count
EndFunction

Bool Function RoadValid(ObjectReference point)
    Return RoadBlock(point) == 0
EndFunction
Int Function RoadBlock(ObjectReference point)
    If point == None
        Return 13
    EndIf
    If point.IsDisabled()
        Return 18
    EndIf
    ; Only the fixed whitelist is passed here. Do not make an unavailable
    ; exterior parent/world a veto before the proven interior safety branch.
    Cell roadCell = point.GetParentCell()
    If roadCell != None && roadCell.IsInterior()
        Return 16
    EndIf
    WorldSpace world = point.GetWorldSpace()
    If world != None && world != CityWorld
        Return 17
    EndIf
    Return 0
EndFunction

Int Function ArrivalBlock(ObjectReference point)
    If point == None
        Return 13
    EndIf
    If point.IsDisabled()
        Return 18
    EndIf
    Actor viewer = Game.GetPlayer()
    If viewer.IsInInterior()
        ; v0.1's proven off-screen cell-transition path. The destination comes
        ; from fixed exterior VMAD bindings. It does not depend on attached-cell
        ; state or GetWorldSpace returning a value for an unloaded marker.
        Return 0
    EndIf
    WorldSpace playerWorld = viewer.GetWorldSpace()
    If playerWorld == None
        Return 15
    EndIf
    If playerWorld != CityWorld
        Return 0
    EndIf
    Cell pointCell = point.GetParentCell()
    Float separation = viewer.GetDistance(point)
    If pointCell != None
        If !pointCell.IsAttached() && separation >= 4096.0
            Return 0
        EndIf
    ElseIf !point.Is3DLoaded() && separation >= 8192.0
        Return 0
    EndIf
    Return 14
EndFunction

Bool Function SafeArrival(ObjectReference point)
    Return RoadValid(point) && ArrivalBlock(point) == 0
EndFunction

Bool Function SafeRemoval(Actor child, Int s)
    hiddenCount[s] = RemovalObservation(child, hiddenCount[s])
    Return hiddenCount[s] >= 2
EndFunction
Int Function RemovalObservation(Actor child, Int previous)
    Actor viewer = Game.GetPlayer()
    Cell childCell = child.GetParentCell()
    Cell playerCell = viewer.GetParentCell()
    If !child.Is3DLoaded()
        If viewer.IsInInterior() || child.IsInInterior()
            If playerCell != None && childCell != playerCell
                Return 2
            EndIf
        ElseIf viewer.GetWorldSpace() != None && viewer.GetWorldSpace() != CityWorld
            Return 2
        EndIf
        Return 0
    EndIf
    If childCell == None || playerCell == None
        Return 0
    EndIf
    If viewer.HasLOS(child) || viewer.GetDistance(child) < 768.0
        Return 0
    EndIf
    Return previous + 1
EndFunction

Function SetPhase(Int s, Int wanted, Bool refresh = False)
    Actor child = residents[s]
    phase[s] = wanted
    If child != None
        Int rank = s * 4 + wanted
        If wanted == 0
            rank = 24
        ElseIf wanted == 1 || wanted == 2
            rank = 32 + destination[s] * 4 + wanted
        EndIf
        Bool changed = child.GetFactionRank(RoamFaction) != rank
        If changed
            child.SetFactionRank(RoamFaction, rank)
        EndIf
        If (changed || refresh) && !child.IsDisabled()
            child.EvaluatePackage()
            Log("AI EvaluatePackage requested; slot=" + s + "; ref=" + child + "; phase=" + wanted, True)
        EndIf
    EndIf
EndFunction

Int Function PickDestination(Int s)
    Actor child = residents[s]
    Bool farTrip = Utility.RandomInt(0, 99) < 70
    Int tries = 0
    While tries < 24
        Int pick = Utility.RandomInt(0, 17)
        If pick != destination[s] && pick != priorDestination[s] && RoadValid(roads[pick])
            Float distance = child.GetDistance(roads[pick])
            Bool appropriate = distance >= 1800.0
            If !farTrip
                appropriate = distance >= 450.0 && distance <= 2400.0
            EndIf
            Bool occupiedDestination = False
            Int peer = 0
            While peer < 6
                If peer != s && residents[peer] != None && !retireSlot[peer] && destination[peer] == pick
                    occupiedDestination = True
                EndIf
                peer += 1
            EndWhile
            If appropriate && !occupiedDestination
                Return pick
            EndIf
        EndIf
        tries += 1
    EndWhile
    ; Bounded fallback relaxes peer spacing but still rejects the last two goals.
    Int offset = Utility.RandomInt(0, 17)
    tries = 0
    While tries < 18
        Int candidate = (offset + tries * 5) % 18
        If candidate != destination[s] && candidate != priorDestination[s] && RoadValid(roads[candidate])
            If child.GetDistance(roads[candidate]) >= 450.0
                Return candidate
            EndIf
        EndIf
        tries += 1
    EndWhile
    Return -1
EndFunction

Function BeginTrip(Int s, Float stamp)
    Int ticket = workEpoch
    Int pick = PickDestination(s)
    If pick < 0
        SetPhase(s, 0)
        deadline[s] = stamp + 5.0 / 1440.0
        Return
    EndIf
    If !DayAIReady(s, pick, "BeginTrip.direct road")
        Return
    EndIf
    deferredReason[s] = 0
    priorDestination[s] = destination[s]
    destination[s] = pick
    diagGoal = pick
    ; The selected package already targets this road ref. No marker MoveTo.
    diagSelectedPoint = roads[pick]
    stamp = Utility.GetCurrentGameTime()
    If ticket != workEpoch
        Return
    EndIf
    If !Daylight(HourAt(stamp)) || residentCycle[s] != CycleAt(stamp) || retireSlot[s]
        SetPhase(s, 3)
        Return
    EndIf
    lastX[s] = residents[s].GetPositionX()
    lastY[s] = residents[s].GetPositionY()
    lastZ[s] = residents[s].GetPositionZ()
    stallCount[s] = 0
    progressAt[s] = stamp + 6.0 / 1440.0
    deadline[s] = stamp + Utility.RandomFloat(55.0, 85.0) / 1440.0
    If Utility.RandomInt(0, 99) < 25
        runUntil[s] = stamp + Utility.RandomFloat(2.0, 6.0) / 1440.0
        SetPhase(s, 2, True)
    Else
        SetPhase(s, 1, True)
    EndIf
EndFunction

Function AbandonTrip(Int s)
    ; A different package must run before retrying a failed trip: EvaluatePackage
    ; alone can retain a still-eligible travel procedure and its cached goal.
    ; The new pause package is actor-relative; no marker/actor teleport.
    If !RequiredDayPackage(s, 0, "AbandonTrip.pause")
        Return
    EndIf
    Float stamp = Utility.GetCurrentGameTime()
    If !Daylight(HourAt(stamp)) || residentCycle[s] != CycleAt(stamp) || retireSlot[s]
        SetPhase(s, 3)
        Return
    EndIf
    SetPhase(s, 0)
    deadline[s] = stamp + Utility.RandomFloat(2.0, 5.0) / 1440.0
EndFunction

Function UpdateRoaming(Int s, Float stamp)
    If phase[s] == 3
        BeginTrip(s, stamp)
        Return
    EndIf
    If phase[s] == 0
        If stamp >= deadline[s]
            BeginTrip(s, stamp)
        EndIf
        Return
    EndIf
    ObjectReference goal = DirectGoal(s)
    If goal == None || !RoadValid(goal)
        MissingTarget(s, "UpdateRoaming.roads[destination]", 24, 0, goal)
        AbandonTrip(s)
        Return
    EndIf
    Float distance = residents[s].GetDistance(goal)
    If distance <= 180.0
        SetPhase(s, 0)
        deadline[s] = stamp + Utility.RandomFloat(5.0, 25.0) / 1440.0
        Return
    EndIf
    If stamp >= deadline[s]
        AbandonTrip(s)
        Return
    EndIf
    If stamp >= progressAt[s]
        Float x = residents[s].GetPositionX()
        Float y = residents[s].GetPositionY()
        Float z = residents[s].GetPositionZ()
        ; Measure actual displacement, not distance-to-goal. A valid route may
        ; initially go away from its goal to get around stairs or buildings.
        Float moved = (x-lastX[s])*(x-lastX[s]) + (y-lastY[s])*(y-lastY[s]) + (z-lastZ[s])*(z-lastZ[s])
        If moved < 1024.0
            stallCount[s] += 1
        Else
            stallCount[s] = 0
        EndIf
        lastX[s] = x
        lastY[s] = y
        lastZ[s] = z
        progressAt[s] = stamp + 6.0 / 1440.0
        If stallCount[s] >= 3
            AbandonTrip(s)
            Return
        EndIf
    EndIf
    If phase[s] == 2 && stamp >= runUntil[s]
        SetPhase(s, 1)
    EndIf
EndFunction

Bool Function ReferenceInUse(Actor child)
    If child == None || !residents
        Return False
    EndIf
    Int s = 0
    While s < 6
        If residents[s] == child
            Return True
        EndIf
        s += 1
    EndWhile
    Return False
EndFunction
; Keep all old indices and saved selectedVariant values0..5 unchanged.
; The four new gender/outfit combinations occupy the appended24 references.
Int Function PoolIndex(Int slot, Int variant)
    If variant < 6
        Return slot * 6 + variant
    EndIf
    Return 36 + slot * 4 + variant - 6
EndFunction
Int Function SlotFromPoolIndex(Int index)
    If index < 36
        Return index / 6
    EndIf
    Return (index - 36) / 4
EndFunction
Bool Function PoolSlotDisabled(Int s)
    Int v = 0
    While v < 10
        If pool[PoolIndex(s, v)] != None && !pool[PoolIndex(s, v)].IsDisabled()
            Return False
        EndIf
        v += 1
    EndWhile
    Return True
EndFunction
Bool Function ClearArrivalPoint(Int index, Int slot)
    ObjectReference point = roads[index]
    Int peer = 0
    While peer < 6
        If peer != slot
            If arrivalIndex[peer] == index && lastArrivalCycle[peer] == todayCycle
                Return False
            EndIf
            If residents[peer] != None && !residents[peer].IsDisabled()
                If residents[peer].GetDistance(point) < 384.0
                    Return False
                EndIf
            EndIf
        EndIf
        peer += 1
    EndWhile
    Return True
EndFunction
Function TryArrival(Int s, Int cycle)
    Int ticket = workEpoch
    diagSlot = s
    diagGoal = -1
    diagSelectedActor = None
    diagSelectedPoint = None
    diagTargetContext = "TryArrival.actor selection"
    If !diagStorageReady
        Defer(s, 30, "runtime arrays have not passed setup validation")
        repairRequested = True
        Return
    EndIf
    If orphanPresent
        Defer(s, 21, "unexpected extra saved actors are awaiting safe reconciliation")
        Return
    EndIf
    If ResidentCount() >= dailyPopulation
        Defer(s, 22, "visible carry-overs/tracked actors already consume today's capacity")
        Return
    EndIf
    Status(8)
    Log("spawn attempt; slot=" + s + "; cycle=" + cycle, True)
    If !PoolSlotDisabled(s)
        Defer(s, 21, "slot contains an enabled reference awaiting adoption/retirement")
        Return
    EndIf
    If selectedVariant[s] < 0
        Int gender = Utility.RandomInt(0, 1)
        Int clothing = Utility.RandomInt(0, 4)
        If clothing < 3
            selectedVariant[s] = gender * 3 + clothing
        Else
            selectedVariant[s] = 6 + gender * 2 + clothing - 3
        EndIf
    EndIf
    If pool[PoolIndex(s, selectedVariant[s])] == None
        Int variantOffset = Utility.RandomInt(0, 9)
        Int v = 0
        selectedVariant[s] = -1
        While v < 10 && selectedVariant[s] < 0
            Int candidateVariant = (variantOffset + v) % 10
            If pool[PoolIndex(s, candidateVariant)] != None
                selectedVariant[s] = candidateVariant
            EndIf
            v += 1
        EndWhile
        If selectedVariant[s] < 0
            Defer(s, 11, "no resolved actor reference in this slot")
            Return
        EndIf
    EndIf
    Actor chosen = pool[PoolIndex(s, selectedVariant[s])]
    diagSelectedActor = chosen
    If chosen == None
        Defer(s, 11, "actor readback returned None; variant=" + selectedVariant[s])
        Return
    EndIf
    If ReferenceInUse(chosen)
        Defer(s, 25, "selected actor is already tracked in another resident slot")
        Return
    EndIf
    diagTargetContext = "TryArrival.road selection"
    Int index = -1
    Int offset = Utility.RandomInt(0, 17)
    Int tries = 0
    While tries < 18 && index < 0
        Int candidate = (offset + tries * 5) % 18
        If SafeArrival(roads[candidate]) && ClearArrivalPoint(candidate, s)
            index = candidate
        EndIf
        tries += 1
    EndWhile
    If index < 0
        Int reason = 19
        Bool valid = False
        Int n = 0
        While n < 18
            If RoadValid(roads[n])
                valid = True
                Int block = ArrivalBlock(roads[n])
                If block != 0
                    reason = block
                EndIf
            ElseIf !valid
                reason = RoadBlock(roads[n])
            EndIf
            n += 1
        EndWhile
        Defer(s, reason, "no admissible free destination; refs=" + diagRoads + "/18 road refs resolved; 13=missing, 14=loaded exterior, 15=player world unavailable, 16=interior, 17=wrong world, 18=disabled, 19=spacing")
        Return
    EndIf
    ObjectReference point = roads[index]
    diagGoal = index
    diagSelectedPoint = point
    If point == None
        Defer(s, 13, "selected road readback returned None")
        Return
    EndIf
    If !DayAIReady(s, index, "TryArrival.day AI before enable")
        Return
    EndIf
    diagSelectedActor = chosen
    diagSelectedPoint = point
    Status(9)
    Log("spawn selected; slot=" + s + "; ref=" + chosen + "; destination=" + point, True)
    If ticket != workEpoch || !chosen.IsDisabled() || ReferenceInUse(chosen)
        Return
    EndIf
    chosen.MoveTo(point, 0.0, 0.0, 0.0, True)
    Status(10)
    Float stamp = Utility.GetCurrentGameTime()
    If ticket != workEpoch
        Return
    EndIf
    ; Actor MoveTo is latent: schedule/visibility/occupancy checks repeat.
    If !Daylight(HourAt(stamp)) || CycleAt(stamp) != cycle
        Defer(s, 23, "schedule changed during placement; captured cycle=" + cycle + "; now cycle=" + CycleAt(stamp) + "; hour=" + HourAt(stamp))
        Return
    EndIf
    If !SafeArrival(point)
        Defer(s, 24, "visibility or destination validity changed during placement")
        Return
    EndIf
    ; The validated exterior destination and repeated separate-cell safety
    ; establish the arrival path, as in v0.1. Do not gate enabling on a second
    ; parent-cell/world query of a disabled actor immediately after MoveTo.
    If orphanPresent || ResidentCount() >= dailyPopulation || !PoolSlotDisabled(s) || ReferenceInUse(chosen) || !ClearArrivalPoint(index, s)
        Return
    EndIf
    residents[s] = chosen
    residentCycle[s] = cycle
    lastArrivalCycle[s] = cycle
    arrivalIndex[s] = index
    retireSlot[s] = False
    disablingSlot[s] = False
    hiddenCount[s] = 0
    destination[s] = index
    priorDestination[s] = -1
    deadline[s] = stamp + Utility.RandomFloat(2.0, 8.0) / 1440.0
    SetPhase(s, 0)
    If ticket != workEpoch || !Daylight(HourAt(Utility.GetCurrentGameTime())) || CycleAt(Utility.GetCurrentGameTime()) != cycle || !SafeArrival(point)
        If ticket == workEpoch
            residents[s] = None
            lastArrivalCycle[s] = -100000
        EndIf
        Return
    EndIf
    enableUntil[s] = Utility.GetCurrentRealTime() + 120.0
    chosen.EnableNoWait(False)
    deferredReason[s] = 0
    Status(11)
    Log("enable requested; slot=" + s + "; ref=" + chosen + "; destination=" + point)
    chosen.EvaluatePackage()
    Log("AI EvaluatePackage requested after enable; slot=" + s, True)
EndFunction

Function Tick()
    Float stamp = Utility.GetCurrentGameTime()
    Float hour = HourAt(stamp)
    Int cycle = CycleAt(stamp)
    If Daylight(hour)
        Status(13)
    ElseIf InWindow(hour)
        Status(14, 20)
    Else
        Status(15, 20)
    EndIf
    If orphanPresent
        RecoverOrphans()
    EndIf
    If dailyPopulation < 3 || dailyPopulation > 6
        todayCycle = -100000
    EndIf
    If cycle != todayCycle
        todayCycle = cycle
        dailyPopulation = Utility.RandomInt(3, 6)
        Status(6)
        Log("daily population selected=" + dailyPopulation + "; cycle=" + cycle + "; hour=" + hour)
        Int reset = 0
        While reset < 6
            selectedVariant[reset] = -1
            If residents[reset] == None
                arrivalIndex[reset] = -1
            EndIf
            reset += 1
        EndWhile
    EndIf
    ; This global is retained for the v0.1 fallback packages, not child state.
    If Daylight(hour)
        NightMode.SetValue(0.0)
    Else
        NightMode.SetValue(1.0)
    EndIf
    Bool arrivalsNeeded = False
    Int s = 0
    While s < 6
        If s < dailyPopulation && residents[s] == None && lastArrivalCycle[s] != cycle
            arrivalsNeeded = True
        EndIf
        s += 1
    EndWhile
    If Daylight(hour) && arrivalsNeeded
        Int r = 0
        While r < 18
            safeRoads[r] = SafeArrival(roads[r])
            r += 1
        EndWhile
    EndIf
    s = 0
    While s < 6
        Actor child = residents[s]
        If child != None
            If enableUntil[s] > 0.0 && !child.IsDisabled()
                enableUntil[s] = 0.0
                Status(12)
                Log("enabled confirmed; slot=" + s + "; ref=" + child)
            EndIf
            If child.IsDisabled() && !disablingSlot[s] && Utility.GetCurrentRealTime() >= enableUntil[s]
                ; An enable command absent from the loaded VM must not reserve
                ; a disabled resident forever. Observe disabled state before reuse.
                disablingSlot[s] = True
            EndIf
            If disablingSlot[s]
                If child.IsDisabled()
                    Log("disabled confirmed; slot=" + s + "; ref=" + child)
                    residents[s] = None
                    disablingSlot[s] = False
                    retireSlot[s] = False
                    hiddenCount[s] = 0
                EndIf
            Else
                If !InWindow(hour) || residentCycle[s] != cycle
                    retireSlot[s] = True
                EndIf
                If retireSlot[s]
                    SetPhase(s, 3)
                    If SafeRemoval(child, s)
                        If !Game.GetPlayer().HasLOS(child)
                            child.DisableNoWait(False)
                            Log("safe retirement disable requested; slot=" + s + "; ref=" + child)
                            disablingSlot[s] = True
                        Else
                            hiddenCount[s] = 0
                        EndIf
                    EndIf
                ElseIf !Daylight(hour)
                    SetPhase(s, 3)
                Else
                    UpdateRoaming(s, stamp)
                EndIf
            EndIf
        ElseIf s < dailyPopulation && Daylight(hour) && lastArrivalCycle[s] != cycle
            TryArrival(s, cycle)
        EndIf
        ; Native calls may yield; later slots must use the actual current time.
        stamp = Utility.GetCurrentGameTime()
        hour = HourAt(stamp)
        cycle = CycleAt(stamp)
        If cycle != todayCycle
            Return
        EndIf
        s += 1
    EndWhile
    If !Daylight(hour) && ResidentCount() == 0
        Status(7, 20)
    EndIf
EndFunction

Function PlanNext()
    UnregisterForUpdate()
    UnregisterForUpdateGameTime()
    If schemaVersion < 6 || repairRequested
        RegisterForSingleUpdate(30.0)
        Return
    EndIf
    Float stamp = Utility.GetCurrentGameTime()
    Float hour = HourAt(stamp)
    Float delta = 0.5
    Float boundary = 0.0
    If hour < 3.0
        boundary = 3.0 - hour
    ElseIf hour < 8.0
        boundary = 8.0 - hour
    ElseIf hour < 19.0
        boundary = 19.0 - hour
    Else
        boundary = 27.0 - hour
    EndIf
    If boundary < delta
        delta = boundary
    EndIf
    Bool retirementPending = orphanPresent
    Bool arrivalPending = False
    Int s = 0
    While s < 6
        If residents[s] != None
            If retireSlot[s] || disablingSlot[s]
                retirementPending = True
            ElseIf Daylight(hour)
                Float until = (deadline[s] - stamp) * 24.0
                If phase[s] == 1 || phase[s] == 2
                    If delta > 0.08
                        delta = 0.08
                    EndIf
                    If phase[s] == 2
                        until = (runUntil[s] - stamp) * 24.0
                    EndIf
                EndIf
                If until > 0.0 && until < delta
                    delta = until
                EndIf
            EndIf
        ElseIf s < dailyPopulation && lastArrivalCycle[s] != CycleAt(stamp) && Daylight(hour)
            arrivalPending = True
        EndIf
        s += 1
    EndWhile
    ; Preserve the documented safe lower bound for game-time update intervals.
    If delta < 0.05
        delta = 0.05
    EndIf
    RegisterForSingleUpdateGameTime(delta)
    If retirementPending
        RegisterForSingleUpdate(10.0)
    ElseIf arrivalPending
        If Game.GetPlayer().IsInInterior()
            RegisterForSingleUpdate(5.0)
        Else
            RegisterForSingleUpdate(30.0)
        EndIf
    EndIf
EndFunction

; Diagnostics are plain plugin globals readable by Skyrim's vanilla console.
; Debug 0=normal, 1=verbose traces, 2=one-shot status, 3=one-shot safe repair.
Function InitDiagnostics()
    If !DiagnosticGlobals || DiagnosticGlobals.Length != 17
        DiagnosticGlobals = new GlobalVariable[17]
        If !DiagnosticGlobals || DiagnosticGlobals.Length != 17
            StorageFailure("DiagnosticGlobals", 17)
            Return
        EndIf
    EndIf
    Int n = 0
    While n < 17
        If DiagnosticGlobals[n] == None
            Int localID = 0x856 + n
            If n >= 12
                localID = 0x887 + n - 12
            EndIf
            DiagnosticGlobals[n] = Game.GetFormFromFile(localID, "MoreBrats.esp") as GlobalVariable
        EndIf
        n += 1
    EndWhile
    ; Globals persist in saves; stamp all runtime build identifiers explicitly.
    WriteDiagnostic(10, 1000.0)
    WriteDiagnostic(11, 1000.0)
    WriteDiagnostic(16, 1000.0)
EndFunction
Function WriteDiagnostic(Int index, Float value)
    If (DiagnosticGlobals as Bool) && DiagnosticGlobals.Length == 17 && DiagnosticGlobals[index] != None
        DiagnosticGlobals[index].SetValue(value)
    EndIf
EndFunction
Function RecordEvent(Int code)
    InitDiagnostics()
    WriteDiagnostic(9, code as Float)
EndFunction
Function Status(Int stage, Int reason = 0)
    If stage != 16
        lastWorkerStage = stage
    EndIf
    diagStage = stage
    diagReason = reason
    WriteDiagnostic(1, stage as Float)
    WriteDiagnostic(2, reason as Float)
EndFunction
Function Log(String message, Bool verbose = False)
    Bool allowed = !verbose
    If verbose && (DiagnosticGlobals as Bool) && DiagnosticGlobals[0] != None
        allowed = DiagnosticGlobals[0].GetValue() == 1.0
    EndIf
    If allowed
        Debug.Trace("[MoreBrats] v1.0.0 " + message)
    EndIf
EndFunction
Function Defer(Int slot, Int reason, String explanation)
    diagSlot = slot
    Status(8, reason)
    If (deferredReason as Bool) && deferredReason[slot] != reason
        deferredReason[slot] = reason
        Log("spawn deferred; slot=" + slot + "; reason=" + reason + "; " + explanation)
    EndIf
EndFunction
Int Function EnabledCount()
    Int count = 0
    If (pool as Bool)
        Int n = 0
        While n < pool.Length
            If pool[n] != None && !pool[n].IsDisabled()
                count += 1
            EndIf
            n += 1
        EndWhile
    EndIf
    Return count
EndFunction
Function PublishSnapshot()
    Int count = EnabledCount()
    Int pending = dailyPopulation - count
    If pending < 0
        pending = 0
    EndIf
    WriteDiagnostic(3, dailyPopulation as Float)
    WriteDiagnostic(4, count as Float)
    WriteDiagnostic(5, pending as Float)
    WriteDiagnostic(6, diagResolved as Float)
    WriteDiagnostic(7, diagRoads as Float)
    WriteDiagnostic(8, diagTicks as Float)
    WriteDiagnostic(12, diagLegacyTargets as Float)
    WriteDiagnostic(13, diagSlot as Float)
    WriteDiagnostic(14, diagGoal as Float)
    WriteDiagnostic(15, diagLookupResult as Float)
EndFunction
Int Function ResidentCountSafe()
    If !residents || residents.Length != 6
        Return 0
    EndIf
    Return ResidentCount()
EndFunction
Function ShowStatus()
    PublishSnapshot()
    String message = "[MoreBrats] v1.0.0 — status\nQuest running=" + IsRunning() + "; schema=" + schemaVersion
    message += "\nStage=" + diagStage + "; reason=" + diagReason + "; ticks=" + diagTicks
    message += "\nPopulation=" + dailyPopulation + "; enabled=" + EnabledCount() + "; tracked=" + ResidentCountSafe()
    message += "\nPool=" + diagResolved + "/60; roads=" + diagRoads + "/18; legacy markers=" + diagLegacyTargets + "/6 (unused)"
    message += "\nRuntime storage ready=" + diagStorageReady + "; failure=" + diagStorageFailure
    message += "\nResolved inputs pool=" + diagPoolInputs + "/60; roads=" + diagRoadInputs + "/18 (stored counts above)"
    message += "\nLast non-busy stage=" + lastWorkerStage
    message += "\nTransition queued=" + transitionPending + "; lease remaining=" + (leaseUntil - Utility.GetCurrentRealTime())
    message += "\nBusy=" + processing + "; slot=" + diagSlot + "; direct goal=" + diagGoal
    message += "\nStage 91/reason 30=unusable array; 31=binding readback; arrival reason 25=actor already tracked"
    message += "\nPer-slot reasons=" + SlotCodes(deferredReason) + "; legacy lookup=" + SlotCodes(targetLookupState)
    message += "\nLast target check=" + diagTargetContext + "; lookup=" + diagLookupResult
    message += "\nExpected=" + diagLookupFile + " local ID=" + diagExpectedID + "; raw=" + diagRawLookup
    If diagSlot >= 0 && diagSlot < 6 && (targetLookupState as Bool) && (targetBoundArray as Bool) && (targetBoundValue as Bool) && (targetRawForms as Bool) && (targets as Bool)
        message += "\nLegacy slot " + diagSlot + " MB_RoadTarget" + diagSlot + " ID=" + (0x836 + diagSlot)
        message += "; array bound=" + targetBoundArray[diagSlot] + "; entry bound=" + targetBoundValue[diagSlot]
        message += "; raw=" + targetRawForms[diagSlot] + "; cached=" + targets[diagSlot]
    EndIf
    Actor inspected = diagSelectedActor
    If inspected == None && (residents as Bool)
        Int n = 0
        While n < 6 && inspected == None
            inspected = residents[n]
            n += 1
        EndWhile
    EndIf
    message += "\nSelected ref=" + inspected + "\nRoad destination=" + diagSelectedPoint
    If inspected != None
        message += "\nCurrent engine package=" + inspected.GetCurrentPackage()
        message += "\nActual cell=" + inspected.GetParentCell() + "; world=" + inspected.GetWorldSpace()
    EndIf
    message += "\nSee v1.0.0 README for codes."
    Debug.MessageBox(message)
EndFunction
String Function SlotCodes(Int[] codes)
    If !codes
        Return "uninitialized"
    EndIf
    String result = ""
    Int n = 0
    While n < 6
        result += codes[n] + " "
        n += 1
    EndWhile
    Return result
EndFunction
ObjectReference Function DirectGoal(Int slot)
    If !roads || !destination
        Return None
    EndIf
    Int index = destination[slot]
    If index < 0 || index >= 18
        Return None
    EndIf
    Return roads[index]
EndFunction
Bool Function RequiredDayPackage(Int slot, Int index, String where)
    If !dayPackageForms || index < 0 || index >= 37
        MissingTarget(slot, where, 20, 0, None)
        Return False
    EndIf
    Int localID = 0x862 + index
    If dayPackageForms[index] == None
        dayPackageForms[index] = Game.GetFormFromFile(localID, "MoreBrats.esp")
    EndIf
    If dayPackageForms[index] == None
        MissingTarget(slot, where, 20, localID, None)
        Return False
    EndIf
    Return True
EndFunction
Bool Function DayAIReady(Int slot, Int goal, String where)
    diagSlot = slot
    diagGoal = goal
    diagTargetContext = where
    diagLookupResult = 0
    diagExpectedID = 0
    diagRawLookup = None
    If goal < 0 || goal >= 18 || !roads
        MissingTarget(slot, where + ".road index", 23, 0, None)
        Return False
    EndIf
    If roads[goal] == None || !RoadValid(roads[goal])
        MissingTarget(slot, where + ".roads[]", 24, 0, roads[goal])
        Return False
    EndIf
    Int roadID = 0x2C934 + goal
    If goal == 17
        roadID = 0x2D3CE
    EndIf
    ; The package's fixed reference must match the cached goal. A legacy
    ; arrival fallback at a different FormID is not a valid direct travel goal.
    If roads[goal].GetFormID() != roadID
        MissingTarget(slot, where + ".road/package binding mismatch", 24, roadID, roads[goal])
        Return False
    EndIf
    If !RequiredDayPackage(slot, 0, where + ".pause")
        Return False
    EndIf
    If !RequiredDayPackage(slot, 1 + goal * 2, where + ".walk")
        Return False
    EndIf
    If !RequiredDayPackage(slot, 2 + goal * 2, where + ".run")
        Return False
    EndIf
    Return True
EndFunction
Function MissingTarget(Int slot, String where, Int lookup, Int expected, Form raw)
    diagSlot = slot
    diagTargetContext = where
    diagLookupResult = lookup
    diagExpectedID = expected
    diagRawLookup = raw
    diagLookupFile = "MoreBrats.esp"
    If lookup == 23 || lookup == 24
        diagLookupFile = "Skyrim.esm"
    EndIf
    Defer(slot, 12, "required DAY AI dependency missing; where=" + where + "; lookup=" + lookup + "; expected=" + diagLookupFile + "; local=" + expected + "; raw=" + raw)
EndFunction
