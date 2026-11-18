Scriptname MB_VillageController extends Quest
; More Brats 0.5.0 - Tsoxer. New Phase3 settlements only; nine existing cities unchanged.
; Parameterized copy of the proven v0.2.5 lifecycle for NEW city quests only.
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
Actor[] Property ImperialRefs Auto
Actor[] Property BretonRefs Auto
Actor[] Property RedguardRefs Auto
; v1.2.4: appended donor references; old arrays/indices are unchanged.
FormList Property NamedDonorForms Auto
Actor[] donorActors0
Int[] donorHidden0
Actor[] donorActors1
Int[] donorHidden1
Actor[] donorActors2
Int[] donorHidden2
Actor[] donorActors3
Int[] donorHidden3
Actor[] donorActors4
Int[] donorHidden4

Int[] imperialHidden
Int[] bretonHidden
Int[] redguardHidden
ObjectReference[] Property RoadRefs Auto
ObjectReference[] Property TargetRefs Auto
GlobalVariable[] Property DiagnosticGlobals Auto

; New cities only. Whiterun keeps its original controller and saved state.
String Property CityName Auto
Int Property ConfigBase Auto
Int Property WorldID Auto
Int Property LocationID Auto
Int Property InnPointID Auto
Int Property InnCellID Auto
Int Property MinPopulation Auto
Int Property MaxPopulation Auto
Int[] Property RoadIDs Auto
Location Property CityLocation Auto
String Property SourceMaster = "Skyrim.esm" Auto
Quest Property AvailabilityQuest Auto
Int Property AvailabilityQuestID = 0 Auto
Int Property AvailabilityStage = 70 Auto

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
Int diagNamedResolved = 0
Int diagNamedIDRecovered = 0
Int diagNamedMissing = 0
Int diagNamedCatalogState = 0
Int diagAppearanceFallbacks = 0

; One pending cell/location notification; saved field is additive.
Bool transitionPending = False
Int lastWorkerStage = 0


; v1.2.4 additive state: absolute game days, never a new actor/reference pool.
Float nextArrivalAt = 0.0
Int arrivalScheduleCycle = -100000
Bool arrivalWasRelevant = False
Bool poolAudited = False
Float nextPoolAuditAt = 0.0
Int diagFullEnabled = -1

; v1.2.4 additive diagnostic counters and an official clock binding only.
GlobalVariable arrivalTimeScale
Int diagRealUpdates = 0
Int diagGameUpdates = 0

; v1.2.4 additive queue/diagnostic scalars. No resident array layout changes.
Bool transitionWakeArmed = False
Int diagEnableConfirmed = 0
Int diagPlacementRetries = 0
; Arrival-only cache/diagnostics. Existing serialized fields are unchanged.
FormList arrivalDoorTypes
ObjectReference priorArrivalDoor
ObjectReference diagArrivalDoor
Bool diagDoorFallback = False

Event OnInit()
    RecordEvent(1)
    Status(1)
    Log("controller OnInit; quest running=" + IsRunning())
    Wake()
EndEvent
Function Loaded()
    transitionWakeArmed = False
    ; Do not clear a saved busy flag while a suspended stack may still resume.
    repairRequested = True
    Log("load recovery/migration requested; saved schema=" + schemaVersion)
    Wake()
EndFunction
Function RecoveryPulse()
    ; Preserve the watchdog's recovery role without waking an empty remote city.
    If processing || repairRequested || ResidentCountSafe() > 0 || ArrivalRelevant()
        Wake()
    EndIf
EndFunction
Function Wake()
    UnregisterForUpdate()
    UnregisterForUpdateGameTime()
    RegisterForSingleUpdate(2.0)
EndFunction
Function Transition()
    transitionPending = True
    ; Coalesce moving-player notifications. Repeated events must not keep
    ; pushing the same deferred wake two seconds into the future.
    If !transitionWakeArmed
        transitionWakeArmed = True
        UnregisterForUpdate()
        RegisterForSingleUpdate(2.0)
    EndIf
EndFunction
Event OnUpdateGameTime()
    diagGameUpdates += 1
    Service()
