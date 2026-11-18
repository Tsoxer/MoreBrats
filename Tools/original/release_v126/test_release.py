"""Final ESP/PEX regression checks. Native timing/AI/save serialization are models, NOT Skyrim."""
from pathlib import Path
import ast,collections,copy,hashlib,json,runpy,struct,sys
W=Path('work');ROOT=W/'release_v126';R=W/'build/v1.2.6';RT=R/'runtime'
sys.path[:0]=[str(W/'src'),str(W/'deps/esplib/src')]
b=runpy.run_path(str(W/'release_v125/test_release.py'),run_name='support_only')
m=b['m'];Pex=b['Pex'];load=b['load'];subs=b['subs'];variant=b['variant'];roster=b['roster']
plugin,recs=load(RT);_,old=load(W/'build/v1.2.5/runtime')
m.SETS['1.2.6']=(RT,recs,{k:r for k,r in recs.items() if r.signature=='PACK'},0x3000000)
results={}
def out(name,value=True):results[name]=value;print('PASS:',name,flush=True)
def env(name='Whiterun',version='1.2.6',hour=10):return b['env'](name,hour,version)
def due(e,s):
 e.now=m.f32(s.vm.vars['nextarrivalat']+0.000003);e.real+=2;s.vm.call('OnUpdateGameTime');e.check(s)
def fill(e,s):
 for _ in range(s.maximum+3):
  if len(e.enabled(s))==s.vm.vars['dailypopulation']:return
  due(e,s)
 raise AssertionError((s.name,'unfilled',s.vm.vars['diagreason']))
def norm(x):
 if isinstance(x,str):return x.replace('v1.2.6','v1.2.5')
 if isinstance(x,(tuple,list)):return [norm(v) for v in x]
 if isinstance(x,dict):return {k:norm(v) for k,v in x.items()}
 return x

def structure():
 assert len(recs)==len(old)==19942 and set(old)==set(recs)
 assert plugin.header.author=='Tsoxer' and plugin.header.masters==['Skyrim.esm','HearthFires.esm','Dragonborn.esm']
 changed=[]
 for key,a in old.items():
  c=recs[key];assert(a.signature,a.flags,a.editor_id)==(c.signature,c.flags,c.editor_id)
  if subs(a)!=subs(c):
   assert a.signature=='GLOB' and subs(a,['FLTV'])==subs(c,['FLTV'])
   assert struct.unpack('<f',c.get_subrecord('FLTV').data)[0]==1206;changed.append(a.editor_id)
 assert len(changed)==58
 assert (RT/'Seq/MoreBrats.seq').read_bytes()==(W/'build/v1.2.5/runtime/Seq/MoreBrats.seq').read_bytes()
 assert (R/'settlements.json').read_bytes()==(W/'build/v1.2.4/settlements.json').read_bytes()
 allowed={'loaded','service','ensuresetup','reconcile','tryarrival','processarrival','placearrival','showstatus','initdiagnostics'}
 added={'loadresidentcheck':('bool',False),'diagarrivaldueat':('float',0.),'diagarrivalattemptat':('float',0.),'diagarrivalenabledat':('float',0.)};diffs={}
 for p in (RT/'Scripts').glob('*.pex'):
  a=Pex(W/'build/v1.2.5/runtime/Scripts'/p.name);c=Pex(p)
  assert a.version==c.version and a.obj['properties']==c.obj['properties']
  for k,v in a.obj['variables'].items():assert c.obj['variables'][k]==v,(p.name,k)
  delta=[k for k,v in a.obj['functions'].items() if norm(c.obj['functions'][k])!=norm(v)]
  assert set(delta)<=allowed,(p.name,delta)
  if 'Controller' not in p.stem:assert p.read_bytes()==(W/'build/v1.2.5/runtime/Scripts'/p.name).read_bytes()
  else:
   assert {k:v for k,v in c.obj['variables'].items() if k not in a.obj['variables']}==added
   for fn in ['tick','saferemoval','removalobservation','updateroaming','begintrip','pickdestination','setphase','recoverorphans','selectdonorvariant','doorarrivalindex','poolindex','poolactor','enabledcount']:
    assert norm(c.obj['functions'][fn])==norm(a.obj['functions'][fn]),(p.name,fn)
  for fn,f in c.obj['functions'].items():
   types=dict(f['locals']+f['params'])|{k:v[0] for k,v in c.obj['variables'].items()}
   for op,args,_ in f['ins']:
    if op==14:assert not(args[1]==(0,None) and types.get(args[0][1].lower(),'').endswith('[]'))
    if op==30:assert types[args[0][1].lower()].endswith('[]') and 1<=args[1][1]<=128
  diffs[p.name]=delta
 out('19942 record identities; only58 version globals; exact NPC/ACHR/PACK/QUST/VMAD/appearance payloads and SEQ',changed)
 out('Nine independently parsed PEX: original serialized fields/properties, AI/departure/RNG/counting unchanged; four additive scalars',diffs)

