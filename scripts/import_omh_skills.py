#!/usr/bin/env python3
"""Import OMH (oh-my-hermes) skills so Codex and Claude Code can use them.

Copies every SKILL.md folder from an installed OMH skills tree into
shared/skills/omh/<name>/ (flat), rewrites the frontmatter to `name` plus a
quoted `description`, and records the OMH version in shared/skills/omh/SOURCE.json.
Hermes keeps using its own OMH plugin and does not install this copy.

  python3 scripts/import_omh_skills.py                 # from ~/.omh/skills
  python3 scripts/import_omh_skills.py --source DIR --version <release-tag>
"""
import argparse
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "shared" / "skills" / "omh"
SKIP = {"__pycache__", ".usage.json", ".DS_Store"}


def frontmatter(text):
    match = re.match(r"---\n(.*?)\n---\n?", text, re.S)
    if not match:
        raise ValueError("missing frontmatter")
    fields = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep and not line.startswith((" ", "\t")):
            fields[key.strip()] = value.strip()
    return fields, text[match.end():]


def normalize(text):
    fields, body = frontmatter(text)
    description = fields.get("description", "").strip()
    if len(description) >= 2 and description[0] == description[-1] and description[0] in "\"'":
        description = description[1:-1]
    head = "---\nname: " + fields["name"] + "\ndescription: " + json.dumps(description, ensure_ascii=False) + "\n---\n"
    return head + body.lstrip("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", type=Path, default=Path.home() / ".omh" / "skills")
    parser.add_argument("--version", help="OMH version; read from <source>/../manifest.json when omitted")
    args = parser.parse_args()
    source = args.source.expanduser().resolve()
    version = args.version
    manifest = source.parent / "manifest.json"
    if not version and manifest.is_file():
        version = json.loads(manifest.read_text()).get("version")
    if version:
        version = version.removeprefix("v")
    folders = sorted(p.parent for p in source.rglob("SKILL.md"))
    if not folders:
        raise SystemExit("OMH source contains no skills: " + str(source))
    # Validate the complete input before replacing the previous release copy.
    for folder in folders:
        normalize((folder / "SKILL.md").read_text(encoding="utf-8"))
    names = [p.name for p in folders]
    if len(names) != len(set(names)):
        raise SystemExit("duplicate OMH skill names")
    if TARGET.exists():
        shutil.rmtree(TARGET)
    TARGET.mkdir(parents=True)
    for folder in folders:
        destination = TARGET / folder.name
        shutil.copytree(folder, destination, symlinks=False,
                        ignore=lambda _dir, entries: [e for e in entries if e in SKIP])
        skill = destination / "SKILL.md"
        skill.write_text(normalize(skill.read_text(encoding="utf-8")), encoding="utf-8")
    (TARGET / "SOURCE.json").write_text(json.dumps({
        "package": "oh-my-hermes",
        "upstream": "https://github.com/rlaope/oh-my-hermes",
        "version": version,
        "license": "MIT (../LICENSE-OMH)",
        "skills": len(folders),
        "installed_for": ["codex", "claude"],
    }, indent=2) + "\n")
    print(f"imported {len(folders)} OMH skills (version {version}) into {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