EndEvent
Event OnUpdate()
    transitionWakeArmed = False
    diagRealUpdates += 1
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
    If request == 2
        ShowStatus()
    EndIf
    Float now = Utility.GetCurrentRealTime()
    Bool recoveredLease = False
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
            RegisterForSingleUpdate(5.0)
            Return
        EndIf
        workEpoch += 1
        processing = False
        repairRequested = True
        recoveredLease = True
    EndIf
    ; No native call between the free-lock check and claiming ownership.
    processing = True
    transitionPending = False
    leaseArmed = True
    leaseStart = now
    leaseUntil = now + 120.0
    Int ticket = workEpoch
    ; Arm the existing lease before native work; PlanNext replaces this on success.
    RegisterForSingleUpdate(125.0)
    Status(2)
    If recoveredLease
        Log("expired update lease; reconciling saved references")
    EndIf
    ; Maintain the legacy fallback even if new pool metadata is not ready yet.
    If NightMode != None
        If Daylight(HourAt(Utility.GetCurrentGameTime()))
            NightMode.SetValue(0.0)
        Else
            NightMode.SetValue(1.0)
        EndIf
    EndIf
    ; Fresh, unvisited settlements have nothing to recover. Older initialized
    ; saves always take EnsureSetup/Reconcile before becoming dormant.
    ; Make this decision under the existing worker lease, never outside it.
    If request != 3 && schemaVersion == 0 && dailyPopulation == 0 && activeIndex < 0 && ResidentCountSafe() == 0 && !ArrivalRelevant()
        If ticket == workEpoch
            PlanDormant()
            If ticket == workEpoch
                processing = False
                transitionWakeArmed = False
                leaseArmed = False
                If transitionPending
                    RegisterForSingleUpdate(0.1)
                EndIf
            EndIf
        EndIf
        Return
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
            transitionWakeArmed = False
            leaseArmed = False
            If transitionPending
                RegisterForSingleUpdate(0.1)
            EndIf
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
    If ConfigBase < 0x1000 || MinPopulation < 1 || MaxPopulation > 9 || MinPopulation > MaxPopulation || !RoadIDs
        SetupFailure()
        Return False
    EndIf
    If RoadIDs.Length < MaxPopulation || RoadIDs.Length > 24
        SetupFailure()
        Return False
    EndIf
    If NightMode == None
        NightMode = Game.GetFormFromFile(ConfigBase + 1, "MoreBrats.esp") as GlobalVariable
    EndIf
    If DayArea == None
        DayArea = Game.GetFormFromFile(ConfigBase + 2, "MoreBrats.esp") as GlobalVariable
    EndIf
    If AvailabilityQuestID != 0 && AvailabilityQuest == None
        AvailabilityQuest = Game.GetFormFromFile(AvailabilityQuestID, SourceMaster) as Quest
        If AvailabilityQuest == None
            Status(3, 33)
            Log("required availability quest unresolved; master=" + SourceMaster + "; local=" + AvailabilityQuestID)
            Return False
        EndIf
    EndIf
    If CityWorld == None
        CityWorld = Game.GetFormFromFile(WorldID, SourceMaster) as WorldSpace
    EndIf
    If CityLocation == None
        CityLocation = Game.GetFormFromFile(LocationID, SourceMaster) as Location
    EndIf
    If TavernPoint == None
        TavernPoint = Game.GetFormFromFile(InnPointID, SourceMaster) as ObjectReference
    EndIf
    If TavernCell == None
        TavernCell = Game.GetFormFromFile(InnCellID, SourceMaster) as Cell
    EndIf
    If RoamFaction == None
        RoamFaction = Game.GetFormFromFile(ConfigBase + 3, "MoreBrats.esp") as Faction
    EndIf
    Status(3)
    If RoamFaction == None || CityWorld == None || NightMode == None || CityLocation == None || TavernPoint == None || TavernCell == None
        SetupFailure()
        Return False
    EndIf
    If !pool || pool.Length != 90
        Actor[] previousPool = pool
        pool = new Actor[90]
        If !pool || pool.Length != 90
            StorageFailure("pool", 90)
            Return False
        EndIf
        Int copyActor = 0
        While (previousPool as Bool) && copyActor < previousPool.Length && copyActor < 90
            pool[copyActor] = previousPool[copyActor]
            copyActor += 1
        EndWhile
        repairRequested = True
    EndIf
    If !roads || roads.Length != 24
        roads = new ObjectReference[24]
        If !roads || roads.Length != 24
            StorageFailure("roads", 24)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !targets || targets.Length != 9
        targets = new ObjectReference[9]
        If !targets || targets.Length != 9
            StorageFailure("targets", 9)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !dayPackageForms || dayPackageForms.Length != 49
        dayPackageForms = new Form[49]
        If !dayPackageForms || dayPackageForms.Length != 49
            StorageFailure("dayPackageForms", 49)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !targetRawForms || targetRawForms.Length != 9
        targetRawForms = new Form[9]
        If !targetRawForms || targetRawForms.Length != 9
            StorageFailure("targetRawForms", 9)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !targetLookupState || targetLookupState.Length != 9
        targetLookupState = new Int[9]
        If !targetLookupState || targetLookupState.Length != 9
            StorageFailure("targetLookupState", 9)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !targetBoundArray || targetBoundArray.Length != 9
        targetBoundArray = new Bool[9]
        If !targetBoundArray || targetBoundArray.Length != 9
            StorageFailure("targetBoundArray", 9)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !targetBoundValue || targetBoundValue.Length != 9
        targetBoundValue = new Bool[9]
        If !targetBoundValue || targetBoundValue.Length != 9
            StorageFailure("targetBoundValue", 9)
            Return False
        EndIf
        repairRequested = True
    EndIf
    Int n = 0
    If !deferredReason || deferredReason.Length != 9
        deferredReason = new Int[9]
        If !deferredReason || deferredReason.Length != 9
            StorageFailure("deferredReason", 9)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !enableUntil || enableUntil.Length != 9
        enableUntil = new Float[9]
        If !enableUntil || enableUntil.Length != 9
            StorageFailure("enableUntil", 9)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !residents || residents.Length != 9
        residents = new Actor[9]
        If !residents || residents.Length != 9
            StorageFailure("residents", 9)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !residentCycle || residentCycle.Length != 9
        residentCycle = new Int[9]
        If !residentCycle || residentCycle.Length != 9
            StorageFailure("residentCycle", 9)
            Return False
        EndIf
        repairRequested = True
        n = 0
        While n < 9
            residentCycle[n] = -100000
            n += 1
        EndWhile
        repairRequested = True
    EndIf
    If !lastArrivalCycle || lastArrivalCycle.Length != 9
        lastArrivalCycle = new Int[9]
        If !lastArrivalCycle || lastArrivalCycle.Length != 9
            StorageFailure("lastArrivalCycle", 9)
            Return False
        EndIf
        repairRequested = True
        n = 0
        While n < 9
            lastArrivalCycle[n] = -100000
            n += 1
        EndWhile
        repairRequested = True
    EndIf
    If !phase || phase.Length != 9
        phase = new Int[9]
        If !phase || phase.Length != 9
            StorageFailure("phase", 9)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !destination || destination.Length != 9
        destination = new Int[9]
        If !destination || destination.Length != 9
            StorageFailure("destination", 9)
            Return False
        EndIf
        repairRequested = True
        n = 0
        While n < 9
            destination[n] = -1
            n += 1
        EndWhile
        repairRequested = True
    EndIf
    If !priorDestination || priorDestination.Length != 9
        priorDestination = new Int[9]
        If !priorDestination || priorDestination.Length != 9
            StorageFailure("priorDestination", 9)
            Return False
        EndIf
        repairRequested = True
        n = 0
        While n < 9
            priorDestination[n] = -1
            n += 1
        EndWhile
        repairRequested = True
    EndIf
    If !arrivalIndex || arrivalIndex.Length != 9
        arrivalIndex = new Int[9]
        If !arrivalIndex || arrivalIndex.Length != 9
            StorageFailure("arrivalIndex", 9)
            Return False
        EndIf
        repairRequested = True
        n = 0
        While n < 9
            arrivalIndex[n] = -1
            n += 1
        EndWhile
        repairRequested = True
    EndIf
    If !selectedVariant || selectedVariant.Length != 9
        selectedVariant = new Int[9]
        If !selectedVariant || selectedVariant.Length != 9
            StorageFailure("selectedVariant", 9)
            Return False
        EndIf
        repairRequested = True
        n = 0
        While n < 9
            selectedVariant[n] = -1
            n += 1
        EndWhile
        repairRequested = True
    EndIf
    If !hiddenCount || hiddenCount.Length != 9
        hiddenCount = new Int[9]
        If !hiddenCount || hiddenCount.Length != 9
            StorageFailure("hiddenCount", 9)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !stallCount || stallCount.Length != 9
        stallCount = new Int[9]
        If !stallCount || stallCount.Length != 9
            StorageFailure("stallCount", 9)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !retireSlot || retireSlot.Length != 9
        retireSlot = new Bool[9]
        If !retireSlot || retireSlot.Length != 9
            StorageFailure("retireSlot", 9)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !disablingSlot || disablingSlot.Length != 9
        disablingSlot = new Bool[9]
        If !disablingSlot || disablingSlot.Length != 9
            StorageFailure("disablingSlot", 9)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !safeRoads || safeRoads.Length != 24
        safeRoads = new Bool[24]
        If !safeRoads || safeRoads.Length != 24
            StorageFailure("safeRoads", 24)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !deadline || deadline.Length != 9
        deadline = new Float[9]
        If !deadline || deadline.Length != 9
            StorageFailure("deadline", 9)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !runUntil || runUntil.Length != 9
        runUntil = new Float[9]
        If !runUntil || runUntil.Length != 9
            StorageFailure("runUntil", 9)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !progressAt || progressAt.Length != 9
        progressAt = new Float[9]
        If !progressAt || progressAt.Length != 9
            StorageFailure("progressAt", 9)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !lastX || lastX.Length != 9
        lastX = new Float[9]
        If !lastX || lastX.Length != 9
            StorageFailure("lastX", 9)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !lastY || lastY.Length != 9
        lastY = new Float[9]
        If !lastY || lastY.Length != 9
            StorageFailure("lastY", 9)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !lastZ || lastZ.Length != 9
        lastZ = new Float[9]
        If !lastZ || lastZ.Length != 9
            StorageFailure("lastZ", 9)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !orphanHidden || orphanHidden.Length != 90
        Int[] previousOrphanHidden = orphanHidden
        orphanHidden = new Int[90]
        If !orphanHidden || orphanHidden.Length != 90
            StorageFailure("orphanHidden", 90)
            Return False
        EndIf
        Int copyHidden = 0
        While (previousOrphanHidden as Bool) && copyHidden < previousOrphanHidden.Length && copyHidden < 90
            orphanHidden[copyHidden] = previousOrphanHidden[copyHidden]
            copyHidden += 1
        EndWhile
        repairRequested = True
    EndIf
    If !EnsureAppearanceStorage()
        Return False
    EndIf
    If repairRequested || bindingsPending || schemaVersion < 7
        diagResolved = 0
        diagRoads = 0
        diagPoolInputs = 0
        diagRoadInputs = 0
        bindingsPending = False
        n = 0
        While n < MaxPopulation * 10
            Actor candidate = None
            If (PoolRefs as Bool) && n < PoolRefs.Length
                candidate = PoolRefs[n]
            EndIf
            If candidate == None
                candidate = Game.GetFormFromFile(ConfigBase + 0x100 + n, "MoreBrats.esp") as Actor
            EndIf
            If candidate != None
                If pool[n] == None && !candidate.IsDisabled()
                    repairRequested = True
                EndIf
                diagPoolInputs += 1
                pool[n] = candidate
                If pool[n] != candidate
                    StorageFailure("pool binding index " + n, 90, 31)
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
        While n < RoadIDs.Length
            ObjectReference road = None
            If (RoadRefs as Bool) && n < RoadRefs.Length
                road = RoadRefs[n]
            EndIf
            If road == None
                road = Game.GetFormFromFile(RoadIDs[n], SourceMaster) as ObjectReference
            EndIf
            If road != None
                diagRoadInputs += 1
                roads[n] = road
                If roads[n] != road
                    StorageFailure("roads binding index " + n, 24, 31)
                    Return False
                EndIf
            Else
                bindingsPending = True
            EndIf
            If roads[n] != None
                diagRoads += 1
            EndIf
            n += 1
        EndWhile
        If !ResolveAppearancePools()
            Return False
        EndIf
    EndIf
    ; Every required array passed its presence/length checks above. Binding
    ; counts now come from runtime storage, not merely resolved input forms.
    diagStorageReady = True
    diagStorageFailure = ""
    If ticket != workEpoch
        Return False
    EndIf
    If repairRequested || schemaVersion < 7
        Status(4)
        Log("reconciling saved references; schema=" + schemaVersion + "; pool resolved=" + diagResolved)
        Reconcile()
        If ticket != workEpoch
            Return False
        EndIf
        ; Commit only after caches, per-slot state and adoption are complete.
        schemaVersion = 7
        poolAudited = True
        nextPoolAuditAt = Utility.GetCurrentGameTime() + 0.25
        diagFullEnabled = FullEnabledCount()
        repairRequested = False
        setupWarning = False
        activeIndex = -1
        If !announced
            announced = True
            Log("controller initialized; schema 7; city=" + CityName + "; pool=" + diagResolved + "; roads=" + diagRoads)
        EndIf
        Log("city reconciliation complete; direct road packages selected per actor")
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
        Log("setup failed; base=" + ConfigBase + "; range=" + MinPopulation + ".." + MaxPopulation + "; road IDs bound=" + (RoadIDs as Bool))
        Log("core properties: faction=" + RoamFaction + "; world=" + CityWorld + "; location=" + CityLocation + "; night=" + NightMode + "; inn cell=" + TavernCell + "; inn marker=" + TavernPoint + "; existing actors retained")
    EndIf
