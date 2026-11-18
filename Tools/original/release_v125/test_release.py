"""Actual v124 ESP/PEX, controlled native failures and moving geometry; NOT Skyrim."""
from pathlib import Path
import ast,collections,hashlib,json,math,runpy,struct,sys
ROOT=Path(__file__).resolve().parent;W=ROOT.parent;R=W/'build/v1.2.5';RT=R/'runtime'
base=runpy.run_path(str(W/'release_v123/test_release.py'),run_name='support_only')
m=base['m'];load=base['load'];subs=base['subs'];variant=base['variant'];Pex=base['Pex'];roster=base['roster']
plugin,recs=load(RT);_,old=load(W/'build/v1.2.4/runtime')
m.SETS['1.2.4']=(W/'build/v1.2.4/runtime',old,{k:r for k,r in old.items() if r.signature=='PACK'},0x3000000)
m.SETS['1.2.5']=(RT,recs,{k:r for k,r in recs.items() if r.signature=='PACK'},0x3000000)
results={};metrics={}
def out(name,value=True):results[name]=value;print('PASS:',name,flush=True)

# Extend only native boundaries absent from the old fixture. The synchronous
# Enable mock can fail; bookkeeping alone must not qualify as an arrival.
oldinit=m.Env.__init__;oldnative=m.Env.native
def init(self,*args,**kwargs):
    oldinit(self,*args,**kwargs)
    self.fail_enable=False;self.no_doors=False;self.door_queries=[];self.doors=[]
    self.forms[0x3a]=m.Global(20.)
    flst=recs[0x32221e0]
    self.forms[0x32221e0]=m.FormList([struct.unpack('<I',x.data)[0] for x in flst.get_subrecords('LNAM')])
    for s in self.cities.values():
        for i,road in enumerate(s.roads):
            door=m.Ref(s.name+' SYNTHETIC ordinary door '+str(i),road.cell,road.world,[road.xyz[0]+128,road.xyz[1],road.xyz[2]])
            door.base=self.forms[0x32221e0].values[i%17];self.doors.append(door)
    self.door_rng=__import__('random').Random(765)
def native(self,target,method,args):
    name=method.lower()
    if isinstance(target,str) and target.lower()=='game' and name=='findrandomreferenceofanytypeinlistfromref':
        self.native_calls[name]+=1
        if self.native_hook:self.native_hook(target,name,args)
        catalog,point,radius=args;assert radius==512 and catalog is self.forms[0x32221e0]
        self.door_queries.append([self.real,point.name])
        candidates=[] if self.no_doors or self.player.cell.interior else [d for d in self.doors if d.base in catalog.values and d.world is point.world and math.dist(d.xyz,point.xyz)<=radius]
        return self.door_rng.choice(candidates) if candidates else None
    if isinstance(target,m.Ref) and name=='enable':
        self.native_calls[name]+=1
        if self.native_hook:self.native_hook(target,name,args)
        assert args==[False]
        s=self.owners[target];assert target.disabled,'duplicate actual enable'
        assert len(self.enabled(s))<s.vm.vars['dailypopulation']<=s.maximum
        points=[p for p in s.roads if p.cell is target.cell and p.xyz==target.xyz]
        assert len(points)==1 and not target.cell.interior and target.world is s.world
        if self.fail_enable:self.logs.append(('enable_failed',target.name,self.now));return
        target.disabled=False;self.logs.append(('enable',target.name,self.now));self.refresh();return
    return oldnative(self,target,method,args)
m.Env.__init__=init;m.Env.native=native

def env(name='Whiterun',hour=8.001,version='1.2.5',seed=42):
    e=m.Env(seed,version=version);s=e.cities[name];e.set_time(40,hour);e.place_player(s.cells[0],s.roads[0].xyz)
    return e,s

def due(e,s):
    assert s.vm.vars['nextarrivalat']>0
    e.now=m.f32(s.vm.vars['nextarrivalat']+0.000003);e.real+=2;s.vm.call('OnUpdateGameTime');e.check(s)
def fill(e,s):
    for _ in range(s.maximum+3):
        if len(e.enabled(s))==s.vm.vars['dailypopulation']:return
        due(e,s)
    raise AssertionError((s.name,'did not fill',s.vm.vars['diagreason'],s.vm.vars['deferredreason']))
class Pump(base['Pump']):
    def clock(self,real):
        super().clock(max(real,self.e.real))
        move=getattr(self,'move',None)
        if move:move(self.e.real)

