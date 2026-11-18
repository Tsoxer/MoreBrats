from pathlib import Path
import datetime,hashlib,json,re,zipfile
W=Path('work');R=W/'build/v1.2.6';RT=R/'runtime';D=W/'delivery_v126'
# The current clock was independently checked immediately before packaging.
date="11-18-2026"
assert date==(R/'publication-date.txt').read_text().strip()
v=json.loads((R/'validation.json').read_text());assert v['status']=='PASS' and len(v['checks'])==16
expected={'MoreBrats.esp','Seq/MoreBrats.seq','README.txt','CHANGELOG.txt'}|{'Scripts/'+p.name for p in (W/'build/v1.2.5/runtime/Scripts').glob('*.pex')}
files={p.relative_to(RT).as_posix():p for p in RT.rglob('*') if p.is_file()};assert set(files)==expected and len(files)==13
for p in [RT/'README.txt',RT/'CHANGELOG.txt']:
 assert date in p.read_text()
assert (RT/'CHANGELOG.txt').read_bytes().startswith((W/'build/v1.2.5/runtime/CHANGELOG.txt').read_bytes())
for n,h in json.loads((W/'release_v126/protected-baselines.json').read_text()).items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h,n
out=R/'playtest';out.mkdir(exist_ok=True);archive=out/'MoreBrats-v1.2.6.zip';assert not archive.exists()
stamp=datetime.datetime.strptime(date,'%m-%d-%Y')
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for name,p in sorted(files.items()):
  i=zipfile.ZipInfo(name,(stamp.year,stamp.month,stamp.day,12,0,0));i.external_attr=0o100644<<16;i.compress_type=zipfile.ZIP_DEFLATED;z.writestr(i,p.read_bytes(),compresslevel=9)
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for name,p in files.items():assert z.read(name)==p.read_bytes()
sha=hashlib.sha256(archive.read_bytes()).hexdigest();Path(str(archive)+'.sha256').write_text(sha+'  '+archive.name+'\n')
report={'version':'v1.2.6','build':1206,'date':date,'zip':archive.name,'bytes':archive.stat().st_size,'sha256':sha,'members':13,'CRC':'PASS','files':{n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in files.items()},'settlements':19,'appearance_donors':40,'variants':200,'preserved_record_identities':19942,'changed_records':'58 diagnostic build globals; header description; other record payloads unchanged','changed_scripts':4,'identical_helper_PEX':5,'SEQ_byte_identical':True,'old_serialized_fields_properties_defaults_unchanged':True,'new_fields':'one load-check bool, three diagnostic float timestamps','schemas':'6/7 unchanged','Papyrus_estimate':'Moderate; code-based, not measured in Skyrim','Skyrim_executed':False,'ESS_files_tested':False,'automated_check_groups':16,'root_cause_limit':'Redundant scan costs and healthy-load full-audit requests demonstrated in compiled PEX; exact share of reported in-game latency is not proven.'}
(R/'INTEGRITY-v1.2.6.json').write_text(json.dumps(report,indent=2)+'\n')
(R/'VALIDATION-v1.2.6.json').write_text(json.dumps(v,indent=2)+'\n')
notes='''More Brats v1.2.6 — unpublished arrival-latency playtest
Author: Tsoxer
Build date: '''+date+'''

Direct continuation of final v1.2.5 (3–7 in-game-minute revision).

Confirmed code findings:
- A warm first arrival used210 IsDisabled calls, including a 200-variant scan
  after the deadline had already expired. Comparable v126 path uses11.
- Healthy loads requested full repair for every initialized controller. A
  controlled empty-save case used15,200 checks inv125 and0 inv126. Missing or
  unsafe state still gets the full census; first initialization can take longer.
- A periodic full census also ran ahead of pending arrivals. It now waits for
  the gradual sequence to finish; explicit recovery still runs before arrivals.
- Same-cycle daytime city departure does not itself delete the old residents.
- These are actual PEX/native-boundary call counts, not Skyrim latency results.
  They support avoidable pre-enable work as a delay mechanism. They do not
  establish one exact engine cause for every reported30–60-minute delay.

Changes: four existing controller sources/PEX, version globals/description,
README/changelog, build/verification utilities. No new scripts or polling cadence.
One additive load-check flag and three diagnostic timestamp fields; all previous
serialized names/types/defaults, schemas, properties, indices and IDs remain.
Five helper PEX and SEQ are byte-identical. All NPC/ref/PACK/QUST/VMAD payloads
remain unchanged.40 donors,200 variants,19 populations and night rules retained.

Tests:16 compiled-code/structural groups, all19 outdoor callbacks and movement,
15,200 appearance mappings, city hops, repeat visits,57 typed upgrade transfers
fromv110/v121/v125, failed enabling, incomplete-state adoption, watched03 safety,
periodic and explicit recovery. Native events, clocks, serialization and paths
are models. No Skyrim/ESS execution or in-game benchmark was performed.

Papyrus: Moderate estimate. At most76 routine enabled checks across maximum
tracked populations. Cold initialization and exceptional recovery remain heavy
operations. No measured zero-lag or exact3–7-minute activation guarantee.

Manual test: back up your save; replace the preceding build and let all included
PEX files win. Keep one MoreBrats.esp enabled. Arrive during8 AM–7 PM, walk/run
outdoors through Whiterun→Riften→Windhelm, then Solitude/Markarth and open-world
settlements. Observe staggered3–7 IN-GAME MINUTE arrivals, counts, roaming and
return visits. Test saving/loading mid-sequence, waiting across8 AM,19:00 inn
routines and unchanged safe post03:00 removal. Do not use quest resets or cleaning.
Optional named settlement debug requests display1206 and distinct due/attempt/
confirmed-enabled game-day timestamps. Zero means that event is not recorded.

v1.1.0 and every earlier download remain untouched. No Nexus publication.
'''
for a,b in [('used210','used 210'),('uses11','uses 11'),('used15,200','used 15,200'),('and0','and 0'),('inv125','in v1.2.5'),('inv126','in v1.2.6'),('reported30','reported 30'),('remain.40','remain. 40'),('donors,200','donors, 200'),('variants,19','variants, 19'),('Tests:16','Tests: 16'),('all19','all 19'),('transfers\nfromv110/v121/v125','transfers\nfrom v1.1.0/v1.2.1/v1.2.5'),('most76','most 76'),('exact3','exact 3'),('during8','during 8'),('across8','across 8'),('AM,19','AM, 19'),('display1206','display 1206')]:notes=notes.replace(a,b)
(R/'REVIEW-v1.2.6.txt').write_text(notes)
print(json.dumps({k:report[k] for k in ['version','date','zip','bytes','sha256','members']},indent=2))
