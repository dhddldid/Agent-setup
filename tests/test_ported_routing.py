"""Executor-scoped routing and shared-tool contracts."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HERMES_ONLY_SKILLS = {
    "dag-ulw-notes": "Uses the Hermes-only omh_dag runtime for split-first orchestration.",
}


CLAUDE_COMMON = {
    # OMH v4.0.0 deep-work head (Opus 5.5 -> GPT-6.1 Sol, max), applied 2026-10-20.
    "deep-work": ("claude-opus-5-5 gpt-6.1-sol", "max"),
}
CLAUDE_PRESETS = {
    # OMH 4.0.7 recommended order limited to GPT and Claude models (decision 2026-11-10).
    "claude-generous": {
        "ultrabrain": ("gpt-6-astra", "xhigh"),
        "deep": ("claude-opus-5-5 gpt-6.1-sol", "high"),
        "architect": ("claude-opus-5-5 gpt-6-astra claude-fable-5-1", "xhigh"),
        "unspecified-high": ("gpt-6.1-sol claude-opus-5-5", "medium"),
        "unspecified-low": ("gpt-6.1-sol claude-sonnet-5-5", "low"),
        "quick": ("gpt-6-luna claude-haiku-5-5", "low"),
        "writing": ("claude-opus-5-5 claude-sonnet-5-5", "medium"),
        "visual-engineering": ("claude-opus-5-5 claude-fable-5-1", "high"),
        "artistry": ("claude-opus-5-5 claude-fable-5-1", "high"),
        "capable": ("claude-opus-5-5 gpt-6.1-sol claude-fable-5-1", "medium"),
        "simple-work": ("gpt-6-luna claude-haiku-5-5", "low"),
    },
    "gpt-generous": {
        "ultrabrain": ("gpt-6-astra claude-fable-5-1 claude-opus-5-5", "xhigh"),
        "deep": ("gpt-6.1-sol claude-fable-5-1 claude-opus-5-5", "high"),
        "architect": ("claude-fable-5-1 gpt-6-astra claude-opus-5-5", "xhigh"),
        "unspecified-high": ("claude-opus-5-5", "medium"),
        "unspecified-low": ("claude-opus-5-5", "low"),
        "quick": ("gpt-6-luna claude-fable-5-1 claude-opus-5-5 gpt-6-astra", "low"),
        "simple-work": ("gpt-6-luna claude-fable-5-1 claude-opus-5-5 claude-haiku-5-5", "low"),
        "writing": ("gpt-6.1-sol claude-opus-5-5", "medium"),
        "visual-engineering": ("claude-fable-5-1 gpt-6-astra claude-opus-5-5", "high"),
        "artistry": ("claude-fable-5-1 gpt-6-astra claude-opus-5-5", "high"),
        "capable": ("claude-fable-5-1 gpt-6-astra claude-opus-5-5 claude-sonnet-5-5", "medium"),
    },
}


class PortedRoutingTests(unittest.TestCase):
    def test_external_claude_presets_preserve_their_approved_policy(self):
        claude = json.loads((ROOT / "claude/routes/claude-code.json").read_text())["presets"]
        for preset, own in CLAUDE_PRESETS.items():
            rows = {**CLAUDE_COMMON, **own}
            expected = {k: [{"model": m, "effort": e} for m in models.split()] for k, (models, e) in rows.items()}
            self.assertEqual(claude[preset], expected, preset)

    def test_aside_rule_is_present_for_codex_and_claude(self):
        for path in ("codex/instructions/AGENTS.md", "claude/templates/global-rules.md"):
            text = (ROOT / path).read_text()
            self.assertIn("aside repl", text, path)
            self.assertIn("aside exec", text, path)

    def test_hermes_copies_match_shared_skills(self):
        manifest = json.loads((ROOT / "hermes/manifest.json").read_text())
        local = [s["name"] for s in manifest["skills"] if s["source_kind"] == "local"]
        self.assertEqual(sorted(local), sorted(p.name for p in (ROOT / "hermes/skills").iterdir() if p.is_dir()))
        for name in local:
            shared = ROOT / "shared/skills/core" / name
            if not shared.is_dir():
                shared = ROOT / "shared/skills/packs/mac" / name
            if name in HERMES_ONLY_SKILLS and not shared.is_dir():
                continue
            hermes = ROOT / "hermes/skills" / name
            def tracked(root):
                return sorted(p.relative_to(root) for p in root.rglob("*")
                              if p.is_file() and "__pycache__" not in p.parts)
            files = tracked(shared)
            self.assertEqual(files, tracked(hermes), name)
            for rel in files:
                self.assertEqual((hermes / rel).read_bytes(), (shared / rel).read_bytes(), f"{name}/{rel}")

    def test_shared_core_has_no_personal_or_executor_paths(self):
        omh = ROOT / "shared/skills/omh"
        for path in (ROOT / "shared/skills").rglob("*.md"):
            text = path.read_text()
            # OMH skills are upstream copies; executor mapping lives in shared/rules/omh.md.
            checks = ("/Users/",) if omh in path.parents else ("/Users/", "~/.hermes", "omh runtime", "Codex-Setup/03-skills")
            for bad in checks:
                self.assertNotIn(bad, text, f"{path}: {bad}")

    def test_omh_copy_records_its_upstream_version(self):
        source = json.loads((ROOT / "shared/skills/omh/SOURCE.json").read_text())
        skills = list((ROOT / "shared/skills/omh").glob("*/SKILL.md"))
        self.assertEqual(source["skills"], len(skills))
        self.assertTrue(source["version"])
        for skill in skills:
            head = skill.read_text().split("---")[1]
            self.assertIn("\ndescription: \"", head, str(skill))


if __name__ == "__main__":
    unittest.main()
