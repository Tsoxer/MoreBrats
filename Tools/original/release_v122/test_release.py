"""v1.2.2: actual ESP/PEX + fault-aware interpreter, synthetic natives/events.
This cannot test Skyrim callback delivery, camera geometry, AI or ESS loading.
"""
from pathlib import Path
import collections,copy,difflib,hashlib,json,runpy,struct,sys,zipfile
ROOT=Path(__file__).resolve().parent; W=ROOT.parent; R=W/'build/v1.2.2'; RT=R/'runtime'
sys.path[:0]=[str(W/'src'),str(W/'deps/esplib/src')]
from pexcheck import Pex
support=runpy.run_path(str(W/'release_v121/test_release.py'),run_name='support_only')
m=support['mod']; load=support['load']; subs=support['subs']; variant=support['variant']
_,old=load(W/'build/v1.2.1/runtime');plugin,recs=load(RT)
m.SETS['1.2.2']=(RT,recs,{k:r for k,r in recs.items() if r.signature=='PACK'},0x3000000)
_,v120=load(W/'build/v1.2.0/runtime')
m.SETS['1.2.0']=(W/'build/v1.2.0/runtime',v120,{k:r for k,r in v120.items() if r.signature=='PACK'},0x3000000)
roster=json.loads((ROOT/'Config/appearance-roster.json').read_text())
results={};metrics={}
def out(name,value=True):
    results[name]=value; print('PASS:',name,flush=True)
def env(name='Whiterun',hour=8.001,seed=42):
    e=m.Env(seed,version='1.2.2');s=e.cities[name]
    e.set_time(40,hour);start=s.roads[0].xyz[:];start[1]-=2000.;e.place_player(s.cells[0],start)
    return e,s
def due(e,s):
    at=s.vm.vars['nextarrivalat'];assert at>0,(s.name,s.vm.vars['diagreason'])
    e.now=m.f32(at+0.000003);e.real+=2
    s.vm.call('OnUpdateGameTime');e.check(s)
def fill(e,s):
    for _ in range(s.maximum+2):
        if len(e.enabled(s))==s.vm.vars['dailypopulation']:break
        due(e,s)
    assert len(e.enabled(s))==s.vm.vars['dailypopulation'],(s.name,len(e.enabled(s)),s.vm.vars['diagreason'])
def normalize(x):
    if isinstance(x,str):return x.replace('v1.2.2','v1.2.1')
    if isinstance(x,(tuple,list)):return [normalize(v) for v in x]
    if isinstance(x,dict):return {k:normalize(v) for k,v in x.items()}
    return x