def ordinary_all19():
 e=m.Env(42,version='1.2.6');e.set_time(40,10);rows=[];mapping=0
 for name,s in e.cities.items():
  e.set_time(40,10)
  e.place_player(s.cells[0],s.roads[0].xyz);p=b['Pump'](e,drop_game=True);s.alias.call('OnCellLoad');p.run(3)
  assert s.vm.vars['nextarrivalat']>e.now,(name,e.now,s.vm.vars['diagstage'],s.vm.vars['diagreason'])
  target=s.vm.vars['dailypopulation'];e.native_calls.clear();count=0;checks=[]
  # Moving right onto the chosen point must still be accepted.
  e.move_hook=lambda child,point:e.place_player(point.cell,point.xyz)
  while len(e.enabled(s))<target:
   e.native_calls.clear();at=s.vm.vars['nextarrivalat'];assert -0.2<=(at-e.now)*1440<=7.1
   p.base_real=e.real;p.base_game=float(e.now);p.run((at-e.now)*86400/20+2)
   assert len(e.enabled(s))==count+1,(name,count,len(e.enabled(s)),s.vm.vars['diagreason'])
   count+=1;checks.append(e.native_calls['isdisabled'])
   assert s.vm.vars['diagarrivalenabledat']>=s.vm.vars['diagarrivalattemptat']>=s.vm.vars['diagarrivaldueat']
   assert all(not a.disabled and a.package for a in e.enabled(s));e.check(s)
  before=len(e.enabled(s));p.base_real=e.real;p.base_game=float(e.now);p.run(45);assert len(e.enabled(s))==before
  for slot in range(s.maximum):
   for v in range(200):
    index=s.vm.call('PoolIndex',slot,v);a=s.vm.call('PoolActor',index)
    assert a is not None and variant(e,s,a)==v and s.vm.call('SlotFromPoolIndex',index)==slot;mapping+=1
  rows.append({'settlement':name,'population':count,'max_enabled_checks_for_scheduled_callback':max(checks),'scheduled_and_confirmed_timestamps':True})
 assert mapping==15200
 out('All19 outdoor moving-player real-time callbacks: gradual actual Enable, package evaluation, target cap, no interior/GT required',rows)
 out('All15200 reference mappings and200 saved indices remain valid',mapping)
 # At maximum populated slots the common routine still checks only76 refs.
 for s in e.cities.values():
  e.place_player(s.inn);s.vm.vars['dailypopulation']=s.maximum
  for i in range(s.maximum):
   if e.residents(s)[i] is None:s.vm.call('TryArrival',i,40)
 e.native_calls.clear()
 for s in e.cities.values():s.vm.call('EnabledCount')
 assert e.native_calls['isdisabled']==76
 out('Routine EnabledCount across maximum population still76 native checks',76)
 return e

