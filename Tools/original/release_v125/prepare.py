"""Progress-safe recovery and initial scheduling directly from released v1.2.4."""
from pathlib import Path
import re,shutil
ROOT=Path(__file__).resolve().parent;W=ROOT.parent;OUT=W/'v1.2.5/src'
def change(t,name,fn):
 p=re.compile(r'^(?:[A-Za-z]+ )?Function '+name+r'\([^\n]*\)\n.*?^EndFunction',re.M|re.S);m=p.search(t);assert m,name
 return t[:m.start()]+fn(m.group())+t[m.end():]
for p in (W/'v1.2.4/src').glob('*.psc'):
 if 'Controller' not in p.stem:shutil.copyfile(p,OUT/p.name);continue
 white=p.stem=='MB_Controller';t=p.read_text().replace('v1.2.4','v1.2.5').replace('1204.0','1205.0').replace('Utility.RandomFloat(15.0, 30.0)','Utility.RandomFloat(3.0, 7.0)')
 # Schedule the existing first arrival deadline before long cache/recovery work.
 # No new serialized state: existing absolute deadline and cycle keep meanings.
 def service(f):
  f=f.replace('            RegisterForSingleUpdate(5.0)','            RegisterForSingleUpdate(leaseUntil - now + 1.0)')
  needle='    If EnsureSetup() && ticket == workEpoch'
  assert needle in f
  f=f.replace(needle,'''    If !WorkerProgress(ticket)
        Return
    EndIf
    PrimeArrivalDeadline()
    If ticket != workEpoch
        Return
    EndIf
'''+needle,1)
  return f
 t=change(t,'Service',service)
 # Keep the exact setup/recovery/census contracts. Reconcile's one full pass
 # already counted all enabled references; do not run a third native census.
 def setup(f):
  needle='        diagFullEnabled = FullEnabledCount()';assert needle in f
  return f.replace(needle,'        ; Reconcile recorded its complete, ownership-checked census.')
 t=change(t,'EnsureSetup',setup)
 def reconcile(f):
  if '    Int ticket = workEpoch' not in f:f=f.replace('Function Reconcile()\n','Function Reconcile()\n    Int ticket = workEpoch\n',1)
  f=f.replace('    Int i = 0\n    While i < poolSize','    Int census = 0\n    Bool extraEnabled = False\n    Int i = 0\n    While i < poolSize',1)
  needle='''        Actor child = PoolActor(i)
        If child != None && !child.IsDisabled() && !ReferenceInUse(child)''';assert needle in f
  f=f.replace(needle,'''        If i % 32 == 0 && !WorkerProgress(ticket)
            Return
        EndIf
        Actor child = PoolActor(i)
        Bool enabled = child != None && !child.IsDisabled()
        If ticket != workEpoch
            Return
        EndIf
        If enabled
            census += 1
        EndIf
        If enabled && !ReferenceInUse(child)''',1)
  needle='''                Debug.Trace("[MoreBrats] v1.2.5: adopted saved enabled pool index " + i)
            EndIf
        EndIf
        i += 1''';assert needle in f
  f=f.replace(needle,'''                Debug.Trace("[MoreBrats] v1.2.5: adopted saved enabled pool index " + i)
                StoreOrphanSamples(i, 0)
            Else
                extraEnabled = True
            EndIf
        Else
            StoreOrphanSamples(i, 0)
        EndIf
        i += 1''',1)
  needle='    RecoverOrphans()\nEndFunction';assert needle in f
  f=f.replace(needle,'''    If !WorkerProgress(ticket)
        Return
    EndIf
    diagFullEnabled = census
    orphanPresent = extraEnabled
    If extraEnabled
        ; Existing exact orphan safety/retirement logic, only when necessary.
        RecoverOrphans()
    EndIf
EndFunction''',1)
  return f
 t=change(t,'Reconcile',reconcile)
 # Long native loops renew ONLY after bounded work. No recurring progress timer.
 def checkpoints(f,ret,needle,index):
  if '    Int ticket = workEpoch' not in f:f=f.replace('\n','\n    Int ticket = workEpoch\n',1)
  assert needle in f
  return f.replace(needle,needle+f'''\n        If {index} % 32 == 0 && !WorkerProgress(ticket)
            Return {ret}
        EndIf''',1)
 # ResolveAppearancePools has an expression after '<', insert after full line.
 def resolver(f):
  if '    Int ticket = workEpoch' not in f:f=f.replace('\n','\n    Int ticket = workEpoch\n',1)
  return re.sub(r'(^    While namedIndex < [^\n]+\n)',r'\1        If namedIndex % 32 == 0 && !WorkerProgress(ticket)\n            Return False\n        EndIf\n',f,count=1,flags=re.M)
 t=change(t,'ResolveAppearancePools',resolver)
 t=change(t,'RecoverOrphans',lambda f:checkpoints(f,'','    While i < poolSize','i'))
 t=change(t,'FullEnabledCount',lambda f:checkpoints(f,'-1','        While n < poolSize','n'))
 t=change(t,'PoolSlotDisabled',lambda f:checkpoints(f,'False','    While v < 200','v'))
 # A cancelled audit must not overwrite the replacement worker's diagnostics.
 def attempt(f):
  needle='    If !PoolSlotDisabled(s)';assert needle in f
  return f.replace(needle,'''    Bool slotDisabled = PoolSlotDisabled(s)
    If ticket != workEpoch
        Return
    EndIf
    If !slotDisabled''',1)
 t=change(t,'TryArrival',attempt)
 t+='''

Bool Function WorkerProgress(Int ticket)
    ; Progress, not total workload duration, determines whether work is stuck.
    ; Called at bounded checkpoints inside existing finite loops, never polled.
    If ticket != workEpoch
        Return False
    EndIf
    If processing && leaseArmed
        Float now = Utility.GetCurrentRealTime()
        If ticket != workEpoch
            Return False
        EndIf
        leaseStart = now
        leaseUntil = now + 120.0
    EndIf
    Return True
EndFunction

Function PrimeArrivalDeadline()
    ; Preserve the existing game-minute design, measured from relevance/entry,
    ; not from the end of a potentially long old-save cache/recovery pass.
    If !ArrivalRelevant()
        Return
    EndIf
    Float stamp = Utility.GetCurrentGameTime()
    If !Daylight(HourAt(stamp))
        Return
    EndIf
    Int cycle = CycleAt(stamp)
    Float anchor = stamp
    If arrivalScheduleCycle != cycle
        If arrivalWasRelevant
            anchor = (cycle as Float) + 8.0 / 24.0
        EndIf
        arrivalScheduleCycle = cycle
        nextArrivalAt = 0.0
    EndIf
    Bool olderLongDelay = (nextArrivalAt - stamp) * 1440.0 > 7.1
    If (nextArrivalAt <= 0.0 || olderLongDelay) && (dailyPopulation == 0 || ResidentCountSafe() < dailyPopulation)
        nextArrivalAt = anchor + Utility.RandomFloat(3.0, 7.0) / 1440.0
    EndIf
EndFunction
'''
 # Keep the already-planned daytime AI deadline alive after the population
 # is full. This is a matching fallback, NOT a new polling frequency.
 def plan(f):
  needle='        Float fallback = ArrivalFallbackDelay()';assert needle in f
  return f.replace(needle,'''        Float fallback = ArrivalFallbackDelay()
        If Daylight(hour) && ResidentCountSafe() > 0
            If arrivalTimeScale == None
                arrivalTimeScale = Game.GetFormFromFile(0x3A, "Skyrim.esm") as GlobalVariable
            EndIf
            If arrivalTimeScale != None
                Float scale = arrivalTimeScale.GetValue()
                If scale > 0.0
                    Float roamingWake = delta * 3600.0 / scale
                    If roamingWake < 2.0
                        roamingWake = 2.0
                    EndIf
                    If fallback <= 0.0 || roamingWake < fallback
                        fallback = roamingWake
                    EndIf
                EndIf
            EndIf
        EndIf''',1)
 t=change(t,'PlanNext',plan)
 # Walled controller must use the same location fallback for roaming as it
 # already uses for arrivals. An unavailable world query is not a different city.
 if p.stem=='MB_CityController':
  def relevance(f):
   needle='''    If !viewer.IsInInterior()
        Return False
    EndIf
''';assert needle in f
   return f.replace(needle,'',1)
  t=change(t,'PlayerInCity',relevance)
 # Documented vanilla registration contract: explicitly replace an unelapsed
 # timer. Previously mocks silently guaranteed replacement without this call.
 lines=t.splitlines(True);out=[]
 for line in lines:
  if re.match(r'^\s*RegisterForSingleUpdate\(',line):
   indent=line[:len(line)-len(line.lstrip())]
   if not out or not(out[-1].strip()=='UnregisterForUpdate()' or (out[-1].strip()=='UnregisterForUpdateGameTime()' and len(out)>1 and out[-2].strip()=='UnregisterForUpdate()')):out.append(indent+'UnregisterForUpdate()\n')
  out.append(line)
 t=''.join(out)
 (OUT/p.name).write_text(t)
print('v1.2.5: progress checkpoints, one-pass normal reconciliation and entry-anchored deadlines; no new serialized fields.')
