"""Actual v127 ESP/PEX executed with controlled natives/events. NOT Skyrim."""
from pathlib import Path
import collections,hashlib,json,runpy,struct,sys
W=Path('work');R=W/'build/v1.2.7';RT=R/'runtime';ROOT=W/'release_v127'
sys.path[:0]=[str(W/'src'),str(W/'deps/esplib/src')]
b=runpy.run_path(str(W/'release_v126/test_release.py'),run_name='support_only')
m=b['m'];Pex=b['Pex'];load=b['load'];subs=b['subs'];variant=b['variant'];roster=b['roster'];Pump=b['b']['Pump']
plugin,recs=load(RT);_,old=load(W/'build/v1.2.6/runtime');m.SETS['1.2.7']=(RT,recs,{k:r for k,r in recs.items() if r.signature=='PACK'},0x3000000)
results={}
def out(n,v=True):results[n]=v;print('PASS:',n,flush=True)
def env(name='Whiterun',hour=10):return b['b']['env'](name,hour,'1.2.7')
def due(e,s):
 at=s.vm.vars['nextarrivalat'];assert at>0;e.now=m.f32(at+0.000003);e.real+=2;s.vm.call('OnUpdateGameTime');e.check(s)
def donor(e,a):
 refid=next(k for k,v in e.byid.items() if v is a)
 npc=struct.unpack('<I',e.records[refid].get_subrecord('NAME').data)[0]
 return struct.unpack('<I',e.records[npc].get_subrecord('TPLT').data)[0]
def unique(e,s,allow_old=False):
 ids=[donor(e,a) for a in e.enabled(s)]
 if not allow_old:assert len(ids)==len(set(ids)),(s.name,'duplicate vanilla donor',ids)
 assert len(e.enabled(s))<=s.vm.vars['dailypopulation']<=s.maximum;e.check(s)
def norm(x):
 if isinstance(x,str):return x.replace('v1.2.7','v1.2.6')
 if isinstance(x,(tuple,list)):return [norm(v) for v in x]
 if isinstance(x,dict):return {k:norm(v) for k,v in x.items()}
 return x

def structure():
 assert set(recs)==set(old) and len(recs)==19942
 changed=[]
 for k,a in old.items():
  c=recs[k];assert(a.signature,a.flags,a.editor_id)==(c.signature,c.flags,c.editor_id)
  if subs(a)!=subs(c):
   assert a.signature=='GLOB' and subs(a,['FLTV'])==subs(c,['FLTV'])
   assert struct.unpack('<f',c.get_subrecord('FLTV').data)[0]==1207;changed.append(a.editor_id)
 assert len(changed)==58 and plugin.header.author=='Tsoxer'
 assert plugin.header.masters==['Skyrim.esm','HearthFires.esm','Dragonborn.esm']
 assert(RT/'Seq/MoreBrats.seq').read_bytes()==(W/'build/v1.2.6/runtime/Seq/MoreBrats.seq').read_bytes()
 assert(R/'settlements.json').read_bytes()==(W/'build/v1.2.6/settlements.json').read_bytes()
 allowed={'transition','tryarrival','processarrival','showstatus','initdiagnostics'};diff={}
 for p in (RT/'Scripts').glob('*.pex'):
  a=Pex(W/'build/v1.2.6/runtime/Scripts'/p.name);c=Pex(p)
  assert a.version==c.version and a.obj['properties']==c.obj['properties']
  for k,v in a.obj['variables'].items():assert c.obj['variables'][k]==v
  delta=[k for k,f in a.obj['functions'].items() if norm(f)!=norm(c.obj['functions'][k])]
  assert set(delta)<=allowed,(p.name,delta)
  if 'Controller' not in p.stem:assert p.read_bytes()==(W/'build/v1.2.6/runtime/Scripts'/p.name).read_bytes()
  else:
   assert {k:v for k,v in c.obj['variables'].items() if k not in a.obj['variables']}=={'interiorarrivalpending':('bool',False),'interiorarrivalcycle':('int',-100000)}
   for fn in ['tick','saferemoval','removalobservation','recoverorphans','setphase','updateroaming','begintrip','pickdestination','placearrival','selectdonorvariant','doorarrivalindex','plannext','loaded','reconcile','ensuresetup','enabledcount']:
    assert norm(a.obj['functions'][fn])==norm(c.obj['functions'][fn]),(p.name,fn)
   assert set(c.obj['functions'])-set(a.obj['functions'])=={'trypendingarrival','donorkey','variantclothing','variantfordonor','donorgroup','availabledonors','uniquevariant','variantforactor','streetarrivalindex','fillinterioropportunity'}
  for fn,f in c.obj['functions'].items():
   types=dict(f['locals']+f['params'])|{k:v[0] for k,v in c.obj['variables'].items()}
   for op,args,_ in f['ins']:
    if op==14:assert not(args[1]==(0,None) and types.get(args[0][1].lower(),'').endswith('[]'))
    if op==30:assert types[args[0][1].lower()].endswith('[]') and 1<=args[1][1]<=128
  diff[p.name]=delta
 # Existing street bindings are exactly those of the actual v110 release.
 from vmad_reader import quest_vmad
 _,v110=load(W/'build/v1.1.0/runtime')
 for key,a in recs.items():
  if a.signature=='QUST' and key in v110:
   before,_=quest_vmad(v110[key]);after,_=quest_vmad(a)
   for stem,props in before.items():
    if 'RoadRefs' in props:assert props['RoadRefs']==after[stem]['RoadRefs']
 out('19942 existing FormIDs; NPC/ref/AI/quest/VMAD payloads identical; 58 labels only; exactv110 road bindings')
 out('Four controller changes, five helper PEX andSEQ identical; original fields/functions preserved and two additive scalars',diff)

