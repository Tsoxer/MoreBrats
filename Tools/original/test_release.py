"""Actual final ESP/PEX, fault-aware mock natives; no Skyrim execution."""
from pathlib import Path
import json,struct,hashlib,types,sys,re
from esplib import Plugin
from pexcheck import Pex
from vmad_reader import quest_vmad
R=Path('work/build/v1.1.0');RT=R/'runtime';BASE=Path('work/v1.0.0/runtime')
TYPES=['GLOB','FACT','NPC_','CELL','ACHR','REFR','PACK','QUST','FLST']
def load(root):
 p=Plugin(root/'MoreBrats.esp');return p,{int(r.form_id):r for t in TYPES for r in p.get_records_by_signature(t)}
p,recs=load(RT);old,before=load(BASE)
assert p.header.author=='Tsoxer' and p.header.masters==old.header.masters
assert len(recs)==4722 and set(before)<=set(recs) and p.header.next_object_id>max(k&0xffffff for k in recs)
def subs(r,omit=()):return [(s.signature,s.data) for s in r.subrecords if s.signature not in omit]
def fid(r,t):return struct.unpack('<I',r.get_subrecord(t).data)[0]
def ids(r,t):return [struct.unpack('<I',s.data)[0] for s in r.get_subrecords(t)]
changed=[]
for k,a in before.items():
 b=recs[k];assert a.signature==b.signature and a.editor_id==b.editor_id and a.flags==b.flags
 if subs(a)==subs(b):continue
 if a.signature=='GLOB':assert a.editor_id.endswith(('_Build','_ScriptBuild','_DiagAIRevision')) or a.editor_id in ['MB_Build','MB_ScriptBuild','MB_DiagAIRevision','MB_RepairBuild'];assert subs(a,['FLTV'])==subs(b,['FLTV'])
 elif a.signature=='QUST':
  assert subs(a,['VMAD'])==subs(b,['VMAD'])
  am,aa=quest_vmad(a);bm,ba=quest_vmad(b);assert aa==ba and am.keys()==bm.keys()
  for script,props in am.items():
   assert {n:v for n,v in bm[script].items() if n not in ['ImperialRefs','BretonRefs','RedguardRefs']}==props
 else:raise AssertionError(('Unapproved old record change',a.editor_id))
 changed.append(a.editor_id)
assert len(changed)==77
allrefs=set()
cfg=json.loads((R/'settlements.json').read_text())
for c in cfg:
 root=0x3000000+c['base'];new=0x3000000+0x20000+c['base'];script,b=next(iter(quest_vmad(recs[root])[0].items()))
 count=c['maximum']*10
 for race,name in enumerate(['Imperial','Breton','Redguard']):
  refs=[x['form'] for x in b[name+'Refs']];assert refs==list(range(new+0x100+race*count,new+0x100+(race+1)*count))
  allrefs.update(refs)
  for i,key in enumerate(refs):
   assert recs[key].signature=='ACHR' and int(recs[key].flags)&0xc00==0xc00
   npc=recs[fid(recs[key],'NAME')];source=before[0x3000000+c['npc_ids'][i%10]]
   assert subs(npc,['EDID','RNAM','TPLT'])==subs(source,['EDID','RNAM','TPLT'])
   assert fid(npc,'RNAM')==[0x2c659,0x2c65c,0x2c65a][race]
   girl=bool(struct.unpack_from('<I',npc.get_subrecord('ACBS').data)[0]&1)
   assert fid(npc,'TPLT')==[([0x13359,0x13bad]),([0x1003f56,0x133ab]),([0x100403c,0x13ba9])][race][int(girl)]
   assert npc.get_subrecord('FULL').data==b'Child\0' and not npc.get_subrecords('VMAD')
   assert ids(npc,'PKID')==ids(source,'PKID')
assert len(allrefs)==2280
assert (RT/'Seq/MoreBrats.seq').read_bytes()==(BASE/'Seq/MoreBrats.seq').read_bytes()
def norm(x):
 if isinstance(x,str):return x.replace('v1.1.0','v1.0.0')
 if isinstance(x,(list,tuple)):return [norm(v) for v in x]
 if isinstance(x,dict):return {k:norm(v) for k,v in x.items()}
 return x
