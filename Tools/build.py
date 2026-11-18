"""Portable source-export driver. Original gameplay and generator logic remain separate."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parents[1];BUILD=ROOT/'.build';WORK=BUILD/'work'
VERSIONS=['1.1.0']+['1.2.'+str(i) for i in range(8)]
def run(args,cwd=ROOT,env=None):
 print('+',' '.join(str(x) for x in args),flush=True);subprocess.run([str(x) for x in args],cwd=cwd,env=env,check=True)
def copytree(src,dest):
 for p in src.rglob('*'):
  if p.is_file():q=dest/p.relative_to(src);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--dotnet',default='dotnet');ap.add_argument('--compiler',type=Path);ap.add_argument('--build-compiler',action='store_true');ap.add_argument('--boost-root',type=Path);ap.add_argument('--tests',action='store_true');args=ap.parse_args()
 BUILD.mkdir(exist_ok=True);env=os.environ.copy();env.setdefault('DOTNET_CLI_HOME',str(BUILD/'dotnet-home'));env.setdefault('XDG_DATA_HOME',str(BUILD/'xdg-data'));env['DOTNET_CLI_TELEMETRY_OPTOUT']='1';env['NUGET_PACKAGES']=env.get('MB_NUGET_PACKAGES',str(BUILD/'nuget'));env['TMPDIR']=str(BUILD/'tmp');(BUILD/'tmp').mkdir(exist_ok=True)
 env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONPATH']=os.pathsep.join([str(WORK/'src'),str(WORK/'deps/esplib/src')])
 compiler=(args.compiler or BUILD/'compiler/Caprica').resolve()
 if args.build_compiler:
  cmd=['cmake','-S',ROOT/'Compiler','-B',BUILD/'compiler','-G','Ninja','-DCMAKE_BUILD_TYPE=Release']
  if args.boost_root:cmd.append('-DMB_BOOST_ROOT='+str(args.boost_root.resolve()))
  run(cmd);run(['cmake','--build',BUILD/'compiler','--parallel','2'])
 if not compiler.is_file():raise SystemExit('Build the bundled compiler with --build-compiler, or pass --compiler to a preserved patched Caprica executable.')
 copytree(ROOT/'Baseline/v1.0.0/Runtime',WORK/'v1.0.0/runtime');copytree(ROOT/'Tools/support',WORK/'src');copytree(ROOT/'ThirdParty/esplib/src',WORK/'deps/esplib/src');copytree(ROOT/'Config/fixtures',WORK/'research');copytree(ROOT/'Tools/original',WORK)
 copytree(ROOT/'Papyrus',WORK/'v1.2.7/src')
 for v in VERSIONS:
  c=WORK/'build'/('v'+v);c.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/'Baseline'/('v'+v)/'settlements.json',c/'settlements.json')
  if v!='1.2.7':copytree(ROOT/'Baseline'/('v'+v)/'Papyrus',WORK/('v'+v)/'src')
 # Run the actual historical incremental generators in order. There is no
 # reconstructed final ESP and no dependency on an unpublished v126 binary.
 for v in VERSIONS:
  tag='release_v'+v.replace('.','');project=ROOT/'PluginBuilder/PluginBuilder.csproj' if v=='1.2.7' else WORK/tag/'PluginBuilder/PluginBuilder.csproj'
  run([args.dotnet,'restore',project,'--locked-mode'],env=env)
  run([args.dotnet,'run','--project',project,'--no-restore'],cwd=BUILD,env=env)
  if v=='1.1.0':copytree(WORK/'build/v1.1.0/runtime',WORK/'v1.1.0/runtime')
 def compile_sources(source,out):
  out.mkdir(parents=True,exist_ok=True);run([compiler,'--game','skyrim','--import',ROOT/'API','--flags',ROOT/'API/TESV_Papyrus_Flags.flg','--output',out,'--anonymize',*[p.name for p in sorted(source.glob('MB_*.psc'))]],cwd=source,env=env)
 runtime=WORK/'build/v1.2.7/runtime';compile_sources(ROOT/'Papyrus',runtime/'Scripts')
 shutil.copyfile(ROOT/'Docs/v1.2.7/README.txt',runtime/'README.txt');shutil.copyfile(ROOT/'Docs/v1.2.7/CHANGELOG.txt',runtime/'CHANGELOG.txt')
 run([args.dotnet,'restore',ROOT/'PluginAudit/PluginAudit.csproj','--locked-mode'],env=env)
 run([args.dotnet,'run','--project',ROOT/'PluginAudit/PluginAudit.csproj','--no-restore','--',runtime/'MoreBrats.esp'],env=env)
 from verify_build import verify
 verify(runtime)
 if args.tests:
  for v in VERSIONS[:-1]:
   output=WORK/'build'/('v'+v)/'runtime/Scripts';compile_sources(ROOT/'Baseline'/('v'+v)/'Papyrus',output)
   if v!='1.1.0':
    for p in (WORK/'build/v1.1.0/runtime/Scripts').glob('*.pex'):
     if 'Controller' not in p.stem:shutil.copyfile(p,output/p.name)
  # The release froze these five helpers at v110. Preserve that byte-level
  # fixture relationship after recompilation too, without bundling reference PEX.
  for p in (WORK/'build/v1.1.0/runtime/Scripts').glob('*.pex'):
   if 'Controller' not in p.stem:shutil.copyfile(p,runtime/'Scripts'/p.name)
  verify(runtime)
  copytree(WORK/'build/v1.1.0/runtime',WORK/'v1.1.0/runtime')
  for n in ['README.txt','CHANGELOG.txt']:shutil.copyfile(ROOT/'Docs/v1.1.0'/n,WORK/'v1.1.0/runtime'/n)
  fixture=WORK/'build/v1.1.0/deliverables/MoreBrats-v1.1.0.zip';fixture.parent.mkdir(parents=True,exist_ok=True)
  with zipfile.ZipFile(fixture,'w',zipfile.ZIP_DEFLATED) as z:
   for p in (WORK/'v1.1.0/runtime').rglob('*'):
    if p.is_file():z.write(p,p.relative_to(WORK/'v1.1.0/runtime').as_posix())
  # This is a newly generated fixture manifest, not a claim that recompiled
  # historical PEX headers equal the original historical released binaries.
  frozen={p.relative_to(BUILD).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for v in VERSIONS[:-1] for folder in [WORK/'build'/('v'+v)/'runtime',WORK/('v'+v)/'src'] for p in folder.rglob('*') if p.is_file()}
  (WORK/'release_v127/protected-baselines.json').write_text(json.dumps(frozen,indent=2)+'\n')
  run([sys.executable,'-B',WORK/'release_v127/test_release.py'],cwd=BUILD,env=env)
 artifact=BUILD/'MoreBrats-v1.2.7-rebuilt.zip'
 with zipfile.ZipFile(artifact,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted(runtime.rglob('*')):
   if p.is_file():z.write(p,p.relative_to(runtime).as_posix())
 print('Source rebuild and parity checks complete:',artifact.name)
if __name__=='__main__':main()
