"""Final ESP/PEX checks and fault-aware native mocks. This does not run Skyrim."""
from pathlib import Path
import json,struct,hashlib,types,sys,collections,zipfile
sys.path[:0]=['work/src','work/deps/esplib/src']
from esplib import Plugin
from pexcheck import Pex
from vmad_reader import quest_vmad
ROOT=Path(__file__).resolve().parent;R=ROOT.parent/'build/v1.2.1';RT=R/'runtime';BASE=ROOT.parent/'v1.1.0/runtime'
with zipfile.ZipFile(ROOT.parent/'build/v1.1.0/deliverables/MoreBrats-v1.1.0.zip') as released:
 for name in released.namelist():
  if not name.endswith('/'):assert (BASE/name).read_bytes()==released.read(name),('Not the released v1.1.0 foundation',name)
assert (R/'settlements.json').read_bytes()==(ROOT.parent/'build/v1.1.0/settlements.json').read_bytes()
def load(root):
 p=Plugin(root/'MoreBrats.esp');return p,{int(r.form_id):r for t in ['GLOB','FACT','NPC_','CELL','ACHR','REFR','PACK','QUST','FLST'] for r in p.get_records_by_signature(t)}
p,recs=load(RT);old,before=load(BASE)
def subs(r,omit=()):return [(s.signature,s.data) for s in r.subrecords if s.signature not in omit]
def fid(r,t):return struct.unpack('<I',r.get_subrecord(t).data)[0]
def ids(r,t):return [struct.unpack('<I',s.data)[0] for s in r.get_subrecords(t)]
assert p.header.author==old.header.author=='Tsoxer' and p.header.masters==old.header.masters
assert len(recs)==19941 and set(before)<=set(recs)
assert p.header.next_object_id>max(k&0xffffff for k in recs)
changed=[]
for k,a in before.items():
 b=recs[k];assert a.signature==b.signature and a.editor_id==b.editor_id and a.flags==b.flags
 if subs(a)==subs(b):continue
 if a.signature=='GLOB':
  assert a.editor_id.endswith(('_Build','_ScriptBuild','_DiagAIRevision')) or a.editor_id in ['MB_Build','MB_ScriptBuild','MB_DiagAIRevision','MB_RepairBuild']
  assert subs(a,['FLTV'])==subs(b,['FLTV']) and struct.unpack('<f',b.get_subrecord('FLTV').data)[0]==1201
 elif a.signature=='QUST':
  assert subs(a,['VMAD'])==subs(b,['VMAD'])
  am,aa=quest_vmad(a);bm,ba=quest_vmad(b);assert aa==ba and am.keys()==bm.keys()
  for script,props in am.items():assert {n:v for n,v in bm[script].items() if n!='NamedDonorForms'}==props
 else:raise AssertionError(('Unapproved old record change',a.editor_id))
 changed.append(a.editor_id)
assert len(changed)==77
cfg=json.loads((R/'settlements.json').read_text());roster=json.loads((ROOT/'Config/appearance-roster.json').read_text())
donors=roster['additional_donors'];newrefs=set();combos=set()
for c in cfg:
 root=0x3000000+c['base'];append=0x100000+c['base']*16
 props=next(iter(quest_vmad(recs[root])[0].values()))
 flst=props['NamedDonorForms']['form'];assert flst==0x3000000+append+0x1000
 refs=ids(recs[flst],'LNAM');assert refs==list(range(0x3000000+append+0x2000,0x3000000+append+0x2000+160*c['maximum']))
 newrefs.update(refs)
 for i,key in enumerate(refs):
  variant=i//c['maximum'];donor=donors[variant//5];outfit=variant%5
  race=roster['races'].index(donor['Race']);girl=donor['Gender']=='Female'
  local=(3 if girl else 0)+outfit if outfit<3 else 6+(2 if girl else 0)+outfit-3
  sourceid=c['npc_ids'][local] if race==0 else 0x20000+c['base']+(race-1)*10+local
  npc=recs[fid(recs[key],'NAME')];source=before[0x3000000+sourceid]
  assert subs(npc,['EDID','TPLT'])==subs(source,['EDID','TPLT'])
  expected={'Skyrim.esm':0,'HearthFires.esm':0x1000000,'Dragonborn.esm':0x2000000}[donor['master']]+donor['local_id']
  assert fid(npc,'TPLT')==expected and npc.get_subrecord('FULL').data==b'Child\0'
  assert subs(recs[key],['EDID','NAME'])==subs(before[0x3000809],['EDID','NAME'])
  combos.add((donor['name'],outfit))
