"""Portable, resumable Codex setup. Runtime data is always outside this repository."""
from __future__ import annotations
import argparse,datetime,hashlib,json,os,re,shutil,subprocess,sys,tempfile,time,tomllib,urllib.error,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
# Import the repository-level resolver independently of the caller's working directory.
sys.path.insert(0,str(ROOT.parent/'scripts'))
from latest_release import latest_release, tag_commit, validate_repo

def resolve_source(source):
 """Resolve a GitHub source to its stable release or default branch commit."""
 repo=source.removeprefix('https://github.com/').removesuffix('.git').rstrip('/')
 validate_repo(repo)
 tag=latest_release(repo)
 if tag:
  commit=tag_commit(repo,tag)
 else:
  output=subprocess.check_output(['git','ls-remote','https://github.com/'+repo+'.git','HEAD'],text=True)
  rows=[line.split() for line in output.splitlines() if line.split()[-1:] == ['HEAD']]
  if len(rows)!=1 or not re.fullmatch(r'[0-9a-f]{40}',rows[0][0]):raise RuntimeError('Cannot resolve default branch: '+repo)
  commit=rows[0][0]
 return {'tag':tag,'commit':commit}

def skill_sources(root=None):
 # Shared core skills, OMH workflow skills (Hermes has them natively), then Codex-only skills.
 root=Path(root or ROOT)
 return [p for p in (root.parent/'shared'/'skills'/'core',root.parent/'shared'/'skills'/'omh',root/'skills') if p.is_dir()]
def skill_dir(name,root=None):
 for base in skill_sources(root):
  if (base/name/'SKILL.md').is_file():return base/name
 raise FileNotFoundError(name)