def structure():
    assert set(old)==set(recs) and len(recs)==19941
    assert plugin.header.author=='Tsoxer' and plugin.header.masters==['Skyrim.esm','HearthFires.esm','Dragonborn.esm']
    changes=[]
    for key,a in old.items():
        b=recs[key];assert (a.signature,a.flags,a.editor_id)==(b.signature,b.flags,b.editor_id)
        if subs(a)!=subs(b):
            assert a.signature=='GLOB' and subs(a,['FLTV'])==subs(b,['FLTV'])
            assert struct.unpack('<f',b.get_subrecord('FLTV').data)[0]==1202
            changes.append(a.editor_id)
    assert len(changes)==58
    assert (RT/'Seq/MoreBrats.seq').read_bytes()==(W/'build/v1.2.1/runtime/Seq/MoreBrats.seq').read_bytes()
    assert (R/'settlements.json').read_bytes()==(W/'build/v1.2.1/settlements.json').read_bytes()
    protected=['saferemoval','removalobservation','setphase','pickdestination','begintrip','abandontrip','updateroaming','recoverorphans','refreshresident','reconcile','selectdonorvariant','poolindex','slotfrompoolindex','poolactor','poolslotdisabled','cleararrivalpoint','tryarrival','roadblock','resolveappearancepools','ensurenameddonorstorage']
    diffs={};added={}
    for p in (RT/'Scripts').glob('*.pex'):
        a=Pex(W/'build/v1.2.1/runtime/Scripts'/p.name);b=Pex(p)
        assert a.obj['properties']==b.obj['properties']
        for k,v in a.obj['variables'].items():assert b.obj['variables'][k]==v,(p.name,k)
        added[p.name]={k:v[0] for k,v in b.obj['variables'].items() if k not in a.obj['variables']}
        diffs[p.name]=[k for k,v in a.obj['functions'].items() if normalize(v)!=normalize(b.obj['functions'][k])]
        if 'Controller' not in p.stem:
            assert p.read_bytes()==(W/'build/v1.2.1/runtime/Scripts'/p.name).read_bytes()
        else:
            for name in protected:
                if name in a.obj['functions']:assert normalize(a.obj['functions'][name])==normalize(b.obj['functions'][name]),(p.name,name)
            # Source-level equality of the entire existing resident/departure arm.
            ta=(W/'v1.2.1/src'/f'{p.stem}.psc').read_text();tb=(W/'v1.2.2/src'/f'{p.stem}.psc').read_text()
            def resident_branch(t):
                t=t[t.index('Function Tick()'):];t=t[t.index('        Actor child = residents[s]'):]
                return t[:t.index('        ; Native calls may yield')]
            aa=resident_branch(ta).replace('        ElseIf s < dailyPopulation && Daylight(hour) && lastArrivalCycle[s] != cycle\n            TryArrival(s, cycle)\n','')
            assert aa==resident_branch(tb),(p.name,'resident/departure arm changed')
        for fn,f in b.obj['functions'].items():
            types=dict(f['locals']+f['params'])|{k:v[0] for k,v in b.obj['variables'].items()}
            for op,args,_ in f['ins']:
                if op==14:assert not(args[1]==(0,None) and types.get(args[0][1].lower(),'').endswith('[]'))
                if op==30:assert types[args[0][1].lower()].endswith('[]') and 1<=args[1][1]<=128
    out('19941 stable records; only 58 display globals changed; all NPC/ACHR/PACK/QUST/VMAD unchanged',len(recs))
    out('Departure, movement, appearance-selection functions and old serialized fields preserved',{'function_changes':diffs,'additive_fields':added})

