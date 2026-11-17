"""Actual compiled PEX + actual VMAD/PACK data; synthetic natives/geometry ONLY."""
from dataclasses import dataclass
from pathlib import Path
from collections import Counter
import math,random,struct,json
from array_vm import VM,Pex,f32
from esplib import Plugin
from vmad_reader import quest_vmad
@dataclass(eq=False)
class Cell:
 name:str
 interior:bool
 attached:bool=True
@dataclass(eq=False)
class Ref:
 name:str
 cell:Cell
 world:object
 xyz:list
 actor:bool=False
 disabled:bool=False
 loaded:bool=False
 rank:int=-1
 package:object=None
 pending:bool=False
@dataclass(eq=False)
class Global:
 value:float=0.
@dataclass(eq=False)
class FormList:
 values:list
R=Path('work/build/v0.5.1');ROOT=R/'runtime'
TOWNS=json.loads(Path('work/research/v041/towns.json').read_text())
CITIES=json.loads(Path('work/research/v030/cities.json').read_text())
VILLAGES=json.loads(Path('work/research/v050/settlements.json').read_text())
SETS={}
def files(version):
 if version not in SETS:
  path=Path('work/build/v0.5.1/runtime') if version=='0.5.1' else Path('work/v'+version+'/runtime')
  plug=Plugin(path/'MoreBrats.esp');recs={int(r.form_id):r for t in ['GLOB','FACT','NPC_','CELL','ACHR','REFR','PACK','QUST','FLST'] for r in plug.get_records_by_signature(t)}
  SETS[version]=(path,recs,{k:r for k,r in recs.items() if r.signature=='PACK'},len(plug.header.masters)*0x1000000)
 return SETS[version]
def fid(r,t):return struct.unpack('<I',r.get_subrecord(t).data)[0]
def ids(r,t):return [struct.unpack('<I',s.data)[0] for s in r.get_subrecords(t)]
@dataclass(eq=False)
class Location:
 name:str
 parent:object=None
class State:
 pass
