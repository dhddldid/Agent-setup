"""Portable OMH lifecycle dates and recall gates; no store I/O.

GAM records carry the contract under metadata.lifecycle or a JSON body section
headed `## GAM lifecycle`. UTC timestamps are authoritative; expiry tags are a
legacy compatibility index. Call derive() once at capture, preserving its output
through approval and cosmetic updates.
"""
import datetime as dt
import json
import math
import unicodedata

UTC = dt.timezone.utc
TYPE_MAP = {'fact': 'fact', 'decision': 'decision', 'solution': 'lesson',
            'convention': 'procedure', 'session_summary': 'episode',
            'preference': 'fact', 'reference': 'fact', 'entity': 'fact', 'project': 'fact'}
TYPES = {'fact', 'decision', 'lesson', 'procedure', 'episode'}
CLASSES = {'durable', 'standard', 'volatile'}


def timestamp(value):
    if not isinstance(value, str) or not value:
        raise ValueError('An absolute ISO timestamp is required')
    parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Timestamp requires a timezone')
    return parsed.astimezone(UTC)


def iso(value):
    return value.astimezone(UTC).isoformat()


def lifecycle(meta, body=''):
    direct = meta.get('lifecycle')
    if direct is None:
        direct = (meta.get('metadata') or {}).get('lifecycle')
    if isinstance(direct, dict):
        return dict(direct)
    marker = '## GAM lifecycle\n```json\n'
    if marker in body:
        return json.loads(body.split(marker, 1)[1].split('\n```', 1)[0])
    return {}


def derive(semantic_type='fact', retention_class='durable', captured_at=None,
           *, ttl_days=None, expires_at=None, stale_days=None, review_due_at=None,
           resolution=None, policy=None):
    """Validate capture overrides and compute immutable deadlines.

    Model captures default durable; CLI callers explicitly choose standard.
    Volatile admits an integer TTL of 1..7 and its default review cadence only.
    """
    policy = policy or {}
    if semantic_type not in TYPES or retention_class not in CLASSES:
        raise ValueError('Unknown semantic type or retention class')
    captured = timestamp(captured_at)
    if ttl_days is not None and expires_at is not None:
        raise ValueError('TTL and absolute expiry are mutually exclusive')
    if stale_days is not None and review_due_at is not None:
        raise ValueError('Review days and absolute deadline are mutually exclusive')
    if retention_class == 'durable' and (ttl_days is not None or expires_at is not None):
        raise ValueError('Durable records carry no TTL')
    if retention_class == 'volatile':
        if expires_at is not None or stale_days is not None or review_due_at is not None:
            raise ValueError('Volatile records accept only a TTL override')
        ttl_days = policy.get('volatile_ttl_days', 7) if ttl_days is None else ttl_days
        if type(ttl_days) is not int or not 1 <= ttl_days <= 7:
            raise ValueError('Volatile TTL must be an integer from 1 to 7')
    if ttl_days is not None and (type(ttl_days) is not int or ttl_days < 1):
        raise ValueError('TTL must be a positive integer')
    if stale_days is not None and (type(stale_days) is not int or stale_days < 1):
        raise ValueError('Review cadence must be a positive integer')
    if retention_class == 'standard' and semantic_type == 'episode' and ttl_days is None and expires_at is None:
        ttl_days = policy.get('standard_episode_ttl_days', 30)
    explicit_review = stale_days is not None or review_due_at is not None
    if not explicit_review and (resolution == 'open' or (retention_class != 'durable' and semantic_type != 'episode')):
        stale_days = policy.get('standard_review_days', 90)
    expiry = timestamp(expires_at) if expires_at else (captured + dt.timedelta(days=ttl_days) if ttl_days else None)
    review = timestamp(review_due_at) if review_due_at else (captured + dt.timedelta(days=stale_days) if stale_days else None)
    if expiry and expiry <= captured:
        raise ValueError('Expiry must follow capture')
    result = {'policy_version': 2, 'semantic_type': semantic_type,
              'retention_class': retention_class, 'captured_at': iso(captured),
              'confirmed_at': iso(captured), 'expires_at': iso(expiry) if expiry else None,
              'review_due_at': iso(review) if review else None,
              'cadence_source': 'explicit' if explicit_review else 'default'}
    if resolution == 'open':
        result.update(resolution='open', open_since=iso(captured),
                      open_expires_at=None if retention_class == 'durable' else iso(captured + dt.timedelta(days=policy.get('open_ceiling_days', 365))),
                      next_ask_at=iso(captured + dt.timedelta(days=policy.get('open_ask_days', 14))))
    elif resolution is not None and resolution != 'resolved':
        raise ValueError('Unknown resolution')
    return result


def protected(meta, policy):
    overlay = policy.get('archive_protection', policy)
    return (bool(set(meta.get('tags', [])).intersection(overlay.get('protect_tags', [])))
            or meta.get('type') in overlay.get('protect_types', ['decision', 'preference', 'convention'])
            or float(meta.get('importance', 1)) >= overlay.get('importance_at_least', .8))