def arrival_tests():
    allcity=[]
    for name in m.Env(version='1.2.2').cities:
        e,s=env(name);s.alias.call('OnCellLoad');e.check(s)
        assert not e.enabled(s)
        first=s.vm.vars['nextarrivalat'];assert 14.9<=(first-e.now)*1440<=30.1
        assert abs(e.gt[s.vm]-(first-e.now)*24)<0.001
        assert s.vm not in e.rt,'arrival-only real-time polling'
        times=[]
        while len(e.enabled(s))<s.vm.vars['dailypopulation']:
            before=len(e.enabled(s));due(e,s)
            assert len(e.enabled(s))==before+1,(name,before,len(e.enabled(s)),s.vm.vars['diagreason'],s.vm.vars['diagselectedactor'],s.vm.vars['diagselectedpoint'],s.vm.vars['deferredreason'],e.now,s.vm.vars['nextarrivalat'])
            child=e.enabled(s)[-1]
            assert e.native(e.player,'GetDistance',[child])>=1536.
            times.append(float(e.now))
            delta=(s.vm.vars['nextarrivalat']-e.now)*1440
            assert 14.9<=delta<=30.1
            # Repeated cell events at the same instant must not admit another.
            s.alias.call('OnCellLoad');s.alias.call('OnLocationChange',None,s.location)
            assert len(e.enabled(s))==before+1;e.check(s)
        allcity.append({'settlement':name,'population':len(e.enabled(s)),'arrival_game_days':times})
    out('All 19 settlements: outdoor sequential arrivals, same safety rule, no duplicate transition activation',allcity)
    walls=[]
    for name in ['Whiterun','Markarth','Riften','Windhelm','Solitude']:
        before=m.Env(42,version='1.2.1');s=before.cities[name];before.set_time(40,11);before.place_player(s.cells[0],s.roads[0].xyz)
        before.tick(s);assert len(before.enabled(s))==0 and s.vm.vars['diagreason']==14
        after,ns=env(name,11);after.tick(ns);fill(after,ns)
        assert all(p.cell.attached for p in ns.roads)
        walls.append(name)
    out('Actual old PEX reproduces loaded-cell reason14 in all five synthetic walled cities; new PEX progresses',walls)
    e,s=env();e.tick(s);s.vm.vars['dailypopulation']=5
    fill(e,s);assert len(e.enabled(s))==5
    out('Five children arrive at separate 15–30 game-minute intervals')
    timer_cases=[]
    for name in ['Whiterun','Solitude','Morthal']:
        e,s=env(name,hour=11);e.tick(s);arrivals=[]
        for _ in range(350):
            before=len(e.enabled(s));delay=e.gt.pop(s.vm)
            e.now=m.f32(e.now+delay/24.);e.real+=1
            s.vm.call('OnUpdateGameTime');e.check(s)
            if len(e.enabled(s))>before:arrivals.append(float(e.now))
            assert len(e.enabled(s))<=before+1
            if len(e.enabled(s))==s.vm.vars['dailypopulation']:break
        else:raise AssertionError(('registered timer did not complete arrivals',name))
        assert all(14.9<=(b-a)*1440<=33.2 for a,b in zip(arrivals,arrivals[1:]))
        timer_cases.append({'settlement':name,'arrival_game_days':arrivals})
    out('Synthetic event driver follows actual registered game-time intervals through complete populations',timer_cases)
    e,s=env();e.tick(s)
    # Make every candidate within the minimum distance. Test geometry ONLY.
    saved=[p.xyz[:] for p in s.roads]
    for p in s.roads:p.xyz=e.player.xyz[:]
    due(e,s);assert not e.enabled(s) and s.vm.vars['diagreason']==40
    assert (s.vm.vars['nextarrivalat']-e.now)*1440>=14.9
    e.native_calls.clear();s.alias.call('OnCellLoad')
    assert not e.native_calls['getdistance'],'distance should be checked only when due'
    for p,xyz in zip(s.roads,saved):p.xyz=xyz
    e.place_player(s.cells[0],s.roads[0].xyz);due(e,s);assert len(e.enabled(s))==1
    out('All roads too close: deferred without a distance loop; next due attempt recovers')
    point=s.roads[-1];point.loaded=True;e.visible.add(point)
    assert s.vm.call('ArrivalBlock',point)==41
    e.visible.clear();assert s.vm.call('ArrivalBlock',point)==0
    out('Loaded visible marker rejected by a bounded native LOS check')
    # Waiting through several due times must activate only one, then rebase.
    e,s=env(hour=7.5);e.place_player(s.inn);e.tick(s)
    e.set_time(40,11);e.tick(s);assert len(e.enabled(s))==1
    next_due=s.vm.vars['nextarrivalat'];assert 14.9<=(next_due-e.now)*1440<=30.1
    e.tick(s);assert len(e.enabled(s))==1
    e.place_player(s.cells[0],s.roads[0].xyz);s.alias.call('OnCellLoad');assert len(e.enabled(s))==1
    due(e,s);assert len(e.enabled(s))==2
    out('Indoor overnight wait and exit: one overdue arrival, no missed-event burst')
    e,s=env(hour=20);e.place_player(s.inn);e.tick(s);assert not e.enabled(s)
    e.set_time(41,8.55);e.tick(s);assert len(e.enabled(s))==1
    due(e,s);assert len(e.enabled(s))==2
    out('Fresh evening installation and overnight indoor wait initialize next morning')
    # Several fast travels in one retained world. Only current settlement due.
    e=m.Env(51,version='1.2.2');e.set_time(40,11);e.place_player(e.rural,[0,0,0]);e.tick_all()
    assert all(not e.enabled(s) for s in e.cities.values())
    assert sum(s.vm.vars['diagstorageready'] for s in e.cities.values())==0
    visits=['Whiterun','Morthal','Solitude','Riften','Riverwood','Whiterun']
    for name in visits:
        s=e.cities[name];e.place_player(s.cells[0],s.roads[0].xyz)
        for peer in e.cities.values():peer.alias.call('OnCellLoad')
        e.check(s);before=len(e.enabled(s));due(e,s)
        assert len(e.enabled(s))<=before+1
        for peer in e.cities.values():
            if peer is not s and not e.residents(peer).count(None)==peer.maximum:
                continue
            if peer is not s:assert peer.vm not in e.rt,'empty irrelevant settlement real-time polling'
    out('Cold irrelevant settlements dormant; consecutive fast-travel/location visits resume independently',visits)