class Env:
 def __init__(self,seed=64,version="0.5.1"):
  self.version=version;self.rootpath,self.records,self.packs,self.self_prefix=files(version)
  self.city_pex=Pex(self.rootpath/'Scripts/MB_CityController.pex');self.city_alias=Pex(self.rootpath/'Scripts/MB_CityAlias.pex')
  self.town_pex=Pex(self.rootpath/'Scripts/MB_TownController.pex');self.town_alias=Pex(self.rootpath/'Scripts/MB_TownAlias.pex')
  self.white_pex=Pex(self.rootpath/'Scripts/MB_Controller.pex');self.white_alias=Pex(self.rootpath/'Scripts/MB_PlayerAlias.pex')
  self.village_pex=Pex(self.rootpath/'Scripts/MB_VillageController.pex') if version!='0.4.1' else None
  self.village_alias=Pex(self.rootpath/'Scripts/MB_VillageAlias.pex') if version!='0.4.1' else None
  self.towns=TOWNS;self.native_hook=None;self.availability=object();self.skaal_stage=70
  self.rng=random.Random(seed);self.now=f32(0);self.real=1000.;self.logs=[];self.rng_calls=[];self.native_calls=Counter();self.rt={};self.gt={};self.visible=set();self.forms={};self.owners={};self.byid={};self.cities={};self.running={};self.world_drop_ids=set();self.pending=[];self.move_hook=None
  self.worlds={};self.tamriel=object();self.worlds[0x3c]=self.tamriel;self.keep_parent=False
  self.storage=Cell('Storage',True);self.storage.world=None;self.storage.location=None
  self.outside=Cell('Other world',False);self.outside.world=object();self.outside.location=None
  self.rural=Cell('SYNTHETIC distant Tamriel field',False);self.rural.world=self.tamriel;self.rural.location=Location('Hold countryside')
  self.player=Ref('Player',self.outside,self.outside.world,[0.,0.,0.],True,False,True)
  wb=quest_vmad(self.records[self.self_prefix+0x800])[0]['MB_Controller']
  cfgs=[dict(name='Whiterun',base=0x800,minimum=3,maximum=6,world=wb['CityWorld']['form'],location=0x18A56,inn='Bannered Mare',inn_cell=wb['TavernCell']['form'],inn_point=wb['TavernPoint']['form'])]+CITIES+self.towns+([dict(c,**{f:c[f]+(0x2000000 if c['master']=='Dragonborn.esm' else 0) for f in ['world','location','inn_cell','inn_point']}) for c in VILLAGES] if version!='0.4.1' else [])
  for cfg in cfgs:
   s=State();s.cfg=cfg;s.name=cfg['name'];s.maximum=cfg['maximum'];s.whiterun=s.name=='Whiterun';s.village=cfg['base']>=0x9000;s.town=cfg['world']==0x3c or s.village;s.root=self.self_prefix+cfg['base'];s.world=self.worlds.setdefault(cfg['world'],object());s.location=Location(s.name);s.inn=Cell(cfg['inn'],True);s.inn.world=None;s.inn.location=Location(s.name+' inn',Location(s.name+' district',s.location));s.shop=Cell(s.name+' public shop',True);s.shop.world=None;s.shop.location=Location(s.name+' shop',s.location)
   script,aliases=quest_vmad(self.records[s.root]);s.bindings=script['MB_Controller' if s.whiterun else 'MB_VillageController' if s.village else 'MB_TownController' if s.town else 'MB_CityController']
   roads=[a['form'] for a in s.bindings['RoadRefs']];pool=[a['form'] for a in s.bindings['PoolRefs']]
   s.cells=[];s.roads=[];s.pool=[];s.packages=[]
   self.forms[cfg['world']]=s.world;self.forms[cfg['location']]=s.location;self.forms[cfg['inn_cell']]=s.inn
   for i,key in enumerate(roads):
    cell=Cell(f'{s.name} SYNTHETIC road{i}',False);cell.world=s.world;cell.location=s.location;s.cells.append(cell)
    z=float((i%4)*250 if s.name=='Markarth' else 0)
    origin=50000.+(cfg['base']//0x1000-5)*50000. if s.town else 0.
    xyz=[origin+float(i%3*1100),50000.+float(i//3*1300),0.] if s.town else [float(i%6*1600),float(i//6*1800),z]
    ref=Ref(f'{s.name} Road{i}',cell,s.world,xyz);s.roads.append(ref);self.forms[key]=ref;self.byid[key]=ref
   for i,key in enumerate(pool):
    ref=Ref(f'{s.name} Actor{i}',self.storage,None,[0.,0.,0.],True,True);s.pool.append(ref);self.forms[key]=ref;self.byid[key]=ref;self.owners[ref]=s
    npc=self.records[fid(self.records[key],'NAME')];s.packages.append(ids(npc,'PKID'))
   s.tavern=self.forms.get(cfg['inn_point'])
   if s.tavern is None:
    s.tavern=Ref(cfg['inn'],s.inn,None,[500.,500.,0.]);self.forms[cfg['inn_point']]=s.tavern;self.byid[cfg['inn_point']]=s.tavern
   if s.name=='Dawnstar':
    s.tavern.cell=s.cells[1];s.tavern.world=s.world;s.tavern.xyz=s.roads[1].xyz[:]
   # Resolve every VMAD binding through an explicit map built from ESP records.
   for key in [s.bindings[k]['form'] for k in ['NightMode','DayArea','RoamFaction','PoolForms','RoadForms']]+[a['form'] for a in s.bindings['DiagnosticGlobals']]:
    rec=self.records[key]
    if rec.signature=='GLOB':obj=Global(struct.unpack('<f',rec.get_subrecord('FLTV').data)[0])
    elif rec.signature=='FACT':obj=object()
    elif rec.signature=='FLST':obj=FormList([self.forms[f] for f in ids(rec,'LNAM')])
    self.forms[key]=obj
   if s.whiterun:
    for key in [a['form'] for a in s.bindings['TargetRefs']]:
     self.forms[key]=Ref('legacy '+hex(key),self.storage,None,[0.,0.,0.]);self.byid[key]=self.forms[key]
    self.forms[s.bindings['TargetForms']['form']]=FormList([self.forms[a['form']] for a in s.bindings['TargetRefs']])
    for i,a in enumerate(s.bindings['ArrivalPoints']):self.forms[a['form']]=s.roads[[0,7,13][i]]
   s.pex=self.white_pex if s.whiterun else self.village_pex if s.village else self.town_pex if s.town else self.city_pex;s.vm=VM(s.pex,self.native);s.alias=VM(self.white_alias if s.whiterun else self.village_alias if s.village else self.town_alias if s.town else self.city_alias,self.native)
   self.owners[s.vm]=s;self.owners[s.alias]=s;self.forms[s.root]=s.vm;self.running[s.vm]=True
   for k,v in s.bindings.items():
    value=self.forms.get(v['form']) if isinstance(v,dict) else [self.forms[a['form']] for a in v] if isinstance(v,list) and v and isinstance(v[0],dict) else v
    s.vm.property(k,value)
   s.alias.property('Controller',s.vm)
   s.night=self.forms[s.bindings['NightMode']['form']];s.faction=self.forms[s.bindings['RoamFaction']['form']];s.diagnostics=[self.forms[a['form']] for a in s.bindings['DiagnosticGlobals']]
   self.cities[s.name]=s
  self.forms[0x2017f90]=self.availability
  if 'SkaalVillage' in self.cities:self.cities['SkaalVillage'].vm.property('AvailabilityQuest',self.availability)
  self.forms.update(self.packs)
  self.refresh()
 def set_time(self,day,hour):self.now=f32(day+hour/24.)
 def place_player(self,cell,xyz=None):
  self.player.cell=cell;self.player.world=cell.world
  if xyz is not None:self.player.xyz=list(xyz)
  self.refresh()
 def refresh(self):
  # Synthetic loading grid. Towns share one world but only nearby cells attach.
  for s in self.cities.values():
   if s.town:
    for road in s.roads:road.cell.attached=self.player.world is s.world and not self.player.cell.interior and math.dist(self.player.xyz,road.xyz)<6000.
   for c in s.pool:c.loaded=not c.disabled and (c.cell is self.player.cell or (not self.player.cell.interior and c.world is self.player.world and c.cell.attached))
 def enabled(self,s):return [c for c in s.pool if not c.disabled]
 def residents(self,s):return s.vm.vars.get('residents') or [None]*s.maximum
 def tick(self,s):s.vm.call('OnUpdate');self.check(s)
 def tick_all(self):
  for s in self.cities.values():self.tick(s)
 def check(self,s):
  assert not s.vm.array_errors,(s.name,s.vm.array_errors)
  assert len(self.enabled(s))<=s.maximum
  residents=[c for c in self.residents(s) if c is not None]
  assert len(residents)==len(set(residents)),(s.name,'duplicate residents')
  assert set(self.enabled(s))<=set(residents),(s.name,'orphan')
  assert not s.vm.vars['processing']
  for slot,c in enumerate(self.residents(s)):
   if c is not None:
    phase=s.vm.vars['phase'][slot];goal=s.vm.vars['destination'][slot]
    assert c.rank==(24 if phase==0 else slot*4+3 if phase==3 else 32+goal*4+phase)
 def save_load(self,s):
  old=s.vm;new=VM(s.pex,self.native);new.vars=old.vars.copy();s.vm=new;self.forms[s.root]=new;self.owners[new]=s;self.running[new]=True;s.alias.property('Controller',new);s.alias.call('OnPlayerLoadGame')
 def variant(self,s,c):
  base=fid(self.records[next(k for k,v in self.byid.items() if v is c)],'NAME')
  if not s.whiterun:return (base&0xffffff)-(s.cfg['base']+0x80)
  return ((base&0xffffff)-0x808)//2 if (base&0xffffff)<0x88C else 6+(base&0xffffff)-0x88C
 def visible_to_player(self,c):return c in self.visible and c.loaded and not c.disabled
 def package_for(self,c):
  s=self.owners[c];index=s.pool.index(c)
  for key in s.packages[index]:
   pack=self.packs[key];schedule=pack.get_subrecord('PSDT').data;start=schedule[3];duration=struct.unpack_from('<I',schedule,8)[0];hour=(self.now-int(self.now))*24
   if start!=255 and (hour-start)%24>=duration/60:continue
   valid=True
   for cond in pack.get_subrecords('CTDA'):
    b=cond.data;op=b[0]>>5;expected=struct.unpack_from('<f',b,4)[0];fn=struct.unpack_from('<H',b,8)[0];param=struct.unpack_from('<I',b,12)[0]
    assert op==0
    if fn==73:actual=c.rank if self.forms[param] is s.faction else -1
    elif fn==67:actual=int(c.cell is self.forms[param])
    elif fn==74:actual=self.forms[param].value
    else:raise AssertionError(('condition',fn))
    valid &= actual==expected
   if valid:return pack
  raise AssertionError(('no eligible package',s.name,c.rank))
 def simulate_travel(self,s,minutes):
  for c in self.enabled(s):
   pack=self.package_for(c);_,template,_=struct.unpack('<III',pack.get_subrecord('PKCU').data)
   if template!=0x16FAA:continue
   _,target,radius=struct.unpack('<III',pack.get_subrecord('PLDT').data);goal=self.forms[target];dist=math.dist(c.xyz,goal.xyz);speed=260 if pack.get_subrecord('PKDT').data[6]==2 else 110;step=min(max(dist-radius,0),minutes*speed)
   if dist:c.xyz=[a+(b-a)*step/dist for a,b in zip(c.xyz,goal.xyz)]
   if step>=dist-radius:c.cell=goal.cell;c.world=goal.world
  self.refresh()
 def native(self,target,method,args):
  m=method.lower();self.native_calls[m]+=1
  if self.native_hook:self.native_hook(target,m,args)
  if target is self.availability:
   if m=='isstagedone':return self.skaal_stage>=args[0]
   if m=='iscompleted':return self.skaal_stage>=200
  if isinstance(target,VM):
   if m in target.obj['functions']:return target.call(method,*args)
   if m=='getowningquest':return self.owners[target].vm
   if m=='isrunning':return self.running.get(target,True)
   if m=='start':self.running[target]=True;return True
   if m=='unregisterforupdate':self.rt.pop(target,None);return
   if m=='unregisterforupdategametime':self.gt.pop(target,None);return
   if m=='registerforsingleupdate':assert args[0]>0;self.rt[target]=args[0];return
   if m=='registerforsingleupdategametime':assert .025<=args[0]<=24;self.gt[target]=args[0];return
  if isinstance(target,str):
   if target.lower()=='game':
    if m=='getplayer':return self.player
    if m=='getformfromfile':
     assert args[1] in ['Skyrim.esm','MoreBrats.esp','Dragonborn.esm'];key=({'MoreBrats.esp':self.self_prefix,'Skyrim.esm':0,'Dragonborn.esm':0x2000000}[args[1]])+args[0];return self.forms.get(key)
   if target.lower()=='utility':
    if m=='getcurrentgametime':return self.now
    if m=='getcurrentrealtime':return f32(self.real)
    if m=='randomint':
     value=self.rng.randint(*args);self.rng_calls.append((args,value));return value
    if m=='randomfloat':return f32(self.rng.uniform(*args))
   if target.lower()=='debug' and m in ['trace','messagebox','notification']:self.logs.append((m,args[0]));return
  if isinstance(target,Location):
   if m=='ischild':
    loc=args[0].parent
    while loc is not None:
     if loc is target:return True
     loc=loc.parent
    return False
  if isinstance(target,Cell):
   if m=='isinterior':return target.interior
   if m=='isattached':return target.attached
  if isinstance(target,FormList):
   if m=='getsize':return len(target.values)
   if m=='getat':return target.values[args[0]]
  if isinstance(target,Global):
   if m=='getvalue':return target.value
   if m=='setvalue':target.value=args[0];return
  if isinstance(target,Ref):
   if m=='getformid':return next(k for k,v in self.byid.items() if v is target)
   if m=='getparentcell':return None if not self.keep_parent and not target.cell.interior and not target.cell.attached and target is not self.player else target.cell
   if m=='getworldspace':return None if target.name in self.world_drop_ids else target.world
   if m=='getcurrentlocation':return target.cell.location
   if m=='isdisabled':return target.disabled
   if m=='is3dloaded':return target.loaded
   if m=='isininterior':return target.cell.interior
   if m=='getdistance':
    b=args[0];same=(target.world is not None and target.world is b.world) or target.cell is b.cell
    return f32(math.dist(target.xyz,b.xyz)) if same else 1e9
   if m in ['getpositionx','getpositiony','getpositionz']:return f32(target.xyz[{'getpositionx':0,'getpositiony':1,'getpositionz':2}[m]])
   if m=='getfactionrank':assert args[0] is self.owners[target].faction;return target.rank
   if m=='setfactionrank':assert args[0] is self.owners[target].faction and 0<=args[1]<=127;target.rank=args[1];return
   if m=='haslos':return self.visible_to_player(args[0])
   if m=='moveto':
    assert not target.actor or target.disabled,'Enabled actor teleported'
    p=args[0];target.cell=p.cell;target.world=p.world;target.xyz=[f32(x+o) for x,o in zip(p.xyz,args[1:4])];self.logs.append(('move',target.name,self.now,p.name))
    if self.move_hook:self.move_hook(target,p)
    return
   if m=='enablenowait':
    s=self.owners[target];assert target.disabled,'duplicate enable';assert len(self.enabled(s))<s.maximum
    assert s.vm.call('SafeArrival',next(p for p in s.roads if p.cell is target.cell and p.xyz==target.xyz))
    target.disabled=False;self.logs.append(('enable',target.name,self.now));self.refresh();return
   if m=='disablenowait':
    assert not self.visible_to_player(target),'visible disappearance'
    target.disabled=True;target.loaded=False;self.logs.append(('disable',target.name,self.now));return
   if m=='getcurrentpackage':return self.package_for(target).editor_id
   if m=='evaluatepackage':target.package=self.package_for(target).editor_id;self.logs.append(('evaluate',target.name,self.now,target.package));return
  raise AssertionError(('unmocked native',type(target).__name__,method,args))