EndFunction

Function Reconcile()
    Int ticket = workEpoch
    Float stamp = Utility.GetCurrentGameTime()
    Int cycle = CycleAt(stamp)
    Int poolSize = AppearancePoolSize()
    Int s = 0
    ; Keep each valid saved resident and its cycle/retirement state. Dedupe
    ; bookkeeping, never disable an actor just because two slots refer to it.
    While s < MaxPopulation
        If ticket != workEpoch
            Return
        EndIf
        Actor saved = residents[s]
        If saved != None
            Bool found = False
            Int n = 0
            While n < poolSize && !found
                If PoolActor(n) == saved
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
            If ticket != workEpoch
                Return
            EndIf
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
                If !saved.IsDisabled()
                    RefreshResident(s, stamp)
                EndIf
            EndIf
        EndIf
        s += 1
    EndWhile
    ; Scan this city's fixed references. A VM stack may
    ; have enabled a child before its saved array assignment was completed.
    Int i = 0
    While i < poolSize
        Actor child = PoolActor(i)
        If child != None && !child.IsDisabled() && !ReferenceInUse(child)
            If ticket != workEpoch
                Return
            EndIf
            Int slot = SlotFromPoolIndex(i)
            If residents[slot] != None
                slot = 0
                While slot < MaxPopulation && residents[slot] != None
                    slot += 1
                EndWhile
            EndIf
            If slot < MaxPopulation
                residents[slot] = child
                residentCycle[slot] = cycle
                lastArrivalCycle[slot] = cycle
                retireSlot[slot] = !InWindow(HourAt(stamp))
                disablingSlot[slot] = False
                hiddenCount[slot] = 0
                destination[slot] = -1
                priorDestination[slot] = -1
                arrivalIndex[slot] = -1
                If todayCycle > -99999 && todayCycle != cycle
                    retireSlot[slot] = True
                EndIf
                RefreshResident(slot, stamp)
                Debug.Trace("[MoreBrats] v1.2.4: adopted saved enabled pool index " + i)
            EndIf
        EndIf
        i += 1
    EndWhile
    ; Recover an empty saved slot without deleting/replacing any enabled actor.
    ; A queued EnableNoWait still owns its reference until observed or timed out.
    Float realNow = Utility.GetCurrentRealTime()
    s = 0
    While s < MaxPopulation
        If ticket != workEpoch
            Return
        EndIf
        If enableUntil[s] > realNow + 120.0
            enableUntil[s] = 0.0
        EndIf
        If residents[s] == None && lastArrivalCycle[s] == cycle
            Int variant = selectedVariant[s]
            Actor pendingActor = None
            If variant >= 0 && variant < 200 && enableUntil[s] > realNow
                pendingActor = PoolActor(PoolIndex(s, variant))
            EndIf
            If pendingActor != None && !ReferenceInUse(pendingActor)
                residents[s] = pendingActor
                residentCycle[s] = cycle
                RefreshResident(s, stamp)
                Log("restored pending enable bookkeeping; slot=" + s)
            ElseIf PoolSlotDisabled(s)
                If ticket != workEpoch
                    Return
                EndIf
                lastArrivalCycle[s] = -100000
                enableUntil[s] = 0.0
                arrivalIndex[s] = -1
                Log("rearmed empty saved arrival slot=" + s)
            EndIf
        EndIf
        s += 1
    EndWhile
    If ticket != workEpoch
        Return
    EndIf
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
    Int ticket = workEpoch
    orphanPresent = False
    Int poolSize = AppearancePoolSize()
    Int i = 0
    While i < poolSize
        Actor child = PoolActor(i)
        If child != None && !child.IsDisabled() && !ReferenceInUse(child)
            If ticket != workEpoch
                Return
            EndIf
            orphanPresent = True
            If child.GetFactionRank(RoamFaction) != 3
                child.SetFactionRank(RoamFaction, 3)
                child.EvaluatePackage()
            EndIf
            StoreOrphanSamples(i, RemovalObservation(child, OrphanSamples(i)))
            If OrphanSamples(i) >= 2 && !Game.GetPlayer().HasLOS(child)
                If ticket != workEpoch || ReferenceInUse(child)
                    Return
                EndIf
                child.DisableNoWait(False)
            EndIf
        Else
            StoreOrphanSamples(i, 0)
        EndIf
        i += 1
    EndWhile
EndFunction

Int Function ResidentCount()
    Int count = 0
    Int s = 0
    While s < MaxPopulation
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
    ; Arrival visibility, player distance and occupancy are intentionally irrelevant.
    Return RoadBlock(point)
EndFunction

Bool Function SafeArrival(ObjectReference point)
    Return RoadValid(point)
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
        ElseIf viewer.GetWorldSpace() == CityWorld && childCell != playerCell
            ; A different town can share Tamriel. Require unloaded 3D PLUS
            ; an unattached distant cell, following the existing arrival rule.
            Float separation = viewer.GetDistance(child)
            If childCell != None
                If !childCell.IsAttached() && separation >= 4096.0
                    Return 2
                EndIf
            ElseIf separation >= 8192.0
                Return 2
            EndIf
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
        Int pick = Utility.RandomInt(0, RoadIDs.Length - 1)
        If pick != destination[s] && pick != priorDestination[s] && RoadValid(roads[pick])
            Float distance = child.GetDistance(roads[pick])
            Bool appropriate = distance >= 1800.0
            If !farTrip
                appropriate = distance >= 450.0 && distance <= 2400.0
            EndIf
            Bool occupiedDestination = False
            Int peer = 0
            While peer < MaxPopulation
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
    Int offset = Utility.RandomInt(0, RoadIDs.Length - 1)
    tries = 0
    While tries < RoadIDs.Length
        Int candidate = (offset + tries) % RoadIDs.Length
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
    If Utility.RandomInt(0, 9999) < 3325
        runUntil[s] = stamp + Utility.RandomFloat(2.66, 7.98) / 1440.0
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
    While s < MaxPopulation
        If residents[s] == child
            Return True
        EndIf
        s += 1
    EndWhile
    Return False
EndFunction
; New city pools use ten fixed references per slot; Whiterun is untouched.
Int Function PoolIndex(Int slot, Int variant)
    If variant >= 40
        Return (MaxPopulation * 40) + (variant - 40) * MaxPopulation + slot
    EndIf
    If variant >= 10
        Return (variant / 10) * (MaxPopulation * 10) + slot * 10 + variant % 10
    EndIf
    Return slot * 10 + variant
EndFunction
Int Function SlotFromPoolIndex(Int index)
    If index >= (MaxPopulation * 40)
        Return (index - (MaxPopulation * 40)) % MaxPopulation
    EndIf
    If index >= (MaxPopulation * 10)
        Return (index % (MaxPopulation * 10)) / 10
    EndIf
    Return index / 10
EndFunction
Bool Function PoolSlotDisabled(Int s)
    Int v = 0
    While v < 200
        Actor candidate = PoolActor(PoolIndex(s, v))
        If candidate != None && !candidate.IsDisabled()
            Return False
        EndIf
        v += 1
    EndWhile
    Return True
