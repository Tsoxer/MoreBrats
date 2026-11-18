"""Narrow arrival-latency repair on the final v1.2.5 (3–7 minute) sources."""
from pathlib import Path
import hashlib,json,re,shutil,difflib
W=Path('work');R=W/'release_v126';OUT=W/'v1.2.6/src';BUILD=W/'build/v1.2.6'
protected={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for folder in [W/'build/v1.1.0',W/'build/v1.2.5',W/'v1.2.5/src'] for p in folder.rglob('*') if p.is_file()}
(R/'protected-baselines.json').write_text(json.dumps(protected,indent=2)+'\n')
def change(t,name,fn):
 rx=re.compile(r'^(?:[A-Za-z]+ )?Function '+name+r'\([^\n]*\)\n.*?^EndFunction',re.M|re.S);m=rx.search(t);assert m,name
 return t[:m.start()]+fn(m.group())+t[m.end():]
for p in (W/'v1.2.5/src').glob('*.psc'):
 if 'Controller' not in p.stem:shutil.copyfile(p,OUT/p.name);continue
 white=p.stem=='MB_Controller';schema=6 if white else 7
 t=p.read_text().replace('v1.2.5','v1.2.6').replace('1205.0','1206.0')
 t=t.replace('Event OnInit()','''; Additive v1.2.6 fields: old names, types, defaults and slot meanings stay intact.
Bool loadResidentCheck = False
Float diagArrivalDueAt = 0.0
Float diagArrivalAttemptAt = 0.0
Float diagArrivalEnabledAt = 0.0

Event OnInit()''',1)
 t=change(t,'Loaded',lambda f:f.replace('    repairRequested = True',f'''    ; A healthy serialized pool is already a complete census. Validate tracked
    ; residents after loading; retain a full audit for missing/unsafe old state.
    loadResidentCheck = True
    If schemaVersion < {schema} || !diagStorageReady || !poolAudited || bindingsPending || orphanPresent || processing
        repairRequested = True
    EndIf'''))
 def service(f):
  old='If request != 3 && schemaVersion == 0 && dailyPopulation == 0 && activeIndex < 0 && ResidentCountSafe() == 0 && !ArrivalRelevant()'
  assert old in f
  return f.replace(old,'If request != 3 && activeIndex < 0 && ResidentCountSafe() == 0 && !orphanPresent && !ArrivalRelevant()').replace('''    ; Fresh, unvisited settlements have nothing to recover. Older initialized
    ; saves always take EnsureSetup/Reconcile before becoming dormant.''','''    ; Empty remote settlements defer expensive setup/recovery until relevant.
    ; Saved repair flags remain pending; no arrival can bypass that recovery.''')
 t=change(t,'Service',service)
 def setup(f):
  needle=f'    If repairRequested || schemaVersion < {schema}\n        Status(4)';assert needle in f
  f=f.replace(needle,f'    If repairRequested || schemaVersion < {schema} || loadResidentCheck\n        Status(4)')
  needle='''        poolAudited = True
        nextPoolAuditAt = Utility.GetCurrentGameTime() + 0.25
        ; Reconcile recorded its complete, ownership-checked census.
        repairRequested = False''';assert needle in f
  return f.replace(needle,'''        ; Reconcile itself records full audits; a tracked-only load check must
        ; not postpone an already-due periodic census.
        repairRequested = False
        loadResidentCheck = False''')
 t=change(t,'EnsureSetup',setup)
 def reconcile(f):
  f=f.replace('''            If !found
                residents[s] = None''','''            If !found
                residents[s] = None
                repairRequested = True''')
  # Missing/disabled reservations still need the old full pending-state path.
  needle2='''        Actor saved = residents[s]
        If saved != None''';assert needle2 in f
  f=f.replace(needle2,'''        Actor saved = residents[s]
        If saved == None && (lastArrivalCycle[s] == cycle || enableUntil[s] > 0.0)
            repairRequested = True
        ElseIf saved != None && saved.IsDisabled()
            repairRequested = True
        EndIf
        If saved != None''',1)

  needle='    Int census = 0';assert needle in f
  f=f.replace(needle,f'''    ; Our actor is reserved in residents BEFORE Enable. With a complete saved
    ; census and no repair/orphan flag, validate those residents without another
    ; native enabled-state call for every unused appearance reference.
    If !repairRequested && poolAudited && schemaVersion >= {schema} && !orphanPresent && !bindingsPending
        Return
    EndIf
'''+needle,1)
  needle='    diagFullEnabled = census';assert needle in f
  f=f.replace(needle,'''    poolAudited = True
    nextPoolAuditAt = Utility.GetCurrentGameTime() + 0.25
'''+needle,1)
  return f
 t=change(t,'Reconcile',reconcile)
 def attempt(f):
  f=f.replace('    Int ticket = workEpoch\n','''    Int ticket = workEpoch
    diagArrivalDueAt = nextArrivalAt
    diagArrivalAttemptAt = Utility.GetCurrentGameTime()
''',1)
  needle='''    Bool slotDisabled = PoolSlotDisabled(s)
    If ticket != workEpoch
        Return
    EndIf
    If !slotDisabled
        Defer(s, 21, "slot contains an enabled reference awaiting adoption/retirement")
        Return
    EndIf'''
  if not white:needle=needle.replace('    If !slotDisabled\n','    If !slotDisabled\n        repairRequested = True\n')
  assert needle in f
  f=f.replace(needle,'''    ; The completed full census and serialized single writer already establish
    ; unused-slot safety. Keep the 200-reference check for exceptional/incomplete
    ; state, not as extra native work in front of every scheduled arrival.
    If !poolAudited || repairRequested || bindingsPending
        Bool slotDisabled = PoolSlotDisabled(s)
        If ticket != workEpoch
            Return
        EndIf
        If !slotDisabled
            repairRequested = True
            Defer(s, 21, "slot contains an enabled reference awaiting adoption/retirement")
            Return
        EndIf
    EndIf''')
  needle='    If ReferenceInUse(chosen)';assert needle in f
  f=f.replace(needle,'''    If !chosen.IsDisabled()
        repairRequested = True
        Defer(s, 21, "selected actor is unexpectedly enabled; full reconciliation requested")
        Return
    EndIf
'''+needle,1)
  return f
 t=change(t,'TryArrival',attempt)
 def process(f):
  needle='    If !poolAudited || stamp >= nextPoolAuditAt';assert needle in f
  f=f.replace(needle,'''    ; Explicit recovery still runs before arrivals. A routine six-hour census
    ; can wait until the short arrival sequence finishes, instead of blocking
    ; an already-due child behind another whole-pool native scan.
    If !poolAudited || (stamp >= nextPoolAuditAt && !HasPendingArrivals())''',1)
  needle='    Bool wasRelevant = arrivalWasRelevant';assert needle in f
  f=f.replace(needle,'''    ; A full native audit may yield for a long time: never use its old clock.
    stamp = Utility.GetCurrentGameTime()
    cycle = CycleAt(stamp)
    If arrivalScheduleCycle != cycle
        Return
    EndIf
'''+needle,1)
  return f
 t=change(t,'ProcessArrival',process)
 t=change(t,'PlaceArrival',lambda f:f.replace('    diagEnableConfirmed += 1','''    diagArrivalEnabledAt = Utility.GetCurrentGameTime()
    diagEnableConfirmed += 1
    Log("activation timing; due(game days)=" + diagArrivalDueAt + "; attempt=" + diagArrivalAttemptAt + "; enabled=" + diagArrivalEnabledAt + "; overdue(game min)=" + (diagArrivalEnabledAt - diagArrivalDueAt) * 1440.0)'''))
 t=change(t,'ShowStatus',lambda f:f.replace('    message += "\\nCallbacks: real="','''    message += "\\nLast arrival: due=" + diagArrivalDueAt + "; attempt=" + diagArrivalAttemptAt + "; enabled=" + diagArrivalEnabledAt
    message += "\\nLast successful enable game time is recorded only AFTER Enable and IsDisabled confirmation."
    message += "\\nCallbacks: real="''').replace('See v1.2.6 README for codes.','Status reason 42=waiting for the saved deadline; 21=repair; 44=failed enable.'))
 (OUT/p.name).write_text(t)
 patch=''.join(difflib.unified_diff(p.read_text().splitlines(True),t.splitlines(True),fromfile='v1.2.5/'+p.name,tofile='v1.2.6/'+p.name))
 with (BUILD/'SOURCE-CHANGES.patch').open('a') as h:h.write(patch)
