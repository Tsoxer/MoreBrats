from pathlib import Path
import datetime,hashlib,json,re,zipfile
W=Path('work');R=W/'build/v1.2.7';RT=R/'runtime'
date="11-18-2026"
assert date==(R/'publication-date.txt').read_text().strip()
v=json.loads((R/'validation.json').read_text());assert v['status']=='PASS' and len(v['checks'])==17
assert any('Explicit Whiterun roll5' in x for x in v['checks'])
files={p.relative_to(RT).as_posix():p for p in RT.rglob('*') if p.is_file()}
expected={'MoreBrats.esp','Seq/MoreBrats.seq','README.txt','CHANGELOG.txt'}|{'Scripts/'+p.name for p in (W/'build/v1.2.6/runtime/Scripts').glob('*.pex')}
assert set(files)==expected and len(files)==13
assert files['CHANGELOG.txt'].read_bytes().startswith((W/'build/v1.2.6/runtime/CHANGELOG.txt').read_bytes())
for name in ['README.txt','CHANGELOG.txt']:
 s=files[name].read_text();assert date in s
for n,h in json.loads((W/'release_v127/protected-baselines.json').read_text()).items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h,n
out=R/'playtest';out.mkdir(exist_ok=True);zpath=out/'MoreBrats-v1.2.7.zip';assert not zpath.exists()
stamp=datetime.datetime.strptime(date,'%m-%d-%Y')
with zipfile.ZipFile(zpath,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n,p in sorted(files.items()):
  i=zipfile.ZipInfo(n,(stamp.year,stamp.month,stamp.day,12,0,0));i.external_attr=0o100644<<16;i.compress_type=zipfile.ZIP_DEFLATED;z.writestr(i,p.read_bytes(),compresslevel=9)
with zipfile.ZipFile(zpath) as z:
 assert z.testzip() is None
 for n,p in files.items():assert z.read(n)==p.read_bytes()
sha=hashlib.sha256(zpath.read_bytes()).hexdigest();Path(str(zpath)+'.sha256').write_text(sha+'  '+zpath.name+'\n')
report={'version':'v1.2.7','build':1207,'date':date,'zip':zpath.name,'bytes':zpath.stat().st_size,'sha256':sha,'members':13,'CRC':'PASS','files':{n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in files.items()},'settlements':19,'donors':40,'variants':200,'preserved_record_identities':19942,'changed_record_payloads':'58 build globals only; plugin description updated; no NPC/ACHR/PACK/QUST/VMAD changes','changed_PEX':4,'identical_helper_PEX':5,'SEQ_byte_identical':True,'old_saved_fields_properties_defaults_preserved':True,'new_serialized_fields':'interiorArrivalPending bool; interiorArrivalCycle int','routine_enabled_check_bound':76,'schemas':'6/7 unchanged','Papyrus_estimate':'Moderate, code-based; bounded additional identity/selection work per arrival and bounded interior fill','Skyrim_executed':False,'ESS_files_tested':False,'automated_check_groups':17,'legacy_active_duplicates':'Retained until normal departure; no new arrival adds to an occupied donor identity','interior_batch_limit':'Uses existing dailyPopulation/residents/lease, same as gradual arrivals; never a separate roll/cap'}
(R/'INTEGRITY-v1.2.7.json').write_text(json.dumps(report,indent=2)+'\n')
(R/'VALIDATION-v1.2.7.json').write_text(json.dumps(v,indent=2)+'\n')
notes=f'''More Brats v1.2.7 — two requested additions
Author: Tsoxer
Playtest build date: {date}

1. Distinct vanilla donor FormIDs within each settlement's active population.
   All five outfits for Braith are the same donor. Clothing repeats are fine.
   Whiterun and Riften can independently use the same three donors. No global
   donor blacklist is introduced. Derive identity from actual stable references,
   not daily selectedVariant bookkeeping. Handle signed high-load-order FormIDs.

2. Restore v1.1.0-style interior preparation at the original public street
   markers alongside unchanged v1.2.6 gradual door-area arrivals. Both methods
   use the SAME daily roll, resident array, reservations and serialized worker.
   Target five minus three already present permits only two more. Re-entering
   never rolls another population. Capture quick entry/exit for the deferred
   update. No duplicate manager or population is introduced.

Preserved: all 19 settlements, populations, FormIDs, 40 donors, 200 variants,
NPC/reference/AI/quest payloads, ordinary 3–7 IN-GAME MINUTE arrivals, 8 AM–7 PM
window, enhanced running, 7 PM interiors and safe post-3 AM retirement.
Four controller sources/PEX changed; five helper sources/PEX and SEQ identical.
All prior serialized fields/types/defaults/properties and schemas6/7 retained.
Added only two small interior-opportunity fields and temporary local donor masks.

Uniqueness selects another unused donor in the chosen race/gender group. If the
category is exhausted, another available group is chosen. Existing outfit color
is retained. Initial RNG remains unchanged; uniqueness necessarily conditions
which donor categories are still available. All40 donors remain eligible.

Existing older-save duplicates are not forcibly replaced, disabled or changed.
New arrivals do not increase them; normal retirement clears them. All residents,
quests and saved identities are retained. No new game/reset/save cleaning.

17 automated check groups passed: final ESP/PEX, all15,200 variant/reference
mappings and40 actual template IDs, all200 appearances, all19 dual-path caps,
quick transitions, post19:00 rejection, overlap while enabling, failed enabling,
original night lifecycle and19 typedv126 state upgrades. Explicit target5 case:
three gradual children plus two interior children totals exactly5, even with
an overlapping callback. Two cities can use the same donor concurrently.

These checks execute actual compiled instructions with modeled native calls,
clock/event delivery, loading, geometry, AI and save state. They do not execute
Skyrim or actual ESS files. Test the new build in Skyrim before public release.
Papyrus classification: Moderate (estimate). No extra polling cadence; routine
enabled counting stays76 maximum. Identity lookup adds at most8 other tracked
reference-ID reads per arrival. Interior fills are bounded by the existing cap.

Manual test: back up the save; replace the previous build. First stay outdoors
for gradual arrivals, then enter a normal settlement shop/inn with a partial
population and return outside. Observe the remaining population at original
street markers, inspect donor IDs, repeat entries, fast travel to another city,
and verify it can independently use those donors. Confirm the unchanged night
routine. Let older active duplicates finish their normal cycle when upgrading.

No Nexus publication. Stablev1.1.0 and previous downloads remain unchanged.
'''
for a,b in [('schemas6','schemas 6'),('All40','All 40'),('all15,200','all 15,200'),('and40','and 40'),('all200','all 200'),('all19','all 19'),('post19','post-19'),('and19 typedv126','and 19 typed v1.2.6'),('target5','target 5'),('exactly5','exactly 5'),('stays76','stays 76'),('most8','most 8'),('Stablev1','Stable v1')]:notes=notes.replace(a,b)
(R/'REVIEW-v1.2.7.txt').write_text(notes)
print(json.dumps({k:report[k] for k in ['zip','date','bytes','sha256','automated_check_groups']},indent=2))