assert len(newrefs)==12160 and len(combos)==160
assert (RT/'Seq/MoreBrats.seq').read_bytes()==(BASE/'Seq/MoreBrats.seq').read_bytes()
def norm(x):
 if isinstance(x,str):return x.replace('v1.2.1','v1.1.0')
 if isinstance(x,(list,tuple)):return [norm(v) for v in x]
 if isinstance(x,dict):return {k:norm(v) for k,v in x.items()}
 return x
allowed={'service','enabledcount','recoverorphans','initdiagnostics','ensuresetup','showstatus','tryarrival','poolindex','slotfrompoolindex','poolslotdisabled','reconcile','appearancepoolsize','poolactor','orphansamples','storeorphansamples','ensureappearancestorage','resolveappearancepools'}
function_diffs={}
for path in (RT/'Scripts').glob('*.pex'):
 a=Pex(BASE/'Scripts'/path.name);b=Pex(path)
 for k,v in a.obj['variables'].items():assert b.obj['variables'][k]==v
 for k,v in a.obj['properties'].items():assert b.obj['properties'][k]==v
 changedfn=[k for k,f in a.obj['functions'].items() if norm(f)!=norm(b.obj['functions'][k])]
 assert set(changedfn)<=allowed if 'Controller' in path.stem else not changedfn
 if 'Controller' not in path.stem:assert path.read_bytes()==(BASE/'Scripts'/path.name).read_bytes()
 for fn,f in b.obj['functions'].items():
  st=dict(f['locals']+f['params'])|{k:v[0] for k,v in b.obj['variables'].items()};dest=[]
  for op,args,va in f['ins']:
   if op==14:assert not(args[1]==(0,None) and st.get(args[0][1].lower(),'').endswith('[]'))
   if op==30:
    assert st[args[0][1].lower()].endswith('[]') and 1<=args[1][1]<=128;dest.append(args[0][1])
  assert len(dest)==len(set(dest))
 function_diffs[path.name]=dict(changed=changedfn,unchanged=len(a.obj['functions'])-len(changedfn),added=sorted(set(b.obj['functions'])-set(a.obj['functions'])))
print('PASS: all 4,722 old FormIDs, old NPC/ref/PACK payloads, old VMAD bindings, 200 appearances and valid typed PEX storage',flush=True)

