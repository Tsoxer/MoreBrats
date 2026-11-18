"""Actual v1.2.3 ESP/PEX with fault-aware VM and cancellable synthetic clocks.
Native callback loss/metadata transients are injected faults, not Skyrim proof.
"""
from pathlib import Path
import ast,hashlib,json,runpy,struct,sys
ROOT=Path(__file__).resolve().parent;W=ROOT.parent;R=W/'build/v1.2.3';RT=R/'runtime'
base=runpy.run_path(str(W/'release_v122/test_release.py'),run_name='support_only')
m=base['m'];load=base['load'];subs=base['subs'];variant=base['variant'];Pex=base['Pex'];roster=base['roster']
plugin,recs=load(RT);_,old=load(W/'build/v1.2.2/runtime')
m.SETS['1.2.3']=(RT,recs,{k:r for k,r in recs.items() if r.signature=='PACK'},0x3000000)
results={};metrics={}
def out(name,value=True):results[name]=value;print('PASS:',name,flush=True)
def env(name='Whiterun',hour=9.5333,version='1.2.3'):
    e=m.Env(42,version=version);s=e.cities[name]
    e.set_time(40,hour);pos=s.roads[0].xyz[:];pos[1]-=2000.;e.place_player(s.cells[0],pos)
    e.forms[0x3a]=m.Global(20.0)
    return e,s
def due(e,s):
    assert s.vm.vars['nextarrivalat']>0
    e.now=m.f32(s.vm.vars['nextarrivalat']+0.000003);e.real+=2
    s.vm.call('OnUpdateGameTime');e.check(s)
def fill(e,s):
    for _ in range(s.maximum+2):
        if len(e.enabled(s))==s.vm.vars['dailypopulation']:return
        due(e,s)
    raise AssertionError((s.name,'population did not complete',s.vm.vars['diagreason']))
def normalize(x):
    if isinstance(x,str):return x.replace('v1.2.3','v1.2.2')
    if isinstance(x,(list,tuple)):return [normalize(y) for y in x]
    if isinstance(x,dict):return {k:normalize(v) for k,v in x.items()}
    return x

class Pump:
    """Native registrations become absolute deadlines. Unregister cancels them.
    Already queued simultaneous events can still run. No implicit cell events.
    """
    def __init__(self,e,drop_game=False):
        self.e=e;self.real={};self.game={};self.drop_game=drop_game;self.base_real=e.real;self.base_game=float(e.now);self.fired=[]
        self.scale=e.forms[0x3a].value;e.native_hook=self.hook
    def hook(self,target,method,args):
        if not isinstance(target,m.VM):return
        if method=='registerforsingleupdate':self.real[target]=self.e.real+args[0]
        elif method=='registerforsingleupdategametime':self.game[target]=float(self.e.now)+args[0]/24.
        elif method=='unregisterforupdate':self.real.pop(target,None)
        elif method=='unregisterforupdategametime':self.game.pop(target,None)
    def clock(self,real):
        self.e.real=real;self.e.now=m.f32(self.base_game+(real-self.base_real)*self.scale/86400.)
    def set_scale(self,value):
        self.base_real=self.e.real;self.base_game=float(self.e.now);self.scale=value;self.e.forms[0x3a].value=value
    def skip_game_hours(self,hours):
        self.base_game=float(self.e.now)+hours/24.;self.base_real=self.e.real;self.clock(self.e.real)
    def run(self,seconds):
        end=self.e.real+seconds;events=0
        while True:
            candidates=[(at,'OnUpdate',target) for target,at in self.real.items()]
            if self.scale>0:
                candidates += [(self.base_real+(at-self.base_game)*86400./self.scale,'OnUpdateGameTime',target) for target,at in self.game.items()]
            if not candidates:break
            at=min(c[0] for c in candidates)
            if at>end:break
            self.clock(max(at,self.e.real));queued=[c for c in candidates if abs(c[0]-at)<0.0001]
            for _,kind,target in queued:(self.real if kind=='OnUpdate' else self.game).pop(target,None)
            for _,kind,target in queued:
                events+=1;assert events<5000,'timer loop'
                if kind=='OnUpdateGameTime' and self.drop_game:continue
                self.fired.append([self.e.real,kind,self.e.owners[target].name]);target.call(kind)
                self.e.check(self.e.owners[target])
        self.clock(end)