def classify(meta, now, policy, body='', source_state='unchanged'):
    """Report first. Protection affects archive authorization, never expiry."""
    result = {'id': meta.get('id'), 'version': meta.get('updated_at'),
              'state': 'ineligible', 'reasons': [], 'archive_eligible': False,
              'ordinary_recall': False}
    if meta.get('scope') != 'project' or meta.get('status') != 'active':
        result['reasons'] = ['scope_or_status']
        return result
    try:
        data = lifecycle(meta, body)
        legacy = not data
        if legacy:
            # Preserve old temporary-tag maintenance, with date midnight UTC.
            tags = meta.get('tags', [])
            dates = [t[8:] for t in tags if t.startswith('expires:')]
            if 'temporary' in tags and len(dates) == 1:
                expiry = timestamp(dates[0] + 'T00:00:00+00:00')
                data = {'expires_at': iso(expiry)}
            else:
                result.update(state='legacy_review', reasons=['classification_required'])
                return result
        else:
            if data.get('semantic_type') not in TYPES or data.get('retention_class') not in CLASSES:
                raise ValueError('Unknown lifecycle classification')
            timestamp(data['captured_at'])
        expiry = timestamp(data['expires_at']) if data.get('expires_at') else None
        review = timestamp(data['review_due_at']) if data.get('review_due_at') else None
        if data.get('retention_class') == 'durable' and expiry:
            raise ValueError('Durable expiry conflicts with policy')
        if expiry and now >= expiry:
            result.update(state='expired', reasons=['ttl_expired'])
        elif source_state == 'changed':
            result.update(state='stale', reasons=['source_changed'])
        elif source_state == 'unreadable':
            result.update(state='unknown', reasons=['source_unreadable'])
        elif source_state != 'unchanged':
            raise ValueError('Unknown source state')
        elif data.get('resolution') == 'open':
            reasons = []
            if data.get('open_expires_at') and now >= timestamp(data['open_expires_at']):
                reasons.append('open_ceiling_reached')
            if review and now >= review:
                reasons.append('open_review_due')
            if data.get('next_ask_at') and now >= timestamp(data['next_ask_at']):
                reasons.append('open_ask_due')
            result.update(state='open', reasons=reasons, ordinary_recall=False)
        elif review and now >= review:
            result.update(state='stale', reasons=['review_due'])
        else:
            window = policy.get('due_soon_days', 14)
            expiry_window = window
            if expiry and data.get('captured_at'):
                lifespan = (expiry - timestamp(data['captured_at'])).total_seconds() / 86400
                expiry_window = min(window, max(math.floor(lifespan / 2), 1))
            if expiry and expiry - now <= dt.timedelta(days=expiry_window):
                result.update(state='expiring_soon', reasons=['expiry_due_soon'], ordinary_recall=True)
            elif review and review - now <= dt.timedelta(days=window):
                result.update(state='review_soon', reasons=['review_due_soon'], ordinary_recall=True)
            else:
                result.update(state='current', ordinary_recall=not legacy)
        if result['state'] == 'expired':
            blocked = protected(meta, policy)
            result['archive_eligible'] = not blocked
            if blocked:
                result['reasons'].append('archive_protected')
        if legacy:
            result['ordinary_recall'] = False
        result['legacy'] = legacy
    except (ValueError, TypeError, KeyError, OverflowError):
        result.update(state='invalid', reasons=['invalid_lifecycle'], archive_eligible=False, ordinary_recall=False)
    return result


def duplicate_key(summary):
    return ' '.join(unicodedata.normalize('NFC', summary).lower().split())


def recall(records, now, policy, project, *, rejected=False, tags=(), limit=6):
    """Policy gate over fetched candidates; native GAM ranking stays approximate.

    Newest subject revision wins before eligibility, preventing resurrection of
    an older fact when its replacement expires. Rejected evidence stays separate.
    Input order is the upstream candidate rank, not an OMH parity claim.
    """
    newest = {}
    for record in records:
        data = lifecycle(record, record.get('body', ''))
        subject = data.get('subject')
        if subject and record.get('project') == project and record.get('scope') == 'project':
            rank = (timestamp(data['captured_at']), str(record['id']))
            if subject not in newest or rank > newest[subject][0]:
                newest[subject] = (rank, record['id'])
    out, seen = [], set()
    for record in records:
        if record.get('project') != project or record.get('scope') != 'project':
            continue
        data = lifecycle(record, record.get('body', ''))
        if data.get('subject') and newest[data['subject']][1] != record['id']:
            continue
        expected = 'rejected' if rejected else 'active'
        if record.get('status') != expected or not set(tags).issubset(record.get('tags', [])):
            continue
        if record.get('superseded_by') or record.get('safety_status', data.get('safety_status')) != 'safe':
            continue
        if rejected and (record.get('type') != 'decision' or not record.get('reviewed_at') or not record.get('rejection_reason')):
            continue
        state = classify(dict(record, status='active'), now, policy, record.get('body', ''), record.get('source_state', 'unchanged'))
        if not state['ordinary_recall']:
            continue
        key = duplicate_key(record.get('summary', record.get('title', '')))
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(record)
        if len(out) >= min(max(limit, 1), 20 if rejected else 100):
            break
    return out
