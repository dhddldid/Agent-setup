"""Bounded retention: own logs only; explicitly expired temporary GAM notes are archived."""
import argparse,asyncio,datetime,json,os,sys
from pathlib import Path
from setup_runtime import ROOT,state_root,write_json

def expired_memory(meta,now,policy):
 tags=set(meta.get('tags',[]))
 if meta.get('scope')!='project' or meta.get('status')!='active' or 'temporary' not in tags:return False
 if tags.intersection(policy['protect_tags']) or meta.get('type') in ('decision','preference','convention') or float(meta.get('importance',1))>=0.8:return False
 dates=[]
 for tag in tags:
  if tag.startswith('expires:'):
   try:dates.append(datetime.date.fromisoformat(tag[8:]))
   except ValueError:return False
 return len(dates)==1 and dates[0]<now.date()

def stale_memory(meta,now,policy):
 # Report only: active project notes not updated for stale_review_days. Never archived automatically.
 if meta.get('scope')!='project' or meta.get('status')!='active' or set(meta.get('tags',[])).intersection(policy['protect_tags']):return False
 try:updated=datetime.datetime.fromisoformat(str(meta.get('updated_at')).replace('Z','+00:00'))
 except ValueError:return False
 if updated.tzinfo is None:updated=updated.replace(tzinfo=datetime.timezone.utc)
 return (now-updated).days>=policy.get('stale_review_days',180)

def log_candidates(state,now,policy):
 state=Path(state).resolve();out=[]
 for sub,days in [('logs',policy['owned_log_days']),('receipts',policy['receipt_days'])]:
  base=state/sub
  if base.is_symlink():continue
  for p in base.glob('*'):
   if p.is_symlink() or not p.is_file():continue
   if p.suffix not in ('.json','.jsonl','.log'):continue
   if (now.timestamp()-p.stat().st_mtime)>days*86400:out.append(p)
 # Completed, reviewed evaluations own these raw logs. Keep pending/failed cases intact.
 evaluations=state/'evaluations'
 if evaluations.is_dir() and not evaluations.is_symlink():
  for run in evaluations.iterdir():
   if run.is_symlink() or not run.is_dir() or (run/'.keep').exists():continue
   for case in run.iterdir():
    if case.is_symlink() or not case.is_dir() or (case/'.keep').exists():continue
    receipt=case/'receipt.json'
    if not receipt.is_file() or receipt.is_symlink():continue
    try:record=json.loads(receipt.read_text())
    except (ValueError,OSError):continue
    if record.get('semantic_verdict')!='passed' or record.get('execution_status')!='executed':continue
    for name in ('events.jsonl','stderr.log','prompt.txt'):
     path=case/name
     if path.is_file() and not path.is_symlink() and now.timestamp()-path.stat().st_mtime>policy['owned_log_days']*86400:out.append(path)
 runs=state/'runs'
 if runs.is_dir() and not runs.is_symlink():
  for run in runs.iterdir():
   if run.is_symlink() or not run.is_dir() or (run/'.keep').exists():continue
   receipt=run/'receipt.json'
   if not receipt.is_file() or receipt.is_symlink():continue
   try:record=json.loads(receipt.read_text())
   except (ValueError,OSError):continue
   if record.get('status')!='executed_not_verified' or record.get('exit_code')!=0 or record.get('disposable_logs') is not True:continue
   for name in ('events.jsonl','stderr.log'):
    path=run/name
    if path.is_file() and not path.is_symlink() and now.timestamp()-path.stat().st_mtime>policy['owned_log_days']*86400:out.append(path)
 return out
async def maintain(state,vault,apply=False,config=None,gam_state=None):
 # Shared lifecycle policy and adapter serve every executor. Legacy public
 # predicates above remain compatibility-only for old callers and tests.
 shared = ROOT.parent/'shared/skills/core/gam-memory/scripts'
 if str(shared) not in sys.path:sys.path.insert(0,str(shared))
 from gam_retention import maintain as maintain_gam
 policy=json.loads((ROOT/'config/retention.json').read_text())
 gam_policy=json.loads((ROOT.parent/'shared/retention/policy.json').read_text())['gam']
 now=datetime.datetime.now(datetime.timezone.utc);state=Path(state)
 tools=json.loads((state/'tools.json').read_text())
 result=await maintain_gam(vault,gam_policy,apply=apply,config=config,gam_state=gam_state,command=tools['gam_mcp'],now=now)
 logs=log_candidates(state,now,policy)
 result.update(log_candidates=len(logs),logs_deleted=0)
 if apply:
  for path in logs:
   if path in log_candidates(state,now,policy):path.unlink();result['logs_deleted']+=1
  write_json(state/'receipts/maintenance-latest.json',dict(result,at=now.isoformat()))
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--state',type=Path,default=state_root());p.add_argument('--vault',type=Path,default=Path.home()/'Documents/Global Agent Memory');p.add_argument('--apply',action='store_true');a=p.parse_args()
 print(json.dumps(asyncio.run(maintain(a.state,a.vault,a.apply)),indent=2))