def load_and_scan_costs():
 rows=[]
 for version in ['1.2.5','1.2.6']:
  e=m.Env(42,version=version);e.set_time(40,11)
  for s in e.cities.values():e.place_player(s.inn);e.tick(s)
  s=e.cities['Whiterun'];e.place_player(s.cells[0],s.roads[0].xyz)
  e.native_calls.clear()
  for c in e.cities.values():c.alias.call('OnPlayerLoadGame')
  for c in e.cities.values():e.tick(c)
  checks=e.native_calls['isdisabled'];rows.append({'version':version,'19_initialized_empty_controllers_after_load_native_enabled_checks':checks})
  assert checks>=15200 if version=='1.2.5' else checks<10
  if version=='1.2.6':
   # Healthy reload retains the existing last full census deadline.
   oldaudit=s.vm.vars['nextpoolauditat'];s.alias.call('OnPlayerLoadGame');e.tick(s);assert s.vm.vars['nextpoolauditat']==oldaudit
   # Missing array is a demonstrated repair trigger; full adoption must remain.
   spare=s.vm.call('PoolActor',s.vm.call('PoolIndex',2,199));spare.disabled=False
   s.vm.vars['poolaudited']=False;s.alias.call('OnPlayerLoadGame');e.native_calls.clear();e.tick(s)
   assert spare in e.residents(s) and e.native_calls['isdisabled']>=1200;e.check(s)
   out('Incomplete census still forces full recovery/adoption before any arrival')
 out('Compiled loaded-save path: redundant19-settlement full scans removed for healthy empty state',rows)
 # Exact warm arrival path under injected native service latency.
 measured=[]
 for version in ['1.2.5','1.2.6']:
  e,s=env(version=version);e.tick(s);p=b['Pump'](e);at=float(s.vm.vars['nextarrivalat']);p.clock(e.real+max(0,(at-e.now)*86400/20)+.1)
  def native_delay(target,method,args):
   p.hook(target,method,args)
   if method=='isdisabled':p.clock(e.real+0.05)
  e.native_hook=native_delay;e.native_calls.clear();s.vm.call('OnUpdateGameTime')
  assert len(e.enabled(s))==1
  measured.append({'version':version,'IsDisabled':e.native_calls['isdisabled'],'synthetic_overdue_game_minutes':(s.vm.vars.get('diagarrivalenabledat') or e.now-at)*1440 if version=='1.2.5' else (s.vm.vars['diagarrivalenabledat']-at)*1440})
 assert measured[0]['IsDisabled']-measured[1]['IsDisabled']==199
 out('Due-to-Enable path with explicitly injected50ms per enabled check; synthetic timing only',measured)

def hops_and_existing_residents():
 e=m.Env(64,version='1.2.6');e.set_time(40,10);seen={}
 for name in ['Whiterun','Riften','Windhelm','Solitude','DragonBridge','Morthal','Riverwood','Whiterun','Riften']:
  s=e.cities[name];e.place_player(s.cells[0],s.roads[0].xyz);p=b['Pump'](e,drop_game=True)
  for c in e.cities.values():c.alias.call('OnCellLoad')
  p.run(35);assert e.enabled(s),(name,s.vm.vars['diagstage'],s.vm.vars['diagreason'])
  for n,actors in seen.items():assert all(not a.disabled for a in actors),'daytime city departure disabled an actor'
  seen[name]=e.enabled(s)[:];e.check(s)
 out('Whiterun→Riften→Windhelm→Solitude and open-world repeat visits: no door trigger; same-day old actors retained',list(seen))
 for name in ['Whiterun','Solitude','Riverwood','SkaalVillage']:
  s=e.cities[name];e.place_player(s.inn);e.tick(s);actors=e.enabled(s)[:]
  for _ in range(3):s.alias.call('OnPlayerLoadGame');e.tick(s)
  assert all(a in e.residents(s) and not a.disabled for a in actors);e.check(s)
 out('Repeated healthy loads keep active identities, counts and appearances')


def exceptional_recovery_and_lifecycle():
 e=m.Env(42,version='1.2.6');e.set_time(40,10)
 for s in e.cities.values():
  e.place_player(s.cells[0],s.roads[0].xyz);e.tick(s);fill(e,s)
  e.set_time(40,19.1);e.tick(s)
  assert all(a.rank==slot*4+3 for slot,a in enumerate(e.residents(s)) if a)
  for a in e.enabled(s):a.cell=s.inn;a.world=None
  e.place_player(s.inn);e.visible.update(e.enabled(s));e.refresh();e.set_time(41,3.1);e.tick(s);assert e.enabled(s)
  e.visible.clear();e.place_player(e.rural,[0,0,0]);e.tick(s);e.tick(s);assert not e.enabled(s)
  e.set_time(44,10);e.place_player(s.cells[0],s.roads[0].xyz);e.tick(s);fill(e,s);e.check(s)
  e.set_time(40,10)
 out('All19: 19:00 packages, watched03 retention, safe unloaded retirement and skipped-day refill unchanged')
 for name in ['Whiterun','Solitude','Morthal','Riverwood']:
  e,s=env(name);e.tick(s)
  e.fail_enable=True;due(e,s);assert not e.enabled(s) and s.vm.vars['diagreason']==44 and s.vm.vars['diagarrivalenabledat']==0
  e.fail_enable=False;due(e,s);assert len(e.enabled(s))==1
  # An unexpectedly enabled selected actor forces the existing full recovery.
  s.vm.vars['dailypopulation']=s.maximum
  slot=1;actor=s.vm.call('PoolActor',s.vm.call('PoolIndex',slot,199));actor.disabled=False;s.vm.vars['selectedvariant'][slot]=199
  s.vm.call('TryArrival',slot,40);assert s.vm.vars['repairrequested'],(name,s.vm.vars['diagreason']);e.tick(s);assert actor in e.residents(s);e.check(s)
  # Request3 is still a full census; it has not become the cheap load path.
  s.diagnostics[0].value=3;e.native_calls.clear();e.tick(s);assert e.native_calls['isdisabled']>=s.maximum*200
  # Native-disabled stale residents expire through untouched Tick handling.
  for a in e.enabled(s):a.disabled=True
  e.tick(s);assert not e.enabled(s)
 out('Four script classes: failed Enable not counted, unexpected selected actor adopted, explicit full recovery retained')
 # A due periodic audit waits for pending arrivals, then still runs.
 e,s=env();e.tick(s);s.vm.vars['nextpoolauditat']=0;e.native_calls.clear();due(e,s);assert e.native_calls['isdisabled']<60
 fill(e,s);e.native_calls.clear();e.tick(s);assert e.native_calls['isdisabled']>=1200
 out('Periodic whole-pool audit deferred during arrival sequence, executed after target fills')