allowed={'ensuresetup','reconcile','recoverorphans','poolindex','slotfrompoolindex','poolslotdisabled','tryarrival','enabledcount','showstatus','initdiagnostics'}
functions={}
for path in (RT/'Scripts').glob('*.pex'):
 a=Pex(BASE/'Scripts'/path.name);b=Pex(path)
 for k,v in a.obj['variables'].items():assert b.obj['variables'][k]==v
 for k,v in a.obj['properties'].items():assert b.obj['properties'][k]==v
 changedfn=[k for k,f in a.obj['functions'].items() if norm(f)!=norm(b.obj['functions'][k])]
 assert set(changedfn)<=allowed if 'Controller' in path.stem else not changedfn
 for fn,f in b.obj['functions'].items():
  st=dict(f['locals']+f['params'])|{k:v[0] for k,v in b.obj['variables'].items()}
  dest=[]
  for op,args,va in f['ins']:
   if op==14:assert not(args[1]==(0,None) and st.get(args[0][1].lower(),'').endswith('[]'))
   if op==30:
    assert st[args[0][1].lower()].endswith('[]') and 1<=args[1][1]<=128;dest.append(args[0][1])
  assert len(dest)==len(set(dest))
 functions[path.name]=dict(changed=changedfn,unchanged=len(a.obj['functions'])-len(changedfn))
print('PASS: old records, all new appearances, properties, opcodes/unchanged functions, array layout, SEQ',flush=True)
# Extend only the fixture's appearance map; no mock implementation of race RNG.
text=Path('work/src/test_support_v051.py').read_text()
text=text.replace("pool=[a['form'] for a in s.bindings['PoolRefs']]", "pool=[a['form'] for a in s.bindings['PoolRefs']]\n   for label in ['ImperialRefs','BretonRefs','RedguardRefs']:\n    pool += [a['form'] for a in s.bindings.get(label,[])]")
mod=types.ModuleType('appearance_test_support');exec(compile(text,'appearance_test_support','exec'),mod.__dict__)
mod.SETS['1.1.0']=(RT,recs,{k:r for k,r in recs.items() if r.signature=='PACK'},0x3000000)
from collections import Counter
stats={n:Counter() for n in [c['name'] for c in cfg]};counts={n:set() for n in stats}
def variant(e,s,child):
 base=fid(e.records[next(k for k,v in e.byid.items() if v is child)],'NAME')&0xffffff
 if base>=0x20000:return 10+(base-(0x20000+s.cfg['base']))
 return e.variant(s,child)
e=mod.Env(77,version='1.1.0');e.place_player(e.rural,[0.,0.,0.]);sizes={n:len(s.pool) for n,s in e.cities.items()}
assert sum(sizes.values())==3040
for day in range(100):
 e.set_time(day,8.55);e.tick_all()
 for n,s in e.cities.items():
  refs=e.enabled(s);assert len(refs)==s.vm.vars['dailypopulation'];counts[n].add(len(refs));stats[n].update(variant(e,s,c) for c in refs)
  # Frozen AI packages/schedule perform their original state transitions.
  e.place_player(s.cells[0],s.roads[0].xyz);e.tick(s)
  if day%25==0:e.save_load(s);e.tick(s)
  e.place_player(e.rural,[0.,0.,0.])
 e.set_time(day,19.1);e.tick_all()
 for s in e.cities.values():assert all(c.rank==slot*4+3 for slot,c in enumerate(e.residents(s)) if c is not None)
 e.set_time(day+1,3.1);e.tick_all();e.tick_all();assert all(not e.enabled(s) for s in e.cities.values())
 if day%25==24:print('Progress: completed',day+1,'mock days across 19 settlements',flush=True)