def pending_upgrades():
    cases=[]
    for name in ['Whiterun','Markarth','Riften','Windhelm','Solitude']:
        e=m.Env(72,version='1.2.1');s=e.cities[name]
        e.set_time(40,11);e.place_player(s.cells[0],s.roads[0].xyz);e.tick(s)
        assert not e.enabled(s) and s.vm.vars['diagreason']==14
        selected=s.vm.vars['selectedvariant'][:];target=s.vm.vars['dailypopulation']
        arrays={k:v for k,v in s.vm.vars.items() if isinstance(v,list)}
        stem='MB_Controller' if s.whiterun else 'MB_CityController'
        pex=Pex(RT/'Scripts'/f'{stem}.pex');vm=m.VM(pex,e.native);vm.vars.update(s.vm.vars)
        s.vm=vm;s.pex=pex;e.owners[vm]=s;e.forms[s.root]=vm;e.running[vm]=True;s.alias.property('Controller',vm)
        s.alias.call('OnPlayerLoadGame');e.tick(s)
        assert not e.enabled(s) and vm.vars['diagreason']==42
        fill(e,s)
        assert len(e.enabled(s))==target and vm.vars['selectedvariant']==selected
        assert all(vm.vars[k] is value for k,value in arrays.items())
        cases.append({'settlement':name,'old_reason':14,'new_population':target,'old_selected_variants_retained':True})
    out('Five loaded-city reason14 saved states upgrade and finish gradual arrivals without reroll/reset',cases)

def mapping_and_upgrades():
    e=m.Env(42,version='1.2.2');e.set_time(40,11);mapping=0
    for s in e.cities.values():
        e.place_player(s.inn);assert s.vm.call('EnsureSetup')
        for slot in range(s.maximum):
            for v in range(200):
                idx=s.vm.call('PoolIndex',slot,v);actor=s.vm.call('PoolActor',idx)
                assert actor is not None and variant(e,s,actor)==v and s.vm.call('SlotFromPoolIndex',idx)==slot
                mapping+=1
    assert mapping==15200;out('All 15200 existing slot/variant/reference mappings preserved',mapping)
    s=e.cities['Whiterun'];e.place_player(s.inn);s.vm.vars['dailypopulation']=3;s.vm.vars['todaycycle']=40
    native=s.vm.native;seen=set()
    for group in roster['groups']:
        for donor in range(group['count']):
            for outfit in range(5):
                gender=group['gender'];legacy=(gender*3+outfit if outfit<3 else 6+gender*2+outfit-3)+(group['race']-1)*10
                expected=legacy if donor==0 else group['additional'][donor-1]+outfit
                def controlled(target,method,args):
                    if isinstance(target,str) and target.lower()=='utility' and method.lower()=='randomint':
                        bounds=tuple(args)
                        if bounds==(1,4):return group['race']
                        if bounds==(1,2):return gender+1
                        if bounds==(0,4):return outfit
                        if bounds==(0,group['count']-1):return donor
                        assert bounds==(0,17),bounds
                    return native(target,method,args)
                s.vm.native=controlled;s.vm.vars['selectedvariant'][0]=-1;s.vm.vars['lastarrivalcycle'][0]=-100000
                s.vm.call('TryArrival',0,40);actor=e.residents(s)[0]
                assert actor is not None and not actor.disabled and actor.package is not None
                assert s.vm.vars['selectedvariant'][0]==expected
                seen.add(expected);actor.disabled=True;s.vm.vars['residents'][0]=None
    s.vm.native=native;assert seen==set(range(200));out('Actual compiled TryArrival reaches all 200 appearances with unchanged independent RNG bounds',len(seen))
    cases=[]
    for version in ['1.1.0','1.2.0','1.2.1']:
        for mode in ['day','inn','watched03']:
            e=m.Env(91,version=version);e.set_time(40,11);e.place_player(e.rural,[0,0,0]);e.tick_all()
            e.records=recs;e.rootpath=RT
            for s in e.cities.values():
                arrays={k:v for k,v in s.vm.vars.items() if isinstance(v,list)};actors=e.enabled(s)[:];selected=s.vm.vars['selectedvariant'][:]
                stem='MB_Controller' if s.whiterun else 'MB_VillageController' if s.village else 'MB_TownController' if s.town else 'MB_CityController'
                pex=Pex(RT/'Scripts'/f'{stem}.pex');new=m.VM(pex,e.native);new.vars.update(s.vm.vars)
                s.vm=new;s.pex=pex;e.owners[new]=s;e.forms[s.root]=new;e.running[new]=True;s.alias.property('Controller',new)
                if mode=='day':e.set_time(40,11);e.place_player(s.cells[0],s.roads[0].xyz)
                else:
                    for i,a in enumerate(actors):a.cell=s.inn;a.world=None;a.xyz=[4000.+i*700,0,0]
                    e.place_player(s.inn);e.set_time(41 if mode=='watched03' else 40,3.1 if mode=='watched03' else 22)
                    if mode=='watched03':e.visible.add(actors[0])
                s.alias.call('OnPlayerLoadGame');e.tick(s)
                assert all(new.vars[k] is v for k,v in arrays.items())
                assert new.vars['selectedvariant']==selected
                assert all(a in e.residents(s) for a in actors if not a.disabled)
                if mode=='watched03':assert not actors[0].disabled
                if mode=='day':
                    for _ in range(3):e.save_load(s);e.tick(s)
                    assert all(a in e.residents(s) for a in actors)
                cases.append([version,mode,s.name])
            print('Upgrade group complete:',version,mode,flush=True)
    out('171 typed saved-state upgrade cases, retaining arrays/actors/variants; repeated daytime reloads',cases)

