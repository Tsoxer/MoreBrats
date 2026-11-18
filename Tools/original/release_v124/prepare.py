"""Targeted movement/activation correction directly from released v1.2.3."""
from pathlib import Path
import re,shutil
ROOT=Path(__file__).resolve().parent;W=ROOT.parent;OUT=W/'v1.2.4/src'
def function(t,name,edit):
    p=re.compile(r'^(?:[A-Za-z]+ )?Function '+name+r'\([^\n]*\)\n.*?^EndFunction',re.M|re.S);m=p.search(t);assert m,name
    return t[:m.start()]+edit(m.group())+t[m.end():]
for path in (W/'v1.2.3/src').glob('*.psc'):
    if 'Controller' not in path.stem:shutil.copyfile(path,OUT/path.name);continue
    white=path.stem=='MB_Controller';maximum='6' if white else 'MaxPopulation'
    t=path.read_text().replace('v1.2.3','v1.2.4').replace('1203.0','1204.0')
    t=t.replace('Event OnInit()', '''; v1.2.4 additive queue/diagnostic scalars. No resident array layout changes.
Bool transitionWakeArmed = False
Int diagEnableConfirmed = 0
Int diagPlacementRetries = 0

Event OnInit()''',1)
    t=t.replace('Function Loaded()\n','Function Loaded()\n    transitionWakeArmed = False\n',1)
    t=t.replace('Event OnUpdate()\n','Event OnUpdate()\n    transitionWakeArmed = False\n',1)
    t=function(t,'Transition',lambda f:'''Function Transition()
    transitionPending = True
    ; Coalesce moving-player notifications. Repeated events must not keep
    ; pushing the same deferred wake two seconds into the future.
    If !transitionWakeArmed
        transitionWakeArmed = True
        UnregisterForUpdate()
        RegisterForSingleUpdate(2.0)
    EndIf
EndFunction''')
    t=function(t,'Service',lambda f:f.replace('            processing = False\n            leaseArmed = False','            processing = False\n            transitionWakeArmed = False\n            leaseArmed = False').replace('                processing = False\n                leaseArmed = False','                processing = False\n                transitionWakeArmed = False\n                leaseArmed = False'))
    def reconcile(f):
        old='                RefreshResident(s, stamp)';assert old in f
        if white:
            f=f.replace('    Float stamp = Utility.GetCurrentGameTime()', '    Float stamp = Utility.GetCurrentGameTime()\n    Float activationClock = Utility.GetCurrentRealTime()',1)
            return f.replace(old,'''                If saved.IsDisabled()
                    ; The shared city/town/village controllers already expire
                    ; impossible saved enable deadlines. Whiterun lacked it.
                    If !disablingSlot[s] && enableUntil[s] > activationClock + 120.0
                        enableUntil[s] = 0.0
                        Log("expired stale saved enable deadline; disabled slot=" + s)
                    EndIf
                Else
                    RefreshResident(s, stamp)
                EndIf''',1)
        return f.replace(old,'''                If !saved.IsDisabled()
                    RefreshResident(s, stamp)
                EndIf''',1)
    t=function(t,'Reconcile',reconcile)
    def tick(f):
        if white:f=f.replace('''                Else
                    UpdateRoaming(s, stamp)''','''                ElseIf !child.IsDisabled()
                    UpdateRoaming(s, stamp)''',1)
        else:f=f.replace('                ElseIf relevant\n                    UpdateRoaming', '                ElseIf relevant && !child.IsDisabled()\n                    UpdateRoaming',1)
        return f
    t=function(t,'Tick',tick)
    def arrival(f):
        # Keep actor/appearance selection and one complete slot audit unchanged.
        # Only the movement-sensitive placement tail is replaced.
        start=f.index('    diagTargetContext = "TryArrival.road selection"')
        count='18' if white else 'RoadIDs.Length'
        candidate='(offset + probes * 5) % 18' if white else '(offset + probes) % RoadIDs.Length'
        return f[:start]+f'''    diagTargetContext = "TryArrival.road selection"
    Int offset = Utility.RandomInt(0, {('17' if white else 'RoadIDs.Length - 1')})
    Int probes = 0
    Int placements = 0
    Int reason = 19
    While probes < {count} && placements < 3
        Int index = {candidate}
        probes += 1
        ObjectReference point = roads[index]
        Int roadReason = RoadBlock(point)
        If roadReason == 0
            Int block = ArrivalBlock(point)
            If block == 0 && ClearArrivalPoint(index, s)
                placements += 1
                If PlaceArrival(s, cycle, chosen, index)
                    Return
                EndIf
                If ticket != workEpoch
                    Return
                EndIf
                ; Only moving/visibility changes justify another disabled
                ; placement in this opportunity. Never move an enabled actor.
                If deferredReason[s] != 24
                    Return
                EndIf
                diagPlacementRetries += 1
                reason = 24
            ElseIf block != 0
                reason = block
            EndIf
        Else
            reason = roadReason
        EndIf
    EndWhile
    Defer(s, reason, "no safe free road after bounded current-position checks; placement attempts=" + placements)
EndFunction'''
    t=function(t,'TryArrival',arrival)
    def plan(f):
        old='''        Float fallback = ArrivalFallbackDelay()
        If fallback > 0.0''';assert old in f
        return f.replace(old,'''        Float fallback = ArrivalFallbackDelay()
        Float confirmation = PendingEnableDelay()
        If confirmation > 0.0 && (fallback <= 0.0 || confirmation < fallback)
            fallback = confirmation
        EndIf
        If fallback > 0.0''',1)
    t=function(t,'PlanNext',plan)
    def status(f):
        f=f.replace('    Int snapshotEnabled = -1','    Int liveEnabled = EnabledCount()\n    Int snapshotEnabled = -1',1)
        f=f.replace('"; enabled(last completed sample)=" + snapshotEnabled + "; tracked=" + ResidentCountSafe()', '"; enabled NOW=" + liveEnabled + "; tracked/reserved=" + ResidentCountSafe() + "; previous sample=" + snapshotEnabled')
        needle='    message += "\\nCallbacks: real="';assert needle in f
        return f.replace(needle,'''    message += "\\nConfirmed enables this script=" + diagEnableConfirmed + "; moving-marker retries=" + diagPlacementRetries
    message += "\\nPer-slot state=" + ActivationStates()
    message += "\\nCallbacks: real="''',1)
    t=function(t,'ShowStatus',status)
    t+=f'''

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
    If !SafeArrival(point) || !ClearArrivalPoint(index, s)
        Defer(s, 24, "player/spacing changed after MoveTo; trying another verified road")
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
    Bool safe = Daylight(HourAt(Utility.GetCurrentGameTime())) && CycleAt(Utility.GetCurrentGameTime()) == cycle && ClearArrivalPoint(index, s) && SafeArrival(point)
    If ticket != workEpoch
        Return False
    EndIf
    If !safe
        residents[s] = None
        lastArrivalCycle[s] = -100000
        arrivalIndex[s] = -1
        Defer(s, 24, "current-position safety changed before enable; trying another road")
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
    While s < {maximum}
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
    If !residents || residents.Length != {('6' if white else '9')} || !enableUntil || enableUntil.Length != {('6' if white else '9')}
        Return "storage not initialized"
    EndIf
    String result = ""
    Int s = 0
    Float now = Utility.GetCurrentRealTime()
    While s < {maximum}
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
'''
    (OUT/path.name).write_text(t)
print('Prepared v1.2.4 directly from v1.2.3; records, running tuning and departure functions retained.')
