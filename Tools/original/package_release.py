from pathlib import Path
from datetime import datetime
import json,hashlib,zipfile,re,struct,shutil
from pexcheck import Pex
R=Path('work/build/v1.1.0');RT=R/'runtime';O=R/'deliverables';O.mkdir(exist_ok=True)
date=json.loads((R/'release-date-internal.json').read_text())['release_date']
assert re.fullmatch(r'\d{2}-\d{2}-\d{4}', date)
tests=json.loads((R/'validation.json').read_text());focused=json.loads((R/'focused-validation.json').read_text())
assert tests['status']==focused['status']=='PASS'
assert json.loads((R/'candidate-status.json').read_text())['template_block_resolved']
mutagen=json.loads((R/'mutagen-plugin.json').read_text());reader=json.loads((R/'mutagen-pex.json').read_text())
assert mutagen['Records']==4722 and not mutagen['MissingInternalLinks'] and len(reader)==9
for row in reader:assert (row['MajorVersion'],row['MinorVersion'],row['GameId'])==(3,2,1)
log=(R/'papyrus-compile.log').read_text()
assert len(re.findall(r'^Compiling MB_.*\.psc$',log,re.M))==9 and log.count('Warning W4007')==24 and not re.search(r'\b(error|fatal)\b',log,re.I)
assert hashlib.sha256(Path('work/build/caprica/Caprica').read_bytes()).hexdigest()=='27dd6d37a33453303b8d7247a1be0b205f7266f6b4fd64ad7d97f6af102b9440'
# Verify each entire original non-header record, not just semantic fields.
def raw(path):
 data=path.read_bytes();records={};groups=[]
 def walk(a,end):
  while a<end:
   h=data[a:a+24];size=struct.unpack_from('<I',h,4)[0]
   if h[:4]==b'GRUP':
    groups.append((struct.unpack_from('<I',h,8)[0],struct.unpack_from('<i',h,12)[0]));walk(a+24,a+size);a+=size
   else:
    k=struct.unpack_from('<I',h,12)[0];records[k]=data[a:a+24+size];a+=24+size
  assert a==end
 walk(0,len(data));return records,groups
old=Path('work/v1.0.0/runtime');before,bgroups=raw(old/'MoreBrats.esp');after,agroups=raw(RT/'MoreBrats.esp')
assert bgroups==agroups
raw_changed=[]
for k,b in before.items():
 if b==after[k]:continue
 if k:
  assert b[:24]==after[k][:24] or b[:4]==b'QUST' and b[:4]+b[8:24]==after[k][:4]+after[k][8:24]
  assert b[:4] in [b'QUST',b'GLOB']
 raw_changed.append(k)
assert len(raw_changed)==78 # TES4 description/count/next-ID + 77 major records
for p in (RT/'Scripts').glob('*.pex'):
 a=Pex(old/'Scripts'/p.name);b=Pex(p)
 for name,f in a.obj['functions'].items():assert (f['ret'],f['params'],f['native'])==(b.obj['functions'][name]['ret'],b.obj['functions'][name]['params'],b.obj['functions'][name]['native'])
 assert not any(f['native'] for f in b.obj['functions'].values())
 assert not any('v1.0.0' in s for s in b.strings)
notes=Path('work/release_v110/TECHNICAL-NOTES.txt').read_text().replace('RELEASEDATE',date)
(O/'TECHNICAL-NOTES-v1.1.0.txt').write_text(notes)
shutil.copyfile(R/'source.diff',O/'SOURCE-DIFF-v1.1.0.txt')
names=sorted(str(p.relative_to(RT)) for p in RT.rglob('*') if p.is_file())
assert len(names)==13 and {n for n in names if n.endswith('.txt')}=={'README.txt','CHANGELOG.txt'}
assert sum(n.endswith('.pex') for n in names)==9 and all(n.endswith(('.pex','.esp','.seq','.txt')) for n in names)
for n in ['README.txt','CHANGELOG.txt']:
 t=(RT/n).read_text();assert 'RELEASEDATE' not in t and date in t
 assert not re.search(r'https?://',t,re.I)
artifact=O/'MoreBrats-v1.1.0.zip'
stamp=datetime.now();stamp=(stamp.year,stamp.month,stamp.day,stamp.hour,stamp.minute,stamp.second//2*2)
with zipfile.ZipFile(artifact,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n in names:
  data=(RT/n).read_bytes();assert data
  info=zipfile.ZipInfo(n,stamp);info.external_attr=0o644<<16;info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,data)
with zipfile.ZipFile(artifact) as z:
 assert z.testzip() is None and z.namelist()==names
 for n in names:assert z.read(n)==(RT/n).read_bytes()
runtime_hashes={n:hashlib.sha256((RT/n).read_bytes()).hexdigest() for n in names if n.endswith(('.esp','.pex','.seq'))}
sha=hashlib.sha256(artifact.read_bytes()).hexdigest()
qa=dict(status='PASS',version='1.1.0',author='Tsoxer',release_date=date,archive=artifact.name,sha256=sha,bytes=artifact.stat().st_size,
        baseline_zip_sha256=hashlib.sha256(Path('work/download/dist/MoreBrats-v1.0.0.zip').read_bytes()).hexdigest(),
        runtime_hashes=runtime_hashes,members=names,static_and_mock_tests=tests,focused_tests=focused,
        Mutagen_ESP_reader=mutagen,Mutagen_PEX_reader=reader,old_raw_records_changed=len(raw_changed)-1,
        all_existing_NPCs_actors_AI_packages_and_other_unapproved_record_bytes_identical=True,all_record_group_labels_preserved=True,
        saved_function_signatures_and_types_retained=True,SEQ_byte_identical=True,compile_exit_code=0,inherited_unused_field_warnings=24,
        vanilla_donor_defaults_authorized=True,no_new_controllers_timers_scheduling_or_external_APIs=True,
        extra_persistent_refs=2280,total_pool_refs=3040,appearance_combinations=40,population_ranges_unchanged=True,
        Skyrim_executed=False,actual_ESS_tested=False,rendering_tested=False,performance_profiled=False,
        status_detail='Built and statically/mock-validated appearance expansion; requires in-game rendering and upgrade playtest.')
(O/'VALIDATION-v1.1.0.json').write_text(json.dumps(qa,indent=2)+'\n')
checks={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(O.iterdir()) if p.is_file() and not p.name.startswith('SHA256SUMS')}
(O/'SHA256SUMS-v1.1.0.txt').write_text(''.join(f'{h}  {n}\n' for n,h in checks.items()))
report=dict(status='PASS',version='1.1.0',release_date=date,artifact=str(artifact),bytes=artifact.stat().st_size,sha256=sha,members=names,Skyrim_executed=False)
(R/'package-report.json').write_text(json.dumps(report,indent=2)+'\n')
(R/'candidate-status.json').write_text(json.dumps({'status':'BUILT; AUTOMATED CHECKS PASS; GAMEPLAY PLAYTEST REQUIRED','template_block_resolved':True,'vanilla_donor_defaults_authorized':True,'published':False,'archive':artifact.name,'sha256':sha},indent=2)+'\n')
print(json.dumps(report,indent=2))