def lifecycle_and_faults():
    cases=[]
    for name in m.Env(version='1.2.2').cities:
        e,s=env(name);e.tick(s);fill(e,s)
        e.set_time(40,19.1);e.tick(s)
        assert all(c.rank==slot*4+3 for slot,c in enumerate(e.residents(s)) if c is not None)
        # Move to inn in the fixture; native door pathfinding is NOT tested.
        for c in e.enabled(s):c.cell=s.inn;c.world=None
        e.place_player(s.inn);e.refresh();e.visible.update(e.enabled(s))
        e.set_time(41,3.1);e.tick(s);assert e.enabled(s)
        e.visible.clear();e.place_player(e.rural,[0,0,0]);e.tick(s);e.tick(s)
        assert not e.enabled(s)
        e.set_time(44,8.1);pos=s.roads[0].xyz[:];pos[1]-=2000.;e.place_player(s.cells[0],pos);e.tick(s);fill(e,s)
        assert len(e.enabled(s))<=s.maximum
        cases.append(name)
    out('All 19: 19:00 priorities, watched03 retention, existing safe retirement, skipped-day reroll',cases)
    e,s=env();e.tick(s);due(e,s);child=e.enabled(s)[0]
    # Simulate a latent move spanning19:00: pre-enable guard must still veto.
    before=len(e.enabled(s));e.move_hook=lambda actor,point:e.set_time(40,19.1)
    due(e,s);assert len(e.enabled(s))==before
    out('Latent placement crossing19:00 does not enable another child')
    e,s=env();e.tick(s)
    def close_during_move(actor,point):e.place_player(point.cell,point.xyz)
    e.move_hook=close_during_move;due(e,s)
    assert not e.enabled(s) and s.vm.vars['diagreason']==24
    assert s.vm.call('ArrivalBlock',s.vm.vars['diagselectedpoint'])==40
    out('Distance rechecked after latent MoveTo and immediately before activation')
    fault=[]
    for name in ['Whiterun','Solitude','Morthal','Riverwood']:
        e,s=env(name);s.vm.deny_allocations.add('donoractors0');s.vm.call('Service')
        assert s.vm.vars['diagreason']==30 and not s.vm.vars['diagstorageready']
        assert all('injected allocation failure' in item for item in s.vm.array_errors)
        s.vm.deny_allocations.clear();s.vm.array_errors.clear();e.tick(s);fill(e,s)
        # Optional catalog absent: stable-ID fallback must remain functional.
        e2,s2=env(name);key=s2.bindings['NamedDonorForms']['form'];s2.vm.property('NamedDonorForms',None);e2.forms.pop(key)
        e2.tick(s2);fill(e2,s2);assert s2.vm.vars['diagnamedidrecovered']==s2.maximum*160
        # Debug status remains immediate even if the worker is busy.
        s.diagnostics[0].value=2;s.vm.vars['processing']=True;s.vm.vars['leasearmed']=True
        s.vm.vars['leasestart']=e.real;s.vm.vars['leaseuntil']=e.real+120
        n=len([a for a in e.logs if a[0]=='messagebox']);s.vm.call('Service')
        assert len([a for a in e.logs if a[0]=='messagebox'])==n+1 and s.diagnostics[0].value==0
        e.real+=130;s.vm.call('Service');assert not s.vm.vars['processing']
        fault.append(name)
    out('Fault-aware allocations, absent catalogs, immediate diagnostics and expired-worker recovery',fault)
    # Orphan audit: existing recovery must adopt an externally enabled pool ref.
    e,s=env();e.tick(s);fill(e,s)
    spare=s.vm.call('PoolActor',s.vm.call('PoolIndex',5,199))
    # Choose an actually unused slot if population rolled6.
    victim=e.residents(s)[-1]
    if victim is not None:victim.disabled=True;s.vm.vars['residents'][-1]=None
    spare.disabled=False;s.vm.vars['nextpoolauditat']=0
    s.vm.call('Service');assert s.vm.vars['repairrequested']
    e.tick(s);assert spare in e.residents(s)
    out('Periodic consistency census requests unchanged reconciliation for an untracked enabled actor')
    e,s=env('SkaalVillage');e.skaal_stage=10;e.tick(s)
    assert not e.enabled(s) and s.vm.vars['diagreason']==32
    e.skaal_stage=70;e.tick(s);fill(e,s)
    out('Skaal quest availability gate preserved')