EndFunction
Bool Function ClearArrivalPoint(Int index, Int slot)
    ObjectReference point = roads[index]
    Int peer = 0
    While peer < MaxPopulation
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
        repairRequested = True
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
        repairRequested = True
        Defer(s, 21, "slot contains an enabled reference awaiting adoption/retirement")
        Return
    EndIf
    If selectedVariant[s] < 0
        Int race = Utility.RandomInt(1, 4)
        Int gender = Utility.RandomInt(1, 2) - 1
        Int clothing = Utility.RandomInt(0, 4)
        If clothing < 3
            selectedVariant[s] = gender * 3 + clothing
        Else
            selectedVariant[s] = 6 + gender * 2 + clothing - 3
        EndIf
        selectedVariant[s] += (race - 1) * 10
        selectedVariant[s] = SelectDonorVariant(race, gender, clothing, selectedVariant[s])
    EndIf
    If PoolActor(PoolIndex(s, selectedVariant[s])) == None
        diagAppearanceFallbacks += 1
        Log("appearance binding unavailable; selected variant=" + selectedVariant[s] + "; using existing per-slot fallback")
        Int variantOffset = Utility.RandomInt(0, 199)
        Int v = 0
        selectedVariant[s] = -1
        While v < 200 && selectedVariant[s] < 0
            Int candidateVariant = (variantOffset + v) % 200
            If PoolActor(PoolIndex(s, candidateVariant)) != None
                selectedVariant[s] = candidateVariant
            EndIf
            v += 1
        EndWhile
        If selectedVariant[s] < 0
            Defer(s, 11, "no resolved actor reference in this slot")
            Return
        EndIf
    EndIf
    Actor chosen = PoolActor(PoolIndex(s, selectedVariant[s]))
    diagSelectedActor = chosen
    If chosen == None
        Defer(s, 11, "actor readback returned None; variant=" + selectedVariant[s])
        Return
    EndIf
    If ReferenceInUse(chosen)
        Defer(s, 25, "selected actor is already tracked in another resident slot")
        Return
    EndIf
    diagTargetContext = "TryArrival.random exterior door / existing outdoor ground"
    Int index = DoorArrivalIndex()
    If index < 0
        Defer(s, 19, "no valid existing outdoor ground reference; door fallback also unavailable")
        Return
    EndIf
    If ticket != workEpoch
        Return
    EndIf
    PlaceArrival(s, cycle, chosen, index)
EndFunction

Bool Function PlayerInCity()
    Actor viewer = Game.GetPlayer()
    ; All four towns share Tamriel. World equality alone is not town relevance.
    If TavernCell != None && viewer.GetParentCell() == TavernCell
        Return True
    EndIf
    Location here = viewer.GetCurrentLocation()
    If here != None && CityLocation != None
        If here == CityLocation || CityLocation.IsChild(here)
            Return True
        EndIf
    EndIf
    ; Bounded street proximity covers exterior location seams, using only the
    ; same verified town points. It never gates arrival preparation.
    If viewer.GetWorldSpace() == CityWorld && !viewer.IsInInterior() && (roads as Bool) && (RoadIDs as Bool)
        Int n = 0
        While n < RoadIDs.Length && n < roads.Length
            If roads[n] != None && viewer.GetDistance(roads[n]) <= 4096.0
                Return True
            EndIf
            n += 1
        EndWhile
    EndIf
    Return False
EndFunction

Function Tick()
    ; Skaal only: resume with the vanilla village after its liberation.
    If AvailabilityQuest != None && !AvailabilityQuest.IsStageDone(AvailabilityStage) && !AvailabilityQuest.IsCompleted()
        Status(18, 32)
        Return
    EndIf
    Float stamp = Utility.GetCurrentGameTime()
    Float hour = HourAt(stamp)
    Int cycle = CycleAt(stamp)
    Int ticket = workEpoch
    Bool relevant = PlayerInCity()
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
    If dailyPopulation < MinPopulation || dailyPopulation > MaxPopulation
        todayCycle = -100000
    EndIf
    If cycle != todayCycle
        todayCycle = cycle
        dailyPopulation = Utility.RandomInt(MinPopulation, MaxPopulation)
        Status(6)
        Log("daily population selected=" + dailyPopulation + "; cycle=" + cycle + "; hour=" + hour)
        Int reset = 0
        While reset < MaxPopulation
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
    Int s = 0
    While s < MaxPopulation
        Actor child = residents[s]
        If child != None
            If enableUntil[s] > 0.0 && !child.IsDisabled()
                enableUntil[s] = 0.0
                Status(12)
                Log("enabled confirmed; slot=" + s + "; ref=" + child)
            EndIf
            If child.IsDisabled() && !disablingSlot[s] && Utility.GetCurrentRealTime() >= enableUntil[s]
                ; Unexpectedly disabled/current-day actors must not reserve an empty
                ; slot for the rest of the day. This is not planned retirement.
                If Daylight(hour) && !retireSlot[s] && residentCycle[s] == cycle
                    lastArrivalCycle[s] = -100000
                    Log("unexpected disabled resident; rearming slot=" + s)
                EndIf
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
                ElseIf relevant && !child.IsDisabled()
                    UpdateRoaming(s, stamp)
                EndIf
            EndIf
        EndIf
        ; Native calls may yield; a cancelled worker must stop before later slots.
        If ticket != workEpoch
            Return
        EndIf
        stamp = Utility.GetCurrentGameTime()
        hour = HourAt(stamp)
        cycle = CycleAt(stamp)
        If cycle != todayCycle
            Return
        EndIf
        s += 1
    EndWhile
    ; One serialized due arrival per callback, never a missed-event burst.
    ProcessArrival()
    If !Daylight(hour) && ResidentCount() == 0
        Status(7, 20)
    EndIf
EndFunction

Function PlanNext()
    UnregisterForUpdate()
    UnregisterForUpdateGameTime()
    If schemaVersion < 7 || repairRequested
        If diagStorageReady
            RegisterForSingleUpdate(1.0)
        Else
            RegisterForSingleUpdate(30.0)
        EndIf
        Return
    EndIf
    If !ArrivalRelevant() && ResidentCountSafe() == 0 && !orphanPresent
        PlanDormant()
        Return
    EndIf
    If !ArrivalRelevant()
        RegisterForSingleUpdate(120.0)
        ; Empty cities also need the next08:00 game-time boundary.
        Float hourAway = HourAt(Utility.GetCurrentGameTime())
        Float until = 0.0
        If hourAway < 3.0
            until = 3.0 - hourAway
        ElseIf hourAway < 8.0
            until = 8.0 - hourAway
        ElseIf hourAway < 19.0
            until = 19.0 - hourAway
        Else
            until = 27.0 - hourAway
        EndIf
        If until < 0.05
            until = 0.05
        EndIf
        RegisterForSingleUpdateGameTime(until)
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
    Int s = 0
    While s < MaxPopulation
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
        EndIf
        s += 1
    EndWhile
    If Daylight(hour) && ArrivalRelevant() && nextArrivalAt > 0.0 && HasPendingArrivals()
        Float arrivalDelta = (nextArrivalAt - stamp) * 24.0
        If arrivalDelta < delta
            delta = arrivalDelta
        EndIf
    EndIf
    ; Preserve the documented safe lower bound for game-time update intervals.
    If delta < 0.05
        delta = 0.05
    EndIf
    RegisterForSingleUpdateGameTime(delta)
    If retirementPending
        RegisterForSingleUpdate(10.0)
    Else
        Float fallback = ArrivalFallbackDelay()
        Float confirmation = PendingEnableDelay()
        If confirmation > 0.0 && (fallback <= 0.0 || confirmation < fallback)
            fallback = confirmation
        EndIf
        If fallback > 0.0
            RegisterForSingleUpdate(fallback)
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
        If DiagnosticGlobals[n] == None && ConfigBase >= 0x1000
            DiagnosticGlobals[n] = Game.GetFormFromFile(ConfigBase + 0x10 + n, "MoreBrats.esp") as GlobalVariable
        EndIf
        n += 1
    EndWhile
    WriteDiagnostic(10, 1204.0)
    WriteDiagnostic(11, 1204.0)
    WriteDiagnostic(16, 1204.0)
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
        Debug.Trace("[MoreBrats] v1.2.4 [" + CityName + "] " + message)
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
    If (residents as Bool) && residents.Length == 9
        Int s = 0
        While s < MaxPopulation
            Actor child = residents[s]
            If child != None && !child.IsDisabled()
                count += 1
            EndIf
            s += 1
        EndWhile
    EndIf
    Return count
EndFunction

Int Function FullEnabledCount()
    Int count = 0
    If (pool as Bool)
        Int n = 0
        Int poolSize = AppearancePoolSize()
        While n < poolSize
            Actor candidate = PoolActor(n)
            If candidate != None && !candidate.IsDisabled()
                count += 1
            EndIf
            n += 1
        EndWhile
    EndIf
    Return count
