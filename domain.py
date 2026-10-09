"""Approval depends on the current version of campaign-required artifacts."""
import math
from urllib.parse import urlsplit
from core import Problem, require, text, integer, iso

PIECES = {'script', 'video', 'cover', 'caption'}

def missing(delivery):
    return [piece for piece in delivery['required_pieces'] if not delivery['pieces'].get(piece)
            or not delivery['pieces'][piece][-1]['approved']]

def refresh(delivery):
    pending = missing(delivery)
    delivery['pending_pieces'] = pending
    delivery['state'] = 'in_production' if pending else ('approved' if delivery['approval_requested'] else 'ready_for_approval')
    return delivery

def role(data, expected): require(text(data, 'actor') == expected, expected + ' role required', 403)

def dispatch(state, method, path, data, now):
    campaigns, deliveries = state.setdefault('campaigns', {}), state.setdefault('deliveries', {})
    if method == 'POST' and path == '/campaigns':
        role(data, 'brand')
        ident, required = text(data, 'id'), data.get('required_pieces')
        require(isinstance(required, list) and len(required) > 0 and all(isinstance(p, str) and p in PIECES for p in required), 'required_pieces must list known pieces')
        require(len(required) == len(set(required)), 'required pieces must be unique')
        require(ident not in campaigns, 'campaign already exists', 409)
        campaigns[ident] = {'id': ident, 'required_pieces': required}
        return campaigns[ident]
    if method == 'POST' and path == '/deliveries':
        role(data, 'creator')
        ident, campaign_id = text(data, 'id'), text(data, 'campaign_id')
        require(campaign_id in campaigns, 'campaign not found', 404)
        require(ident not in deliveries, 'delivery already exists', 409)
        deliveries[ident] = {'id': ident, 'campaign_id': campaign_id, 'required_pieces': campaigns[campaign_id]['required_pieces'][:],
                             'pieces': {}, 'approval_requested': False, 'events': []}
        return refresh(deliveries[ident])
    parts = path.strip('/').split('/')
    require(len(parts) >= 2 and parts[0] == 'deliveries', 'route not found', 404)
    delivery = deliveries.get(parts[1])
    require(delivery is not None, 'delivery not found', 404)
    if method == 'GET' and len(parts) == 2: return refresh(delivery)
    require(method == 'POST', 'route not found', 404)
    if len(parts) == 3 and parts[2] == 'approve':
        role(data, 'brand')
        pending = missing(delivery)
        require(not pending, 'required pieces pending: ' + ', '.join(pending), 409)
        delivery['approval_requested'] = True
        delivery['events'].append({'action': 'delivery_approved', 'at': iso(now)})
        return refresh(delivery)
    require(len(parts) in (5, 7) and parts[2] == 'pieces' and parts[4] == 'versions', 'route not found', 404)
    piece = parts[3]
    require(piece in PIECES, 'unknown piece')
    versions = delivery['pieces'].setdefault(piece, [])
    if len(parts) == 5:
        role(data, 'creator')
        require(integer(data, 'previous_version') == len(versions), 'stale piece version', 409)
        url = text(data, 'url')
        require(urlsplit(url).scheme in ('https', 'http') and bool(urlsplit(url).netloc), 'absolute HTTP(S) URL required')
        duration = data.get('duration_seconds')
        if piece == 'video':
            require(type(duration) in (int, float) and math.isfinite(duration) and duration > 0, 'positive finite video duration required')
        versions.append({'version': len(versions) + 1, 'url': url, 'duration_seconds': duration if piece == 'video' else None,
                         'submitted_at': iso(now), 'approved': False, 'comments': []})
        delivery['events'].append({'action': 'version_submitted', 'piece': piece, 'version': len(versions), 'at': iso(now)})
        return refresh(delivery)
    require(parts[5].isdigit() and 1 <= int(parts[5]) <= len(versions), 'version not found', 404)
    version = versions[int(parts[5]) - 1]
    if parts[6] == 'approve':
        role(data, 'brand')
        require(version is versions[-1], 'cannot approve a superseded version', 409)
        version.update(approved=True, approved_at=iso(now))
        delivery['events'].append({'action': 'piece_approved', 'piece': piece, 'version': version['version'], 'at': iso(now)})
    elif parts[6] == 'comments':
        require(text(data, 'actor') in ('brand', 'creator'), 'invalid actor', 403)
        require(piece == 'video', 'timestamp comments apply to video')
        seconds = data.get('second')
        require(type(seconds) in (int, float) and math.isfinite(seconds) and 0 <= seconds <= version['duration_seconds'], 'comment timestamp outside video')
        version['comments'].append({'id': len(version['comments']) + 1, 'second': seconds, 'text': text(data, 'text'),
                                    'actor': data['actor'], 'version': version['version'], 'created_at': iso(now)})
    else:
        raise Problem('route not found', 404)
    return refresh(delivery)