assert set().union(*(set(v) for v in stats.values()))==set(range(40))
assert all({v//10 for v in c}==set(range(4)) for c in stats.values())
assert all(counts[n]==set(range(s.cfg['minimum'],s.maximum+1)) for n,s in e.cities.items())
assert sizes=={n:len(s.pool) for n,s in e.cities.items()}
print('PASS: actual-PEX 1,900 settlement-days, all races per settlement, all 40 appearances sampled globally, fixed pool and retained night/retirement phases',flush=True)
# Exact stable Nord index meaning and one-to-one new index mapping in every slot.
for s in e.cities.values():
 for slot in range(s.maximum):
  for v in range(40):
   idx=s.vm.call('PoolIndex',slot,v);actor=s.vm.call('PoolActor',idx)
   assert s.vm.call('SlotFromPoolIndex',idx)==slot and actor is not None
   assert variant(e,s,actor)==v
print('PASS: all 3,040 slot/variant mappings and legacy Nord identity',flush=True)
# Old state transplanted into new actual PEX. Newly introduced properties really
# remain None, so stable-ID lookup/allocation must initialize them.
upgrades=[]
for mode in ['day','inn','watched03']:
 e=mod.Env(42,version='1.0.0');e.set_time(20,11);e.place_player(e.rural,[0,0,0]);e.tick_all()
 # Add new forms to the same mock world, but preserve ALL old actor objects.
 for name,s in e.cities.items():
  oldvm=s.vm;oldactors=e.enabled(s)[:];arrays={k:v for k,v in oldvm.vars.items() if isinstance(v,list)}
  script='MB_Controller' if s.whiterun else 'MB_VillageController' if s.village else 'MB_TownController' if s.town else 'MB_CityController'
  new=mod.VM(Pex(RT/'Scripts'/f'{script}.pex'),e.native);new.vars.update(oldvm.vars);s.vm=new;s.pex=Pex(RT/'Scripts'/f'{script}.pex');e.owners[new]=s;e.forms[s.root]=new;s.alias.property('Controller',new)
  main=next(iter(quest_vmad(recs[s.root])[0].values()))
  for label in ['ImperialRefs','BretonRefs','RedguardRefs']:
   for a in main[label]:
    key=a['form'];child=mod.Ref(f'{name} Extra{key}',e.storage,None,[0.,0.,0.],True,True)
    s.pool.append(child);e.forms[key]=child;e.byid[key]=child;e.owners[child]=s;s.packages.append(ids(recs[fid(recs[key],'NAME')],'PKID'))
  if mode!='day':
   for i,c in enumerate(oldactors):c.cell=s.inn;c.world=None;c.xyz=[4000.+i*700,0.,0.]
   e.place_player(s.inn);e.set_time(21 if mode=='watched03' else 20,3.1 if mode=='watched03' else 22)
   if mode=='watched03':e.visible.add(oldactors[0])
  else:e.set_time(20,11);e.place_player(e.rural,[0,0,0])
  s.alias.call('OnPlayerLoadGame');e.tick(s)
  for k,a in arrays.items():assert new.vars[k] is a
  if mode in ['day','inn']:assert e.enabled(s)==oldactors
  else:assert oldactors[0] in e.enabled(s)
  assert s.vm.call('AppearancePoolSize')==s.maximum*40
  assert all(s.vm.call('PoolActor',i) is not None for i in range(s.maximum*40))
  upgrades.append((name,mode))
print('PASS: 57 typed old-save active-day/inn/watched03 appearance-storage upgrades; old actors/arrays retained',flush=True)
result=dict(status='PASS',version='1.1.0',records=4722,old_records_retained=1872,old_records_modified=changed,
            new_NPC_bases=570,new_reusable_refs=2280,total_reusable_refs=3040,all_AI_PACK_records_byte_identical=True,
            SEQ_byte_identical=True,settlements=19,appearance_combinations=40,unchanged_functions=functions,
            mock_settlement_days=1900,mock_upgrade_cases=upgrades,frequencies={n:dict(c) for n,c in stats.items()},
            Skyrim_executed=False,actual_ESS_tested=False,scope='Compiled PEX with fault-aware arrays and mocked native calls/geometry; no native door solver or rendering test.')
(R/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
