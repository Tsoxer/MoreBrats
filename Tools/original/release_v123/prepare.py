"""Narrow callback/relevance repair of complete v1.2.2, plus requested running tuning."""
from pathlib import Path
import re,shutil
ROOT=Path(__file__).resolve().parent;W=ROOT.parent;OUT=W/'v1.2.3/src'
def function(text,name,edit):
    pat=re.compile(r'^(?:[A-Za-z]+ )?Function '+name+r'\([^\n]*\)\n.*?^EndFunction',re.M|re.S)
    match=pat.search(text);assert match,name
    return text[:match.start()]+edit(match.group())+text[match.end():]
for p in (W/'v1.2.2/src').glob('*.psc'):
    if 'Controller' not in p.stem:
        shutil.copyfile(p,OUT/p.name);continue
    white=p.stem=='MB_Controller'
    t=p.read_text().replace('v1.2.2','v1.2.3').replace('1202.0','1203.0')
    t=t.replace('Event OnInit()', '''; v1.2.3 additive diagnostic counters and an official clock binding only.
GlobalVariable arrivalTimeScale
Int diagRealUpdates = 0
Int diagGameUpdates = 0

Event OnInit()''',1)
    t=t.replace('Event OnUpdateGameTime()\n    Service()', 'Event OnUpdateGameTime()\n    diagGameUpdates += 1\n    Service()',1)
    t=t.replace('Event OnUpdate()\n    Service()', 'Event OnUpdate()\n    diagRealUpdates += 1\n    Service()',1)
    t=function(t,'Transition',lambda f:'''Function Transition()
    transitionPending = True
    ; Coalesce the entry notification through the existing real-time event.
    ; Do not cancel the already armed game-time arrival deadline here.
    UnregisterForUpdate()
    RegisterForSingleUpdate(2.0)
EndFunction''')
    # A transient location/world read can suspend an arrival, never erase its
    # saved deadline. Cycle/night/completion retain their existing reset paths.
    t=function(t,'ProcessArrival',lambda f:f.replace('''    If !relevant
        arrivalWasRelevant = False
        nextArrivalAt = 0.0
        Return''','''    If !relevant
        arrivalWasRelevant = False
        Return''',1))
    t=function(t,'PlanDormant',lambda f:f.replace('    nextArrivalAt = 0.0\n','',1))
    if white:
        # Whiterun's location check previously applied only in interiors.
        t=function(t,'ArrivalRelevant',lambda f:f.replace('''    If !viewer.IsInInterior()
        Return False
    EndIf
''','',1))
        t=function(t,'RecoveryPulse',lambda f:'''Function RecoveryPulse()
    ; The existing 60-second watchdog must also service a manual MB_Debug
    ; request while Whiterun is empty/remote. No new recurring task is added.
    Bool requested = False
    If (DiagnosticGlobals as Bool) && DiagnosticGlobals.Length == 17
        If DiagnosticGlobals[0] != None
            requested = DiagnosticGlobals[0].GetValue() >= 2.0
        EndIf
    EndIf
    If requested || processing || repairRequested || ResidentCountSafe() > 0 || ArrivalRelevant()
        Wake()
    EndIf
EndFunction''')
    elif p.stem=='MB_CityController':
        # Match the existing towns' independent location signal. A missing
        # world query must not veto an otherwise verified local location.
        t=function(t,'ArrivalRelevant',lambda f:'''Bool Function ArrivalRelevant()
    If PlayerInCity()
        Return True
    EndIf
    Location here = Game.GetPlayer().GetCurrentLocation()
    If here != None && CityLocation != None
        Return here == CityLocation || CityLocation.IsChild(here)
    EndIf
    Return False
EndFunction''')
    def plan(f):
        f=f.replace('    If !PlayerInCity()\n','    If !ArrivalRelevant()\n',1)
        needle='''    If retirementPending
        RegisterForSingleUpdate(10.0)
    EndIf'''
        assert needle in f
        return f.replace(needle,'''    If retirementPending
        RegisterForSingleUpdate(10.0)
    Else
        Float fallback = ArrivalFallbackDelay()
        If fallback > 0.0
            RegisterForSingleUpdate(fallback)
        EndIf
    EndIf''',1)
    t=function(t,'PlanNext',plan)
    # Independent requested content change. No packages or movement goals change.
    def running(f):
        assert 'Utility.RandomInt(0, 99) < 25' in f
        assert 'Utility.RandomFloat(2.0, 6.0)' in f
        return f.replace('Utility.RandomInt(0, 99) < 25','Utility.RandomInt(0, 9999) < 3325',1).replace('Utility.RandomFloat(2.0, 6.0)','Utility.RandomFloat(2.66, 7.98)',1)
    t=function(t,'BeginTrip',running)
    def status(f):
        if white:
            f=f.replace(' — status\\nQuest running=', ' Whiterun — status\\nQuest running=',1)
            f=f.replace('    message += "\\nStage="','''    message += "\\nMB_Debug reports Whiterun. Elsewhere use MB_<Settlement>_Debug."
    message += "\\nStage="''',1)
        f=f.replace('; 43=not relevant','')
        f=f.replace('    message += "\\nLast non-busy stage="','''    message += "\\nCallbacks: real=" + diagRealUpdates + "; game=" + diagGameUpdates
    message += "\\nNow(game days)=" + Utility.GetCurrentGameTime() + "; due in(game min)=" + (nextArrivalAt - Utility.GetCurrentGameTime()) * 1440.0
    message += "\\nPlayer world=" + Game.GetPlayer().GetWorldSpace() + "; expected world=" + CityWorld
    message += "\\nPlayer location=" + Game.GetPlayer().GetCurrentLocation()
    message += "\\nDeadline fallback clock=" + arrivalTimeScale
    message += "\\nLast non-busy stage="''',1)
        f=f.replace('Arrivals prepare off-city; relevance gates roaming only.','Arrivals require local relevance; suspended deadlines are retained.')
        f=f.replace('14=loaded exterior;19=no free road;21=reconcile;24=post-MoveTo safety;91/30=array failure','19=no free road;21=reconcile;24=post-MoveTo safety;40=distance;41=LOS;42=not due;91/30=array failure')
        return f
    t=function(t,'ShowStatus',status)
    t+='''

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
'''
    (OUT/p.name).write_text(t)
print('Prepared v1.2.3 directly from v1.2.2: callback repair and separate +33% running tuning.')