def structure():
    assert set(recs)==set(old) and len(recs)==19941
    assert plugin.header.author=='Tsoxer' and plugin.header.masters==['Skyrim.esm','HearthFires.esm','Dragonborn.esm']
    changed=[]
    for key,a in old.items():
        b=recs[key];assert(a.signature,a.flags,a.editor_id)==(b.signature,b.flags,b.editor_id)
        if subs(a)!=subs(b):
            assert a.signature=='GLOB' and subs(a,['FLTV'])==subs(b,['FLTV'])
            assert struct.unpack('<f',b.get_subrecord('FLTV').data)[0]==1203
            changed.append(a.editor_id)
    assert len(changed)==58
    assert(RT/'Seq/MoreBrats.seq').read_bytes()==(W/'build/v1.2.2/runtime/Seq/MoreBrats.seq').read_bytes()
    assert(R/'settlements.json').read_bytes()==(W/'build/v1.2.2/settlements.json').read_bytes()
    allowed={'onupdate','onupdategametime','transition','processarrival','plandormant','arrivalrelevant','recoverypulse','plannext','begintrip','showstatus','initdiagnostics'}
    diffs={};newvars={}
    for path in (RT/'Scripts').glob('*.pex'):
        a=Pex(W/'build/v1.2.2/runtime/Scripts'/path.name);b=Pex(path)
        assert a.version==b.version and a.obj['properties']==b.obj['properties']
        for k,v in a.obj['variables'].items():assert b.obj['variables'][k]==v,(path.name,k)
        newvars[path.name]={k:v[0] for k,v in b.obj['variables'].items() if k not in a.obj['variables']}
        diff=[k for k,v in a.obj['functions'].items() if normalize(v)!=normalize(b.obj['functions'][k])]
        assert set(diff)<=allowed,(path.name,diff)
        diffs[path.name]=diff
        if 'Controller' not in path.stem:assert path.read_bytes()==(W/'build/v1.2.2/runtime/Scripts'/path.name).read_bytes()
        else:
            import re
            trip=re.compile(r'^Function BeginTrip\([^\n]*\)\n.*?^EndFunction',re.M|re.S)
            ta=trip.search((W/'v1.2.2/src'/f'{path.stem}.psc').read_text()).group()
            tb=trip.search((W/'v1.2.3/src'/f'{path.stem}.psc').read_text()).group()
            assert ta.replace('Utility.RandomInt(0, 99) < 25','Utility.RandomInt(0, 9999) < 3325').replace('Utility.RandomFloat(2.0, 6.0)','Utility.RandomFloat(2.66, 7.98)')==tb
        for fn,f in b.obj['functions'].items():
            types=dict(f['locals']+f['params'])|{k:v[0] for k,v in b.obj['variables'].items()}
            for op,args,_ in f['ins']:
                if op==14:assert not(args[1]==(0,None) and types.get(args[0][1].lower(),'').endswith('[]'))
                if op==30:assert types[args[0][1].lower()].endswith('[]') and 1<=args[1][1]<=128
    out('19941 stable records, only58 display globals; five helper PEX and SEQ identical',changed)
    out('Old serialized fields/properties and every unrelated PEX function preserved',{'changed_functions':diffs,'new_scalar_fields':newvars})

