"""Bounded checks of declared logical objects and explicit directed geometry.

This module is dependency-free. It validates a scene contract, not scientific
truth inferred from a bitmap. Unspecified semantics remain REVIEW_REQUIRED.
"""
from __future__ import annotations
import math


def _distance(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])


def _point(value):
    return isinstance(value, (list, tuple)) and len(value) == 2 and all(
        isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) for x in value)


def _status(findings):
    return 'FAIL' if any(f['level'] == 'FAIL' for f in findings) else 'REVIEW_REQUIRED' if findings else 'PASS'


def _endpoints(item):
    if item.get('type') == 'line' and len(item.get('points', [])) >= 2:
        return item['points'][0], item['points'][-1]
    if item.get('type') == 'path':
        commands = item.get('commands', [])
        # Multiple subpaths and closed shapes have no unique directed endpoint.
        if sum(c[0] == 'M' for c in commands) == 1 and not any(c[0] == 'Z' for c in commands):
            if commands and commands[0][0] == 'M' and commands[-1][0] in ('L', 'C'):
                return commands[0][1:3], commands[-1][-2:]
    return None


def audit_semantics(spec):
    items = {p['id']: p for p in spec['items']}
    groups, relations = [], []
    for rule in spec.get('count_constraints', []):
        findings = []
        def issue(level, check, **details):
            findings.append(dict(level=level, check=check, **details))
        scope = rule.get('scope')
        expected = rule.get('expected_logical_ids')
        if not scope or expected is None:
            issue('REVIEW_REQUIRED', 'legacy_count_scope', reason='Enumerated item IDs prove presence only; extra objects and states are not covered')
        else:
            if set(scope) - {'id_prefix', 'entity'} or not any(scope.get(k) for k in ('id_prefix', 'entity')):
                issue('FAIL', 'invalid_count_scope')
            if not isinstance(expected, list) or any(not isinstance(x, str) for x in expected):
                issue('FAIL', 'invalid_logical_ids')
                expected = []
            if len(expected) != len(set(expected)) or len(expected) != rule.get('expected'):
                issue('FAIL', 'logical_count_contract')
            selected = [p for p in items.values() if
                (not scope.get('id_prefix') or p['id'].startswith(scope['id_prefix'])) and
                (not scope.get('entity') or p.get('entity') == scope['entity'])]
            primary = {}
            for p in selected:
                part, logical = p.get('object_part'), p.get('logical_id')
                if part not in ('primary', 'decoration', 'legend', 'detail'):
                    issue('FAIL', 'unclassified_counted_item', item=p['id'])
                elif part == 'primary':
                    primary.setdefault(logical, []).append(p)
                elif part in ('decoration', 'detail') and logical not in expected:
                    issue('FAIL', 'unbound_decorative_or_detail_item', item=p['id'], logical_id=logical)
            actual = set(primary)
            if actual != set(expected):
                issue('FAIL', 'logical_object_set', expected=expected,
                      actual=sorted(actual, key=str), missing=sorted(set(expected)-actual),
                      extra=sorted(actual-set(expected), key=str))
            for logical, parts in primary.items():
                if len(parts) != 1:
                    issue('FAIL', 'duplicate_logical_primary', logical_id=logical, items=[p['id'] for p in parts])
            if 'expected_states' in rule:
                states, state_field = rule['expected_states'], rule.get('state_field', 'state')
                if not isinstance(states, dict) or set(states) != set(expected):
                    issue('FAIL', 'incomplete_state_contract')
                else:
                    for logical, value in states.items():
                        for p in primary.get(logical, []):
                            # JSON booleans are not interchangeable with 0/1 occupancy.
                            actual_value = p.get(state_field)
                            if state_field not in p or type(actual_value) is not type(value) or actual_value != value:
                                issue('FAIL', 'logical_state', item=p['id'], expected=value, actual=actual_value)
                            styles = [x['style'] for x in rule.get('state_styles', []) if
                                      type(x.get('state')) is type(value) and x['state'] == value]
                            if len(styles) > 1:
                                issue('FAIL', 'ambiguous_state_style', logical_id=logical)
                            elif styles:
                                for key, expected_style in styles[0].items():
                                    if p.get(key) != expected_style:
                                        issue('FAIL', 'state_visual_encoding', item=p['id'], field=key,
                                              expected=expected_style, actual=p.get(key))
                            else:
                                issue('REVIEW_REQUIRED', 'state_visual_encoding_unspecified', item=p['id'])
            elif any('occupied' in p or 'state' in p for parts in primary.values() for p in parts):
                issue('REVIEW_REQUIRED', 'expected_states_unspecified')
        groups.append({'name': rule['name'], 'status': _status(findings), 'findings': findings})

    for relation in spec.get('relations', []):
        findings = []
        def issue(level, check, **details):
            findings.append(dict(level=level, check=check, **details))
        geometry = relation.get('geometry')
        if not geometry:
            issue('REVIEW_REQUIRED', 'relation_geometry_unspecified')
        else:
            tolerance = geometry.get('tolerance', 1.)
            if not isinstance(tolerance, (int, float)) or not math.isfinite(tolerance) or tolerance < 0:
                issue('FAIL', 'invalid_relation_tolerance')
                tolerance = 0.
            item = items.get(geometry.get('item_id'))
            expected_start, expected_end = geometry.get('from'), geometry.get('to')
            if item is None:
                issue('FAIL', 'relation_item_absent')
            elif item.get('relation') != relation['id']:
                issue('FAIL', 'relation_item_binding', item=item['id'])
            if not _point(expected_start) or not _point(expected_end) or expected_start == expected_end:
                issue('FAIL', 'invalid_explicit_endpoints')
            elif item is not None:
                endpoints = _endpoints(item)
                if endpoints is None:
                    issue('REVIEW_REQUIRED', 'relation_geometry_not_auditable', item=item['id'])
                elif any(_distance(a, b) > tolerance for a, b in zip(endpoints, (expected_start, expected_end))):
                    issue('FAIL', 'directed_relation_endpoints', expected=[expected_start, expected_end], actual=endpoints)
                arrow = geometry.get('arrow')
                if arrow is None and geometry.get('arrow_required', True):
                    issue('REVIEW_REQUIRED', 'arrow_geometry_unspecified')
                elif arrow is not None:
                    shape = items.get(arrow.get('item_id'))
                    tip, base = arrow.get('tip'), arrow.get('base')
                    if shape is None:
                        issue('FAIL', 'arrow_item_absent')
                    elif shape.get('relation') != relation['id']:
                        issue('FAIL', 'arrow_relation_binding')
                    elif shape.get('type') != 'polygon' or len(shape.get('points', [])) != 3:
                        issue('REVIEW_REQUIRED', 'arrow_geometry_not_auditable', reason='Automatic arrow check supports a three-vertex polygon')
                    elif not _point(tip) or not _point(base):
                        issue('FAIL', 'invalid_arrow_points')
                    else:
                        points = shape['points']
                        tip_index = min(range(3), key=lambda i: _distance(points[i], tip))
                        others = [p for i, p in enumerate(points) if i != tip_index]
                        actual_base = [(a+b)/2 for a, b in zip(*others)]
                        vector = [tip[i]-base[i] for i in (0, 1)]
                        # Compare to the final tangent, not just overall displacement.
                        if item.get('type') == 'line':
                            previous = item['points'][-2]
                        elif item.get('type') == 'path' and endpoints:
                            last = item['commands'][-1]
                            previous = last[3:5] if last[0] == 'C' else item['commands'][-2][-2:]
                        else:
                            previous = expected_start
                        incoming = [expected_end[i]-previous[i] for i in (0, 1)]
                        norms = math.hypot(*vector)*math.hypot(*incoming)
                        cosine = sum(a*b for a, b in zip(vector, incoming))/norms if norms else -1
                        if (_distance(points[tip_index], tip) > tolerance or
                            _distance(actual_base, base) > tolerance or
                            _distance(tip, expected_end) > tolerance or cosine < .95):
                            issue('FAIL', 'arrow_direction_or_geometry', arrow=shape['id'], direction_cosine=cosine)
        relations.append({'id': relation['id'], 'status': _status(findings), 'findings': findings})
    all_findings = [f for entry in groups+relations for f in entry['findings']]
    components = None
    if spec.get('component_constraints') or spec.get('occlusion_constraints'):
        from scene_components import audit_components
        components = audit_components(spec)
        all_findings.extend(components['findings'])
    return {'status': _status(all_findings), 'scope': 'Declared object sets/states and explicit endpoint/triangle geometry only; author meaning remains unverified',
            'object_counts': groups, 'directed_relations': relations,
            'count_scope': 'DECLARED' if groups else 'NOT_DECLARED', 'findings': all_findings,
            **({'components': components} if components is not None else {})}
