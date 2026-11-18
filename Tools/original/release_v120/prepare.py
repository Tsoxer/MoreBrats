"""Extend the retained v1.1.0 sources; never edit the released baseline."""
from pathlib import Path
import json,shutil,re
ROOT=Path(__file__).resolve().parent
WORK=ROOT.parent;BUILD=WORK/'build/v1.2.0';SRC=WORK/'v1.2.0/src'
BUILD.mkdir(parents=True,exist_ok=True);SRC.mkdir(parents=True,exist_ok=True)
(ROOT/'Config').mkdir(exist_ok=True)
roster=json.loads((ROOT/'Config/verified-candidates.json').read_text())
legacy=[['Lars Battle-Born','Dorthe'],['Francois Beaufort','Mila Valentia'],['Blaise','Erith'],['Alesan','Braith']]
races=['Nord','Imperial','Breton','Redguard'];extra=[];groups=[]
excluded={'Babette':'Vampire child/assassin: Traits/Stats/SpellList/Keywords inheritance would not preserve a normal Breton child.',
          'Helgi':'Ghost child: the existing Traits/SpellList/Keywords inheritance cannot isolate a normal living appearance from special ghost data. No special-case stripping or replacement assets are introduced.'}
for r in roster:
 r['accepted']=r['name'] not in excluded
 if not r['accepted']:r['exclusion_reason']=excluded[r['name']]
for ri,race in enumerate(races):
 for gi,gender in enumerate(['Male','Female']):
  rows=[r for r in roster if r['accepted'] and r['Race']==race and r['Gender']==gender]
  old=next(r for r in rows if r['name']==legacy[ri][gi]);others=[r for r in rows if r is not old]
  g=dict(race=ri+1,gender=gi,legacy=old['name'],count=len(rows),additional=[])
  for r in others:
   r['appended_donor_index']=len(extra);r['first_variant']=40+len(extra)*5
   extra.append(r);g['additional'].append(r['first_variant'])
  groups.append(g)
assert len(extra)==32 and sum(r['accepted'] for r in roster)==40
data=dict(version='1.2.0',status='unreleased development',races=races,legacy_donors=legacy,groups=groups,additional_donors=extra,candidates=roster,
          legacy_variant_count=40,variant_count=200,outfits=['red','green','blue','grey','yellow'])
(ROOT/'Config/appearance-roster.json').write_text(json.dumps(data,indent=2)+'\n')
shutil.copyfile(WORK/'build/v1.1.0/settlements.json',BUILD/'settlements.json')
shutil.copyfile(WORK/'build/v1.1.0/settlements.json',ROOT/'Config/settlements.json')
shutil.copyfile(WORK/'release_v110/PluginBuilder/PluginBuilder.csproj',ROOT/'PluginBuilder/PluginBuilder.csproj')
def edit_function(text,name,edit):
 pattern=re.compile(r'(?m)^(?:(?:Bool|Int|Float|Actor|String) )?Function '+name+r'\([^\n]*\)\n.*?^EndFunction',re.S|re.M)
 found=pattern.search(text);assert found,name
 return text[:found.start()]+edit(found.group())+text[found.end():]