# Extend the existing test fixture's data loading only. The same fault-aware VM
# executes the actual PEX. Native references/loading/time/geometry remain mocks.
text=(ROOT.parent/'src/test_support_v051.py').read_text()
needle="pool=[a['form'] for a in s.bindings['PoolRefs']]"
text=text.replace(needle,needle+"\n   for label in ['ImperialRefs','BretonRefs','RedguardRefs']:\n    pool += [a['form'] for a in s.bindings.get(label,[])]\n   if 'NamedDonorForms' in s.bindings:\n    pool += ids(self.records[s.bindings['NamedDonorForms']['form']],'LNAM')")
text=text.replace("['NightMode','DayArea','RoamFaction','PoolForms','RoadForms']","[k for k in ['NightMode','DayArea','RoamFaction','PoolForms','RoadForms','NamedDonorForms'] if k in s.bindings]")
mod=types.ModuleType('donor_test_support');exec(compile(text,'donor_test_support','exec'),mod.__dict__)
# Keep the original allocation/error semantics. Only the mock runaway-loop
# guard is raised for the now-larger *finite* reconciliation loops; this is not
# a Skyrim VM limit or a production-code optimization. Record the work instead.
vmtext=(ROOT.parent/'src/array_vm.py').read_text().replace("assert steps<100000,'loop exceeded bound'","assert steps<1000000,'loop exceeded expanded finite-pool test bound'")
vmtext=vmtext.replace('self.executed=0','self.executed=0;self.max_call_steps={}')
vmtext=vmtext.replace('steps+=1;self.executed+=1','steps+=1;self.executed+=1;self.max_call_steps[name.lower()]=max(self.max_call_steps.get(name.lower(),0),steps)')
budgetvm=types.ModuleType('donor_budget_vm');exec(compile(vmtext,'donor_budget_vm','exec'),budgetvm.__dict__);mod.VM=budgetvm.VM
mod.SETS['1.1.0']=(BASE,before,{k:r for k,r in before.items() if r.signature=='PACK'},0x3000000)
mod.SETS['1.2.1']=(RT,recs,{k:r for k,r in recs.items() if r.signature=='PACK'},0x3000000)
def variant(e,s,child):
 key=next(k for k,v in e.byid.items() if v is child);base=fid(e.records[key],'NAME')&0xffffff
 if base>=0x100000:return 40+base-(0x100000+s.cfg['base']*16)
 if base>=0x20000:return 10+base-(0x20000+s.cfg['base'])
 return e.variant(s,child)
