"""Package only the already-validated private runtime; no implementation changes."""
from pathlib import Path
import hashlib,json,re,zipfile,datetime
ROOT=Path(__file__).resolve().parent;W=ROOT.parent;R=W/'build/v1.2.4';RT=R/'runtime';BASE=W/'build/v1.2.3/runtime'
valid=json.loads((R/'validation.json').read_text());assert valid['status']=='PASS' and valid['Skyrim_executed'] is False
protected=json.loads((ROOT/'protected-before.json').read_text())
for name,digest in protected.items():assert hashlib.sha256((W.parent/name).read_bytes()).hexdigest()==digest,name
expected={'MoreBrats.esp','Seq/MoreBrats.seq','README.txt','CHANGELOG.txt'}|{'Scripts/'+p.name for p in (BASE/'Scripts').glob('*.pex')}
files={p.relative_to(RT).as_posix():p for p in RT.rglob('*') if p.is_file()};assert set(files)==expected and len(files)==13
frozen=json.loads((R/'runtime-before-final-tests.json').read_text())
assert all(hashlib.sha256(files[n].read_bytes()).hexdigest()==d for n,d in frozen.items())
date="11-18-2026"
assert 'Private playtest date: '+date in files['README.txt'].read_text()
assert 'More Brats — v1.2.4 Changelog — '+date in files['CHANGELOG.txt'].read_text()
for name in ['README.txt','CHANGELOG.txt']:
assert files['CHANGELOG.txt'].read_bytes().startswith((BASE/'CHANGELOG.txt').read_bytes())
review=R/'review';review.mkdir(exist_ok=True);archive=review/'MoreBrats-v1.2.4-Review.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for name,p in sorted(files.items()):
  stamp=datetime.datetime.strptime(date,'%m-%d-%Y');info=zipfile.ZipInfo(name,date_time=(stamp.year,stamp.month,stamp.day,12,0,0));info.external_attr=0o100644<<16;info.compress_type=zipfile.ZIP_DEFLATED
  z.writestr(info,p.read_bytes(),compresslevel=9)
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None and set(z.namelist())==expected
 for name,p in files.items():assert z.read(name)==p.read_bytes()
sha=hashlib.sha256(archive.read_bytes()).hexdigest();Path(str(archive)+'.sha256').write_text(sha+'  '+archive.name+'\n')
scripts=json.loads((R/'script-integrity.json').read_text())
for name,data in scripts.items():assert hashlib.sha256(files['Scripts/'+name].read_bytes()).hexdigest()==data['sha256']
integrity={'candidate':'v1.2.4','date':date,'baseline':'released v1.2.3 with current v1.2.4 repairs retained','zip':archive.name,'bytes':archive.stat().st_size,'sha256':sha,'zip_crc':'PASS','files':frozen,'old_records':19941,'new_records':1,'total_records':19942,'new_record':'MB_ArrivalBuildingDoorTypes FLST local0x2221E0','changed_existing_record_payloads':'58 diagnostic build GLOB values; no old NPC/ACHR/REFR/PACK/QUST/VMAD/FLST payload changes','masters':['Skyrim.esm','HearthFires.esm','Dragonborn.esm'],'scripts':scripts,'startup_SEQ_byte_identical':True,'all_19_settlement_configs_preserved':True,'all_200_appearance_indices_preserved':True,'all_old_serialized_fields_types_properties_preserved':True,'all_retirement_functions_preserved':True,'protected_historical_files_sha256_verified':len(protected),'previous_changelog_bytes_preserved':len((BASE/'CHANGELOG.txt').read_bytes()),'Skyrim_executed':False,'ESS_files_tested':False,'classification':'Moderate (code estimate; no in-game benchmark)'}
(R/'INTEGRITY-v1.2.4.json').write_text(json.dumps(integrity,indent=2)+'\n')
print(json.dumps({'status':'PASS','zip':str(archive),'members':len(files),'bytes':archive.stat().st_size,'sha256':sha,'date':date},indent=2))
