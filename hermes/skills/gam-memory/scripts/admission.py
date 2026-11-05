"""Bounded admission preflight for sanitized, project-scoped GAM candidates.

This portable screen supports agent review; the OMH classifier and atomic capture
transaction remain backend gaps. It returns reason codes, never raw payloads.
"""
import json
import re
from lifecycle import duplicate_key

SECRET = re.compile(r'(?:-----BEGIN .*PRIVATE KEY-----|\b(?:api[_-]?key|password|secret|access[_-]?token)\s*[:=]\s*\S+|\b(?:sk|ghp|github_pat)[_-][A-Za-z0-9_-]{12,})', re.I)
RELATIVE = re.compile(r'\b(?:today|tomorrow|yesterday|next week|last week|recently)\b|오늘|내일|어제|다음\s*주|지난\s*주', re.I)
COMMAND = re.compile(r'^(?:ignore|always|never|must|run|execute|delete|send|use)\b', re.I)
EXCLUDED = {'log', 'transcript', 'progress', 'quoted', 'pasted', 'current_task'}


def admission(payload, *, mode='auto-safe', existing=(), origin='user',
              derived=False, force_review=False, safety_status='unknown'):
    """Existing entries must already pass project/account/lifecycle gates."""
    if mode not in ('off', 'review-first', 'auto-safe'):
        raise ValueError('Unknown memory mode')
    if mode == 'off':
        return {'persist': False, 'approve': False, 'reason': 'off'}
    raw = json.dumps(payload, ensure_ascii=False, default=str)
    if SECRET.search(raw):
        return {'persist': False, 'approve': False, 'reason': 'blocked_secret'}
    summary = payload.get('summary', '')
    tags = payload.get('tags', [])
    source_ref = payload.get('source_ref', '')
    invalid = (not isinstance(summary, str) or not summary.strip() or len(summary) > 500
               or '\x00' in raw.replace('\\u0000', '\x00')
               or not isinstance(tags, list) or len(tags) > 8
               or any(not isinstance(t, str) or not t.strip() for t in tags)
               or not isinstance(source_ref, str) or len(source_ref) > 160
               or payload.get('scope') != 'project' or not payload.get('project')
               or not payload.get('working_directory'))
    if invalid or origin in EXCLUDED or (isinstance(summary, str) and COMMAND.search(summary)):
        return {'persist': False, 'approve': False, 'reason': 'invalid_or_ineligible'}
    key = duplicate_key(summary)
    if key and any(key == duplicate_key(s) for s in existing):
        return {'persist': False, 'approve': False, 'reason': 'exact_duplicate'}
    if safety_status != 'safe':
        reason = 'safety_review'
    elif RELATIVE.search(raw):
        reason = 'relative_time'
    elif derived:
        reason = 'derived'
    elif force_review or mode == 'review-first':
        reason = 'review_first'
    else:
        reason = 'auto_safe'
    return {'persist': True, 'approve': reason == 'auto_safe', 'reason': reason}


def consolidation_reasons(turns, *, boundary=False, compaction=False,
                          duplicate_clusters=0, expired_or_soon=0,
                          native_cap=None, native_used=None, last_reasons=()):
    """Agent checkpoints only; a caller supplies observed host events/state."""
    reasons = []
    if turns >= 5:
        reasons.append('session_due' if boundary else 'turn_interval')
    if compaction:
        reasons.append('compaction')
    standing = []
    if duplicate_clusters > 0:
        standing.append('duplicate_clusters')
    if expired_or_soon > 0:
        standing.append('expiry_pressure')
    if native_cap is not None and native_used is not None:
        floor = min(300, max(native_cap, 0) * 300 // 2200)
        if native_cap - native_used < floor:
            standing.append('native_headroom')
    if tuple(standing) != tuple(last_reasons):
        reasons.extend(standing)
    return {'reasons': reasons, 'standing_reasons': standing}