EndFunction
Function PublishSnapshot()
    Int count = EnabledCount()
    If diagStorageReady && count > ResidentCountSafe() && !orphanPresent
        repairRequested = True
        Log("enabled/tracked mismatch; enabled=" + count + "; tracked=" + ResidentCountSafe() + "; reconciliation requested")
    EndIf
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
    If !residents || residents.Length != 9
        Return 0
    EndIf
    Return ResidentCount()
EndFunction
Function ShowStatus()
    ; Report the last completed audit without rescanning thousands of actors
    ; before the requested popup. Current stage/storage fields remain live.
    Int liveEnabled = EnabledCount()
    Int snapshotEnabled = -1
    If (DiagnosticGlobals as Bool) && DiagnosticGlobals.Length == 17
        If DiagnosticGlobals[4] != None
            snapshotEnabled = DiagnosticGlobals[4].GetValue() as Int
        EndIf
    EndIf
    String message = "[MoreBrats] v1.2.4 " + CityName + "\nQuest running=" + IsRunning() + "; schema=" + schemaVersion
    message += "\nPlayer relevant=" + PlayerInCity() + "; range=" + MinPopulation + ".." + MaxPopulation
    message += "\nStage=" + diagStage + "; reason=" + diagReason + "; ticks=" + diagTicks
    message += "\nPopulation=" + dailyPopulation + "; enabled NOW=" + liveEnabled + "; tracked/reserved=" + ResidentCountSafe() + "; previous sample=" + snapshotEnabled
    Int roadCount = 0
    If (RoadIDs as Bool)
        roadCount = RoadIDs.Length
    EndIf
    message += "\nPool=" + diagResolved + "/" + AppearancePoolSize() + "; roads=" + diagRoads + "/" + roadCount
    message += "\nResolved inputs=" + diagPoolInputs + "; road inputs=" + diagRoadInputs
    message += "\nAppended bindings: resolved=" + diagNamedResolved + "; stable-ID recovered=" + diagNamedIDRecovered + "; missing=" + diagNamedMissing
    message += "; catalog=" + diagNamedCatalogState + " (0=unavailable,1=valid,2=wrong size)"
    message += "\nAppearance fallback attempts=" + diagAppearanceFallbacks
    If (selectedVariant as Bool) && diagSlot >= 0 && diagSlot < selectedVariant.Length
        message += "; selected variant=" + selectedVariant[diagSlot]
    EndIf
    message += "\nRuntime storage ready=" + diagStorageReady + "; failure=" + diagStorageFailure
    message += "\nArrivals: due(game days)=" + nextArrivalAt + "; cycle=" + arrivalScheduleCycle + "; relevant=" + ArrivalRelevant()
    message += "\nEnabled sample counts tracked residents; last full census=" + diagFullEnabled + "; next audit(game days)=" + nextPoolAuditAt
    message += "\nArrival 42=waiting for game-time arrival; 44=Enable returned but actor disabled"
    message += "\nArrival exterior door=" + diagArrivalDoor + "; road fallback=" + diagDoorFallback
    message += "\nConfirmed enables this script=" + diagEnableConfirmed + "; invalid placement retries=" + diagPlacementRetries
    message += "\nPer-slot state=" + ActivationStates()
    message += "\nCallbacks: real=" + diagRealUpdates + "; game=" + diagGameUpdates
    message += "\nNow(game days)=" + Utility.GetCurrentGameTime() + "; due in(game min)=" + (nextArrivalAt - Utility.GetCurrentGameTime()) * 1440.0
    message += "\nPlayer world=" + Game.GetPlayer().GetWorldSpace() + "; expected world=" + CityWorld
    message += "\nPlayer location=" + Game.GetPlayer().GetCurrentLocation()
    message += "\nDeadline fallback clock=" + arrivalTimeScale
    message += "\nLast non-busy stage=" + lastWorkerStage
    message += "\nTransition queued=" + transitionPending + "; lease remaining=" + (leaseUntil - Utility.GetCurrentRealTime())
    message += "\nBusy=" + processing + "; epoch=" + workEpoch + "; lease age=" + (Utility.GetCurrentRealTime() - leaseStart)
    message += "\nSlot=" + diagSlot + "; goal=" + diagGoal
    message += "\nPer-slot reasons=" + SlotCodes(deferredReason)
    message += "\nLast target check=" + diagTargetContext + "; lookup=" + diagLookupResult
    message += "\nExpected=" + diagLookupFile + "; local=" + diagExpectedID + "; raw=" + diagRawLookup
    message += "\nSelected ref=" + diagSelectedActor + "\nRoad destination=" + diagSelectedPoint
    message += "\nArrivals require local relevance; suspended deadlines are retained."
    message += "\n19=no free road;21=reconcile;24=post-MoveTo safety;40=distance;41=LOS;42=not due;91/30=array failure"
    Debug.MessageBox(message)
EndFunction
String Function SlotCodes(Int[] codes)
    If !codes
        Return "uninitialized"
    EndIf
    String result = ""
    Int n = 0
    While n < MaxPopulation
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
    If index < 0 || index >= RoadIDs.Length
        Return None
    EndIf
    Return roads[index]
EndFunction
Bool Function RequiredDayPackage(Int slot, Int index, String where)
    If !dayPackageForms || index < 0 || index >= 1 + RoadIDs.Length * 2
        MissingTarget(slot, where, 20, 0, None)
        Return False
    EndIf
    Int localID = ConfigBase + 0x40 + index
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
    If goal < 0 || goal >= RoadIDs.Length || !roads
        MissingTarget(slot, where + ".road index", 23, 0, None)
        Return False
    EndIf
    If roads[goal] == None || !RoadValid(roads[goal])
        MissingTarget(slot, where + ".roads[]", 24, 0, roads[goal])
        Return False
    EndIf
    Int roadID = RoadIDs[goal]
    ; The package's fixed reference must match the cached goal. A legacy
    ; arrival fallback at a different FormID is not a valid direct travel goal.
    If roads[goal] != Game.GetFormFromFile(roadID, SourceMaster)
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
        diagLookupFile = SourceMaster
    EndIf
    Defer(slot, 12, "required DAY AI dependency missing; where=" + where + "; lookup=" + lookup + "; expected=" + diagLookupFile + "; local=" + expected + "; raw=" + raw)
EndFunction

; Additive appearance storage only. Legacy Nord arrays/indices stay unchanged.
Int Function AppearancePoolSize()
    Return (MaxPopulation * 40) + (MaxPopulation * 160)
EndFunction
Actor Function PoolActor(Int index)
    If index < 0 || index >= AppearancePoolSize()
        Return None
    EndIf
    If index >= (MaxPopulation * 40)
        Return DonorActorRead(index - (MaxPopulation * 40))
    EndIf
    Int group = index / (MaxPopulation * 10)
    Int localIndex = index % (MaxPopulation * 10)
    If group == 0
        If !pool || localIndex >= pool.Length
            Return None
        EndIf
        Return pool[localIndex]
    ElseIf group == 1
        If !ImperialRefs || localIndex >= ImperialRefs.Length
            Return None
        EndIf
        Return ImperialRefs[localIndex]
    ElseIf group == 2
        If !BretonRefs || localIndex >= BretonRefs.Length
            Return None
        EndIf
        Return BretonRefs[localIndex]
    EndIf
    If !RedguardRefs || localIndex >= RedguardRefs.Length
            Return None
        EndIf
        Return RedguardRefs[localIndex]
EndFunction
Int Function OrphanSamples(Int index)
    If index >= (MaxPopulation * 40)
        Return DonorHiddenRead(index - (MaxPopulation * 40))
    EndIf
    Int group = index / (MaxPopulation * 10)
    Int localIndex = index % (MaxPopulation * 10)
    If group == 0
        Return orphanHidden[localIndex]
    ElseIf group == 1
        Return imperialHidden[localIndex]
    ElseIf group == 2
        Return bretonHidden[localIndex]
    EndIf
    Return redguardHidden[localIndex]
EndFunction
Function StoreOrphanSamples(Int index, Int samples)
    If index >= (MaxPopulation * 40)
        DonorHiddenWrite(index - (MaxPopulation * 40), samples)
        Return
    EndIf
    Int group = index / (MaxPopulation * 10)
    Int localIndex = index % (MaxPopulation * 10)
    If group == 0
        orphanHidden[localIndex] = samples
    ElseIf group == 1
        imperialHidden[localIndex] = samples
    ElseIf group == 2
        bretonHidden[localIndex] = samples
    Else
        redguardHidden[localIndex] = samples
    EndIf