def norm(v):
    if isinstance(v,str):return v.replace('v1.2.4','v1.2.3')
    if isinstance(v,(list,tuple)):return [norm(x) for x in v]
    if isinstance(v,dict):return {k:norm(x) for k,x in v.items()}
    return v

def structure():
    assert len(recs)==len(old)==19942 and set(old)==set(recs)
    assert plugin.header.author=='Tsoxer' and plugin.header.masters==['Skyrim.esm','HearthFires.esm','Dragonborn.esm']
    changed=[]
    for k,a in old.items():
        b=recs[k];assert (a.signature,a.flags,a.editor_id)==(b.signature,b.flags,b.editor_id)
        if subs(a)!=subs(b):
            assert a.signature=='GLOB' and subs(a,['FLTV'])==subs(b,['FLTV'])
            assert struct.unpack('<f',b.get_subrecord('FLTV').data)[0]==1205;changed.append(a.editor_id)
    assert len(changed)==58
    assert (RT/'Seq/MoreBrats.seq').read_bytes()==(W/'build/v1.2.4/runtime/Seq/MoreBrats.seq').read_bytes()
    allowed={'service','ensuresetup','reconcile','recoverorphans','fullenabledcount','resol veappearancepools'.replace(' ',''),'poolslotdisabled','tryarrival','processarrival','plannext','playerincity','initdiagnostics','showstatus','placearrival'}
    protected={'tick','removalobservation','saferemoval','setphase','updateroaming','begintrip','abandontrip','pickdestination','selectdonorvariant','poolindex','poolactor','referenceinuse','ensureappearancestorage','enabledcount','doorarrivalindex','safearrival','arrivalblock'}
    diffs={}
    for p in (RT/'Scripts').glob('*.pex'):
        a=Pex(W/'build/v1.2.4/runtime/Scripts'/p.name);b=Pex(p)
        assert a.version==b.version and a.obj['properties']==b.obj['properties'] and a.obj['variables']==b.obj['variables']
        def normalize(v):
            if isinstance(v,str):return v.replace('v1.2.5','v1.2.4')
            if isinstance(v,(list,tuple)):return [normalize(x) for x in v]
            if isinstance(v,dict):return {k:normalize(x) for k,x in v.items()}
            return v
        delta=[k for k,v in a.obj['functions'].items() if normalize(v)!=normalize(b.obj['functions'][k])]
        assert set(delta)<=allowed,(p.name,delta)
        for k in protected&set(a.obj['functions']):assert a.obj['functions'][k]==b.obj['functions'][k],(p.name,k)
        diffs[p.name]=delta
        if 'Controller' not in p.stem:assert p.read_bytes()==(W/'build/v1.2.4/runtime/Scripts'/p.name).read_bytes()
        for fn,f in b.obj['functions'].items():
            types=dict(f['locals']+f['params'])|{k:v[0] for k,v in b.obj['variables'].items()}
            for op,args,_ in f['ins']:
                if op==14:assert not(args[1]==(0,None) and types.get(args[0][1].lower(),'').endswith('[]'))
                if op==30:assert types[args[0][1].lower()].endswith('[]') and 1<=args[1][1]<=128
    out('19942 records, all old data identities/bindings/state types; only58 build globals changed',changed)
    out('AI, departure, appearances, direct door placement and routine counting unchanged; five frozen helpers',diffs)