def outdoor_clocks():
    fault=[]
    for name in ['Solitude','Whiterun','DragonBridge']:
        e,s=env(name,version='1.2.2');p=Pump(e,drop_game=True);e.tick(s)
        s.diagnostics[0].value=2;p.run(180.) #60 in-game minutes at20
        assert not e.enabled(s) and not any(k=='messagebox' for k,*_ in e.logs)
        assert s.diagnostics[0].value==2
        fault.append(name)
    out('Old compiled PEX stalls outdoors when its only game-time callback is lost; local debug remains pending',fault)
    cases=[]
    for name in m.Env(version='1.2.3').cities:
        e,s=env(name);p=Pump(e,drop_game=True)
        s.alias.call('OnCellLoad');assert not e.enabled(s)
        p.run(3);assert s.vm.vars['nextarrivalat']>0
        s.diagnostics[0].value=2;p.run(180)
        assert e.enabled(s) and any(k=='messagebox' for k,*_ in e.logs),(name,s.vm.vars['diagreason'])
        assert s.diagnostics[0].value==0
        while len(e.enabled(s))<s.vm.vars['dailypopulation']:
            p.run(95)
        times=[row[2] for row in e.logs if row[0]=='enable']
        assert len(times)==s.vm.vars['dailypopulation']
        assert all(14.8<=(b-a)*1440<=31.0 for a,b in zip(times,times[1:])),(name,times)
        assert s.vm.vars['diaggameupdates']==0 and s.vm.vars['diagrealupdates']>0
        # Completed populations must not keep an arrival fallback timer alive.
        assert s.vm not in p.real
        cases.append({'settlement':name,'population':len(times),'real_callbacks':s.vm.vars['diagrealupdates'],'game_callbacks':0})
    out('All19 outdoor populations complete using actual deadline timers despite dropped GT events; no cell changes',cases)
    mornings=[]
    for name in m.Env(version='1.2.3').cities:
        e,s=env(name,hour=7.5);p=Pump(e,drop_game=True);e.tick(s)
        p.run(90);assert not e.enabled(s) #07:30->08:00 at timescale20
        p.run(100);assert e.enabled(s),(name,e.now,s.vm.vars['diagreason'],s.vm.vars['nextarrivalat'],p.real.get(s.vm))
        mornings.append(name)
    out('All19 fresh08:00 cycles start outdoors without a GT callback or a door transition',mornings)
    e,s=env('Solitude');p=Pump(e);s.alias.call('OnCellLoad');p.run(3)
    p.run(180);assert e.enabled(s)
    times=[row[2] for row in e.logs if row[0]=='enable'];assert len(times)==len(set(times))
    out('Simultaneous game-time and real-time callbacks do not duplicate an arrival')
    # An early fallback after a timescale change must not bypass the game clock.
    e,s=env();p=Pump(e,drop_game=True);e.tick(s);due_at=s.vm.vars['nextarrivalat']
    p.set_scale(10);p.run(50);assert not e.enabled(s) and e.now<due_at
    p.run(150);assert e.enabled(s)
    out('Timescale decrease: early RT callback rearms without early spawning')
    # Too-close roads defer individual attempts, without distance checks on a loop.
    e,s=env();p=Pump(e,drop_game=True);e.tick(s);saved=[a.xyz[:] for a in s.roads]
    for a in s.roads:a.xyz=e.player.xyz[:]
    p.run(100);assert not e.enabled(s) and s.vm.vars['diagreason']==40
    e.native_calls.clear();p.run(5);assert not e.native_calls['getdistance']
    for a,xyz in zip(s.roads,saved):a.xyz=xyz
    p.run(100);assert e.enabled(s)
    out('Unsafe markers defer; moving away allows a later due attempt, without distance polling')

