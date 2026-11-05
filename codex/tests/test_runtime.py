import sys,unittest,tempfile,json,datetime,os
from pathlib import Path
from unittest.mock import patch, Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import setup_runtime as s
from maintain import expired_memory,log_candidates
from route_task import command

class RuntimeTests(unittest.TestCase):
 def test_source_resolves_stable_and_default_branch(self):
  with patch.object(s,'latest_release',return_value='v9.0.0') as latest, patch.object(s,'tag_commit',return_value='a'*40) as tagged:
   self.assertEqual(s.resolve_source('https://github.com/example/tool.git'),{'tag':'v9.0.0','commit':'a'*40})
   latest.assert_called_once_with('example/tool');tagged.assert_called_once_with('example/tool','v9.0.0')
  with patch.object(s,'latest_release',return_value=None), patch.object(s.subprocess,'check_output',return_value='b'*40+'\tHEAD\n'):
   self.assertEqual(s.resolve_source('example/tool'),{'tag':None,'commit':'b'*40})
  with patch.object(s,'latest_release',side_effect=RuntimeError('network')):
   with self.assertRaisesRegex(RuntimeError,'network'):s.resolve_source('example/tool')

 def test_install_tools_uses_resolved_versions_and_local_receipts(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);uvtools=root/'uvtools';uvbin=root/'uvbin';uvbin.mkdir()
   python=uvtools/'global-memory-mcp/bin/python';python.parent.mkdir(parents=True);python.touch()
   for name in ('global-memory','global-memory-mcp'):(uvbin/name).touch()
   pkg=root/'state/tools/codegraph/node_modules/@colbymchenry/codegraph/package.json'
   binary=root/'state/tools/codegraph/node_modules/.bin/codegraph'
   def execute(argv,**kw):
    if argv[0]=='npm':
     pkg.parent.mkdir(parents=True);pkg.write_text(json.dumps({'version':'9.2.0'}))
     binary.parent.mkdir(parents=True);binary.touch()
   def output(argv,**kw):
    if argv==['node','--version']:return 'v22.0.0'
    return str(uvbin if '--bin' in argv else uvtools)
   with patch.object(s,'resolve_source',side_effect=[{'tag':'v8.0.0','commit':'a'*40},{'tag':'v9.2.0','commit':'b'*40}]) as resolver, patch.object(s.shutil,'which',side_effect=lambda name:name), patch.object(s.subprocess,'check_output',side_effect=output), patch.object(s.subprocess,'run',return_value=Mock(returncode=0,stdout='8.0.0')), patch.object(s,'run',side_effect=execute) as run:
    tools=s.install_tools(root/'state')
   self.assertEqual(resolver.call_count,2)
   self.assertIn('git+https://github.com/ozankasikci/global-agent-memory.git@'+'a'*40,run.call_args_list[0].args[0])
   self.assertIn('@colbymchenry/codegraph@9.2.0',run.call_args_list[1].args[0])
   self.assertEqual(Path(tools['codegraph']).resolve(),binary.resolve())
   self.assertEqual(json.loads((root/'state/tool-releases.json').read_text())['gam']['tag'],'v8.0.0')

 def test_source_inventories_follow_latest(self):
  tools=json.loads((s.ROOT/'inventories/tools.lock.json').read_text())
  for name in ('omh','gam','codegraph'):
   self.assertNotIn('version',tools[name]);self.assertNotIn('commit',tools[name])
  skills=json.loads((s.ROOT/'inventories/external-skills.json').read_text())['skills']
  for item in skills.values():
   for key in ('ref','releaseTag','skillFolderHash'):self.assertNotIn(key,item)

 def test_config_preserves_user_keys_and_is_idempotent(self):
  src='model = "user-choice"\n[projects."/sample"]\ntrust_level = "trusted"\n'
  block=s.config_block({'codegraph':'/path with space/cg','gam_mcp':'/gam'})
  first=s.managed_config(src,block)
  self.assertEqual(s.managed_config(first,block),first)
  self.assertIn('model = "user-choice"',first)
  self.assertNotIn('--direct',block)
  self.assertIn('default_mode = "hybrid"',s.gam_profile(Path.home()))
 def test_unmanaged_mcp_conflict_is_refused(self):
  with self.assertRaises(RuntimeError):s.managed_config('[mcp_servers.codegraph]\ncommand="mine"','')
 def test_restore_preserves_later_user_edits(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'config';p.write_text('before');backup=s.backup_write(p,b'after',Path(d)/'state')
   p.write_text('user change')
   with self.assertRaises(RuntimeError):s.restore(backup)
   self.assertEqual(p.read_text(),'user change')
   p.write_text('after');s.restore(backup);self.assertEqual(p.read_text(),'before')
 def test_routes_all_exact_effort(self):
  expected={'ultrabrain':'xhigh','architect':'xhigh','deep':'high','visual-engineering':'high','artistry':'high','deep-work':'max','writing':'medium','capable':'medium','unspecified-high':'medium','quick':'low','simple-work':'low','unspecified-low':'low'}
  self.assertEqual({k:v['effort'] for k,v in s.routes().items()},expected)
  for k,e in expected.items():self.assertIn('model_reasoning_effort='+json.dumps(e),command(k,'test-model','/repo'))
 def test_expiry_protects_valuable_memories(self):
  policy=json.loads((s.ROOT/'config/retention.json').read_text());now=datetime.datetime(2026,10,5,tzinfo=datetime.timezone.utc)
  m={'scope':'project','status':'active','type':'fact','importance':0.5,'tags':['temporary','expires:2026-10-01']}
  self.assertTrue(expired_memory(m,now,policy))
  for patch in [{'scope':'global'},{'status':'candidate'},{'type':'decision'},{'importance':0.9},{'tags':m['tags']+['pinned']},{'tags':['temporary']}]:self.assertFalse(expired_memory(m|patch,now,policy))
 def test_cleanup_does_not_follow_symlinks_or_touch_unknown_files(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);logs=root/'logs';logs.mkdir();outside=root/'outside.log';outside.write_text('keep')
   (logs/'link.log').symlink_to(outside);(logs/'keep.txt').write_text('keep');old=logs/'old.log';old.write_text('expired');os.utime(old,(0,0))
   policy={'owned_log_days':30,'receipt_days':180}
   self.assertEqual(log_candidates(root,datetime.datetime.now(datetime.timezone.utc),policy),[old.resolve()])
 def test_skills_have_real_refs_and_no_runtime_dependency(self):
  manifest=json.loads((s.ROOT/'inventories/coding-skills.json').read_text())
  for item in manifest['skills']:
   p=s.skill_dir(item['name'])/'SKILL.md';t=p.read_text();self.assertIn('description:',t)
   if item['name'].startswith('coding-') or item['name'] in ['gam-memory','codegraph-context']:
    self.assertNotIn('omh runtime',t);self.assertNotIn('~/.hermes',t)
if __name__=='__main__':unittest.main()