def door_arrivals():
    cases=[]
    for name in m.Env(version='1.2.5').cities:
        e,s=env(name);p=Pump(e);e.tick(s);target=s.vm.vars['dailypopulation'];last=None;times=[]
        # Move during each native MoveTo, right ONTO selected spawn point,
        # with simulated LOS. This must not reject an arrival or peer reuse.
        def move(actor,point):e.place_player(point.cell,point.xyz);e.visible.add(actor)
        e.move_hook=move
        while len(e.enabled(s))<target:
            first=float(s.vm.vars['nextarrivalat']);assert 2.9<=(first-e.now)*1440<=7.1
            before=len(e.enabled(s));due(e,s);assert len(e.enabled(s))==before+1
            actor=s.vm.vars['diagselectedactor'];point=s.vm.vars['diagselectedpoint'];door=s.vm.vars['diagarrivaldoor']
            assert actor is not None and not actor.disabled and actor.xyz==point.xyz and not actor.cell.interior and actor.package
            assert math.dist(e.player.xyz,actor.xyz)==0 and door is not last and not s.vm.vars['diagdoorfallback']
            assert math.dist(point.xyz,door.xyz)<=512;last=door;times.append(first)
            s.alias.call('OnCellLoad');s.alias.call('OnLocationChange',None,s.location)
            assert len(e.enabled(s))==before+1
        n=len(e.enabled(s));e.now=m.f32(e.now+1/24);e.tick(s);assert len(e.enabled(s))==n==target
        assert s.vm.vars['diagenableconfirmed']==target
        cases.append({'name':name,'population':target,'times':times,'door_queries':len(e.door_queries)})
    out('All19: real Enable boundary and outdoor MoveTo, randomized doors/no immediate repeat, visible player at point, caps',cases)
    # Same single door is allowed repeatedly when alternatives are absent.
    e,s=env();e.doors=[d for d in e.doors if d.name=='Whiterun SYNTHETIC ordinary door 0'];e.tick(s);s.vm.vars['dailypopulation']=5
    fill(e,s);assert len(e.enabled(s))==5
    out('A sole door may be reused; no occupancy or uniqueness veto')
    fallbacks=[]
    for name in ['Whiterun','Solitude','DragonBridge','SkaalVillage']:
        e,s=env(name);e.no_doors=True;e.tick(s);due(e,s)
        assert len(e.enabled(s))==1 and s.vm.vars['diagdoorfallback'] and s.vm.vars['diagarrivaldoor'] is None
        assert len(e.door_queries)<=len(s.roads)
        fallbacks.append(name)
    out('Unavailable local doors: bounded same-settlement randomized ground fallback enables successfully',fallbacks)

def moving_and_callbacks():
    cases=[]
    for name in ['Whiterun','Markarth','Riften','Windhelm','Solitude','DragonBridge','Morthal','Riverwood']:
        for speed in [110,300]:
            e,s=env(name);p=Pump(e,drop_game=True);s.alias.call('OnCellLoad')
            positions=set()
            def move(real):
                travel=(real-1000)*speed/1600.;index=int(travel)%len(s.roads);r=s.roads[index];nextroad=s.roads[(index+1)%len(s.roads)];fraction=travel-int(travel);xyz=[a+(b-a)*fraction for a,b in zip(r.xyz,nextroad.xyz)]
                e.place_player(r.cell,xyz);positions.add(tuple(xyz))
            p.move=move
            # Continuous movement without cell/location events: only the
            # actual registered deadline callbacks may advance these arrivals.
            for step in range(900):
                move(e.real);p.run(1)
            assert len(e.enabled(s))==s.vm.vars['dailypopulation'] and len(positions)>20 and max(x[0] for x in positions)-min(x[0] for x in positions)>500,(name,speed,len(e.enabled(s)),s.vm.vars['dailypopulation'],s.vm.vars['diagreason'],s.vm.vars['nextarrivalat'],e.now)
            assert any(kind=='OnUpdate' for _,kind,_ in p.fired)
            assert not s.vm.vars['processing'];cases.append([name,'walking' if speed==110 else 'running',len(e.enabled(s))])
    out('Eight regions walking/running for300 game minutes WITHOUT cell events; GT dropped, RT arrival counterpart succeeds',cases)
    e,s=env();p=Pump(e,drop_game=True);s.alias.call('OnCellLoad')
    for _ in range(100):
        s.alias.call('OnLocationChange',s.location,s.location);p.run(1)
    assert e.enabled(s) and not s.vm.vars['processing']
    out('Repeated movement transitions coalesce rather than push the worker wake into the future')
    # Debug through the unchanged alias/watchdog paths while outdoors.
    e,s=env('Solitude');p=Pump(e);e.tick(s);s.diagnostics[0].value=2
    s.vm.call('RecoveryPulse');p.run(3)
    assert any(r[0]=='messagebox' and 'Solitude' in r[1] for r in e.logs)
    out('Named debug request handled outdoors without an interior transition')