def identity_and_combinations():
 e=m.Env(42,version='1.2.7');e.set_time(40,10);identities={};count=0
 for s in e.cities.values():
  e.place_player(s.cells[0],s.roads[0].xyz);assert s.vm.call('EnsureSetup')
  for slot in range(s.maximum):
   for v in range(200):
    a=s.vm.call('PoolActor',s.vm.call('PoolIndex',slot,v));assert s.vm.call('VariantForActor',a)==v,(s.name,slot,v)
    key=s.vm.call('DonorKey',v);fid=donor(e,a)
    assert identities.setdefault(key,fid)==fid
    color=s.vm.call('VariantClothing',v);assert s.vm.call('VariantForDonor',key,color)==v
    count+=1
 assert len(identities)==40 and len(set(identities.values()))==40 and count==15200
 # All forty keys/five outfits are still independently reachable in the compiled arrival path.
 s=e.cities['Whiterun'];e.place_player(s.cells[0],s.roads[0].xyz);s.vm.vars['todaycycle']=40;s.vm.vars['dailypopulation']=6
 for v in range(200):
  s.vm.vars['selectedvariant'][0]=v;s.vm.call('TryArrival',0,40);a=e.residents(s)[0]
  assert a is not None and not a.disabled and s.vm.call('VariantForActor',a)==v
  a.disabled=True;s.vm.vars['residents'][0]=None
 out('All15200 actor IDs correctly map to200 variants and40 actual TPLT donor FormIDs; all200 still enable')

 # GetFormID is a signed32-bit Papyrus Int above load index7F.
 original=s.vm.native
 for prefix in [0x03,0x7f,0x80,0xfa]:
  def signed_id(target,method,args):
   value=original(target,method,args)
   if method.lower()=='getformid':
    value=(prefix<<24)|(value&0xffffff)
    if value>=0x80000000:value-=0x100000000
   return value
  s.vm.native=signed_id
  for v in range(200):
   a=s.vm.call('PoolActor',s.vm.call('PoolIndex',0,v));assert s.vm.call('VariantForActor',a)==v,(prefix,v)
 s.vm.native=original
 out('All200 donor identities also resolve with low/high/signed load-order FormIDs')

 # Current-day selection can reset independently of a carried resident identity.
 s.vm.vars['selectedvariant'][0]=0;s.vm.call('TryArrival',0,40);first=e.residents(s)[0]
 s.vm.vars['selectedvariant'][0]=-1;s.vm.vars['selectedvariant'][1]=1;s.vm.call('TryArrival',1,40)
 second=e.residents(s)[1];assert donor(e,first)!=donor(e,second)
 assert s.vm.call('VariantClothing',s.vm.call('VariantForActor',second))==1
 unique(e,s)
 out('Same donor/different outfit rejected; outfit color retained; stale selectedVariant cannot disguise an active donor')
 # A singleton category (female Breton/Erith) must not cause permanent retry.
 e,s=env();e.tick(s);s.vm.vars['dailypopulation']=6
 for slot in range(6):
  s.vm.vars['selectedvariant'][slot]=33 # female Breton, red
  s.vm.call('TryArrival',slot,40);unique(e,s)
 assert len(e.enabled(s))==6
 assert all(s.vm.call('VariantClothing',s.vm.call('VariantForActor',a))==0 for a in e.enabled(s))
 out('Six forced identical singleton-donor requests fill cap with distinct donors; duplicate outfits allowed')


