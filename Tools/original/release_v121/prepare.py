"""Targeted correction of the actual v1.2.0 source; no older regeneration."""
from pathlib import Path
import re,shutil
ROOT=Path(__file__).resolve().parent;WORK=ROOT.parent;SRC=WORK/'v1.2.1/src'
def function(text,name,edit):
 pat=re.compile(r'(?m)^(?:(?:Bool|Int|Float|Actor|String) )?Function '+name+r'\([^\n]*\)\n.*?^EndFunction',re.M|re.S)
 m=pat.search(text);assert m,name
 return text[:m.start()]+edit(m.group())+text[m.end():]
for path in (WORK/'v1.2.0/src').glob('*.psc'):
 if 'Controller' not in path.stem:
  shutil.copyfile(path,SRC/path.name);continue
 t=path.read_text().replace('v1.2.0','v1.2.1').replace('1200.0','1201.0')
 root='0x108000' if path.stem=='MB_Controller' else '(0x100000 + ConfigBase * 16)'
 # Diagnostic state only. Existing serialized fields/types remain intact.
 t=t.replace('Int diagRoadInputs = 0','Int diagRoadInputs = 0\nInt diagNamedResolved = 0\nInt diagNamedIDRecovered = 0\nInt diagNamedMissing = 0\nInt diagNamedCatalogState = 0\nInt diagAppearanceFallbacks = 0')
 def resolve(f):
  old='''    Int namedIndex = 0
    While namedIndex < '''
  assert old in f
  size='(6 * 160)' if path.stem=='MB_Controller' else '(MaxPopulation * 160)'
  f=f.replace(old,f'''    diagNamedResolved = 0
    diagNamedIDRecovered = 0
    diagNamedMissing = 0
    diagNamedCatalogState = 0
    Bool namedCatalogValid = False
    If NamedDonorForms != None
        namedCatalogValid = NamedDonorForms.GetSize() == {size}
        If namedCatalogValid
            diagNamedCatalogState = 1
        Else
            diagNamedCatalogState = 2
        EndIf
    EndIf
    Int namedIndex = 0
    While namedIndex < ''')
  old='        Actor namedActor = NamedDonorForms.GetAt(namedIndex) as Actor'
  assert old in f
  f=f.replace(old,f'''        ; Match v1.1.0's pool contract: keep valid saved bindings first,
        ; then try editor binding, then the verified stable local actor ID.
        Actor namedActor = DonorActorRead(namedIndex)
        If namedActor == None && namedCatalogValid
            namedActor = NamedDonorForms.GetAt(namedIndex) as Actor
        EndIf
        If namedActor == None
            namedActor = Game.GetFormFromFile({root} + 0x2000 + namedIndex, "MoreBrats.esp") as Actor
            If namedActor != None
                diagNamedIDRecovered += 1
            EndIf
        EndIf''')
  pos=f.index('    Int namedIndex = 0');before=f[:pos];tail=f[pos:]
  tail=tail.replace('        If namedActor != None\n            diagResolved += 1','        If namedActor != None\n            diagNamedResolved += 1\n            diagResolved += 1').replace('        Else\n            bindingsPending = True','        Else\n            diagNamedMissing += 1\n            bindingsPending = True')
  return before+tail
 t=function(t,'ResolveAppearancePools',resolve)
 def arrival(f):
  needle='    If PoolActor(PoolIndex(s, selectedVariant[s])) == None\n'
  assert needle in f
  return f.replace(needle,needle+'        diagAppearanceFallbacks += 1\n        Log("appearance binding unavailable; selected variant=" + selectedVariant[s] + "; using existing per-slot fallback")\n',1)
 t=function(t,'TryArrival',arrival)
 # Same audits and safety decisions, fewer redundant script calls. No new
 # cadence, cache-of-enabled-state assumption, controller, event or timer.
 def count(f):
  f=f.replace('        While n < AppearancePoolSize()','        Int poolSize = AppearancePoolSize()\n        While n < poolSize')
  return f.replace('            If PoolActor(n) != None && !PoolActor(n).IsDisabled()','            Actor candidate = PoolActor(n)\n            If candidate != None && !candidate.IsDisabled()')
 t=function(t,'EnabledCount',count)
 t=function(t,'PoolSlotDisabled',lambda f:f.replace('        If PoolActor(PoolIndex(s, v)) != None && !PoolActor(PoolIndex(s, v)).IsDisabled()','        Actor candidate = PoolActor(PoolIndex(s, v))\n        If candidate != None && !candidate.IsDisabled()'))
 # Service still publishes diagnostics after a failed setup. A partially
 # initialized pool must return None for unreadable pages, never ARRAYGET None.
 def guarded_pool(f):
  for array in ['pool','ImperialRefs','BretonRefs','RedguardRefs']:
   needle='Return '+array+'[localIndex]'
   guard=f'If !{array} || localIndex >= {array}.Length\n            Return None\n        EndIf\n        '+needle
   f=f.replace(needle,guard,1)
  return f
 t=function(t,'PoolActor',guarded_pool)
 def guarded_donors(f):
  for n in re.findall(r'Return donorActors(\d+)\[localIndex\]',f):
   f=f.replace(f'        Return donorActors{n}[localIndex]',f'''        If !donorActors{n} || localIndex >= donorActors{n}.Length
            Return None
        EndIf
        Return donorActors{n}[localIndex]''',1)
  return f
 t=function(t,'DonorActorRead',guarded_donors)
 def reconcile(f):
  f=f.replace('    Int s = 0','    Int poolSize = AppearancePoolSize()\n    Int s = 0',1)
  return f.replace('While n < AppearancePoolSize()','While n < poolSize && !found').replace('While i < AppearancePoolSize()','While i < poolSize')
 t=function(t,'Reconcile',reconcile)
 t=function(t,'RecoverOrphans',lambda f:f.replace('    Int i = 0','    Int poolSize = AppearancePoolSize()\n    Int i = 0',1).replace('While i < AppearancePoolSize()','While i < poolSize'))
 # A debug request is consumed only into this immediate read-only display path,
 # not into a local request that may be lost after the long worker/epoch change.
 def service(f):
  f=re.sub(r'(?m)^            If request == 2\n                ShowStatus\(\)\n            EndIf\n','',f)
  f=re.sub(r'(?m)^        If request == 2\n            ShowStatus\(\)\n        EndIf\n','',f)
  needle='    Float now = Utility.GetCurrentRealTime()'
  assert needle in f
  return f.replace(needle,'    If request == 2\n        ShowStatus()\n    EndIf\n'+needle,1)
 t=function(t,'Service',service)
 def status(f):
  f=f.replace('    PublishSnapshot()\n','',1)
  f=f.replace('Function ShowStatus()\n','''Function ShowStatus()
    ; Report the last completed audit without rescanning thousands of actors
    ; before the requested popup. Current stage/storage fields remain live.
    Int snapshotEnabled = -1
    If (DiagnosticGlobals as Bool) && DiagnosticGlobals.Length == 17
        If DiagnosticGlobals[4] != None
            snapshotEnabled = DiagnosticGlobals[4].GetValue() as Int
        EndIf
    EndIf
''',1)
  f=f.replace('"; enabled=" + EnabledCount()','"; enabled(last completed sample)=" + snapshotEnabled')
  needle='    message += "\\nRuntime storage ready="'
  pos=f.index(needle)
  extra='''    message += "\\nAppended bindings: resolved=" + diagNamedResolved + "; stable-ID recovered=" + diagNamedIDRecovered + "; missing=" + diagNamedMissing
    message += "; catalog=" + diagNamedCatalogState + " (0=unavailable,1=valid,2=wrong size)"
    message += "\\nAppearance fallback attempts=" + diagAppearanceFallbacks
    If (selectedVariant as Bool) && diagSlot >= 0 && diagSlot < selectedVariant.Length
        message += "; selected variant=" + selectedVariant[diagSlot]
    EndIf
'''
  return f[:pos]+extra+f[pos:]
 t=function(t,'ShowStatus',status)
 # A non-None but malformed added page must not be reported usable. Never
 # replace a valid saved array or change its element type/meaning.
 def storage(f):
  # The catalog is a binding convenience, not an AI/safety dependency. When
  # absent or malformed, verify the same actor IDs directly instead of vetoing
  # every child. Array shape/readback validation and per-actor missing handling
  # remain mandatory; a wrong-size catalog is never indexed.
  f=re.sub(r'    If NamedDonorForms == None\n        StorageFailure\("NamedDonorForms",.*?    EndIf\n', '', f, count=1, flags=re.S)
  f=re.sub(r'    If NamedDonorForms.GetSize\(\) != .*?    EndIf\n', '', f, count=1, flags=re.S)
  for kind,typ in [('donorActors','Actor'),('donorHidden','Int')]:
   for n,size in re.findall(rf'{kind}(\d+) = new {typ}\[(\d+)\]',f):
    needle=f'    If !{kind}{n}\n'
    replacement=f'''    If ({kind}{n} as Bool) && {kind}{n}.Length != {size}
        StorageFailure("{kind}{n} saved length", {size})
        Return False
    EndIf
'''+needle
    f=f.replace(needle,replacement,1)
  return f
 t=function(t,'EnsureNamedDonorStorage',storage)
 (SRC/path.name).write_text(t)
print('Prepared v1.2.1 from v1.2.0; old fields, pools, donor RNG and schedules retained.')
