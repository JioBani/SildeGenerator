"""Optional, provider-free creative validation before registering asset work."""

import json
from app.harness_sdk.engine_mode import evaluate_engine_mode


def planning_contract(harness):
    describe = getattr(harness.instance, 'describe_planning_contract', None)
    if describe is None:
        return None
    contract = describe(harness.config)
    if not isinstance(contract, dict) or not isinstance(contract.get('version'), str):
        raise TypeError('Harness planning contract must be a versioned object')
    for field in ('supported_layouts', 'supported_transitions', 'supported_rhythms', 'supported_effects', 'independent_effects', 'constraints'):
        values = contract.get(field)
        if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
            raise TypeError(f'Harness planning contract {field} must be a list of strings')
    routes = contract.get('asset_routes')
    if not isinstance(routes, dict) or any(not isinstance(key, str) or not isinstance(value, str) for key, value in routes.items()):
        raise TypeError('Harness planning contract asset_routes must map strings to strings')
    if len(json.dumps(contract, ensure_ascii=False)) > 12000:
        raise ValueError('Harness planning contract is too large')
    return contract


def validate_harness_plan(harness, scenes):
    boundary_findings = evaluate_engine_mode(scenes, planning_contract(harness))
    validator = getattr(harness.instance, 'validate_plan', None)
    if validator is None:
        return boundary_findings
    findings = validator(scenes, harness.config)
    if not isinstance(findings, list) or any(not isinstance(item, str) for item in findings):
        raise TypeError('Harness validate_plan must return a list of findings')
    return boundary_findings + findings