def activation_faults():
    e,s=env(version='1.2.3');e.place_player(s.inn);assert s.vm.call('EnsureSetup')
    s.vm.vars['dailypopulation']=3;s.vm.vars['todaycycle']=40
    inherited=s.vm.native
    def dropped_enable(target,method,args):
        if isinstance(target,m.Ref) and method.lower()=='enablenowait':return None
        return inherited(target,method,args)
    s.vm.native=dropped_enable;s.vm.call('TryArrival',0,40)
    assert not e.enabled(s) and e.residents(s)[0] is not None and s.vm.vars['diagstage']==11
    out('Actualv123 PEX retains a disabled reservation at stage11 under injected async-enable failure')
    e,s=env();e.tick(s);e.fail_enable=True;due(e,s)
    assert not e.enabled(s) and not any(e.residents(s)) and s.vm.vars['diagenableconfirmed']==0 and s.vm.vars['diagreason']==44
    assert s.vm.vars['nextarrivalat']>e.now
    e.fail_enable=False;due(e,s);assert len(e.enabled(s))==1 and s.vm.vars['diagenableconfirmed']==1
    out('Failed native Enable cannot count as success; pending arrival retained and later genuinely enabled')
    e,s=env(version='1.2.3');assert s.vm.call('EnsureSetup');s.vm.vars['todaycycle']=40;s.vm.vars['dailypopulation']=3
    for i in range(3):
        s.vm.vars['residents'][i]=s.vm.call('PoolActor',s.vm.call('PoolIndex',i,0))
        s.vm.vars['selectedvariant'][i]=0;s.vm.vars['residentcycle'][i]=40;s.vm.vars['lastarrivalcycle'][i]=40
        s.vm.vars['enableuntil'][i]=30000.;s.vm.call('SetPhase',i,0)
    p=Pump(e,drop_game=True);s.alias.call('OnPlayerLoadGame');p.run(90)
    assert not e.enabled(s) and s.vm.vars['enableuntil'][0]==30000. and s.vm not in p.real
    out('Old Whiterun PEX reproduces stale reservation hold; no pending-enable RT wake under injected GT loss')
    cases=[]
    for name in ['Whiterun','Solitude']:
        e,s=env(name);assert s.vm.call('EnsureSetup');n=min(7,s.maximum)
        s.vm.vars['dailypopulation']=n;s.vm.vars['todaycycle']=40
        for i in range(n):
            child=s.vm.call('PoolActor',s.vm.call('PoolIndex',i,0));s.vm.vars['residents'][i]=child
            s.vm.vars['selectedvariant'][i]=0;s.vm.vars['residentcycle'][i]=40;s.vm.vars['lastarrivalcycle'][i]=40
            s.vm.vars['enableuntil'][i]=30000.;s.vm.call('SetPhase',i,0)
        s.vm.vars['arrivalschedulecycle']=-100000;s.vm.vars['nextarrivalat']=0.
        # Matches the observed shape without pretending the stale sample
        # proves that Skyrim had these native disabled flags.
        assert not e.enabled(s) and len([a for a in e.residents(s) if a])==n
        p=Pump(e,drop_game=True);s.alias.call('OnPlayerLoadGame');p.run(90)
        assert e.enabled(s) and s.vm.vars['diagenableconfirmed']>0
        cases.append(name)
    out('Whiterun missing expiry added; shared expiry retained: disabled reservations recover without actor resets',cases)
    e,s=env();assert s.vm.call('EnsureSetup');s.vm.vars['dailypopulation']=3;s.vm.vars['todaycycle']=40
    for i in range(3):
        child=s.vm.call('PoolActor',s.vm.call('PoolIndex',i,0));s.vm.vars['residents'][i]=child
        s.vm.vars['selectedvariant'][i]=0;s.vm.vars['residentcycle'][i]=40;s.vm.vars['lastarrivalcycle'][i]=40;s.vm.vars['enableuntil'][i]=e.real+60;s.vm.call('SetPhase',i,0)
    p=Pump(e,drop_game=True);e.tick(s)
    assert p.real[s.vm]<=e.real+60.01
    p.run(160);assert e.enabled(s)
    out('Full pending reservations receive one existing-timer expiry wake even when no arrival slot is free')

