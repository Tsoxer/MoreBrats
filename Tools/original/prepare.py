from pathlib import Path
import re,json,struct,hashlib,zipfile,difflib
from esplib import Plugin
from vmad_reader import quest_vmad
R=Path('work/build/v1.1.0');S=R/'source';S.mkdir(parents=True,exist_ok=True)
BASE=Path('work/download/dist/MoreBrats-v1.0.0.zip')
assert hashlib.sha256(BASE.read_bytes()).hexdigest()=='e5af15b34332cdeabd135a40850707ba86b5a6fc5159011fa3ee7689ed446bea'
with zipfile.ZipFile(BASE) as z:
 for name in z.namelist():assert z.read(name)==(Path('work/v1.0.0/runtime')/name).read_bytes()
p=Plugin('work/v1.0.0/runtime/MoreBrats.esp');records={int(r.form_id):r for t in ['NPC_','ACHR','QUST'] for r in p.get_records_by_signature(t)}
def fid(r,t):return struct.unpack('<I',r.get_subrecord(t).data)[0]
config=[]
for q in p.get_records_by_signature('QUST'):
 main,_=quest_vmad(q)
 if not main:continue
 _,b=next(iter(main.items()));white='CityName' not in b
 pool=[x['form'] for x in b['PoolRefs']]
 npcs=[fid(records[pool[(v if v<6 else 36+v-6) if white else v]],'NAME')&0xffffff for v in range(10)]
 config.append(dict(name=b.get('CityName','Whiterun'),base=int(q.form_id)&0xffffff,maximum=b.get('MaxPopulation',6),npc_ids=npcs,pool=pool))