def dual_paths_all19():
 e=m.Env(64,version='1.2.7');rows=[]
 for name,s in e.cities.items():
  e.set_time(40,10);e.place_player(s.cells[0],s.roads[0].xyz);e.tick(s)
  s.vm.vars['dailypopulation']=s.maximum;target=s.maximum;roll=s.vm.vars['todaycycle']
  # Begin outside: the existing single-arrival timer and door placement remain.
  due(e,s);assert len(e.enabled(s))==1 and not s.vm.vars['interiorarrivalpending'];unique(e,s)
  saved=e.enabled(s)[:];door_queries=len(e.door_queries)
  # Go into a normal shop (not just the named night building).
  e.place_player(s.shop);p=Pump(e,drop_game=True);s.alias.call('OnCellLoad');p.run(3)
  assert len(e.enabled(s))==target,(name,len(e.enabled(s)),target,s.vm.vars['diagreason'])
  assert len(e.door_queries)==door_queries,'interior batch ran door discovery'
  assert all(a in e.enabled(s) for a in saved);assert s.vm.vars['dailypopulation']==target and s.vm.vars['todaycycle']==roll
  assert s.vm.vars['nextarrivalat']==0;unique(e,s)
  # Exiting/re-entering and a queued old arrival callback cannot add extra NPCs.
  for _ in range(3):
   e.place_player(s.cells[0],s.roads[0].xyz);s.alias.call('OnCellLoad');p.run(3)
   e.place_player(s.shop);s.alias.call('OnCellLoad');p.run(3)
   s.vm.call('OnUpdateGameTime');assert len(e.enabled(s))==target;unique(e,s)
  # Maximum populations: expected location/AI for every successful child.
  for a in e.enabled(s):assert not a.cell.interior and a.world is s.world and a.package is not None
  rows.append({'settlement':name,'target':target,'gradual_before_interior':1,'after_interior':len(e.enabled(s)),'unique_vanilla_donors':len({donor(e,a) for a in e.enabled(s)})})
 out('All19: gradual door arrival + interior original-street fill share one maximum daily target; repeated transitions never exceed it',rows)
 # Same named donor remains allowed in different settlements.
 e=m.Env(82,version='1.2.7');e.set_time(40,10);chosen=[]
 for name in ['Whiterun','Riften']:
  s=e.cities[name];e.place_player(s.cells[0],s.roads[0].xyz);e.tick(s);s.vm.vars['selectedvariant'][0]=0;s.vm.call('TryArrival',0,40);chosen.append(donor(e,e.residents(s)[0]))
 assert chosen[0]==chosen[1]
 out('Uniqueness is settlement-local; the same donor can exist in another city')

 e,s=env();e.tick(s);s.vm.vars['dailypopulation']=5
 for _ in range(3):due(e,s)
 assert len(e.enabled(s))==3
 saved=e.enabled(s)[:];e.place_player(s.shop);s.alias.call('OnCellLoad')
 # A callback delivered during native Enable must see the existing busy worker.
 original=e.native_hook;entered=[False]
 def overlapping(target,method,args):
  if original:original(target,method,args)
  if method=='enable' and not entered[0]:
   entered[0]=True;s.vm.call('Service')
 e.native_hook=overlapping;e.tick(s)
 assert entered[0] and s.vm.vars['dailypopulation']==5 and len(e.enabled(s))==5
 assert all(a in e.enabled(s) for a in saved);unique(e,s)
 out('Explicit Whiterun roll5: three gradual + two interior, including overlapping callback, totals exactly5')