# Reuse the release's real mapping, typed-save and departure tests; update only
# candidate version/fixtures and replace the superseded distance rejection check.
def existing_tests():
    source=(W/'release_v122/test_release.py').read_text();tree=ast.parse(source)
    for name in ['mapping_and_upgrades','lifecycle_and_faults']:
        node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
        text=ast.get_source_segment(source,node).replace("version='1.2.2'","version='1.2.5'")
        if name=='mapping_and_upgrades':
            text=text.replace("['1.1.0','1.2.0','1.2.1']","['1.1.0','1.2.0','1.2.1','1.2.2','1.2.3','1.2.4']").replace('171 typed','342 typed')
            needle='            e.records=recs;e.rootpath=RT'
            text=text.replace(needle,'''            if version in ['1.2.2','1.2.3','1.2.4']:
                for previous in e.cities.values():
                    e.place_player(previous.inn);e.tick(previous)
                    for slot in range(previous.vm.vars['dailypopulation']):
                        previous.vm.call('TryArrival',slot,40)
                    e.check(previous)
'''+needle,1)
        else:
            start=text.index('    assert not e.enabled(s) and s.vm.vars[\'diagreason\']==24')
            end=text.index('    fault=[]',start)
            text=text[:start]+'''    assert len(e.enabled(s))==1 and s.vm.vars['diagenableconfirmed']==1
    out('MoveTo yielding while player reaches the landing point does not veto an arrival')
'''+text[end:]
        exec(compile(text,str(ROOT/'test_release.py')+':reused-'+name,'exec'),globals())
existing_tests()

def workload():
    for version in ['1.2.1','1.2.4','1.2.5']:
        e=m.Env(42,version=version);e.set_time(40,11)
        for s in e.cities.values():
            e.place_player(s.inn);assert s.vm.call('EnsureSetup')
            s.vm.vars['todaycycle']=40;s.vm.vars['dailypopulation']=s.maximum
            for slot in range(s.maximum):s.vm.call('TryArrival',slot,40)
            assert len(e.enabled(s))==s.maximum
        work={}
        for fn in ['EnabledCount','FullEnabledCount','PublishSnapshot','ShowStatus']:
            if fn.lower() not in next(iter(e.cities.values())).vm.obj['functions']:continue
            start=sum(s.vm.executed for s in e.cities.values());e.native_calls.clear()
            for s in e.cities.values():s.vm.call(fn)
            work[fn]={'opcodes':sum(s.vm.executed for s in e.cities.values())-start,'native_calls':dict(e.native_calls)}
        metrics[version]=work
    assert metrics['1.2.1']['EnabledCount']['native_calls']['isdisabled']==15200
    assert metrics['1.2.5']['EnabledCount']['native_calls']['isdisabled']==76
    assert metrics['1.2.4']['EnabledCount']==metrics['1.2.5']['EnabledCount']
    out('Routine count unchanged fromv123: max76 tracked checks vs15200 inv121; census remains exceptional',metrics)

def protected_files():
    table=json.loads((ROOT/'protected-before.json').read_text())
    for name,digest in table.items():assert hashlib.sha256((W.parent/name).read_bytes()).hexdigest()==digest,name
    out('Historical releases and stable publicv110 unchanged',len(table))


def roaming_after_full():
    cases=[]
    for version in ['1.2.4','1.2.5']:
        for name in ['Whiterun','Solitude','DragonBridge','Morthal']:
            e,s=env(name,version=version);p=Pump(e,drop_game=True);e.tick(s)
            fill(e,s)
            last=[a for a in e.residents(s) if a][-1];slot=e.residents(s).index(last)
            assert s.vm.vars['phase'][slot]==0
            before=sum(1 for f in s.vm.calls if f=='begintrip');logstart=len(e.logs);p.base_real=e.real;p.base_game=float(e.now);p.run(180)
            after=sum(1 for f in s.vm.calls if f=='begintrip')
            if version=='1.2.4':assert s.vm.vars['phase'][slot]==0 and after==before
            else:
                travel_names={pack.editor_id for pack in e.packs.values() if struct.unpack('<III',pack.get_subrecord('PKCU').data)[1]==0x16FAA}
                assert after>before and any(row[0]=='evaluate' and row[1]==last.name and row[3] in travel_names for row in e.logs[logstart:])
            cases.append([version,name,before,after])
    out('Actual old full-target PEX loses RT roaming wake under GT loss; candidate starts travel in all four classes',cases)

def walled_location_seams():
    cases=[]
    for name in ['Markarth','Riften','Windhelm','Solitude']:
        e,s=env(name);assert s.vm.call('EnsureSetup');e.world_drop_ids.add('Player')
        assert s.vm.call('PlayerInCity') and s.vm.call('ArrivalRelevant')
        p=Pump(e,drop_game=True);e.tick(s);p.run(100)
        assert e.enabled(s);cases.append(name)
    out('All four shared walled controllers use current location for BOTH arrival and roaming when world query is None',cases)

