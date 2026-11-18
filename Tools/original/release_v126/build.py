"""Build the unpublished v1.2.6 playtest candidate directly from complete v1.2.5."""
from pathlib import Path
import argparse,os,subprocess,shutil,sys
ROOT=Path(__file__).resolve().parent;WORK=ROOT.parent
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--tests',action='store_true');ap.add_argument('--regenerate',action='store_true');ap.add_argument('--scripts-only',action='store_true');args=ap.parse_args()
 env=os.environ.copy();env.setdefault('DOTNET_CLI_HOME',str(WORK/'deps/dotnet-home'));env.setdefault('XDG_DATA_HOME',str(WORK/'deps/xdg-data'));env.setdefault('NUGET_PACKAGES',str(WORK/'deps/nuget'))
 env['PYTHONPATH']=os.pathsep.join([str(WORK/'src'),str(WORK/'deps/esplib/src')])
 dotnet=env.get('MB_DOTNET') or shutil.which('dotnet') or str(WORK/'deps/dotnet/dotnet')
 compiler=env.get('MB_CAPRICA') or str(WORK/'build/caprica/Caprica')
 def run(cmd,cwd=WORK.parent):subprocess.run([str(x) for x in cmd],cwd=cwd,env=env,check=True)
 if args.regenerate:
  run([sys.executable,ROOT/'prepare.py'])
 if not args.scripts_only:run([dotnet,'run','--project',ROOT/'PluginBuilder/PluginBuilder.csproj'])
 runtime=WORK/'build/v1.2.6/runtime';source=WORK/'v1.2.6/src'
 scripts=runtime/'Scripts';scripts.mkdir(parents=True,exist_ok=True)
 run([compiler,'--game','skyrim','--import',ROOT/'API','--import',WORK/'src/api','--flags',WORK/'src/api/TESV_Papyrus_Flags.flg','--output',scripts,'--anonymize','MB_Controller.psc','MB_CityController.psc','MB_TownController.psc','MB_VillageController.psc'],cwd=source)
 for p in (WORK/'build/v1.2.5/runtime/Scripts').glob('*.pex'):
  if 'Controller' not in p.stem:shutil.copyfile(p,scripts/p.name)
 run([dotnet,'run','--project',ROOT/'PluginAudit/PluginAudit.csproj','--',runtime/'MoreBrats.esp'])
 if args.tests:
  run([sys.executable,'-B',ROOT/'test_release.py'])
 print('Unpublished build ready in build/v1.2.6/runtime; no website, Nexus or Git branch was changed.')
if __name__=='__main__':main()