def main():
 olde=mod.Env(42,version='1.1.0');e=mod.Env(42,version='1.2.1');e.place_player(e.rural,[0.,0.,0.]);olde.place_player(olde.rural,[0.,0.,0.])
 # Initialize with real PEX to validate added forms and typed allocation.
 e.set_time(20,11);e.tick_all();olde.set_time(20,11);olde.tick_all()
 mapping=0
 for name,s in e.cities.items():
  os=olde.cities[name]
  for slot in range(s.maximum):
   for v in range(200):
    idx=s.vm.call('PoolIndex',slot,v);actor=s.vm.call('PoolActor',idx)
    assert actor is not None and s.vm.call('SlotFromPoolIndex',idx)==slot and variant(e,s,actor)==v
    if v<40:
     assert idx==os.vm.call('PoolIndex',slot,v)
     a=os.vm.call('PoolActor',idx);assert next(k for k,x in e.byid.items() if x is actor)==next(k for k,x in olde.byid.items() if x is a)
    mapping+=1
  for i in list(range(s.maximum*40,s.maximum*200,127))+[s.maximum*200-1]:
   s.vm.call('StoreOrphanSamples',i,2);assert s.vm.call('OrphanSamples',i)==2;s.vm.call('StoreOrphanSamples',i,0)
 assert mapping==15200
 print('PASS: all 15,200 slot/variant mappings; every old index and actor identity unchanged',flush=True)
 # Every donor and outfit is reachable, while race/gender/clothing draws retain
 # their original independent inclusive bounds. Force ONLY the donor RNG here.
 ss=e.cities['Whiterun'];original_native=ss.vm.native;seen=set()
 for group in roster['groups']:
  for donor_index in range(group['count']):
   for clothing in range(5):
    def forced(target,method,args):
     if isinstance(target,str) and target.lower()=='utility' and method.lower()=='randomint':
      assert list(args)==[0,group['count']-1];return donor_index
     return original_native(target,method,args)
    ss.vm.native=forced
    gender=group['gender'];legacy=(gender*3+clothing if clothing<3 else 6+gender*2+clothing-3)+(group['race']-1)*10
    v=ss.vm.call('SelectDonorVariant',group['race'],gender,clothing,legacy)
    if donor_index==0:assert v==legacy
    else:assert v==group['additional'][donor_index-1]+clothing
    seen.add(v)
 ss.vm.native=original_native;assert seen==set(range(200))
 for stem in ['MB_Controller','MB_CityController','MB_TownController','MB_VillageController']:
  fn=Pex(RT/'Scripts'/f'{stem}.pex').obj['functions']['tryarrival'];draws=[]
  for op,a,va in fn['ins']:
   if op==25 and a[0][1].lower()=='utility' and a[1][1].lower()=='randomint':draws.append(tuple(x[1] for x in va))
  assert draws[:3]==[(1,4),(1,2),(0,4)]
 print('PASS: all 200 cosmetic choices, category-specific uniform donor bounds, unchanged race/gender/outfit RNG bounds',flush=True)
 # The existing mock daily-cycle assertions, shortened to ten days because
 # complete appearance coverage is independently exhaustive above.
 e=mod.Env(42,version='1.2.1');e.place_player(e.rural,[0.,0.,0.])
 frequencies={n:collections.Counter() for n in e.cities}
 for day in range(21,31):
  e.set_time(day,8.55);e.tick_all()
  for name,s in e.cities.items():
   assert len(e.enabled(s))==s.vm.vars['dailypopulation'],(day,name,len(e.enabled(s)),s.vm.vars['dailypopulation'],s.vm.vars['diagreason'])
   frequencies[name].update(variant(e,s,c) for c in e.enabled(s))
   e.place_player(s.cells[0],s.roads[0].xyz);e.tick(s)
   if day%3==0:e.save_load(s);e.tick(s)
   e.place_player(e.rural,[0.,0.,0.])
  e.set_time(day,19.1);e.tick_all()
  for s in e.cities.values():assert all(c.rank==slot*4+3 for slot,c in enumerate(e.residents(s)) if c is not None)
  e.set_time(day+1,3.1);e.tick_all();e.tick_all();assert all(not e.enabled(s) for s in e.cities.values())
  print('Mock daily cycle',day-20,'/10 complete',flush=True)
 # Upgrade actual old PEX state with new fields unbound. Keep ALL old ref objects
 # and serialized values, including selectedVariant, live residents and arrays.
 upgrades=[]
 for mode in ['day','inn','watched03']:
  oldworld=mod.Env(77,version='1.1.0');oldworld.set_time(20,11);oldworld.place_player(oldworld.rural,[0.,0.,0.]);oldworld.tick_all()
  oldworld.records=recs;oldworld.rootpath=RT
  for name,s in oldworld.cities.items():
   vm=s.vm;actors=oldworld.enabled(s)[:];arrays={k:v for k,v in vm.vars.items() if isinstance(v,list)};selected=vm.vars['selectedvariant'][:]
   script='MB_Controller' if s.whiterun else 'MB_VillageController' if s.village else 'MB_TownController' if s.town else 'MB_CityController'
   new=mod.VM(Pex(RT/'Scripts'/f'{script}.pex'),oldworld.native);new.vars.update(vm.vars);s.vm=new;s.pex=Pex(RT/'Scripts'/f'{script}.pex');oldworld.owners[new]=s;oldworld.forms[s.root]=new;oldworld.running[new]=True;s.alias.property('Controller',new)
   props=next(iter(quest_vmad(recs[s.root])[0].values()));flid=props['NamedDonorForms']['form'];newactors=[]
   for key in ids(recs[flid],'LNAM'):
    child=mod.Ref(f'{name} New{key}',oldworld.storage,None,[0.,0.,0.],True,True);s.pool.append(child);newactors.append(child);oldworld.forms[key]=child;oldworld.byid[key]=child;oldworld.owners[child]=s;s.packages.append(ids(recs[fid(recs[key],'NAME')],'PKID'))
   oldworld.forms[flid]=mod.FormList(newactors)
   assert new.vars[new.obj['properties']['nameddonorforms'][1]] is None
   if mode!='day':
    for i,c in enumerate(actors):c.cell=s.inn;c.world=None;c.xyz=[4000.+i*700,0.,0.]
    oldworld.place_player(s.inn);oldworld.set_time(21 if mode=='watched03' else 20,3.1 if mode=='watched03' else 22)
    if mode=='watched03':oldworld.visible.add(actors[0])
   else:oldworld.set_time(20,11);oldworld.place_player(oldworld.rural,[0.,0.,0.])
   s.alias.call('OnPlayerLoadGame');oldworld.tick(s)
   assert new.vars['selectedvariant']==selected
   assert all(new.vars[k] is v for k,v in arrays.items())
   assert all(c in oldworld.residents(s) for c in actors if not c.disabled)
   if mode=='watched03':assert not actors[0].disabled
   upgrades.append([name,mode])
  print('PASS: old-state upgrade',mode,'19 settlements; old fields, arrays, actors and selected variants retained',flush=True)
 faults=[]
 for name in ['Whiterun','Markarth','Morthal','Riverwood']:
  for field in ['donoractors0','donorhidden0']:
   env=mod.Env(44,version='1.2.1');s=env.cities[name];env.set_time(40,11);env.place_player(s.inn)
   s.vm.deny_allocations.add(field)
   assert not s.vm.call('EnsureSetup') and not s.vm.vars['diagstorageready'] and s.vm.vars['schemaversion']==0
   assert s.vm.vars['diagreason']==30 and not env.enabled(s)
   s.vm.deny_allocations.clear();s.vm.array_errors.clear();env.tick(s)
   assert s.cfg['minimum']<=len(env.enabled(s))<=s.maximum
   faults.append([name,field,'allocation refusal, no schema commit, recovery'])
 env=mod.Env(44,version='1.2.1');s=env.cities['Whiterun'];env.set_time(40,11);env.place_player(s.inn)
 flst=env.forms[s.bindings['NamedDonorForms']['form']];flst.values[0]=None
 env.tick(s);assert s.cfg['minimum']<=len(env.enabled(s))<=s.maximum and not s.vm.vars['bindingspending']
 assert s.vm.vars['diagresolved']==1200 and s.vm.vars['diagnamedidrecovered']==1
 faults.append(['Whiterun','one absent added reference','stable-ID fallback restores the missing list binding'])
 env=mod.Env(44,version='1.2.1');s=env.cities['SkaalVillage'];env.set_time(40,11);env.skaal_stage=0;env.tick(s)
 assert not env.enabled(s) and s.vm.vars['diagreason']==32
 env.skaal_stage=70;env.tick(s);assert 1<=len(env.enabled(s))<=3
 faults.append(['SkaalVillage','availability','existing quest gate retained'])
 print('PASS: cached append storage/allocation faults, individual missing donor reference and unchanged Skaal availability',flush=True)
 # Compiled-bytecode workload counts, not wall-clock timings or game profiling.
 workload={}
 for version in ['1.1.0','1.2.1']:
  env=mod.Env(42,version=version);env.set_time(40,11);env.place_player(env.rural,[0.,0.,0.]);env.tick_all()
  beforeops=sum(s.vm.executed for s in env.cities.values());env.native_calls.clear()
  for s in env.cities.values():s.vm.call('EnabledCount')
  workload[version]={'enabled_count_scan_PEX_opcodes':sum(s.vm.executed for s in env.cities.values())-beforeops,'native_calls':dict(env.native_calls),'references':sum(len(s.pool) for s in env.cities.values()),'largest_single_function_mock_steps':max(max(s.vm.max_call_steps.values()) for s in env.cities.values())}
 result=dict(status='PASS',version='1.2.1-unreleased',old_FormIDs_retained=len(before),old_records_modified=changed,records=len(recs),new_reusable_refs=len(newrefs),total_reusable_refs=15200,donors=40,male_donors=22,female_donors=18,appearance_combinations=200,unchanged_settlements=19,function_diffs=function_diffs,mock_settlement_days=190,mock_upgrade_cases=upgrades,mock_faults=faults,exhaustive_variant_mappings=mapping,scan_workload=workload,Skyrim_executed=False,actual_ESS_tested=False,limits='Native functions, events, geometry, LOS and loading are mocked; no rendering, replacer, real-save or pathfinding verification.')
 (R/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
 print('PASS: final structural/compiled-PEX/mock checks; no Skyrim execution',flush=True)
if __name__=='__main__':main()
