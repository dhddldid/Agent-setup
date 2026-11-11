"""Approved Hermes-only routing policy; preserve other executor policies."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    # OMH 4.0.7 recommended order with non-GPT/Claude models removed (decision 2026-11-10);
    # writing/artistry/synthesize put Sol first so Opus stays on coding (decision 2026-11-12).
    'ultrabrain': ('gpt-6-astra', 'xhigh'),
    'deep': ('claude-opus-5-5 gpt-6.1-sol', 'high'),
    'architect': ('claude-opus-5-5 gpt-6-astra claude-fable-5-1', 'xhigh'),
    'unspecified-high': ('gpt-6.1-sol claude-opus-5-5', 'medium'),
    'unspecified-low': ('gpt-6.1-sol claude-sonnet-5-5', 'low'),
    'quick': ('gpt-6-luna claude-haiku-5-5', 'low'),
    'writing': ('gpt-6.1-sol claude-opus-5-5', 'medium'),
    'visual-engineering': ('claude-opus-5-5 claude-fable-5-1', 'high'),
    'artistry': ('gpt-6.1-sol claude-opus-5-5 claude-fable-5-1', 'high'),
    'capable': ('claude-opus-5-5 gpt-6.1-sol claude-fable-5-1', 'medium'),
    'simple-work': ('gpt-6-luna claude-haiku-5-5', 'low'),
    'deep-work': ('claude-opus-5-5 gpt-6.1-sol', 'high'),  # lowered from max (decision 2026-11-12)
    'google-search': ('gpt-6.1-sol claude-opus-5-5', 'medium'),
    'x-search': ('gpt-6.1-sol', 'high'),
    'review': ('gpt-6.1-sol claude-opus-5-5', 'xhigh'),
    'swarm': ('gpt-6-luna', 'low'),
    'forensics': ('gpt-6-astra claude-opus-5-5', 'xhigh'),
    'synthesize': ('gpt-6.1-sol claude-opus-5-5', 'xhigh'),
}

class ClaudeGenerousPolicyTests(unittest.TestCase):
    def test_all_approved_orders_and_efforts(self):
        p = json.loads((ROOT / 'routing-presets/claude-generous.json').read_text())
        actual = {r['category']: [(e['model'], e['reasoning_effort']) for e in r['chain']] for r in p['categories']}
        expected = {k: [(m, effort) for m in models.split()] for k, (models, effort) in EXPECTED.items()}
        self.assertEqual(actual, expected)
        self.assertEqual(p['fallback_providers'], [{'provider': 'anthropic', 'model': 'claude-opus-5-5'}])
        self.assertEqual(p['delegation_fallback_providers'], [
            {'provider': 'anthropic', 'model': 'claude-opus-5-5'},
            {'provider': 'openai-codex', 'model': 'gpt-6-astra'},
            {'provider': 'anthropic', 'model': 'claude-sonnet-5-5'}])