def state_upgrades():
 # Original typed upgrade harness, extended through v1.2.5. Model states are
 # combined with final records; no actual ESS/Papyrus runtime is executed.
 source=(W/'release_v125/test_release.py').read_text();node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='faithful_v110_upgrade')
 code=ast.get_source_segment(source,node).replace("version='1.2.5'","version='1.2.6'")
 exec(compile(code,'faithful-v110-upgrade','exec'),globals());faithful_v110_upgrade()
 cases=[]
 for version in ['1.2.1','1.2.5']:
  e=m.Env(72,version=version);e.set_time(40,10)
  for s in e.cities.values():
   e.place_player(s.inn);assert s.vm.call('EnsureSetup')
   s.vm.vars['todaycycle']=40;s.vm.vars['dailypopulation']=s.maximum;s.vm.call('TryArrival',0,40)
   assert len(e.enabled(s))==1,(version,s.name,'initial test fixture population')
  e.records=recs;e.rootpath=RT
  for s in e.cities.values():
   actors=e.enabled(s)[:];oldvars=s.vm.vars.copy();arrays={k:v for k,v in oldvars.items() if isinstance(v,list)}
   stem='MB_Controller' if s.whiterun else 'MB_VillageController' if s.village else 'MB_TownController' if s.town else 'MB_CityController'
   pex=Pex(RT/'Scripts'/f'{stem}.pex');vm=m.VM(pex,e.native);vm.vars.update(oldvars);s.vm=vm;s.pex=pex;e.owners[vm]=s;e.forms[s.root]=vm;e.running[vm]=True;s.alias.property('Controller',vm)
   e.place_player(s.cells[0],s.roads[0].xyz);s.alias.call('OnPlayerLoadGame');e.tick(s)
   assert all(vm.vars[k] is a for k,a in arrays.items());assert all(a in e.residents(s) for a in actors)
   s.vm.vars['dailypopulation']=s.maximum;s.vm.vars['selectedvariant'][1]=199;s.vm.call('TryArrival',1,40)
   assert len(e.enabled(s))==2 and variant(e,s,e.residents(s)[1])==199,(version,s.name,len(e.enabled(s)),s.vm.vars['diagreason']);e.check(s);cases.append([version,s.name])
 out('38 additional typed existing-state upgrades fromv121/v125, arrays/actors preserved and appended199 enabled',cases)


def preservation():
 for n,h in json.loads((ROOT/'protected-baselines.json').read_text()).items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h,n
 out('Stable v110, final v125 sources/runtime/archive and all protected baseline files untouched')

if __name__=='__main__':
 structure();ordinary_all19();load_and_scan_costs();hops_and_existing_residents();exceptional_recovery_and_lifecycle();state_upgrades();preservation()
 (R/'validation.json').write_text(json.dumps({'status':'PASS','checks':results,'Skyrim_executed':False,'ESS_files_tested':False,'limitations':'Real compiled PEX/ESP bindings in an interpreter. Native completion times are explicitly injected, not measured; rendering, AI, pathfinding and actual callback delivery require Skyrim. Fresh/partial state still needs a full audit.'},indent=2)+'\n')
 print('PASS: v126 final checks. No in-game benchmark or runtime success claimed.',flush=True)