def slow_workers():
    cases=[]
    for version in ['1.2.4','1.2.5']:
        for name in ['Whiterun','Solitude','DragonBridge']:
            e,s=env(name,10,version=version);p=Pump(e);entered=[False];fired=[]
            def hook(target,method,args):
                p.hook(target,method,args)
                if method in ['isdisabled','getformfromfile','getat','getsize']:
                    p.clock(e.real+0.04)
                    if s.vm.vars['processing'] and e.real>1121 and not entered[0]:
                        entered[0]=True;fired.append(e.real);s.vm.call('Service')
            e.native_hook=hook;e.tick(s);e.check(s)
            epoch=s.vm.vars['workepoch'];counts=e.native_calls['isdisabled']
            assert epoch==(1 if version=='1.2.4' else 0),(version,name,epoch)
            if version=='1.2.5':assert e.enabled(s),'entry deadline must not restart after long initialization'
            cases.append({'version':version,'city':name,'native_delay_injected':0.04,'watchdog_at':fired,'epoch':epoch,'enabled_checks':counts,'active':len(e.enabled(s)),'synthetic_elapsed':e.real-1000})
    out('Actual old progress cancelled by lease; candidate keeps lease, single census and reaches Enable after delayed initialization',cases)

def registration_contract():
    # Preserve-first is a conservative allowed behavior for an unelapsed native
    # timer re-registered without unregister. Do not silently guarantee overwrite.
    rows=[]
    for version in ['1.2.4','1.2.5']:
        e,s=env('Solitude',version=version);p=Pump(e);bad=[]
        def sticky(target,method,args):
            if method=='registerforsingleupdate' and target in p.real and p.real[target]>e.real:
                bad.append([p.real[target],args[0]]);return
            p.hook(target,method,args)
        e.native_hook=sticky;p.real[s.vm]=e.real+100;e.tick(s)
        if version=='1.2.4':assert bad
        else:assert not bad
        rows.append([version,len(bad)])
    out('Conservative native timer replacement semantics: old unelapsed re-registration detected; new explicit unregister passes',rows)


def faithful_v110_upgrade():
    legacy=m.Env(42,version='1.1.0');current=m.Env(42,version='1.2.5')
    legacy.set_time(40,11);current.set_time(40,11)
    for s in legacy.cities.values():
        legacy.place_player(s.inn);assert s.vm.call('EnsureSetup')
        s.vm.vars['todaycycle']=40;s.vm.vars['dailypopulation']=max(2,s.cfg['minimum'])
        s.vm.call('TryArrival',0,40)
        assert len(legacy.enabled(s))==1
    reverse={id(value):key for key,value in legacy.forms.items()}
    def remap(value):
        if isinstance(value,list):return [remap(x) for x in value]
        key=reverse.get(id(value))
        if key is not None:return current.forms[key]
        return value
    cases=[]
    for name,os in legacy.cities.items():
        ns=current.cities[name]
        # Actual form identity is the stable FormID, not Python object address.
        for oldactor in legacy.enabled(os):
            key=next(k for k,v in legacy.byid.items() if v is oldactor);newactor=current.byid[key]
            newactor.disabled=False;newactor.rank=oldactor.rank;newactor.xyz=oldactor.xyz[:];newactor.world=ns.world;newactor.cell=ns.cells[os.roads.index(next(r for r in os.roads if r.cell is oldactor.cell))]
        fresh=m.VM(ns.pex,current.native);fresh.vars.update({k:remap(v) for k,v in os.vm.vars.items()})
        ns.vm=fresh;current.owners[fresh]=ns;current.forms[ns.root]=fresh;current.running[fresh]=True;ns.alias.property('Controller',fresh)
        current.place_player(ns.cells[0],ns.roads[0].xyz);ns.alias.call('OnPlayerLoadGame');current.tick(ns)
        assert len(current.enabled(ns))==1 and ns.vm.vars['diagnamedresolved']==ns.maximum*160,(name,len(current.enabled(ns)),ns.vm.vars['diagnamedidrecovered'],ns.maximum,ns.vm.vars['diagstage'],ns.vm.vars['diagreason'],ns.vm.vars.get('diagstoragefailure'),ns.vm.vars.get('processing'),ns.vm.vars.get('diagnamedresolved'),ns.vm.vars.get('diagnamedcatalogstate'),dict(current.native_calls),current.logs[-3:])
        ns.vm.vars['selectedvariant'][1]=199
        ns.vm.call('TryArrival',1,40)
        assert len(current.enabled(ns))==2 and variant(current,ns,current.residents(ns)[1])==199
        current.check(ns);cases.append(name)
    out('Nineteen genuinev110 property layouts transferred into final ESP data; old actors retained and appended199 enables through catalog/ID recovery',cases)


