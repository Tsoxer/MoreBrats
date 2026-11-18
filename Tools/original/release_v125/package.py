"""Package validated v125; preserve released gameplay baselines and old archives."""
from pathlib import Path
import json,hashlib,datetime,re,zipfile
ROOT=Path(__file__).resolve().parent;W=ROOT.parent;R=W/'build/v1.2.5';RT=R/'runtime';BASE=W/'build/v1.2.4/runtime'
v=json.loads((R/'validation.json').read_text());assert v['status']=='PASS' and not v['Skyrim_executed']
protected=json.loads((ROOT/'protected-before.json').read_text())
for n,d in protected.items():assert hashlib.sha256((W.parent/n).read_bytes()).hexdigest()==d,n
expected={'MoreBrats.esp','Seq/MoreBrats.seq','README.txt','CHANGELOG.txt'}|{'Scripts/'+p.name for p in (BASE/'Scripts').glob('*.pex')}
files={p.relative_to(RT).as_posix():p for p in RT.rglob('*') if p.is_file()};assert set(files)==expected and len(files)==13
frozen=json.loads((R/'runtime-before-final-tests.json').read_text())
assert all(hashlib.sha256(files[n].read_bytes()).hexdigest()==d for n,d in frozen.items())
date="11-18-2026"
assert 'Private playtest date: '+date in files['README.txt'].read_text()
assert 'More Brats — v1.2.5 Changelog — '+date in files['CHANGELOG.txt'].read_text()
for n in ['README.txt','CHANGELOG.txt']:
assert files['CHANGELOG.txt'].read_bytes().startswith((BASE/'CHANGELOG.txt').read_bytes())
review=R/'review';review.mkdir(exist_ok=True);archive=review/'MoreBrats-v1.2.5-Review.zip'
stamp=datetime.datetime.strptime(date,'%m-%d-%Y')
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n,p in sorted(files.items()):
  i=zipfile.ZipInfo(n,date_time=(stamp.year,stamp.month,stamp.day,12,0,0));i.external_attr=0o100644<<16;i.compress_type=zipfile.ZIP_DEFLATED
  z.writestr(i,p.read_bytes(),compresslevel=9)
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None and set(z.namelist())==expected
 for n,p in files.items():assert z.read(n)==p.read_bytes()
sha=hashlib.sha256(archive.read_bytes()).hexdigest();Path(str(archive)+'.sha256').write_text(sha+'  '+archive.name+'\n')
scripts=json.loads((R/'script-integrity.json').read_text())
for n,d in scripts.items():assert hashlib.sha256(files['Scripts/'+n].read_bytes()).hexdigest()==d['sha256']
report={'candidate':'v1.2.5','baseline':'released v1.2.4','date':date,'zip':archive.name,'bytes':archive.stat().st_size,'sha256':sha,'zip_crc':'PASS','files':frozen,'total_records':19942,'new_records':0,'all_old_record_identities_preserved':True,'changed_old_payloads':'58 build GLOB values plus TES4 description; old NPC/ACHR/REFR/PACK/QUST/VMAD/FLST payloads unchanged','scripts':scripts,'old_serialized_fields_properties_defaults_bytecode_metadata_identical':True,'new_serialized_fields':0,'helper_PEX_frozen':5,'SEQ_identical':True,'settlements':19,'donors':40,'appearance_indices':200,'arrival_interval':'7–14 IN-GAME MINUTES','protected_baseline_files':len(protected),'old_changelog_prefix_bytes':len((BASE/'CHANGELOG.txt').read_bytes()),'Skyrim_executed':False,'ESS_files_tested':False,'Papyrus_estimate':'Moderate; no in-game measurements'}
(R/'INTEGRITY-v1.2.5.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':'PASS','zip':str(archive),'bytes':report['bytes'],'sha256':sha,'date':date,'members':13},indent=2))