EndFunction
Bool Function EnsureAppearanceStorage()
    If !ImperialRefs || ImperialRefs.Length < (MaxPopulation * 10)
        ImperialRefs = new Actor[90]
        If !ImperialRefs || ImperialRefs.Length < (MaxPopulation * 10)
            StorageFailure("ImperialRefs", (MaxPopulation * 10))
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !BretonRefs || BretonRefs.Length < (MaxPopulation * 10)
        BretonRefs = new Actor[90]
        If !BretonRefs || BretonRefs.Length < (MaxPopulation * 10)
            StorageFailure("BretonRefs", (MaxPopulation * 10))
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !RedguardRefs || RedguardRefs.Length < (MaxPopulation * 10)
        RedguardRefs = new Actor[90]
        If !RedguardRefs || RedguardRefs.Length < (MaxPopulation * 10)
            StorageFailure("RedguardRefs", (MaxPopulation * 10))
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !imperialHidden || imperialHidden.Length < 90
        imperialHidden = new Int[90]
        If !imperialHidden || imperialHidden.Length < 90
            StorageFailure("imperialHidden", 90)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !bretonHidden || bretonHidden.Length < 90
        bretonHidden = new Int[90]
        If !bretonHidden || bretonHidden.Length < 90
            StorageFailure("bretonHidden", 90)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If !redguardHidden || redguardHidden.Length < 90
        redguardHidden = new Int[90]
        If !redguardHidden || redguardHidden.Length < 90
            StorageFailure("redguardHidden", 90)
            Return False
        EndIf
        repairRequested = True
    EndIf
    Return EnsureNamedDonorStorage()
EndFunction
Bool Function ResolveAppearancePools()
    Int n0 = 0
    While n0 < (MaxPopulation * 10)
        Actor candidate0 = ImperialRefs[n0]
        If candidate0 == None
            candidate0 = Game.GetFormFromFile((0x20000 + ConfigBase) + 0x100 + 0 * (MaxPopulation * 10) + n0, "MoreBrats.esp") as Actor
            ImperialRefs[n0] = candidate0
        EndIf
        If candidate0 != None
            If ImperialRefs[n0] != candidate0
                StorageFailure("ImperialRefs binding readback", (MaxPopulation * 10), 31)
                Return False
            EndIf
            diagResolved += 1
            diagPoolInputs += 1
        Else
            bindingsPending = True
        EndIf
        n0 += 1
    EndWhile
    Int n1 = 0
    While n1 < (MaxPopulation * 10)
        Actor candidate1 = BretonRefs[n1]
        If candidate1 == None
            candidate1 = Game.GetFormFromFile((0x20000 + ConfigBase) + 0x100 + 1 * (MaxPopulation * 10) + n1, "MoreBrats.esp") as Actor
            BretonRefs[n1] = candidate1
        EndIf
        If candidate1 != None
            If BretonRefs[n1] != candidate1
                StorageFailure("BretonRefs binding readback", (MaxPopulation * 10), 31)
                Return False
            EndIf
            diagResolved += 1
            diagPoolInputs += 1
        Else
            bindingsPending = True
        EndIf
        n1 += 1
    EndWhile
    Int n2 = 0
    While n2 < (MaxPopulation * 10)
        Actor candidate2 = RedguardRefs[n2]
        If candidate2 == None
            candidate2 = Game.GetFormFromFile((0x20000 + ConfigBase) + 0x100 + 2 * (MaxPopulation * 10) + n2, "MoreBrats.esp") as Actor
            RedguardRefs[n2] = candidate2
        EndIf
        If candidate2 != None
            If RedguardRefs[n2] != candidate2
                StorageFailure("RedguardRefs binding readback", (MaxPopulation * 10), 31)
                Return False
            EndIf
            diagResolved += 1
            diagPoolInputs += 1
        Else
            bindingsPending = True
        EndIf
        n2 += 1
    EndWhile
    diagNamedResolved = 0
    diagNamedIDRecovered = 0
    diagNamedMissing = 0
    diagNamedCatalogState = 0
    Bool namedCatalogValid = False
    If NamedDonorForms != None
        namedCatalogValid = NamedDonorForms.GetSize() == (MaxPopulation * 160)
        If namedCatalogValid
            diagNamedCatalogState = 1
        Else
            diagNamedCatalogState = 2
        EndIf
    EndIf
    Int namedIndex = 0
    While namedIndex < (MaxPopulation * 160)
        ; Match v1.1.0's pool contract: keep valid saved bindings first,
        ; then try editor binding, then the verified stable local actor ID.
        Actor namedActor = DonorActorRead(namedIndex)
        If namedActor == None && namedCatalogValid
            namedActor = NamedDonorForms.GetAt(namedIndex) as Actor
        EndIf
        If namedActor == None
            namedActor = Game.GetFormFromFile((0x100000 + ConfigBase * 16) + 0x2000 + namedIndex, "MoreBrats.esp") as Actor
            If namedActor != None
                diagNamedIDRecovered += 1
            EndIf
        EndIf
        DonorActorWrite(namedIndex, namedActor)
        If DonorActorRead(namedIndex) != namedActor
            StorageFailure("named donor binding readback", (MaxPopulation * 160), 31)
            Return False
        EndIf
        If namedActor != None
            diagNamedResolved += 1
            diagResolved += 1
            diagPoolInputs += 1
        Else
            diagNamedMissing += 1
            bindingsPending = True
        EndIf
        namedIndex += 1
    EndWhile
    Return True
EndFunction


; Independent donor draw inside the already selected race/gender.
Int Function SelectDonorVariant(Int race, Int gender, Int clothing, Int legacyVariant)
    If race == 1 && gender == 0
        Int donor10 = Utility.RandomInt(0, 15)
        If donor10 > 0
            Return 40 + (donor10 - 1) * 5 + clothing
        EndIf
        Return legacyVariant
    EndIf
    If race == 1 && gender == 1
        Int donor11 = Utility.RandomInt(0, 12)
        If donor11 > 0
            Return 115 + (donor11 - 1) * 5 + clothing
        EndIf
        Return legacyVariant
    EndIf
    If race == 2 && gender == 0
        Int donor20 = Utility.RandomInt(0, 1)
        If donor20 > 0
            Return 175 + (donor20 - 1) * 5 + clothing
        EndIf
        Return legacyVariant
    EndIf
    If race == 2 && gender == 1
        Int donor21 = Utility.RandomInt(0, 1)
        If donor21 > 0
            Return 180 + (donor21 - 1) * 5 + clothing
        EndIf
        Return legacyVariant
    EndIf
    If race == 3 && gender == 0
        Int donor30 = Utility.RandomInt(0, 1)
        If donor30 > 0
            Return 185 + (donor30 - 1) * 5 + clothing
        EndIf
        Return legacyVariant
    EndIf
    If race == 4 && gender == 0
        Int donor40 = Utility.RandomInt(0, 1)
        If donor40 > 0
            Return 190 + (donor40 - 1) * 5 + clothing
        EndIf
        Return legacyVariant
    EndIf
    If race == 4 && gender == 1
        Int donor41 = Utility.RandomInt(0, 1)
        If donor41 > 0
            Return 195 + (donor41 - 1) * 5 + clothing
        EndIf
        Return legacyVariant
    EndIf
    Return legacyVariant
EndFunction