def timing_revision_preservation():
    baseline=W/'baselines/v1.2.5-7-14min'
    assert (RT/'MoreBrats.esp').read_bytes()==(baseline/'runtime/MoreBrats.esp').read_bytes()
    assert (RT/'Seq/MoreBrats.seq').read_bytes()==(baseline/'runtime/Seq/MoreBrats.seq').read_bytes()
    changes={}
    for p in (RT/'Scripts').glob('*.pex'):
        a=Pex(baseline/'runtime/Scripts'/p.name);b=Pex(p)
        assert a.obj['properties']==b.obj['properties'] and a.obj['variables']==b.obj['variables']
        changed=[k for k,v in a.obj['functions'].items() if v!=b.obj['functions'][k]]
        assert set(changed)<= {'processarrival','primearrivaldeadline'},(p.name,changed)
        for fn in changed:
            expected=__import__('copy').deepcopy(a.obj['functions'][fn])
            ins=[]
            for op,args,va in expected['ins']:
                va=list(va);args=list(args)
                if op==25 and args[0][1].lower()=='utility' and args[1][1].lower()=='randomfloat' and tuple(x[1] for x in va)==(7.0,14.0):
                    va=[(4,3.0),(4,7.0)]
                if op==18 and args[2][0]==4 and abs(args[2][1]-14.1)<0.001:args[2]=(4,m.f32(7.1))
                ins.append((op,args,va))
            expected['ins']=ins
            assert expected==b.obj['functions'][fn],(p.name,fn,'unrelated bytecode difference')
        if 'Controller' not in p.stem:assert p.read_bytes()==(baseline/'runtime/Scripts'/p.name).read_bytes()
        changes[p.name]=changed
    out('Timing revision: ESP/SEQ/five helpers byte-identical; only arrival constants changed in four PEX',changes)
    for name in m.Env(version='1.2.5').cities:
        e,s=env(name,hour=10);original=s.vm.native
        def lower(target,method,args):
            if isinstance(target,str) and target.lower()=='utility' and method.lower()=='randomfloat' and tuple(args)==(3.0,7.0):return 3.0
            return original(target,method,args)
        s.vm.native=lower;p=Pump(e,drop_game=True);e.tick(s);s.vm.vars['dailypopulation']=s.maximum;at=s.vm.vars['nextarrivalat'];assert 2.99<(at-e.now)*1440<3.01
        p.run(10);assert len(e.enabled(s))==1,(name,e.now,at)
        # An old7–14-minute pending deadline is shortened without resetting state.
        s.vm.vars['nextarrivalat']=e.now+12/1440.;saved=e.residents(s)[:];target=s.vm.vars['dailypopulation']
        s.vm.call('PrimeArrivalDeadline')
        assert 2.99<(s.vm.vars['nextarrivalat']-e.now)*1440<3.01
        assert e.residents(s)==saved and s.vm.vars['dailypopulation']==target
    out('All19: minimum3-game-minute callback succeeds; old long pending deadlines shorten without actor/population reset')
    table=json.loads((ROOT/'protected-timing-baseline.json').read_text())
    for name,digest in table.items():assert hashlib.sha256((W.parent/name).read_bytes()).hexdigest()==digest,name
    out('Originalv125 timing release and preservation snapshot intact',len(table))

if __name__=='__main__':
    timing_revision_preservation();structure();door_arrivals();moving_and_callbacks();activation_faults();roaming_after_full();walled_location_seams();slow_workers();registration_contract();mapping_and_upgrades();faithful_v110_upgrade();lifecycle_and_faults();workload();protected_files()
    (R/'validation.json').write_text(json.dumps({'status':'PASS','checks':results,'workload':metrics,'Skyrim_executed':False,'ESS_files_tested':False,'limits':'Actual PEX branches/ESP bindings; synthetic native Enable can fail and geometry/player position moves. Local door search, timers, save serialization and AI/pathfinding are controlled mocks. No in-game functionality or callback/door-search behavior is proven.'},indent=2)+'\n')
    print('PASS: v1.2.5 structural + fault-aware bytecode verification; Skyrim testing still required.',flush=True)