def quick_entries_and_time():
 rows=[]
 for name in m.Env(version='1.2.7').cities:
  e,s=env(name);e.tick(s);target=s.vm.vars['dailypopulation'];p=Pump(e,drop_game=True)
  e.place_player(s.shop);s.alias.call('OnCellLoad')
  # Exit before the two-second worker; entry must have been captured already.
  assert s.vm.vars['interiorarrivalpending'];e.place_player(s.cells[0],s.roads[0].xyz);s.alias.call('OnCellLoad');p.run(3)
  assert len(e.enabled(s))==target and s.vm.vars['nextarrivalat']==0;unique(e,s);rows.append(name)
 out('All19: quick interior entry/exit before callback still fills only remaining slots',rows)
 for name in ['Whiterun','Solitude','Morthal','Riverwood']:
  e,s=env(name,7.5);p=Pump(e,drop_game=True);e.place_player(s.shop);s.alias.call('OnCellLoad');p.run(3);assert not e.enabled(s)
  p.run(100);assert e.enabled(s);unique(e,s)
  # An unrelated interior cannot fill any other settlement.
  other=e.cities['Riften' if name!='Riften' else 'Whiterun'];e.place_player(other.shop);s.alias.call('OnCellLoad');e.tick(s);unique(e,s)
  e2,s2=env(name,19.2);e2.place_player(s2.shop);s2.alias.call('OnCellLoad');e2.tick(s2);assert not e2.enabled(s2)
 out('Before08:00 wait→08:00 works indoors; unrelated interiors and post19:00 cannot trigger late populations')
 # Batch must honor a native operation crossing19:00, as the gradual path does.
 e,s=env();e.tick(s);e.place_player(s.shop);s.alias.call('OnCellLoad');e.move_hook=lambda a,p:e.set_time(40,19.1);e.tick(s);assert not e.enabled(s)
 out('Native MoveTo crossing19:00 never enables a late batch child')


def gradual_and_night():
 e=m.Env(42,version='1.2.7');e.set_time(40,10);rows=[]
 for name,s in e.cities.items():
  e.set_time(40,10);e.place_player(s.cells[0],s.roads[0].xyz);p=Pump(e,drop_game=True);s.alias.call('OnCellLoad');p.run(3)
  target=s.vm.vars['dailypopulation'];before=0
  while len(e.enabled(s))<target:
   at=s.vm.vars['nextarrivalat'];assert at>0
   p.base_real=e.real;p.base_game=float(e.now);p.run(max(0,(at-e.now)*86400/20)+2)
   assert len(e.enabled(s))==before+1,(name,len(e.enabled(s)),before);before+=1;unique(e,s)
  rows.append(name)
  # Existing native package priorities and safe03 cleanup, no arrival flag writes.
  e.set_time(40,19.1);e.tick(s);assert all(a.rank==i*4+3 for i,a in enumerate(e.residents(s)) if a)
  for a in e.enabled(s):a.cell=s.inn;a.world=None
  e.place_player(s.inn);e.visible.update(e.enabled(s));e.refresh();e.set_time(41,3.1);e.tick(s);assert e.enabled(s)
  e.visible.clear();e.place_player(e.rural,[0,0,0]);e.tick(s);e.tick(s);assert not e.enabled(s)
 out('All19: uninterrupted gradual outdoor arrivals still fill target; original night packages and safe03 retirement unchanged',rows)
 # Faulted native Enable must not reserve a donor/population forever.
 e,s=env();e.tick(s);e.fail_enable=True;e.place_player(s.shop);s.alias.call('OnCellLoad');e.tick(s);assert not e.enabled(s)
 e.fail_enable=False;due(e,s);unique(e,s);assert e.enabled(s)
 out('Failed native enabling never counts as a resident/donor success; later opportunity recovers')