def transition_and_debug():
    cases=[]
    for version in ['1.2.2','1.2.3']:
        for name in ['Whiterun','Solitude']:
            e,s=env(name,version=version);e.world_drop_ids.add('Player')
            relevant=s.vm.call('ArrivalRelevant')
            assert relevant==(version=='1.2.3')
            cases.append([version,name,relevant])
    out('Walled arrival relevance uses a valid location even when the player world query returns None',cases)
    # Old direct transition samples unavailable entry metadata and sleeps until
    # next morning. New transition defers that read, preserving any armed GT.
    transient=[]
    for version in ['1.2.2','1.2.3']:
        for name in ['Solitude','DragonBridge']:
            e,s=env(name,version=version);p=Pump(e)
            native=s.vm.native;missing=[True]
            def read(target,method,args):
                if missing[0] and target is e.player and method.lower() in ['getworldspace','getcurrentlocation']:return None
                return native(target,method,args)
            s.vm.native=read;s.alias.call('OnCellLoad');missing[0]=False
            p.run(185)
            assert bool(e.enabled(s))==(version=='1.2.3')
            transient.append([version,name,len(e.enabled(s))])
    out('Deferred transition handles transient entry metadata without needing a second/interior event',transient)
    # Suspend, do not erase, an existing deadline during a temporary false result.
    for name in ['Whiterun','Solitude','DragonBridge']:
        e,s=env(name);p=Pump(e);e.tick(s);at=s.vm.vars['nextarrivalat']
        e.place_player(e.rural,[0,0,0]);e.tick(s);assert s.vm.vars['nextarrivalat']==at
        pos=s.roads[0].xyz[:];pos[1]-=2000.;e.place_player(s.cells[0],pos);s.alias.call('OnCellLoad');p.run(185)
        assert e.enabled(s)
    out('Pending due time survives irrelevance and resumes without a timer reset')
    e,s=env('Solitude',hour=9);p=Pump(e)
    for peer in e.cities.values():peer.alias.call('OnCellLoad')
    p.run(100);assert e.enabled(s)
    visits=['DragonBridge','Whiterun','Solitude']
    for name in visits:
        s=e.cities[name];pos=s.roads[0].xyz[:];pos[1]-=2000.;e.place_player(s.cells[0],pos)
        p.skip_game_hours(1)
        for peer in e.cities.values():peer.alias.call('OnCellLoad')
        p.run(100);assert e.enabled(s);e.check(s)
    e.place_player(s.inn);s.alias.call('OnCellLoad');p.run(3)
    before=len(e.enabled(s));p.skip_game_hours(2);p.run(0)
    assert len(e.enabled(s))<=before+1
    pos=s.roads[0].xyz[:];pos[1]-=2000.;e.place_player(s.cells[0],pos);s.alias.call('OnCellLoad');p.run(3)
    e.check(s)
    out('Consecutive fast travel, repeat visit, interior wait and exit preserve one arrival sequence',visits)
    # MB_Debug is Whiterun's endpoint, not the current settlement endpoint.
    # Use the unchanged watchdog's existing RecoveryPulse callback outdoors.
    e,s=env('Solitude');w=e.cities['Whiterun'];p=Pump(e)
    assert w.vm.call('EnsureSetup');w.diagnostics[0].value=2
    recovery=m.VM(Pex(RT/'Scripts/MB_Recovery.pex'),e.native)
    recovery.property('Controller',w.vm);recovery.vars['loadedpending']=False
    e.owners[recovery]=w;recovery.call('OnUpdate');p.run(3)
    boxes=[row[1] for row in e.logs if row[0]=='messagebox']
    assert len(boxes)==1 and 'Whiterun' in boxes[0] and 'MB_Debug reports Whiterun' in boxes[0]
    assert '/1200' in boxes[0] and 'relevant=False' in boxes[0]
    out('MB_Debug works outdoors through existing watchdog, explicitly identifies Whiterun')

def running():
    cases=[]
    for name in ['Whiterun','Solitude','Morthal','DragonBridge']:
        e,s=env(name);assert s.vm.call('EnsureSetup')
        s.vm.vars['dailypopulation']=s.maximum;s.vm.vars['todaycycle']=40;s.vm.call('TryArrival',0,40)
        native=s.vm.native
        for draw,wants_run in [(0,True),(3324,True),(3325,False),(9999,False)]:
            def controlled(target,method,args):
                if isinstance(target,str) and target.lower()=='utility' and method.lower()=='randomint' and tuple(args)==(0,9999):return draw
                if isinstance(target,str) and target.lower()=='utility' and method.lower()=='randomfloat' and tuple(round(x,2) for x in args)==(2.66,7.98):return args[0]
                return native(target,method,args)
            s.vm.native=controlled;s.vm.call('BeginTrip',0,e.now)
            assert s.vm.vars['phase'][0]==(2 if wants_run else 1)
            if wants_run:assert abs((s.vm.vars['rununtil'][0]-e.now)*1440-2.66)<0.02
        f=s.pex.obj['functions']['begintrip'];draws=[];bounds=[]
        for op,a,va in f['ins']:
            if op==25 and a[0][1].lower()=='utility':
                if a[1][1].lower()=='randomint':draws.append(tuple(x[1] for x in va))
                if a[1][1].lower()=='randomfloat':bounds.append(tuple(x[1] for x in va))
        assert (0,9999) in draws and any(abs(b[0]-2.66)<0.001 and abs(b[1]-7.98)<0.001 for b in bounds)
        s.vm.native=native;cases.append(name)
    out('Separate running change: 33.25% chance; 2.66–7.98 game-minute cap; exact PEX branch boundaries',cases)

