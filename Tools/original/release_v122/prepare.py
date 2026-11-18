"""Minimal v1.2.2 arrival/counting extension of the complete v1.2.1 sources."""
from pathlib import Path
import re, shutil
ROOT=Path(__file__).resolve().parent; WORK=ROOT.parent
SRC=WORK/'v1.2.2/src'; SRC.mkdir(parents=True,exist_ok=True)
def edit_function(text,name,edit):
    pat=re.compile(r'^(?:[A-Za-z]+ )?Function '+name+r'\([^\n]*\)\n.*?^EndFunction',re.M|re.S)
    match=pat.search(text); assert match,name
    return text[:match.start()]+edit(match.group())+text[match.end():]
for path in (WORK/'v1.2.1/src').glob('*.psc'):
    if 'Controller' not in path.stem:
        shutil.copyfile(path,SRC/path.name); continue
    white=path.stem=='MB_Controller'; maximum='6' if white else 'MaxPopulation'
    saved_length='6' if white else '9'
    text=path.read_text().replace('v1.2.1','v1.2.2').replace('1201.0','1202.0')
    fields='''
; v1.2.2 additive state: absolute game days, never a new actor/reference pool.
Float nextArrivalAt = 0.0
Int arrivalScheduleCycle = -100000
Bool arrivalWasRelevant = False
Bool poolAudited = False
Float nextPoolAuditAt = 0.0
Int diagFullEnabled = -1
'''
    if white: fields+='Location arrivalCityLocation\n'
    text=text.replace('Event OnInit()',fields+'\nEvent OnInit()',1)
    def service(f):
        needle='    If EnsureSetup() && ticket == workEpoch'
        return f.replace(needle,'''    ; Fresh, unvisited settlements have nothing to recover. Older initialized
    ; saves always take EnsureSetup/Reconcile before becoming dormant.
    ; Make this decision under the existing worker lease, never outside it.
    If request != 3 && schemaVersion == 0 && dailyPopulation == 0 && activeIndex < 0 && ResidentCountSafe() == 0 && !ArrivalRelevant()
        If ticket == workEpoch
            PlanDormant()
            If ticket == workEpoch
                processing = False
                leaseArmed = False
                If transitionPending
                    RegisterForSingleUpdate(0.1)
                EndIf
            EndIf
        EndIf
        Return
    EndIf
'''+needle,1)
    text=edit_function(text,'Service',service)
    text=edit_function(text,'RecoveryPulse',lambda f: '''Function RecoveryPulse()
    ; Preserve the watchdog's recovery role without waking an empty remote city.
    If processing || repairRequested || ResidentCountSafe() > 0 || ArrivalRelevant()
        Wake()
    EndIf
EndFunction''')
    # After the unchanged reconciliation has completed, remember the full audit.
    text=edit_function(text,'EnsureSetup',lambda f:f.replace('        repairRequested = False','''        poolAudited = True
        nextPoolAuditAt = Utility.GetCurrentGameTime() + 0.25
        diagFullEnabled = FullEnabledCount()
        repairRequested = False''',1))
    text=edit_function(text,'ArrivalBlock',lambda f:'''Int Function ArrivalBlock(ObjectReference point)
    If point == None
        Return 13
    EndIf
    If point.IsDisabled()
        Return 18
    EndIf
    Actor viewer = Game.GetPlayer()
    If viewer.IsInInterior()
        ; Fixed exterior roads remain safely separate from an interior viewer.
        Return 0
    EndIf
    WorldSpace playerWorld = viewer.GetWorldSpace()
    If playerWorld == None
        Return 15
    EndIf
    If playerWorld != CityWorld
        Return 0
    EndIf
    ; Cell attachment is not visibility. Test only when an arrival is due.
    If viewer.GetDistance(point) < 1536.0
        Return 40
    EndIf
    ; Best-effort camera-clipped LOS on the fixed marker; no visibility loop.
    If point.Is3DLoaded() && viewer.HasLOS(point)
        Return 41
    EndIf
    Return 0
EndFunction''')
    # Preserve the census for initialization/exceptional and periodic audits.
    full=re.search(r'^Int Function EnabledCount\(\)\n.*?^EndFunction',text,re.M|re.S).group().replace('EnabledCount()','FullEnabledCount()',1)
    text=edit_function(text,'EnabledCount',lambda f:f'''Int Function EnabledCount()
    Int count = 0
    If (residents as Bool) && residents.Length == {saved_length}
        Int s = 0
        While s < {maximum}
            Actor child = residents[s]
            If child != None && !child.IsDisabled()
                count += 1
            EndIf
            s += 1
        EndWhile
    EndIf
    Return count
EndFunction

{full}''')
    # Preserve the entire resident/departure branch; remove only batch arrivals.
    def tick(f):
        if white:
            start=f.index('    Bool arrivalsNeeded = False')
            end=f.index('    While s < 6\n        Actor child',start)
            f=f[:start]+'    Int s = 0\n'+f[end:]
        f=f.replace('    ; Prepare arrivals while the player is elsewhere, as Whiterun already does.\n    ; Only scripted daytime roaming remains gated by city relevance.\n','')
        f=f.replace('''        ElseIf s < dailyPopulation && Daylight(hour) && lastArrivalCycle[s] != cycle
            TryArrival(s, cycle)
''','')
        needle='    If !Daylight(hour) && ResidentCount() == 0'
        f=f.replace(needle,'''    ; One serialized due arrival per callback, never a missed-event burst.
    ProcessArrival()
'''+needle,1)
        return f
    text=edit_function(text,'Tick',tick)
    # Replace the away-empty polling branch, retain active remote retirement.
    def plan(f):
        if not white:
            start=f.index('    If !PlayerInCity()')
            end=f.index('    Float stamp = Utility.GetCurrentGameTime()',start)
            old=f[start:end]
            # Retain original remote timers when actual residents need maintenance.
            f=f[:start]+'''    If !ArrivalRelevant() && ResidentCountSafe() == 0 && !orphanPresent
        PlanDormant()
        Return
    EndIf
'''+old+f[end:]
        else:
            f=f.replace('    Float stamp = Utility.GetCurrentGameTime()', '''    If !ArrivalRelevant() && ResidentCountSafe() == 0 && !orphanPresent
        PlanDormant()
        Return
    EndIf
    Float stamp = Utility.GetCurrentGameTime()''',1)
        f=f.replace('    Bool arrivalPending = False\n','')
        f=f.replace('''        ElseIf s < dailyPopulation && lastArrivalCycle[s] != CycleAt(stamp) && Daylight(hour)
            arrivalPending = True
''','')
        f=re.sub(r'    ElseIf arrivalPending\n.*?        EndIf\n(?=    EndIf\nEndFunction)', '',f,flags=re.S)
        f=f.replace('    ; Preserve the documented safe lower bound', '''    If Daylight(hour) && ArrivalRelevant() && nextArrivalAt > 0.0 && HasPendingArrivals()
        Float arrivalDelta = (nextArrivalAt - stamp) * 24.0
        If arrivalDelta < delta
            delta = arrivalDelta
        EndIf
    EndIf
    ; Preserve the documented safe lower bound''',1)
        return f
    text=edit_function(text,'PlanNext',plan)
    text=edit_function(text,'ShowStatus',lambda f:f.replace('    message += "\\nLast non-busy stage="','''    message += "\\nArrivals: due(game days)=" + nextArrivalAt + "; cycle=" + arrivalScheduleCycle + "; relevant=" + ArrivalRelevant()
    message += "\\nEnabled sample counts tracked residents; last full census=" + diagFullEnabled + "; next audit(game days)=" + nextPoolAuditAt
    message += "\\nArrival 40=within 1536 units; 41=marker LOS; 42=waiting for game-time arrival; 43=not relevant"
    message += "\\nLast non-busy stage="''',1))
    # New helpers are bounded, and use only existing state and the existing worker.
    if white:
        relevance='''    Actor viewer = Game.GetPlayer()
    If CityWorld == None
        CityWorld = Game.GetFormFromFile(0x1A26F, "Skyrim.esm") as WorldSpace
    EndIf
    If CityWorld != None && viewer.GetWorldSpace() == CityWorld
        Return True
    EndIf
    If !viewer.IsInInterior()
        Return False
    EndIf
    If TavernCell != None && viewer.GetParentCell() == TavernCell
        Return True
    EndIf
    If arrivalCityLocation == None
        arrivalCityLocation = Game.GetFormFromFile(0x18A56, "Skyrim.esm") as Location
    EndIf
    Location here = viewer.GetCurrentLocation()
    If here != None && arrivalCityLocation != None
        Return here == arrivalCityLocation || arrivalCityLocation.IsChild(here)
    EndIf
    Return False'''
    else:
        relevance='''    If PlayerInCity()
        Return True
    EndIf
'''
        if path.stem in ('MB_TownController','MB_VillageController'):
            relevance+='''    ; Cold exterior location seams can use the same direct VMAD road bindings
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
'''
        relevance+='    Return False'
    text+=f'''

Bool Function ArrivalRelevant()
{relevance}
EndFunction

Function PlanDormant()
    UnregisterForUpdate()
    UnregisterForUpdateGameTime()
    arrivalWasRelevant = False
    nextArrivalAt = 0.0
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
        nextArrivalAt = 0.0
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
'''
    (SRC/path.name).write_text(text)
print('Prepared v1.2.2 from complete v1.2.1: four controller extensions, five sources unchanged.')
