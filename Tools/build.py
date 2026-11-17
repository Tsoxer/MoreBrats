"""New portable export driver; original gameplay/generator logic is preserved."""
from pathlib import Path
import argparse,json,os,shutil,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parents[1];BUILD=ROOT/'.build';WORK=BUILD/'work'
def run(args,cwd=ROOT,env=None):
 print('+', ' '.join(str(x) for x in args),flush=True)
 subprocess.run([str(x) for x in args],cwd=cwd,env=env,check=True)
def copytree(src,dest):
 dest.mkdir(parents=True,exist_ok=True)
 for p in src.rglob('*'):
  if p.is_file():q=dest/p.relative_to(src);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--dotnet',default='dotnet');ap.add_argument('--compiler',type=Path)
 ap.add_argument('--build-compiler',action='store_true');ap.add_argument('--boost-root',type=Path)
 ap.add_argument('--tests',action='store_true');args=ap.parse_args()
 BUILD.mkdir(exist_ok=True)
 env=os.environ.copy()
 env.setdefault('DOTNET_CLI_HOME',str(BUILD/'dotnet-home'))
 env.setdefault('XDG_DATA_HOME',str(BUILD/'xdg-data'))
 env['TMPDIR']=str(BUILD/'tmp');(BUILD/'tmp').mkdir(exist_ok=True)
 env['DOTNET_CLI_TELEMETRY_OPTOUT']='1'
 env['NUGET_PACKAGES']=env.get('MB_NUGET_PACKAGES',str(BUILD/'nuget'))
 env['PYTHONPATH']=os.pathsep.join([str(ROOT/'Tools/support'),str(ROOT/'ThirdParty/esplib/src')])
 compiler=(args.compiler or BUILD/'compiler/Caprica').resolve()
 if args.build_compiler:
  command=['cmake','-S',ROOT/'Compiler','-B',BUILD/'compiler','-G','Ninja','-DCMAKE_BUILD_TYPE=Release']
  if args.boost_root:command.append('-DMB_BOOST_ROOT='+str(args.boost_root.resolve()))
  run(command);run(['cmake','--build',BUILD/'compiler','--parallel','2'])
 if not compiler.is_file():raise SystemExit('Compiler missing: build the included compiler with --build-compiler, or pass --compiler to the preserved patched Caprica executable.')
 # Exact owned baseline binary input, original source fixtures, and original
 # settlement data. No Bethesda masters, BSAs or reference PEX files are needed.
 copytree(ROOT/'Baseline/v1.0.0/Runtime',WORK/'v1.0.0/runtime')
 copytree(ROOT/'Baseline/v1.0.0/Papyrus',WORK/'v1.0.0/src')
 copytree(ROOT/'Config/fixtures',WORK/'research')
 copytree(ROOT/'Tools/support',WORK/'src')
 copytree(ROOT/'Tools/original',WORK/'release_v110')
 release=WORK/'build/v1.1.0';release.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(ROOT/'Config/settlements.json',release/'settlements.json')
 copytree(ROOT/'Papyrus',release/'source')
 restore=['restore',ROOT/'PluginBuilder/PluginBuilder.csproj']
 restore+=['--locked-mode'] if (ROOT/'PluginBuilder/packages.lock.json').exists() else ['--use-lock-file']
 run([args.dotnet,*restore],env=env)
 run([args.dotnet,'build','--no-restore',ROOT/'PluginBuilder/PluginBuilder.csproj'],env=env)
 run([args.dotnet,'run','--no-build','--project',ROOT/'PluginBuilder/PluginBuilder.csproj'],cwd=BUILD,env=env)
 def compile_sources(source,out):
  out.mkdir(parents=True,exist_ok=True)
  run([compiler,'--game','skyrim','--import',ROOT/'API','--flags',ROOT/'API/TESV_Papyrus_Flags.flg','--output',out,'--anonymize',*[p.name for p in sorted(source.glob('MB_*.psc'))]],cwd=source,env=env)
 compile_sources(ROOT/'Papyrus',release/'runtime/Scripts')
 shutil.copyfile(ROOT/'Docs/README-v1.1.0.txt',release/'runtime/README.txt')
 shutil.copyfile(ROOT/'CHANGELOG.txt',release/'runtime/CHANGELOG.txt')
 from verify_build import verify
 verify(release/'runtime')
 if args.tests:
  compile_sources(ROOT/'Baseline/v1.0.0/Papyrus',WORK/'v1.0.0/runtime/Scripts')
  run([sys.executable,ROOT/'Tools/original/test_release.py'],cwd=BUILD,env=env)
  run([sys.executable,ROOT/'Tools/original/focused_checks.py'],cwd=BUILD,env=env)
 artifact=BUILD/'MoreBrats-v1.1.0-rebuilt.zip'
 with zipfile.ZipFile(artifact,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted((release/'runtime').rglob('*')):
   if p.is_file():z.write(p,str(p.relative_to(release/'runtime')))
 print('Build and verification complete:',artifact.name)
if __name__=='__main__':main()