def state_root(home=None):
 h=Path(home or Path.home())
 return h/('Library/Application Support/codex-setup' if sys.platform=='darwin' else '.local/share/codex-setup')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write_json(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');path.chmod(0o600)
def run(argv,**kw):
 return subprocess.run([str(x) for x in argv],check=True,text=True,**kw)
def routes():
 text=(ROOT/'11-working-method.md').read_text(); result={}
 for category,family,effort in re.findall(r'^\| `([a-z-]+)` \| `(sol|astra|luna)` \| `(low|medium|high|xhigh|max)` \|',text,re.M):
  result[category]={'family':family,'effort':effort}
 if len(result)!=12:raise RuntimeError('Expected 12 canonical routing rows in 11-working-method.md')
 return result

def managed_config(text,block):
 begin='# BEGIN CODEX-SETUP MANAGED MCP';end='# END CODEX-SETUP MANAGED MCP'
 parsed=tomllib.loads(text)
 if begin in text:
  if text.count(begin)!=1 or text.count(end)!=1:raise RuntimeError('Invalid managed markers')
  base=text[:text.index(begin)]+text[text.index(end)+len(end):]
 else:base=text
 for name in ('codegraph','global-memory'):
  if name in tomllib.loads(base).get('mcp_servers',{}):raise RuntimeError('Unmanaged MCP conflict: '+name)
 new=base.rstrip()+'\n\n'+begin+'\n'+block.rstrip()+'\n'+end+'\n'
 tomllib.loads(new)
 return new

def config_block(tools):
 quote=lambda value:json.dumps(value,ensure_ascii=False)
 token=tools.get('gam_token',str(Path.home()/('Library/Application Support/global-memory/auth-token' if sys.platform=='darwin' else '.config/global-memory/auth-token')))
 args=['--token-file',token]
 if tools.get('gam_config'):args += ['--config',tools['gam_config']]
 if tools.get('gam_state'):args += ['--state',tools['gam_state']]
 return ('[mcp_servers.codegraph]\ncommand = '+quote(tools['codegraph'])+'\nargs = ["serve", "--mcp"]\n\n'+
 '[mcp_servers.global-memory]\ncommand = '+quote(tools['gam_mcp'])+'\nargs = '+quote(args)+'\n')

def gam_profile(home, *, semantic=True):
 vault=json.dumps(str(Path(home)/'Documents/Global Agent Memory'),ensure_ascii=False)
 if semantic:
  return 'vault_path = '+vault+'\n[embeddings]\nenabled = true\nprovider = "ollama"\nmodel = "nomic-embed-text"\n[search]\ndefault_mode = "hybrid"\n'
 return 'vault_path = '+vault+'\n[embeddings]\nenabled = false\n[search]\ndefault_mode = "keyword"\n'

def ensure_ollama(model):
 ollama=shutil.which('ollama')
 installed=False
 if not ollama:
  brew=shutil.which('brew')
  if not brew:raise RuntimeError('Install Homebrew before the Ollama setup on macOS')
  run([brew,'install','ollama'])
  ollama=shutil.which('ollama')
  if not ollama:raise RuntimeError('Homebrew installed Ollama but its executable is unavailable')
  installed=True
 base='http://127.0.0.1:11434'
 service_started=False
 try:
  with urllib.request.urlopen(base+'/api/version',timeout=5) as response:json.load(response)
 except (urllib.error.URLError,TimeoutError):
  brew=shutil.which('brew')
  if not brew:raise RuntimeError('Ollama is installed but its service is stopped; start Ollama then retry')
  run([brew,'services','start','ollama'])
  service_started=True
  for attempt in range(30):
   try:
    with urllib.request.urlopen(base+'/api/version',timeout=2) as response:json.load(response)
    break
   except (urllib.error.URLError,TimeoutError):
    if attempt==29:raise RuntimeError('Ollama service did not become ready')
    time.sleep(0.5)
 with urllib.request.urlopen(base+'/api/tags',timeout=5) as response:tags=json.load(response)
 expected=model if ':' in model else model+':latest'
 model_pulled=False
 if expected not in {item['name'] for item in tags['models']}:
  run([ollama,'pull',model])
  model_pulled=True
 request=urllib.request.Request(base+'/api/embed',data=json.dumps({'model':model,'input':'Codex setup embedding check'}).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(request,timeout=30) as response:embedded=json.load(response)
 vectors=embedded.get('embeddings')
 if not isinstance(vectors,list) or not vectors or not isinstance(vectors[0],list) or not vectors[0]:raise RuntimeError('Ollama did not return an embedding vector')
 return {'installed':installed,'service_started':service_started,'model_pulled':model_pulled,'embedding_dimensions':len(vectors[0])}

def backup_write(dst,data,state):
 dst=Path(dst);state=Path(state)
 if dst.is_symlink():raise RuntimeError('Refusing file symlink '+str(dst))
 if dst.exists() and dst.read_bytes()==data:return None
 ident=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f')
 folder=state/'backups'/ident;folder.mkdir(parents=True,mode=0o700)
 exists=dst.exists()
 if exists:shutil.copy2(dst,folder/'before');(folder/'before').chmod(0o600)
 write_json(folder/'receipt.json',{'target':str(dst),'existed':exists,'after_sha256':hashlib.sha256(data).hexdigest(),'applied':False,'before_sha256':digest(dst) if exists else None})
 dst.parent.mkdir(parents=True,exist_ok=True)
 fd,tmp=tempfile.mkstemp(dir=dst.parent,prefix='.setup-')
 with os.fdopen(fd,'wb') as f:f.write(data)
 os.chmod(tmp,0o600);os.replace(tmp,dst)
 write_json(folder/'receipt.json',{'target':str(dst),'existed':exists,'after_sha256':digest(dst),'applied':True})
 return folder

def restore(folder):
 folder=Path(folder).resolve();raw=json.loads((folder/'receipt.json').read_text())
 rows=raw if isinstance(raw,list) else [dict(raw,kind='file',backup=str(folder/'before') if raw['existed'] else None,applied_sha256=raw['after_sha256'])]
 # Check every target before restoring any target, including managed skill links.
 actionable=[]
 for row in rows:
  dst=Path(row['target'])
  if row.get('applied') is False:
   if not dst.exists() and not dst.is_symlink() and not row.get('backup'):continue
   if row.get('before_sha256') and dst.is_file() and not dst.is_symlink() and digest(dst)==row['before_sha256']:continue
  if row['kind']=='link':
   if not dst.is_symlink() or dst.resolve()!=Path(row['link_target']).resolve():raise RuntimeError('Managed link changed since application')
  elif dst.is_symlink() or not dst.is_file() or digest(dst)!=row['applied_sha256']:raise RuntimeError('Target changed since application; inspect before restore')
  if row.get('backup'):
   saved=Path(row['backup'])
   if saved.is_symlink() or not saved.resolve().is_relative_to(folder) or not saved.is_file():raise RuntimeError('Backup is missing or outside receipt directory')
  actionable.append(row)
 for row in reversed(actionable):
  dst=Path(row['target'])
  if row.get('backup'):
   shutil.copy2(row['backup'],dst)
   if row.get('previous_mode') is not None:dst.chmod(row['previous_mode'])
  else:dst.unlink()
 return {'restored':[row['target'] for row in actionable]}

def install_tools(state):
 lock=json.loads((ROOT/'inventories/tools.lock.json').read_text());state=Path(state).resolve()
 toolenv=dict(os.environ,npm_config_cache=str(state/"cache/npm"))
 if sys.version_info<(3,12):raise RuntimeError('Python 3.12+ required; install it then resume')
 uv=shutil.which('uv')
 if not uv:raise RuntimeError('uv is required for the official GAM install; on macOS install it with brew install uv')
 if not shutil.which('npm'):raise RuntimeError('Node 20–24 with npm required; install then resume')
 major=int(subprocess.check_output(['node','--version'],text=True).strip().lstrip('v').split('.')[0])
 if not 20<=major<25:raise RuntimeError('CodeGraph requires Node 20–24')
 uv_tools=Path(subprocess.check_output([uv,'tool','dir'],text=True).strip())
 uv_bin=Path(subprocess.check_output([uv,'tool','dir','--bin'],text=True).strip())
 gam_env=uv_tools/lock['gam']['package']
 gam=uv_bin/'global-memory'
 gam_mcp=uv_bin/'global-memory-mcp'
 gam_python=gam_env/'bin/python'
 resolved={name:resolve_source(lock[name]['source']) for name in ('gam','codegraph')}
 source=lock['gam']['source'].removesuffix('.git')+'.git@'+resolved['gam']['commit']
 run([uv,'tool','install','--force','--reinstall','git+'+source])
 version=subprocess.run([str(gam_python),'-c','import importlib.metadata; print(importlib.metadata.version("global-memory-mcp"))'],capture_output=True,text=True)
 if version.returncode or not gam.is_file() or not gam_mcp.is_file():raise RuntimeError('GAM installation verification failed')
 npm=state/'tools/codegraph'
 binary=npm/'node_modules/.bin/codegraph';pkg=npm/'node_modules/@colbymchenry/codegraph/package.json'
 npm.mkdir(parents=True,exist_ok=True)
 tag=resolved['codegraph']['tag']
 spec=lock['codegraph']['package']+'@'+tag.removeprefix('v') if tag else 'git+'+lock['codegraph']['source']+'.git#'+resolved['codegraph']['commit']
 run(['npm','install','--no-audit','--no-fund',spec],cwd=npm.resolve(),env=toolenv)
 if not binary.is_file() or not pkg.is_file():raise RuntimeError('CodeGraph installation verification failed')
 if tag and json.loads(pkg.read_text())['version']!=tag.removeprefix('v'):raise RuntimeError('npm installed an unexpected CodeGraph version')
 write_json(state/'tool-releases.json',resolved)
 for name,item in resolved.items():print('Installed',name,item['tag'] or 'default-branch',item['commit'])
 tools={'python':str(gam_python),'codegraph':str(binary),'gam':str(gam),'gam_mcp':str(gam_mcp)}
 write_json(state/'tools.json',tools);return tools

def validate_isolated(home,codex_home,state):
 from apply_managed import targets
 home=Path(home).resolve();codex_home=Path(codex_home);state=Path(state)
 check=[codex_home,state,home/'.agents/skills',home/'Documents/Global Agent Memory',home/'Library/Application Support/global-memory',home/'.config/global-memory',home/'.local/share/global-memory']
 check += [state/x for x in ('tools','backups','managed-backups','cache','receipts')]
 for path in check:
  if not path.resolve().is_relative_to(home):raise RuntimeError('Isolated path escapes disposable home: '+str(path))
 # Inspect symlink leaves too: path-root checks alone miss state/tools.json and DB redirects.
 # A venv's Python executables intentionally link to the shared read-only system runtime.
 for base in (state,codex_home,home/'Documents/Global Agent Memory',home/'Library/Application Support/global-memory',home/'Library/Logs/global-memory',home/'.config/global-memory',home/'.local/share/global-memory'):
  if not base.resolve().is_relative_to(home):raise RuntimeError('Isolated writable root escapes disposable home')
  for current,dirs,files in os.walk(base,followlinks=False):
   for name in dirs+files:
    path=Path(current)/name
    if not path.is_symlink() or path.resolve().is_relative_to(home):continue
    raise RuntimeError('Isolated writable symlink escapes disposable home: '+str(path))
 for _,dst,kind in targets(home,codex_home):
  if not dst.parent.resolve().is_relative_to(home):raise RuntimeError('Isolated target parent escapes disposable home')
  if kind=='file' and not dst.resolve().is_relative_to(home):raise RuntimeError('Isolated file escapes disposable home')
 cfg=home/('Library/Application Support/global-memory/config.toml' if sys.platform=='darwin' else '.config/global-memory/config.toml')
 if cfg.exists() and not Path(tomllib.loads(cfg.read_text())['vault_path']).expanduser().resolve().is_relative_to(home):raise RuntimeError('Isolated GAM vault escapes disposable home')

def apply(state,home,codex_home,with_tools=True,isolated=False):
 from apply_managed import apply as deploy
 from install_core_skills import install as install_core_skills
 state=Path(state).resolve();home=Path(home).resolve();codex_home=Path(codex_home).resolve()
 if isolated:validate_isolated(home,codex_home,state)
 state.mkdir(parents=True,exist_ok=True);state.chmod(0o700)
 # Preflight all managed files before network or mutation.
 deploy(home,state/'managed-backups',False,codex_home=codex_home)
 tools=install_tools(state) if with_tools else json.loads((state/'tools.json').read_text())
 gamdir=home/'Library/Application Support/global-memory' if sys.platform=='darwin' else home/'.config/global-memory'
 gamdata=gamdir if sys.platform=='darwin' else home/'.local/share/global-memory'
 tools.update(gam_config=str(gamdir/'config.toml'),gam_token=str(gamdir/'auth-token'),gam_state=str(gamdata))
 write_json(state/'tools.json',tools)
 config=codex_home/'config.toml';old=config.read_text() if config.exists() else ''
 new=managed_config(old,config_block(tools))
 result=deploy(home,state/'managed-backups',True,codex_home=codex_home)
 result['core_skills']=install_core_skills(None,home,state)
 backup_write(config,new.encode(),state)
 # Canonical GAM init does not install Hermes or other clients, start a service, or launch UI.
 gamcfg=home/'Library/Application Support/global-memory/config.toml' if sys.platform=='darwin' else home/'.config/global-memory/config.toml'
 if not gamcfg.exists():
  # Use the upstream hybrid default; readiness is verified separately with Ollama.
  gamcfg.parent.mkdir(parents=True,exist_ok=True)
  gamcfg.write_text(gam_profile(home));gamcfg.chmod(0o600)
 elif gamcfg.read_text()==gam_profile(home,semantic=False):
  # Upgrade only the exact keyword profile written by an earlier Setup version.
  backup_write(gamcfg,gam_profile(home).encode(),state)
 embedding=tomllib.loads(gamcfg.read_text()).get('embeddings',{})
 if embedding.get('enabled') and embedding.get('provider')=='ollama':
  result['ollama']=ensure_ollama(embedding['model'])
 else:
  result['ollama']={'status':'not_configured_for_ollama'}
 run([tools['python'],ROOT/'scripts/init_gam.py','--home',home,'--config',gamcfg,'--data',gamdata])
 if with_tools:
  run([tools['python'],ROOT/'scripts/install_external_skills.py','--all','--apply','--home',home,'--state',state])
 write_json(state/'installation.json',{'schema_version':1,'setup_root':str(ROOT),'codex_home':str(codex_home),'tools':tools,'applied_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'applied_not_behavior_verified'})
 return result

def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['plan','apply','doctor','restore']);p.add_argument('--state',type=Path,default=state_root());p.add_argument('--home',type=Path,default=Path.home());p.add_argument('--codex-home',type=Path,default=Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex'))));p.add_argument('--skip-tools',action='store_true');p.add_argument('--isolated',action='store_true');p.add_argument('--backup',type=Path);a=p.parse_args()
 if a.action=='plan':out={'isolated':a.isolated,'source':str(ROOT),'state':str(a.state),'skills':sum(len(list(p.glob('*/SKILL.md'))) for p in skill_sources()),'work_pack_skills':len(json.loads((ROOT/'inventories/external-skills.json').read_text())['skills']),'routes':routes(),'steps':['preflight','install latest stable tools','apply managed skills and instructions','merge MCP config','initialize GAM','install reviewed work packs','run doctor','run behavior evaluations']}
 elif a.action=='apply':
  if sys.platform!='darwin':raise RuntimeError('Codex-Setup installation supports macOS only')
  if a.isolated or a.home.resolve()!=Path.home().resolve():raise RuntimeError('Apply only to the actual macOS user home')
  out=apply(a.state,a.home,a.codex_home,not a.skip_tools,False)
 elif a.action=='restore':out=restore(a.backup)
 else:
  tools=json.loads((a.state/'tools.json').read_text());checks={}
  for name,args in [('codegraph',['--version']),('gam',['--version'])]:
   r=subprocess.run([tools[name],*args],capture_output=True,text=True);checks[name]={'ok':r.returncode==0,'version':r.stdout.strip()}
  checks['routing']={'ok':len(routes())==12}
  print(json.dumps(checks,ensure_ascii=False,indent=2));sys.exit(0 if all(v['ok'] for v in checks.values()) else 1)
 print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