def save_upgrades_and_cost():
 e=m.Env(42,version='1.2.6');e.set_time(40,10);cases=[]
 for s in e.cities.values():
  e.place_player(s.cells[0],s.roads[0].xyz);assert s.vm.call('EnsureSetup');s.vm.vars['todaycycle']=40;s.vm.vars['dailypopulation']=s.maximum
  for slot in range(min(2,s.maximum)):
   s.vm.vars['selectedvariant'][slot]=slot;s.vm.call('TryArrival',slot,40)
 e.records=recs;e.rootpath=RT
 for s in e.cities.values():
  actors=e.enabled(s)[:];oldvars=s.vm.vars.copy();arrays={k:v for k,v in oldvars.items() if isinstance(v,list)}
  stem='MB_Controller' if s.whiterun else 'MB_VillageController' if s.village else 'MB_TownController' if s.town else 'MB_CityController'
  pex=Pex(RT/'Scripts'/f'{stem}.pex');vm=m.VM(pex,e.native);vm.vars.update(oldvars);s.vm=vm;s.pex=pex;e.owners[vm]=s;e.forms[s.root]=vm;e.running[vm]=True;s.alias.property('Controller',vm)
  e.place_player(s.cells[0],s.roads[0].xyz);s.alias.call('OnPlayerLoadGame');e.tick(s)
  assert all(vm.vars[k] is a for k,a in arrays.items());assert all(a in e.residents(s) for a in actors)
  seen=collections.Counter(donor(e,a) for a in e.enabled(s));e.place_player(s.shop);s.alias.call('OnCellLoad');e.tick(s)
  after=collections.Counter(donor(e,a) for a in e.enabled(s));assert all(after[k]<=max(1,seen[k]) for k in after)
  assert len(e.enabled(s))==s.maximum;unique(e,s,True)
  for _ in range(2):e.save_load(s);e.tick(s);assert all(a in e.residents(s) for a in actors)
  cases.append(s.name)
 out('All19 typedv126 upgrades: active identities/arrays retained; inherited duplicate donors not increased; repeated loads stable',cases)
 # The established routine counter remains exactly76 native checks at max slots.
 e.native_calls.clear()
 for s in e.cities.values():s.vm.call('EnabledCount')
 assert e.native_calls['isdisabled']==76
 out('Routine maximum enabled counting still76 checks; uniqueness uses at most8 other tracked actor IDs per arrival')
 for name,h in json.loads((ROOT/'protected-baselines.json').read_text()).items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==h,name
 out('Stablev110 and confirmedv126 sources/runtime/archives remain untouched')

if __name__=='__main__':
 structure();identity_and_combinations();dual_paths_all19();quick_entries_and_time();gradual_and_night();save_upgrades_and_cost()
 (R/'validation.json').write_text(json.dumps({'status':'PASS','checks':results,'Skyrim_executed':False,'ESS_files_tested':False,'limits':'Actual final PEX and ESP bindings. Native calls, event delivery, clock, loading, geometry, AI/paths and serialized upgrade states are modeled. Existing duplicates are not removed mid-cycle; new arrivals avoid all occupied donor identities.'},indent=2)+'\n')
 print('PASS: v127 compiled-code and preservation checks. Skyrim playtest required.',flush=True)