for name in ['API','Config']:
 shutil.copytree(W/'release_v125'/name,R/name,dirs_exist_ok=True)
for name in ['PluginBuilder','PluginAudit']:
 (R/name).mkdir(exist_ok=True)
 for p in (W/'release_v125'/name).glob('*'):
  if p.suffix in ['.cs','.csproj']:shutil.copyfile(p,R/name/p.name)
p=R/'PluginBuilder/Program.cs';t=p.read_text().replace('build/v1.2.4/runtime','build/v1.2.5/runtime').replace('build/v1.2.5/runtime";Directory','build/v1.2.6/runtime";Directory').replace('v1.2.4 is the complete','v1.2.5 is the complete').replace('v1.2.5 development. Progress-safe initialization and arrival scheduling; door placement, appearances and departures retained.','v1.2.6 development. Lower arrival latency; appearances, AI and departures retained.').replace('g.RawFloat=1205','g.RawFloat=1206');p.write_text(t)
for name in ['settlements.json','appearance-mapping.json']:
 src=W/'build/v1.2.5'/name
 if not src.exists():src=W/'build/v1.2.4'/name
 if src.exists():shutil.copyfile(src,BUILD/name)
p=R/'build.py';p.write_text((W/'release_v125/build.py').read_text().replace('v1.2.4','v1.2.5').replace('v1.2.5/runtime','v1.2.6/runtime').replace("WORK/'v1.2.5/src'","WORK/'v1.2.6/src'").replace("WORK/'build/v1.2.6/runtime/Scripts'","WORK/'build/v1.2.5/runtime/Scripts'"))
print('Prepared four controller changes on the final v1.2.5 sources; five helpers copied unchanged.')