Bool Function EnsureNamedDonorStorage()
    If NamedDonorForms == None
        NamedDonorForms = Game.GetFormFromFile((0x100000 + ConfigBase * 16) + 0x1000, "MoreBrats.esp") as FormList
    EndIf
    If (donorActors0 as Bool) && donorActors0.Length != 128
        StorageFailure("donorActors0 saved length", 128)
        Return False
    EndIf
    If !donorActors0
        donorActors0 = new Actor[128]
        If !donorActors0 || donorActors0.Length != 128
            StorageFailure("donorActors0", 128)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If (donorHidden0 as Bool) && donorHidden0.Length != 128
        StorageFailure("donorHidden0 saved length", 128)
        Return False
    EndIf
    If !donorHidden0
        donorHidden0 = new Int[128]
        If !donorHidden0 || donorHidden0.Length != 128
            StorageFailure("donorHidden0", 128)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If (donorActors1 as Bool) && donorActors1.Length != 128
        StorageFailure("donorActors1 saved length", 128)
        Return False
    EndIf
    If !donorActors1
        donorActors1 = new Actor[128]
        If !donorActors1 || donorActors1.Length != 128
            StorageFailure("donorActors1", 128)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If (donorHidden1 as Bool) && donorHidden1.Length != 128
        StorageFailure("donorHidden1 saved length", 128)
        Return False
    EndIf
    If !donorHidden1
        donorHidden1 = new Int[128]
        If !donorHidden1 || donorHidden1.Length != 128
            StorageFailure("donorHidden1", 128)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If (donorActors2 as Bool) && donorActors2.Length != 128
        StorageFailure("donorActors2 saved length", 128)
        Return False
    EndIf
    If !donorActors2
        donorActors2 = new Actor[128]
        If !donorActors2 || donorActors2.Length != 128
            StorageFailure("donorActors2", 128)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If (donorHidden2 as Bool) && donorHidden2.Length != 128
        StorageFailure("donorHidden2 saved length", 128)
        Return False
    EndIf
    If !donorHidden2
        donorHidden2 = new Int[128]
        If !donorHidden2 || donorHidden2.Length != 128
            StorageFailure("donorHidden2", 128)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If (donorActors3 as Bool) && donorActors3.Length != 128
        StorageFailure("donorActors3 saved length", 128)
        Return False
    EndIf
    If !donorActors3
        donorActors3 = new Actor[128]
        If !donorActors3 || donorActors3.Length != 128
            StorageFailure("donorActors3", 128)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If (donorHidden3 as Bool) && donorHidden3.Length != 128
        StorageFailure("donorHidden3 saved length", 128)
        Return False
    EndIf
    If !donorHidden3
        donorHidden3 = new Int[128]
        If !donorHidden3 || donorHidden3.Length != 128
            StorageFailure("donorHidden3", 128)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If (donorActors4 as Bool) && donorActors4.Length != 128
        StorageFailure("donorActors4 saved length", 128)
        Return False
    EndIf
    If !donorActors4
        donorActors4 = new Actor[128]
        If !donorActors4 || donorActors4.Length != 128
            StorageFailure("donorActors4", 128)
            Return False
        EndIf
        repairRequested = True
    EndIf
    If (donorHidden4 as Bool) && donorHidden4.Length != 128
        StorageFailure("donorHidden4 saved length", 128)
        Return False
    EndIf
    If !donorHidden4
        donorHidden4 = new Int[128]
        If !donorHidden4 || donorHidden4.Length != 128
            StorageFailure("donorHidden4", 128)
            Return False
        EndIf
        repairRequested = True
    EndIf
    Return True
EndFunction

Int Function DonorHiddenRead(Int index)
    Int page = index / 128
    Int localIndex = index % 128
    If page == 0
        Return donorHidden0[localIndex]
    ElseIf page == 1
        Return donorHidden1[localIndex]
    ElseIf page == 2
        Return donorHidden2[localIndex]
    ElseIf page == 3
        Return donorHidden3[localIndex]
    ElseIf page == 4
        Return donorHidden4[localIndex]
    EndIf
    Return 0
EndFunction

Function DonorHiddenWrite(Int index, Int samples)
    Int page = index / 128
    Int localIndex = index % 128
    If page == 0
        donorHidden0[localIndex] = samples
    ElseIf page == 1
        donorHidden1[localIndex] = samples
    ElseIf page == 2
        donorHidden2[localIndex] = samples
    ElseIf page == 3
        donorHidden3[localIndex] = samples
    ElseIf page == 4
        donorHidden4[localIndex] = samples
    EndIf
EndFunction

Actor Function DonorActorRead(Int index)
    Int page = index / 128
    Int localIndex = index % 128
    If page == 0
        If !donorActors0 || localIndex >= donorActors0.Length
            Return None
        EndIf
        Return donorActors0[localIndex]
    ElseIf page == 1
        If !donorActors1 || localIndex >= donorActors1.Length
            Return None
        EndIf
        Return donorActors1[localIndex]
    ElseIf page == 2
        If !donorActors2 || localIndex >= donorActors2.Length
            Return None
        EndIf
        Return donorActors2[localIndex]
    ElseIf page == 3
        If !donorActors3 || localIndex >= donorActors3.Length
            Return None
        EndIf
        Return donorActors3[localIndex]
    ElseIf page == 4
        If !donorActors4 || localIndex >= donorActors4.Length
            Return None
        EndIf
        Return donorActors4[localIndex]
    EndIf
    Return None
EndFunction

Function DonorActorWrite(Int index, Actor child)
    Int page = index / 128
    Int localIndex = index % 128
    If page == 0
        donorActors0[localIndex] = child
    ElseIf page == 1
        donorActors1[localIndex] = child
    ElseIf page == 2
        donorActors2[localIndex] = child
    ElseIf page == 3
        donorActors3[localIndex] = child
    ElseIf page == 4
        donorActors4[localIndex] = child
    EndIf
EndFunction


Bool Function ArrivalRelevant()
    If PlayerInCity()
        Return True
    EndIf
    ; Cold exterior location seams can use the same direct VMAD road bindings
    ; before the private road cache exists. No new destinations or boundaries.
    Actor viewer = Game.GetPlayer()
    If CityWorld != None && viewer.GetWorldSpace() == CityWorld && !viewer.IsInInterior() && (RoadRefs as Bool)
        Int n = 0
        While n < RoadRefs.Length
            If RoadRefs[n] != None && viewer.GetDistance(RoadRefs[n]) <= 4096.0
                Return True
            EndIf
            n += 1
        EndWhile
    EndIf
    Return False
EndFunction

Function PlanDormant()
    UnregisterForUpdate()
    UnregisterForUpdateGameTime()
    arrivalWasRelevant = False
    Float hour = HourAt(Utility.GetCurrentGameTime())
    Float until = 32.0 - hour
    If hour < 8.0
        until = 8.0 - hour
    EndIf
    If until < 0.05
        until = 0.05
    EndIf
    ; One daily wake, plus existing load/cell/location events. No arrival polling.
    RegisterForSingleUpdateGameTime(until)
EndFunction

Bool Function HasPendingArrivals()
    If ResidentCount() >= dailyPopulation
        Return False
    EndIf
    Int s = 0
    While s < dailyPopulation
        If residents[s] == None
            Return True
        EndIf
        s += 1
    EndWhile
    Return False
EndFunction

Function ProcessArrival()
    Float stamp = Utility.GetCurrentGameTime()
    Int cycle = CycleAt(stamp)
    Bool relevant = ArrivalRelevant()
    Bool newCycle = arrivalScheduleCycle != cycle
    If newCycle
        arrivalScheduleCycle = cycle
        nextArrivalAt = 0.0
    EndIf
    If !relevant
        arrivalWasRelevant = False
        Return
    EndIf
    ; Retain full-pool recovery, but not a census on every roaming callback.
    If !poolAudited || stamp >= nextPoolAuditAt
        Int ticket = workEpoch
        Int full = FullEnabledCount()
        If ticket != workEpoch
            Return
        EndIf
        diagFullEnabled = full
        poolAudited = True
        nextPoolAuditAt = stamp + 0.25
        If full > EnabledCount()
            repairRequested = True
            Status(16, 21)
            Return
        EndIf
    EndIf
    Bool wasRelevant = arrivalWasRelevant
    arrivalWasRelevant = True
    If !Daylight(HourAt(stamp)) || repairRequested || orphanPresent || !HasPendingArrivals()
        nextArrivalAt = 0.0
        Return
    EndIf
    If nextArrivalAt <= 0.0
        Float anchor = stamp
        If newCycle && wasRelevant
            ; Waiting through 08:00 produces at most one overdue arrival.
            anchor = (cycle as Float) + 8.0 / 24.0
        EndIf
        nextArrivalAt = anchor + Utility.RandomFloat(15.0, 30.0) / 1440.0
    EndIf
    If stamp < nextArrivalAt
        Status(8, 42)
        Return
    EndIf
    Int s = 0
    While s < dailyPopulation && residents[s] != None
        s += 1
    EndWhile
    If s < dailyPopulation
        Int ticket = workEpoch
        If lastArrivalCycle[s] == cycle
            ; An empty saved/current slot is reusable only after verifying that
            ; no appearance reference in that slot remains enabled.
            Bool empty = PoolSlotDisabled(s)
            If ticket != workEpoch
                Return
            EndIf
            If empty
                lastArrivalCycle[s] = -100000
            Else
                repairRequested = True
                Defer(s, 21, "empty tracked slot contains an enabled reference; existing recovery requested")
            EndIf
        EndIf
        If ticket == workEpoch && !repairRequested
            TryArrival(s, cycle)
        EndIf
        If ticket != workEpoch
            Return
        EndIf
        If residents[s] == None && deferredReason[s] == 21
            ; A selected-slot audit found an untracked enabled reference. Use
            ; existing adoption/retirement, rather than deferring until census.
            repairRequested = True
        EndIf
    EndIf
    ; After latent placement use current time, never replay missed intervals.
    nextArrivalAt = Utility.GetCurrentGameTime() + Utility.RandomFloat(15.0, 30.0) / 1440.0