(R/'settlements.json').write_text(json.dumps(config,indent=2))
def funcs(text):return {m[1].lower():m.group() for m in re.finditer(r'^(?:\w+(?:\[\])? )?Function (\w+)\([^\n]*\).*?^EndFunction',text,re.M|re.S)}
diff=[]
for path in sorted(Path('work/v1.0.0/src').glob('MB_*.psc')):
 old=path.read_text();text=old.replace('v1.0.0','v1.1.0')
 if 'Controller' in path.stem:
  white=path.stem=='MB_Controller';count='60' if white else '(MaxPopulation * 10)';capacity=60 if white else 90
  root='0x20800' if white else '(0x20000 + ConfigBase)'
  text=text.replace('1000.0','1100.0')
  text=text.replace('Actor[] Property PoolRefs Auto','Actor[] Property PoolRefs Auto\nActor[] Property ImperialRefs Auto\nActor[] Property BretonRefs Auto\nActor[] Property RedguardRefs Auto\nInt[] imperialHidden\nInt[] bretonHidden\nInt[] redguardHidden')
  fs=funcs(text)
  setup=fs['ensuresetup']
  # Validate additive storage before any reconciliation/arrival. No schema change.
  anchor='    If repairRequested || bindingsPending || schemaVersion < '
  at=setup.index(anchor)
  setup=setup[:at]+'    If !EnsureAppearanceStorage()\n        Return False\n    EndIf\n'+setup[at:]
  anchor='    EndIf\n    ; Every required array'
  assert anchor in setup
  setup=setup.replace(anchor,'        If !ResolveAppearancePools()\n            Return False\n        EndIf\n'+anchor,1)
  text=text.replace(fs['ensuresetup'],setup)
  # Existing Nord binding code remains untouched. All population-wide reads
  # route through one logical index with the original Nord indices preserved.
  for fn in ['reconcile','recoverorphans','poolslotdisabled','tryarrival','enabledcount']:
   current=funcs(text)[fn];new=current
   new=new.replace('pool[PoolIndex(s, variant)]','PoolActor(PoolIndex(s, variant))')
   new=new.replace('pool[PoolIndex(s, v)]','PoolActor(PoolIndex(s, v))')
   new=new.replace('pool[PoolIndex(s, candidateVariant)]','PoolActor(PoolIndex(s, candidateVariant))')
   new=new.replace('pool[PoolIndex(s, selectedVariant[s])]','PoolActor(PoolIndex(s, selectedVariant[s]))')
   new=new.replace('pool[n]','PoolActor(n)').replace('pool[i]','PoolActor(i)')
   new=new.replace('n < MaxPopulation * 10','n < AppearancePoolSize()').replace('i < MaxPopulation * 10','i < AppearancePoolSize()')
   if white:new=new.replace('n < 60','n < AppearancePoolSize()').replace('i < 60','i < AppearancePoolSize()')
   new=new.replace('n < pool.Length','n < AppearancePoolSize()')
   new=new.replace('variant < 10','variant < 40').replace('v < 10','v < 40')
   if fn=='recoverorphans':
    new=new.replace('orphanHidden[i] = RemovalObservation(child, orphanHidden[i])','StoreOrphanSamples(i, RemovalObservation(child, OrphanSamples(i)))')
    new=new.replace('orphanHidden[i] >= 2','OrphanSamples(i) >= 2').replace('orphanHidden[i] = 0','StoreOrphanSamples(i, 0)')
   if fn=='tryarrival':
    new=new.replace('Int gender = Utility.RandomInt(0, 1)','Int race = Utility.RandomInt(1, 4)\n        Int gender = Utility.RandomInt(1, 2) - 1')
    anchor='            selectedVariant[s] = 6 + gender * 2 + clothing - 3\n        EndIf'
    assert anchor in new
    new=new.replace(anchor,anchor+'\n        selectedVariant[s] += (race - 1) * 10')
    new=new.replace('Utility.RandomInt(0, 9)','Utility.RandomInt(0, 39)').replace('(variantOffset + v) % 10','(variantOffset + v) % 40')
   text=text.replace(current,new)
  for fn in ['poolindex','slotfrompoolindex']:
   current=funcs(text)[fn]
   head=current.index('\n')+1
   if fn=='poolindex':extra=f'    If variant >= 10\n        Return (variant / 10) * {count} + slot * 10 + variant % 10\n    EndIf\n'
   else:extra=f'    If index >= {count}\n        Return (index % {count}) / 10\n    EndIf\n'
   text=text.replace(current,current[:head]+extra+current[head:])
  # Diagnostic denominators now describe the complete usable pool.
  text=text.replace('"/" + (MaxPopulation * 10)','"/" + AppearancePoolSize()')
  if white:
   text=text.replace('pool=" + diagResolved + "/60;', 'pool=" + diagResolved + "/240;')
   text=text.replace('"/60; roads=', '"/240; roads=')
  helper=f'''
; Additive appearance storage only. Legacy Nord arrays/indices stay unchanged.
Int Function AppearancePoolSize()
    Return {count} * 4
EndFunction
Actor Function PoolActor(Int index)
    If index < 0 || index >= AppearancePoolSize()
        Return None
    EndIf
    Int group = index / {count}
    Int localIndex = index % {count}
    If group == 0
        Return pool[localIndex]
    ElseIf group == 1
        Return ImperialRefs[localIndex]
    ElseIf group == 2
        Return BretonRefs[localIndex]
    EndIf
    Return RedguardRefs[localIndex]
EndFunction
Int Function OrphanSamples(Int index)
    Int group = index / {count}
    Int localIndex = index % {count}
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
    Int group = index / {count}
    Int localIndex = index % {count}
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
'''
  for name,typ,expected in [('ImperialRefs','Actor',count),('BretonRefs','Actor',count),('RedguardRefs','Actor',count),('imperialHidden','Int',str(capacity)),('bretonHidden','Int',str(capacity)),('redguardHidden','Int',str(capacity))]:
   helper+=f'''    If !{name} || {name}.Length < {expected}
        {name} = new {typ}[{capacity}]
        If !{name} || {name}.Length < {expected}
            StorageFailure("{name}", {expected})
            Return False
        EndIf
        repairRequested = True
    EndIf
'''
  helper+='    Return True\nEndFunction\nBool Function ResolveAppearancePools()\n'
  for group,name in enumerate(['ImperialRefs','BretonRefs','RedguardRefs']):
   helper+=f'''    Int n{group} = 0
    While n{group} < {count}
        Actor candidate{group} = {name}[n{group}]
        If candidate{group} == None
            candidate{group} = Game.GetFormFromFile({root} + 0x100 + {group} * {count} + n{group}, "MoreBrats.esp") as Actor
            {name}[n{group}] = candidate{group}
        EndIf
        If candidate{group} != None
            If {name}[n{group}] != candidate{group}
                StorageFailure("{name} binding readback", {count}, 31)
                Return False
            EndIf
            diagResolved += 1
            diagPoolInputs += 1
        Else
            bindingsPending = True
        EndIf
        n{group} += 1
    EndWhile
'''
  helper+='    Return True\nEndFunction\n'
  text+=helper
 (S/path.name).write_text(text)
 diff.extend(difflib.unified_diff(old.splitlines(True),text.splitlines(True),fromfile='v1.0.0/'+path.name,tofile='v1.1.0/'+path.name))
(R/'source.diff').write_text(''.join(diff))
print('Prepared additive appearance pool sources for 19 settlements; baseline unchanged.')