def cold_upgrades():
    e=m.Env(12,version='1.2.2');e.set_time(40,11);e.place_player(e.rural,[0,0,0]);e.tick_all();cases=[]
    e.forms[0x3a]=m.Global(20.)
    for s in e.cities.values():
        assert s.vm.vars['residents'] is None
        oldvars=s.vm.vars.copy();stem='MB_Controller' if s.whiterun else 'MB_VillageController' if s.village else 'MB_TownController' if s.town else 'MB_CityController'
        pex=Pex(RT/'Scripts'/f'{stem}.pex');vm=m.VM(pex,e.native);vm.vars.update(oldvars)
        s.vm=vm;s.pex=pex;e.owners[vm]=s;e.forms[s.root]=vm;e.running[vm]=True;s.alias.property('Controller',vm)
        pos=s.roads[0].xyz[:];pos[1]-=2000.;e.place_player(s.cells[0],pos);e.set_time(40,11)
        p=Pump(e,drop_game=True);s.alias.call('OnPlayerLoadGame');p.run(100)
        assert e.enabled(s) and vm.vars['diagstorageready'] and not vm.array_errors
        cases.append(s.name)
    out('Nineteen cold v1.2.2 saved controllers initialize new scheduling outdoors without resets',cases)

# Reuse the existing exhaustive mapping, upgrade, departure and workload checks
# directly; change only their candidate paths and add the v1.2.2 upgrade source.
def load_existing_tests():
    source=(W/'release_v122/test_release.py').read_text();tree=ast.parse(source)
    for name in ['mapping_and_upgrades','lifecycle_and_faults','workload']:
        node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
        text=ast.get_source_segment(source,node).replace("version='1.2.2'","version='1.2.3'")
        if name=='mapping_and_upgrades':
            text=text.replace("['1.1.0','1.2.0','1.2.1']","['1.1.0','1.2.0','1.2.1','1.2.2']").replace('171 typed','228 typed')
            # v1.2.2 intentionally leaves unvisited cities cold. Prepare each
            # old saved-state fixture using its real setup and arrival code,
            # rather than assuming its arrays/residents already exist.
            needle='            e.records=recs;e.rootpath=RT'
            assert needle in text
            text=text.replace(needle,'''            if version=='1.2.2':
                for previous in e.cities.values():
                    e.place_player(previous.inn);e.tick(previous)
                    for slot in range(previous.vm.vars['dailypopulation']):
                        previous.vm.call('TryArrival',slot,40)
                    e.check(previous)
'''+needle,1)
        if name=='workload':text=text.replace("['1.2.1','1.2.2']","['1.2.2','1.2.3']").replace("metrics['1.2.1']['EnabledCount']['native_calls']['isdisabled']==15200","metrics['1.2.2']['EnabledCount']['native_calls']['isdisabled']==76").replace("metrics['1.2.2']['EnabledCount']['native_calls']['isdisabled']==76","metrics['1.2.3']['EnabledCount']['native_calls']['isdisabled']==76")
        exec(compile(text,str(ROOT/'test_release.py')+':reused-'+name,'exec'),globals())
load_existing_tests()
if __name__=='__main__':
    structure();outdoor_clocks();transition_and_debug();running();mapping_and_upgrades();cold_upgrades();lifecycle_and_faults();workload()
    data={'status':'PASS','checks':results,'workload':metrics,'Skyrim_executed':False,'ESS_files_tested':False,'limits':'Real PEX instructions and ESP bindings; native events, cancellation, metadata loss and clocks are controlled synthetic faults. This does not prove that native callback loss caused the reported Skyrim failures.'}
    (R/'validation.json').write_text(json.dumps(data,indent=2)+'\n')
    print('PASS: focused v1.2.3 verification complete; Skyrim testing remains necessary.',flush=True)