EndFunction


Float Function ArrivalFallbackDelay()
    ; One counterpart to the saved GAME-TIME deadline, not a polling cadence.
    ; Both events call the same serialized worker and test nextArrivalAt.
    Float stamp = Utility.GetCurrentGameTime()
    If !ArrivalRelevant()
        Return 0.0
    EndIf
    Float due = nextArrivalAt
    If Daylight(HourAt(stamp))
        If due <= 0.0 || !HasPendingArrivals()
            Return 0.0
        EndIf
    Else
        ; Empty local settlements also need one wake for the next08:00 cycle.
        ; Active nighttime residents retain their existing maintenance timers.
        If ResidentCountSafe() > 0 || orphanPresent
            Return 0.0
        EndIf
        ; Use the same hour test as Daylight. Near08:00 float rounding can
        ; otherwise make CycleAt advance while HourAt still reads just before8.
        due = ((stamp as Int) as Float) + 8.0 / 24.0
        If HourAt(stamp) >= 8.0
            due += 1.0
        EndIf
    EndIf
    If arrivalTimeScale == None
        ; UESP extracted Skyrim master metadata: TimeScale [GLOB:0000003A].
        arrivalTimeScale = Game.GetFormFromFile(0x3A, "Skyrim.esm") as GlobalVariable
    EndIf
    If arrivalTimeScale == None
        Return 0.0
    EndIf
    Float scale = arrivalTimeScale.GetValue()
    If scale <= 0.0
        Return 0.0
    EndIf
    Float seconds = (due - stamp) * 86400.0 / scale
    If seconds < 2.0
        seconds = 2.0
    EndIf
    Return seconds
EndFunction


Bool Function PlaceArrival(Int s, Int cycle, Actor chosen, Int index)
    Int ticket = workEpoch
    ObjectReference point = roads[index]
    diagGoal = index
    diagSelectedPoint = point
    If !DayAIReady(s, index, "TryArrival.day AI before enable")
        Return False
    EndIf
    If ticket != workEpoch || residents[s] != None || !chosen.IsDisabled() || ReferenceInUse(chosen)
        Return False
    EndIf
    Status(9)
    If ticket != workEpoch
        Return False
    EndIf
    chosen.MoveTo(point, 0.0, 0.0, 0.0, True)
    Status(10)
    Float stamp = Utility.GetCurrentGameTime()
    If ticket != workEpoch
        Return False
    EndIf
    If !Daylight(HourAt(stamp)) || CycleAt(stamp) != cycle
        Defer(s, 23, "schedule changed during placement")
        Return False
    EndIf
    If !SafeArrival(point)
        Defer(s, 24, "outdoor ground reference became invalid after MoveTo")
        Return False
    EndIf
    ; The complete 200-variant slot audit ran BEFORE marker selection. This
    ; worker alone may activate our references. Preserve ownership, capacity,
    ; chosen-reference and reservation checks without another slow pool scan.
    If orphanPresent || ResidentCount() >= dailyPopulation || residents[s] != None || !chosen.IsDisabled() || ReferenceInUse(chosen)
        Return False
    EndIf
    If ticket != workEpoch
        Return False
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
    If ticket != workEpoch
        Return False
    EndIf
    Bool safe = Daylight(HourAt(Utility.GetCurrentGameTime())) && CycleAt(Utility.GetCurrentGameTime()) == cycle && SafeArrival(point)
    If ticket != workEpoch
        Return False
    EndIf
    If !safe
        residents[s] = None
        lastArrivalCycle[s] = -100000
        arrivalIndex[s] = -1
        Defer(s, 24, "schedule or outdoor ground reference changed before enable")
        Return False
    EndIf
    Float started = Utility.GetCurrentRealTime()
    ; No yielding native between this final owner check and enable request.
    If ticket != workEpoch
        Return False
    EndIf
    enableUntil[s] = started + 120.0
    chosen.Enable(False)
    If ticket != workEpoch
        repairRequested = True
        RegisterForSingleUpdate(1.0)
        Return False
    EndIf
    Bool disabled = chosen.IsDisabled()
    If ticket != workEpoch
        Return False
    EndIf
    If disabled
        ; Enable has returned; a disabled reference is not a successful arrival.
        residents[s] = None
        lastArrivalCycle[s] = -100000
        arrivalIndex[s] = -1
        enableUntil[s] = 0.0
        Defer(s, 44, "native Enable completed but actor is still disabled")
        Return False
    EndIf
    enableUntil[s] = 0.0
    priorArrivalDoor = diagArrivalDoor
    diagEnableConfirmed += 1
    deferredReason[s] = 0
    Status(12)
    If !Daylight(HourAt(Utility.GetCurrentGameTime()))
        SetPhase(s, 3)
    EndIf
    chosen.EvaluatePackage()
    Log("enabled confirmed; slot=" + s + "; ref=" + chosen + "; road=" + point)
    Return True
EndFunction

Float Function PendingEnableDelay()
    ; One deadline wake for legacy async reservations, including full arrays.
    ; No repeating confirmation poll and no scan of unselected appearances.
    Float delay = 0.0
    Float now = Utility.GetCurrentRealTime()
    Int s = 0
    While s < MaxPopulation
        If residents[s] != None && enableUntil[s] > 0.0 && !disablingSlot[s]
            If residents[s].IsDisabled()
                Float until = enableUntil[s] - now
                If until < 1.0
                    until = 1.0
                EndIf
                If delay <= 0.0 || until < delay
                    delay = until
                EndIf
            EndIf
        EndIf
        s += 1
    EndWhile
    Return delay
EndFunction

String Function ActivationStates()
    If !residents || residents.Length != 9 || !enableUntil || enableUntil.Length != 9
        Return "storage not initialized"
    EndIf
    String result = ""
    Int s = 0
    Float now = Utility.GetCurrentRealTime()
    While s < MaxPopulation
        Actor child = residents[s]
        result += s + ":"
        If child == None
            result += "empty "
        ElseIf child.IsDisabled()
            result += "DISABLED(reserved),remaining=" + (enableUntil[s] - now) + " "
        Else
            result += "enabled,3D=" + child.Is3DLoaded() + ",cell=" + child.GetParentCell() + " "
        EndIf
        s += 1
    EndWhile
    Return result
EndFunction


Int Function DoorArrivalIndex()
    ; A bounded, arrival-only query around the SAME preconfigured roaming
    ; points. No player-based queries, global discovery or new territory.
    ; Place at verified ground, never in an unverified door mesh/offset.
    diagArrivalDoor = None
    diagDoorFallback = True
    If arrivalDoorTypes == None
        arrivalDoorTypes = Game.GetFormFromFile(0x2221E0, "MoreBrats.esp") as FormList
    EndIf
    Int count = roads.Length
    If count < 1
        Return -1
    EndIf
    Int offset = Utility.RandomInt(0, count - 1)
    Int probe = 0
    Int fallback = -1
    Int repeated = -1
    ObjectReference repeatedDoor = None
    While probe < count
        Int index = (offset + probe) % count
        ObjectReference ground = roads[index]
        If RoadValid(ground)
            If fallback < 0
                fallback = index
            EndIf
            If arrivalDoorTypes != None
                ObjectReference door = Game.FindRandomReferenceOfAnyTypeInListFromRef(arrivalDoorTypes, ground, 512.0)
                If door != None && !door.IsDisabled()
                    Cell outside = door.GetParentCell()
                    If outside != None && !outside.IsInterior() && door.GetWorldSpace() == CityWorld
                        If door != priorArrivalDoor
                            diagArrivalDoor = door
                            diagDoorFallback = False
                            Return index
                        ElseIf repeated < 0
                            repeated = index
                            repeatedDoor = door
                        EndIf
                    EndIf
                EndIf
            EndIf
        EndIf
        probe += 1
    EndWhile
    If repeated >= 0
        diagArrivalDoor = repeatedDoor
        diagDoorFallback = False
        Return repeated
    EndIf
    ; Unloaded local queries or a missing optional catalog must never stall
    ; an otherwise valid arrival. Random starting point also randomizes fallback.
    Return fallback
EndFunction