def workload():
    for version in ['1.2.1','1.2.2']:
        e=m.Env(42,version=version);e.set_time(40,11);e.place_player(e.rural,[0,0,0])
        # Comparable enabled population (53 with this seed), no arrival RNG drift.
        for s in e.cities.values():
            assert s.vm.call('EnsureSetup')
            s.vm.vars['dailypopulation']=s.maximum;s.vm.vars['todaycycle']=40
            e.place_player(s.inn)
            for slot in range(s.maximum):s.vm.call('TryArrival',slot,40)
            assert len(e.enabled(s))==s.maximum,(version,s.name,len(e.enabled(s)),s.maximum,s.vm.vars['diagreason'])
        work={}
        for fn in ['EnabledCount','FullEnabledCount','PublishSnapshot','ShowStatus']:
            if fn.lower() not in next(iter(e.cities.values())).vm.obj['functions']:continue
            start=sum(s.vm.executed for s in e.cities.values());e.native_calls.clear()
            for s in e.cities.values():s.vm.call(fn)
            work[fn]={'opcodes':sum(s.vm.executed for s in e.cities.values())-start,'native_calls':dict(e.native_calls)}
        metrics[version]=work
    assert metrics['1.2.1']['EnabledCount']['native_calls']['isdisabled']==15200
    assert metrics['1.2.2']['EnabledCount']['native_calls']['isdisabled']==76
    out('Routine count uses at most76 tracked checks instead of15200 potential references',metrics)

if __name__=='__main__':
    structure();arrival_tests();pending_upgrades();mapping_and_upgrades();lifecycle_and_faults();workload()
    (R/'validation.json').write_text(json.dumps({'status':'PASS','checks':results,'workload':metrics,'Skyrim_executed':False,'ESS_files_tested':False,'limitations':'Actual compiled PEX executed in a fault-aware Python interpreter with actual ESP bindings. Native calls, clocks, event delivery, loading, camera geometry and AI movement are mocks.'},indent=2)+'\n')
    print('PASS: v1.2.2 focused verification complete; Skyrim runtime remains untested.',flush=True)
