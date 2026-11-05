#!/usr/bin/env python3
"""Merge Agent-setup Korean cues into OMH's supported user-pack path.

User packs feed OMH recommendation scoring. The plugin's generated Hangul
shortlist remains owned by OMH. Existing phrases and hold-back entries survive.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import re
import tempfile

SOURCE = Path(__file__).resolve().parents[1] / 'omh/trigger-packs/ko.json'
SCHEMA = 'trigger_language_pack/v1'


def read_pack(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(raw, dict):
        raise ValueError(f'{path}: 팩은 JSON 객체여야 합니다')
    if raw.get('schema_version') != SCHEMA or raw.get('language') != 'ko':
        raise ValueError(f'{path}: 한국어 팩 스키마를 확인하세요')
    if set(raw) - {'schema_version', 'language', 'skills', 'whole_phrase_only_tokens'}:
        raise ValueError(f'{path}: 지원하지 않는 필드가 있습니다')
    if not isinstance(raw.get('skills'), dict) or not raw['skills']:
        raise ValueError(f'{path}: skills에 트리거를 지정하세요')
    for field in ('skills', 'whole_phrase_only_tokens'):
        mapping = raw.get(field, {})
        if not isinstance(mapping, dict):
            raise ValueError(f'{path}: {field}는 객체여야 합니다')
        for skill, phrases in mapping.items():
            if not re.fullmatch(r'[a-z][a-z0-9-]*', skill):
                raise ValueError(f'{path}: 스킬 ID를 확인하세요: {skill}')
            if not isinstance(phrases, list) or not phrases:
                raise ValueError(f'{path}: {skill}의 트리거 목록을 확인하세요')
            seen = set()
            for phrase in phrases:
                if (not isinstance(phrase, str) or not phrase.strip()
                        or (field == 'skills' and len(phrase.strip()) > 120)
                        or not any(c.isalnum() for c in phrase)):
                    raise ValueError(f'{path}: {skill}의 트리거 문자열을 확인하세요')
                if phrase.strip() in seen:
                    raise ValueError(f'{path}: {skill}에 중복 트리거가 있습니다')
                seen.add(phrase.strip())
    return raw


def merge_pack(existing: dict, source: dict) -> dict:
    merged = copy.deepcopy(existing)
    for field in ('skills', 'whole_phrase_only_tokens'):
        for skill, phrases in source.get(field, {}).items():
            bucket = merged.setdefault(field, {}).setdefault(skill, [])
            seen = {phrase.strip() for phrase in bucket}
            for phrase in phrases:
                if phrase.strip() not in seen:
                    bucket.append(phrase)
                    seen.add(phrase.strip())
    return merged


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='OMH 한국어 트리거 팩 병합 설치')
    parser.add_argument('--omh-home', type=Path,
                        default=Path(os.environ.get('OMH_HOME') or '~/.omh').expanduser(),
                        help='OMH 사용자 홈 (기본: OMH_HOME 또는 ~/.omh)')
    parser.add_argument('--source', type=Path, default=SOURCE, help='관리 원본 팩')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true', help='누락된 트리거 병합')
    mode.add_argument('--check', action='store_true', help='누락되면 종료 코드 1 반환')
    args = parser.parse_args(argv)
    target = args.omh_home.expanduser() / 'routing/trigger-packs/ko.json'
    try:
        source = read_pack(args.source.expanduser())
        existing = read_pack(target) if target.exists() else {
            'schema_version': SCHEMA, 'language': 'ko', 'skills': {}}
        merged = merge_pack(existing, source)
        drift = merged != existing
        if not drift:
            print(f'일치: 한국어 트리거 팩 {target}')
            return 0
        additions = sum(len(v) for v in merged['skills'].values()) - sum(
            len(v) for v in existing['skills'].values())
        if args.check:
            print(f'차이 있음: 한국어 트리거 {additions}개 추가 필요 ({target})')
            return 1
        if not args.apply:
            print(f'미리보기: 한국어 트리거 {additions}개 추가 예정 ({target}); --apply로 적용')
            return 0
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                             dir=target.parent, delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(merged, stream, ensure_ascii=False, indent=2)
                stream.write('\n')
            temporary.replace(target)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        print(f'적용: 한국어 트리거 {additions}개 추가 ({target}); 새 OMH 프로세스에서 로드')
        return 0
    except (OSError, ValueError) as error:
        print(f'오류: {error}')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