for p in (WORK/'v1.1.0/src').glob('MB_*.psc'):
 text=p.read_text()
 if 'Controller' not in p.stem:
  shutil.copyfile(p,SRC/p.name);continue
 whiterun=p.stem=='MB_Controller'
 cap='6' if whiterun else 'MaxPopulation'
 legacy_size='240' if whiterun else '(MaxPopulation * 40)'
 extra_size=f'({cap} * 160)'
 maxcap={'MB_Controller':6,'MB_CityController':9,'MB_TownController':5,'MB_VillageController':4}[p.stem]
 pages=(maxcap*160+127)//128
 rootid='0x108000' if whiterun else '(0x100000 + ConfigBase * 16)'
 text=text.replace('v1.1.0','v1.2.0').replace('1100.0','1200.0')
 # Preserve all old properties/variables; add only append-only cosmetic storage.
 at='Actor[] Property RedguardRefs Auto'
 declarations='\n; v1.2.0: appended donor references; old arrays/indices are unchanged.\nFormList Property NamedDonorForms Auto\n'
 declarations+='\n'.join(f'Actor[] donorActors{i}\nInt[] donorHidden{i}' for i in range(pages))+'\n'
 text=text.replace(at,at+declarations)
 text=edit_function(text,'PoolIndex',lambda f:f.replace('\n    If variant >= 10',f'\n    If variant >= 40\n        Return {legacy_size} + (variant - 40) * {cap} + slot\n    EndIf\n    If variant >= 10',1))
 text=edit_function(text,'SlotFromPoolIndex',lambda f:f.replace('\n    If index >= ',f'\n    If index >= {legacy_size}\n        Return (index - {legacy_size}) % {cap}\n    EndIf\n    If index >= ',1))
 text=edit_function(text,'PoolSlotDisabled',lambda f:f.replace('v < 40','v < 200'))
 text=edit_function(text,'Reconcile',lambda f:f.replace('variant < 40','variant < 200'))
 def arrival(f):
  line='        selectedVariant[s] += (race - 1) * 10'
  assert line in f
  return f.replace(line,line+'\n        selectedVariant[s] = SelectDonorVariant(race, gender, clothing, selectedVariant[s])').replace('RandomInt(0, 39)','RandomInt(0, 199)').replace('v < 40','v < 200').replace('% 40','% 200')
 text=edit_function(text,'TryArrival',arrival)
 text=edit_function(text,'AppearancePoolSize',lambda f:f.replace('Return 60 * 4',f'Return {legacy_size} + {extra_size}').replace('Return (MaxPopulation * 10) * 4',f'Return {legacy_size} + {extra_size}'))
 def poolactor(f):
  needle='    Int group = index / '
  pos=f.index(needle)
  return f[:pos]+f'    If index >= {legacy_size}\n        Return DonorActorRead(index - {legacy_size})\n    EndIf\n'+f[pos:]
 text=edit_function(text,'PoolActor',poolactor)
 for name in ['OrphanSamples','StoreOrphanSamples']:
  def fn(f):
   pos=f.index('    Int group = index / ')
   action=f'Return DonorHiddenRead(index - {legacy_size})' if name=='OrphanSamples' else f'DonorHiddenWrite(index - {legacy_size}, samples)\n        Return'
   return f[:pos]+f'    If index >= {legacy_size}\n        {action}\n    EndIf\n'+f[pos:]
  text=edit_function(text,name,fn)
 text=edit_function(text,'EnsureAppearanceStorage',lambda f:f.rsplit('    Return True',1)[0]+'    Return EnsureNamedDonorStorage()\nEndFunction')
 def resolve(f):
  insertion=f'''    Int namedIndex = 0
    While namedIndex < {extra_size}
        Actor namedActor = NamedDonorForms.GetAt(namedIndex) as Actor
        DonorActorWrite(namedIndex, namedActor)
        If DonorActorRead(namedIndex) != namedActor
            StorageFailure("named donor binding readback", {extra_size}, 31)
            Return False
        EndIf
        If namedActor != None
            diagResolved += 1
            diagPoolInputs += 1
        Else
            bindingsPending = True
        EndIf
        namedIndex += 1
    EndWhile
'''
  pos=f.rindex('    Return True');return f[:pos]+insertion+f[pos:]
 text=edit_function(text,'ResolveAppearancePools',resolve)
 if whiterun:text=text.replace('/240', '/1200')
 select=['; Independent donor draw inside the already selected race/gender.','Int Function SelectDonorVariant(Int race, Int gender, Int clothing, Int legacyVariant)']
 for g in groups:
  if not g['additional']:continue
  select += [f'    If race == {g["race"]} && gender == {g["gender"]}',f'        Int donor{g["race"]}{g["gender"]} = Utility.RandomInt(0, {g["count"]-1})',f'        If donor{g["race"]}{g["gender"]} > 0',f'            Return {g["additional"][0]} + (donor{g["race"]}{g["gender"]} - 1) * 5 + clothing','        EndIf','        Return legacyVariant','    EndIf']
 select+=['    Return legacyVariant','EndFunction']
 storage=['Bool Function EnsureNamedDonorStorage()',f'    If NamedDonorForms == None\n        NamedDonorForms = Game.GetFormFromFile({rootid} + 0x1000, "MoreBrats.esp") as FormList\n    EndIf',f'    If NamedDonorForms == None\n        StorageFailure("NamedDonorForms", {extra_size}, 31)\n        Return False\n    EndIf',f'    If NamedDonorForms.GetSize() != {extra_size}\n        StorageFailure("NamedDonorForms size", {extra_size}, 31)\n        Return False\n    EndIf']
 for i in range(pages):
  length=min(128,maxcap*160-i*128)
  storage += [f'    If !donorActors{i}',f'        donorActors{i} = new Actor[{length}]',f'        If !donorActors{i} || donorActors{i}.Length != {length}',f'            StorageFailure("donorActors{i}", {length})','            Return False','        EndIf','        repairRequested = True','    EndIf']
  storage += [f'    If !donorHidden{i}',f'        donorHidden{i} = new Int[{length}]',f'        If !donorHidden{i} || donorHidden{i}.Length != {length}',f'            StorageFailure("donorHidden{i}", {length})','            Return False','        EndIf','        repairRequested = True','    EndIf']
 storage += ['    Return True','EndFunction']
 read=['Int Function DonorHiddenRead(Int index)','    Int page = index / 128','    Int localIndex = index % 128']
 write=['Function DonorHiddenWrite(Int index, Int samples)','    Int page = index / 128','    Int localIndex = index % 128']
 for i in range(pages):
  read += [('    If ' if i==0 else '    ElseIf ')+f'page == {i}',f'        Return donorHidden{i}[localIndex]']
  write += [('    If ' if i==0 else '    ElseIf ')+f'page == {i}',f'        donorHidden{i}[localIndex] = samples']
 read+=['    EndIf','    Return 0','EndFunction'];write+=['    EndIf','EndFunction']
 actorread=['Actor Function DonorActorRead(Int index)','    Int page = index / 128','    Int localIndex = index % 128']
 actorwrite=['Function DonorActorWrite(Int index, Actor child)','    Int page = index / 128','    Int localIndex = index % 128']
 for i in range(pages):
  actorread += [('    If ' if i==0 else '    ElseIf ')+f'page == {i}',f'        Return donorActors{i}[localIndex]']
  actorwrite += [('    If ' if i==0 else '    ElseIf ')+f'page == {i}',f'        donorActors{i}[localIndex] = child']
 actorread += ['    EndIf','    Return None','EndFunction'];actorwrite+=['    EndIf','EndFunction']
 text+='\n\n'+'\n'.join(select)+'\n\n'+'\n'.join(storage)+'\n\n'+'\n'.join(read)+'\n\n'+'\n'.join(write)+'\n\n'+'\n'.join(actorread)+'\n\n'+'\n'.join(actorwrite)+'\n'
 (SRC/p.name).write_text(text)
print('Prepared direct v1.1.0 derivatives; 40 donors, 200 variants; no release artifacts touched.')
