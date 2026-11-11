import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('usage_filter', ROOT / 'scripts/configure_provider_usage.py')
assert spec is not None and spec.loader is not None
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)

# The v0.2.0 source anchors, without credentials or dependency imports.
SOURCE = """const WARN_PCT = 80
const $barProviders = atom(null)
if (Array.isArray(bar)) $barProviders.set(bar)
for (const p of data.providers) { check(p) }
const provs = data.providers || []
const rows = data && Array.isArray(data.providers) ? data.providers : []
const panels = () => { const provs = data && Array.isArray(data.providers) ? data.providers : []; return provs }
const CODE = { 'openai-codex': 'codex' }
"""
# The v0.4.x source anchors: no WARN_PCT/CODE map, the bar reads p.code, and
# staleBackend keeps its own two-space provider loop.
SOURCE_V04 = """const USAGE_KEY = ['plugin-provider-usage', 'backend']

const INTERVALS = [
const $barProviders = atom(null)
    if (Array.isArray(bar)) $barProviders.set(bar)
    for (const p of data.providers) {
  for (const p of data.providers) {
      code: p.code || p.id,
  return barContent(barModel(data.providers || [], barSet, sessionProvider, mode, avail, choice))
  const rows = data && Array.isArray(data.providers) ? data.providers : []
  const provs = data && Array.isArray(data.providers) ? data.providers : []
"""


class UsageFilterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR'))
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name).resolve()
        self.source = self.home / 'plugins/provider-usage/desktop/plugin.js'
        self.mirror = self.home / 'desktop-plugins/provider-usage/plugin.js'
        for p in (self.source, self.mirror):
            p.parent.mkdir(parents=True)
            p.write_text(SOURCE)

    def test_preview_apply_and_repeat(self):
        result = installer.install(self.home)
        self.assertTrue(all(r['status'] == 'change' for r in result['files']))
        self.assertEqual(self.source.read_text(), SOURCE)
        self.assertEqual(self.mirror.read_text(), SOURCE)
        self.assertFalse((self.home / 'backups').exists())
        installer.install(self.home, apply=True)
        source = self.source.read_bytes()
        self.assertEqual(self.mirror.read_bytes(), source)
        self.assertEqual(source.decode().count(installer.START), 1)
        result = installer.install(self.home, apply=True)
        self.assertTrue(all(r['status'] == 'unchanged' for r in result['files']))
        self.assertEqual(self.source.read_bytes(), source)
        backups = list((self.home / 'backups/provider-usage').glob('*.js'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), SOURCE)
        self.assertEqual(backups[0].stat().st_mode & 0o777, 0o600)

    def test_display_filter_runs_in_javascript(self):
        result = installer.adapt(SOURCE)
        start = result.index(installer.START)
        end = result.index(installer.END) + len(installer.END)
        program = result[start:end] + """
const input = {providers: [
  {id:'nous', name:'Nous'}, {id:'openai-codex', name:'OpenAI Codex', status:'error'},
  {id:'openrouter', name:'OpenRouter'}, {id:'anthropic', name:'Anthropic', status:'ok'},
  {id:'copilot', name:'GitHub Copilot'}, null
]};
console.log(JSON.stringify({
  providers: setupUsageProviders(input), original: input.providers[1].name,
  absent: setupUsageProviders(undefined), malformed: setupUsageProviders({providers:'bad'})
}));
"""
        run = subprocess.run(['node', '-e', program], capture_output=True, text=True, check=True)
        data = json.loads(run.stdout)
        self.assertEqual([p['id'] for p in data['providers']], ['openai-codex', 'anthropic'])
        self.assertEqual([p['name'] for p in data['providers']], ['GPT', 'Claude'])
        self.assertEqual(data['providers'][0]['status'], 'error')
        self.assertEqual(data['original'], 'OpenAI Codex')
        self.assertEqual(data['absent'], [])
        self.assertEqual(data['malformed'], [])
        self.assertNotIn('for (const p of data.providers)', result)
        self.assertNotIn('const provs = data.providers || []', result)
        self.assertNotIn('const rows = data && Array.isArray(data.providers) ? data.providers : []', result)
        self.assertNotIn('const provs = data && Array.isArray(data.providers) ? data.providers : []', result)

    def test_hidden_provider_choices_survive_eye_toggles(self):
        source = installer.adapt(SOURCE)
        block = source[source.index(installer.START):source.index(installer.END) + len(installer.END)]
        initial = next(line for line in source.splitlines() if line.startswith('const $barProviders'))
        restore = next(line for line in source.splitlines() if line.startswith('if (Array.isArray(bar))'))
        program = """
let value;
const atom = initial => ({set: v => { value = v }, get: () => value});
const bar = ['openrouter', 'openai-codex'];
""" + block + '\n' + initial + '\n' + restore + """
const restored = $barProviders.get().slice();
// The existing eye-toggle operation must not erase hidden ids when persisting.
const next = restored.filter(id => id !== 'openai-codex');
console.log(JSON.stringify({restored, next, input: bar}));
"""
        run = subprocess.run(['node', '-e', program], capture_output=True, text=True, check=True)
        result = json.loads(run.stdout)
        self.assertEqual(result['restored'], ['openrouter', 'openai-codex'])
        self.assertEqual(result['next'], ['openrouter'])
        self.assertEqual(result['input'], ['openrouter', 'openai-codex'])

    def test_prior_managed_filter_upgrades_without_losing_customization(self):
        latest = installer.adapt(SOURCE + '\n// Preserve an unrelated customization.\n')
        prior = latest.replace(
            'if (Array.isArray(bar)) $barProviders.set([...bar])',
            'if (Array.isArray(bar)) $barProviders.set(bar.filter(id => SETUP_USAGE_PROVIDERS.includes(id)))',
        )
        try:
            upgraded = installer.adapt(prior)
        except ValueError as exc:
            self.fail('Known complete prior adapter must upgrade: ' + str(exc))
        self.assertEqual(upgraded, latest)
        self.assertEqual(installer.adapt(prior.replace('\n', '\r\n')), latest.replace('\n', '\r\n'))
        damaged = prior.replace('const $barProviders = atom([...SETUP_USAGE_PROVIDERS])',
                                "const $barProviders = atom(['openai-codex'])")
        with self.assertRaises(ValueError):
            installer.adapt(damaged)
        with self.assertRaises(ValueError):
            installer.adapt(prior + '\nif (Array.isArray(bar)) $barProviders.set([...bar])\n')

    def test_full_plugin_mounts_with_real_desktop_dependencies(self):
        import shutil
        home = Path(os.environ.get('HERMES_HOME', str(Path.home() / '.hermes')))
        installed = home / 'plugins/provider-usage/desktop/plugin.js'
        desktop = home / 'desktop-plugins/provider-usage/plugin.js'
        modules = Path(os.environ.get('HERMES_DESKTOP_NODE_MODULES', str(home / 'hermes-agent/node_modules')))
        if not shutil.which('node') or not installed.is_file() or not desktop.is_file():
            self.skipTest('Installed source + desktop copy and Node are needed for the DOM harness')
        if not (modules / 'react/package.json').is_file() or not (modules / 'jsdom/package.json').is_file():
            self.skipTest('Set HERMES_DESKTOP_NODE_MODULES to existing desktop dependencies; no installs are performed')
        # Apply only to isolated copies. Neither live file nor live storage is changed.
        self.source.write_bytes(installed.read_bytes())
        self.mirror.write_bytes(desktop.read_bytes())
        installer.install(self.home, apply=True)
        for plugin in (self.source, self.mirror):
            run = subprocess.run([
                'node', '--experimental-vm-modules', str(ROOT / 'tests/provider_usage_dom.mjs'),
                str(plugin), str(modules),
            ], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            data = json.loads(run.stdout)
            self.assertEqual(data['checks'], 9)
            cases = {case['name']: case for case in data['scenarios']}
            self.assertEqual(cases['fresh']['bar'], 'gpt 85% · claude 91%')
            self.assertEqual(cases['mixed-hidden-choice']['savedBar'], ['openrouter'])
            self.assertEqual(cases['explicit-empty']['bar'], '')

    def test_v04_source_adapts_once(self):
        result = installer.adapt(SOURCE_V04)
        self.assertIn(installer.BLOCK + '\nconst INTERVALS = [', result)
        self.assertIn('    for (const p of setupUsageProviders(data)) {', result)
        self.assertIn('\n  for (const p of data.providers) {', result)  # staleBackend unchanged
        self.assertIn("code: p.id === 'openai-codex' ? 'gpt' : p.code || p.id,", result)
        self.assertIn('barModel(setupUsageProviders(data), barSet', result)
        self.assertIn('const $barProviders = atom([...SETUP_USAGE_PROVIDERS])', result)
        self.assertEqual(installer.adapt(result), result)
        with self.assertRaises(ValueError):
            installer.adapt(result.replace('const rows = setupUsageProviders(data)',
                                           'const rows = data && Array.isArray(data.providers) ? data.providers : []'))

    def test_v04_source_with_prior_adapted_mirror(self):
        # update.sh adapts the new source and the old desktop copy, then copies the source over.
        prior = installer.adapt(SOURCE)
        self.source.write_text(SOURCE_V04)
        self.mirror.write_text(prior)
        result = installer.install(self.home, apply=True)
        self.assertEqual([r['status'] for r in result['files']], ['changed', 'unchanged'])
        self.assertEqual(self.source.read_text(), installer.adapt(SOURCE_V04))
        self.assertEqual(self.mirror.read_text(), prior)

    def test_unrelated_customization_preserved(self):
        source = SOURCE + '\n// Keep my refresh interval customization.\n'
        self.assertTrue(installer.adapt(source).endswith('// Keep my refresh interval customization.\n'))

    def test_all_targets_validated_before_writes(self):
        self.mirror.write_text('Unsupported upstream version')
        with self.assertRaises(ValueError):
            installer.install(self.home, apply=True)
        self.assertEqual(self.source.read_text(), SOURCE)
        self.assertEqual(self.mirror.read_text(), 'Unsupported upstream version')
        self.assertFalse((self.home / 'backups').exists())

    def test_changed_managed_block_rejected(self):
        patched = installer.adapt(SOURCE).replace("name: p.id === 'openai-codex' ? 'GPT' : 'Claude'", "name: 'Personal label'")
        with self.assertRaises(ValueError):
            installer.adapt(patched)

    def test_partial_install_rejected(self):
        patched = installer.adapt(SOURCE).replace('const provs = setupUsageProviders(data)', 'const provs = data.providers || []')
        with self.assertRaises(ValueError):
            installer.adapt(patched)

    def test_missing_plugin_does_not_create_it(self):
        with self.assertRaises(FileNotFoundError):
            installer.install(self.home / 'absent', apply=True)
        self.assertFalse((self.home / 'absent').exists())

    def test_symlink_refused(self):
        self.mirror.unlink()
        self.mirror.symlink_to(self.source)
        with self.assertRaises(ValueError):
            installer.install(self.home, apply=True)
        self.assertEqual(self.source.read_text(), SOURCE)

    def test_crlf_preserved(self):
        raw = SOURCE.replace('\n', '\r\n')
        self.source.write_bytes(raw.encode())
        self.mirror.write_bytes(raw.encode())
        installer.install(self.home, apply=True)
        content = self.source.read_bytes()
        self.assertNotIn(b'\n', content.replace(b'\r\n', b''))


if __name__ == '__main__':
    unittest.main()
