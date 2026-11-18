"""Focused faults and RNG analysis on actual PEX, using mock engine calls."""
from pathlib import Path
import json,collections,math,hashlib
ns={};text=Path('work/release_v110/test_release.py').read_text()
exec(text[:text.index("e=mod.Env(77,version='1.1.0')")],ns)
mod=ns['mod'];R=ns['R'];RT=ns['RT'];Pex=ns['Pex']
faults=[]
for name in ['Whiterun','Markarth','Morthal','Riverwood']:
 for prop in ['ImperialRefs','BretonRefs','RedguardRefs']:
  e=mod.Env(41,version='1.1.0');s=e.cities[name];e.set_time(20,11);e.place_player(s.inn)
  s.vm.property(prop,None)
  backing=s.vm.obj['properties'][prop.lower()][1]
  s.vm.deny_allocations.add(backing)
  assert not s.vm.call('EnsureSetup')
  assert not e.enabled(s) and not s.vm.vars['diagstorageready'] and s.vm.vars['diagreason']==30
  assert s.vm.vars['schemaversion']==0
  s.vm.deny_allocations.clear();s.vm.array_errors.clear()
  e.tick(s);assert s.cfg['minimum']<=len(e.enabled(s))<=s.maximum
  assert s.vm.call('AppearancePoolSize')==s.maximum*40
  faults.append([name,prop,'allocation failure then stable-ID recovery'])
e=mod.Env(41,version='1.1.0');s=e.cities['Whiterun'];e.set_time(20,11);e.place_player(s.inn)
# A missing added actor defers/falls back only within its slot's appearance
# selection. Other valid references remain available under the old mechanism.
bad=s.bindings['ImperialRefs'][0]['form'];s.vm.property('ImperialRefs',[None]*60);e.forms.pop(bad)
e.tick(s);assert s.cfg['minimum']<=len(e.enabled(s))<=s.maximum and s.vm.vars['bindingspending']
assert s.vm.vars['diagresolved']==239
faults.append(['Whiterun','one missing added actor','other valid children activate; binding remains pending'])
e=mod.Env(41,version='1.1.0');s=e.cities['SkaalVillage'];e.set_time(20,11);e.skaal_stage=0;e.tick(s)
assert not e.enabled(s) and s.vm.vars['diagreason']==32
e.skaal_stage=70;e.tick(s);assert 1<=len(e.enabled(s))<=3
faults.append(['SkaalVillage','quest availability','same stage70 gate retained'])
# Inspect actual CALLSTATIC operands: separate inclusive RNG draws, no location
# conditioned race weights or city-specific substitutions.
for name in ['MB_Controller','MB_CityController','MB_TownController','MB_VillageController']:
 p=Pex(RT/'Scripts'/f'{name}.pex');f=p.obj['functions']['tryarrival'];draws=[]
 for op,a,va in f['ins']:
  if op==25 and a[0][1].lower()=='utility' and a[1][1].lower()=='randomint':draws.append(tuple(x[1] for x in va))
 assert draws[:3]==[(1,4),(1,2),(0,4)],(name,draws)
j=json.loads((R/'validation.json').read_text());freq=collections.Counter()
for c in j['frequencies'].values():freq.update({int(k):v for k,v in c.items()})
N=sum(freq.values());groups=[collections.Counter() for _ in range(3)];pairs=[collections.Counter() for _ in range(3)]
for v,n in freq.items():
 q=v%10;g=q//3 if q<6 else (q-6)//2;o=q%3 if q<6 else 3+(q-6)%2;race=v//10
 for c,key in zip(groups,[race,g,o]):c[key]+=n
 for c,key in zip(pairs,[(race,g),(race,o),(g,o)]):c[key]+=n
chi_uniform=[sum((n-N/len(c))**2/(N/len(c)) for n in c.values()) for c in groups]
assert all(x<20 for x in chi_uniform)
chi_pairs=[]
for pair,(a,b) in zip(pairs,[(0,1),(0,2),(1,2)]):
 x=0.
 for k,n in pair.items():
  expected=groups[a][k[0]]*groups[b][k[1]]/N;x+=(n-expected)**2/expected
 chi_pairs.append(x)
assert all(x<50 for x in chi_pairs)
result=dict(status='PASS',mock_faults=faults,actual_PEX_RNG_bounds=[[1,4],[1,2],[0,4]],
            theoretical_probabilities={'race':0.25,'gender':0.5,'outfit':0.2,'each_combination':0.025},
            mock_sample_size=N,mock_counts={n:dict(c) for n,c in zip(['race','gender','outfit'],groups)},
            uniformity_chi_square=chi_uniform,pairwise_independence_chi_square=chi_pairs,
            all40_sampled=True,Skyrim_executed=False,scope='Native RNG, references, loading, placement and events are mocked; counts are not a Skyrim runtime test.')
(R/'focused-validation.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS: typed allocation failures/recovery, individual missing actor, Skaal gate, independent PEX RNG bounds and sample analysis.')
