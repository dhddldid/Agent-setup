"""Verify the two quota-oriented routing presets and their copyable commands."""
import json
from pathlib import Path
import re
import shlex
import unittest

ROOT = Path(__file__).resolve().parents[1]
CHANGED = {'ultrabrain', 'deep', 'architect', 'unspecified-high', 'unspecified-low', 'quick',
           'writing', 'visual-engineering', 'artistry', 'capable', 'simple-work'}
OMH_ONLY = {'google-search', 'x-search', 'review', 'swarm', 'forensics', 'synthesize'}


class RoutingPresetTests(unittest.TestCase):
    def setUp(self):
        self.presets = {name: json.loads((ROOT / 'routing-presets' / (name + '.json')).read_text())
                        for name in ['claude-generous', 'gpt-generous']}
        self.chains = {name: {item['category']: item['chain'] for item in preset['categories']}
                       for name, preset in self.presets.items()}

    def test_presets_have_independent_category_policies(self):
        a, b = self.chains['claude-generous'], self.chains['gpt-generous']
        self.assertEqual(len(a), 18)
        self.assertEqual(len(b), 12)
        self.assertEqual(set(a) - set(b), OMH_ONLY)
        self.assertEqual({key for key in b if a[key] != b[key]}, CHANGED)

    def test_gpt_keeps_astra_first_and_deep_work_follows_omh(self):
        chains = self.chains['gpt-generous']
        for key in ['visual-engineering', 'artistry', 'capable']:
            self.assertEqual([x['model'] for x in chains[key]][:2],
                             ['gpt-6-astra', 'claude-opus-5-5'])
        for name in self.chains:
            self.assertEqual([(x['model'], x['reasoning_effort']) for x in self.chains[name]['deep-work']],
                             [('claude-opus-5-5', 'max'), ('gpt-6.1-sol', 'max')])

    def test_fable_only_in_claude_preset_and_chain_text_matches(self):
        self.assertNotIn('claude-fable-5-1', json.dumps(self.presets['gpt-generous']))
        self.assertIn('claude-fable-5-1', json.dumps(self.presets['claude-generous']))
        for name, preset in self.presets.items():
            for item in preset['categories']:
                self.assertEqual(item['chain_text'], ', '.join(
                    x['model'] + ':' + x['reasoning_effort'] for x in item['chain']))

    def test_shared_fallbacks_are_identical_and_opus_last(self):
        a, b = self.presets.values()
        for key in ['fallback_providers', 'delegation_fallback_providers', 'gpt_child_fallback_adapter']:
            self.assertEqual(a[key], b[key])
        self.assertEqual([x['model'] for x in a['delegation_fallback_providers']],
                         ['claude-opus-5-5', 'gpt-6-astra', 'claude-sonnet-5-5'])
        self.assertEqual(a['fallback_providers'],
                         [{'provider': 'anthropic', 'model': 'claude-opus-5-5'}])

    def test_removed_families_are_absent_and_writing_uses_sol_opus(self):
        for name, chains in self.chains.items():
            for chain in chains.values():
                self.assertTrue(all(item['model'].startswith(('gpt-', 'claude-'))
                                    for item in chain))
            expected = ['claude-opus-5-5', 'claude-sonnet-5-5']
            if name == 'gpt-generous':
                expected = ['gpt-6.1-sol', 'claude-opus-5-5']
            self.assertEqual([item['model'] for item in chains['writing']], expected)
            self.assertTrue(all(item['reasoning_effort'] == 'medium'
                                for item in chains['writing']))

    def test_legacy_snapshot_stays_claude_compatible(self):
        legacy = json.loads((ROOT / 'routing-snapshot.json').read_text())
        for key in ['categories', 'fallback_providers', 'delegation_fallback_providers']:
            self.assertEqual(legacy[key], self.presets['claude-generous'][key])

    def test_documented_commands_match_selected_presets(self):
        doc = (ROOT / 'docs/model-routing.md').read_text()
        for name, chains in self.chains.items():
            section = doc.split('### ' + name + ' CLI', 1)[1].split('\n### ', 1)[0]
            lines = re.findall(r'^omh model-chains set .+$', section, re.M)
            self.assertEqual(len(lines), len(chains))
            for line in lines:
                command = shlex.split(line)
                key = command[3]
                expected = ', '.join(x['model'] + ':' + x['reasoning_effort'] for x in chains[key])
                self.assertEqual(command[4], expected)


if __name__ == '__main__':
    unittest.main()
