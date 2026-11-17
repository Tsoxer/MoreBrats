"""Verify original source hashes and rebuild parity without a Skyrim install."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'Tools/support'),str(ROOT/'ThirdParty/esplib/src')]
from pexcheck import Pex
def verify(runtime=None):
 runtime=Path(runtime) if runtime else ROOT/'.build/work/build/v1.1.0/runtime'
 expected=json.loads((ROOT/'Verification/released-runtime.json').read_text())
 source_ok=[];result={}
 for name,sha in expected['papyrus_source_sha256'].items():
  assert hashlib.sha256((ROOT/'Papyrus'/name).read_bytes()).hexdigest()==sha,('Original source changed',name)
  source_ok.append(name)
 for name,info in expected['runtime'].items():
  file=runtime/name;data=file.read_bytes()
  actual=hashlib.sha256(data).hexdigest()
  if name.endswith('.pex'):
   p=Pex(file)
   semantic=hashlib.sha256(json.dumps(p.obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()
   assert semantic==info['decoded_object_sha256'],('PEX object/function difference',name)
   result[name]={'raw_byte_identical':actual==info['sha256'],'decoded_object_identical':True}
  else:
   assert actual==info['sha256'],('Runtime bytes differ',name)
   result[name]={'raw_byte_identical':True}
 report={'status':'PASS','original_Papyrus_sources_byte_identical':source_ok,'rebuilt_runtime':result,
         'limits':'PEX header/debug timestamps and source filename metadata may differ. No Skyrim engine test was performed.'}
 (ROOT/'.build/rebuild-verification.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2));return report
if __name__=='__main__':verify()
