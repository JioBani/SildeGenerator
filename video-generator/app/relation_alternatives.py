"""Explicit bounded alternatives for one uncertain inferred cross-beat link."""
import asyncio
import hashlib

from .harness_sdk.semantic_beats import (relation_alternatives_extension, analysis_sha256, inspect_analysis, RELATION_RULES)
from .semantic_gate import SufficiencyVerdict, verdict_findings, gate_context, review_sufficiency
from .semantic_review import review_packet, digest, review_pair, compare_orders
from .tracking import atomic_json


def alternatives_enabled(contract):
    policy = (contract or {}).get('relation_alternatives')
    if policy is None:
        return False
    if policy != relation_alternatives_extension():
        raise ValueError('unsupported_relation_alternatives')
    return True


def relation_variants(analysis, script, report, contract, generator_model):
    if not alternatives_enabled(contract):
        raise ValueError('relation_alternatives_opt_in_required')
    if (report.get('status') != 'REVISE' or not report.get('response_id')
        or report.get('analysis_sha256') != analysis_sha256(analysis)
        or report.get('script_sha256') != hashlib.sha256(script.encode()).hexdigest()
        or report.get('context_sha256') != digest(gate_context(contract))
        or report.get('relation_rules_sha256') != digest(RELATION_RULES)
        or report.get('model') != contract['semantic_review']['model']
        or report.get('model') == generator_model):
        raise ValueError('relation_alternative_review_not_bound')
    if contract['semantic_review']['version'] == 'semantic-sufficiency-0.2':
        from .semantic_evidence import evidence_catalog, expand_evidence
        packet = review_packet(analysis)
        if (report.get('evidence_catalog_sha256') != digest(evidence_catalog(packet))
            or expand_evidence(report.get('wire_verdict'), packet) != report['verdict']):
            raise ValueError('relation_alternative_wire_evidence_changed')
    judgment = SufficiencyVerdict.model_validate(report['verdict'])
    findings, _ = verdict_findings(judgment, review_packet(analysis))
    uncertain = [i for i, b in enumerate(judgment.beats) if b.causality == 'UNKNOWN']
    if len(uncertain) != 1 or len(findings) != 1:
        raise ValueError('relation_alternatives_require_only_one_uncertain_causality')
    index = uncertain[0]
    beat = analysis.beats[index]
    if analysis.version != 'semantic-beats-0.2' or len(beat.relations) != 1:
        raise ValueError('relation_alternatives_require_one_typed_link')
    relation = beat.relations[0]
    if relation.grounding != 'inferred' or relation.kind not in {'motivation', 'event_cause'}:
        raise ValueError('explicit_or_noncausal_relation_cannot_be_weakened')
    variants = []
    for kind, explanation in [
        ('context', 'The prior information supplies background for understanding the next event; this candidate does not assert that it caused the event.'),
        ('sequence', 'The earlier event or information is presented before the target; this candidate asserts order only, not a reason or cause.')]:
        value = analysis.model_copy(deep=True)
        value.beats[index].relations[0].kind = kind
        value.beats[index].relations[0].explanation = explanation
        if inspect_analysis(value, script, contract):
            raise ValueError('relation_alternative_breaks_structure')
        variants.append(value)
    return variants


async def resolve_relation_uncertainty(analysis, script, report, contract, settings, tracker, work,
                                       *, attempt, generator_model):
    if type(attempt) is not int or not 0 <= attempt <= 1:
        raise ValueError('relation_alternative_shared_budget_exhausted')
    variants = relation_variants(analysis, script, report, contract, generator_model)
    prefix = f'relation-alternatives-{attempt}'
    atomic_json(work/f'{prefix}-candidates.json', dict(original_sha256=analysis_sha256(analysis),
        original_report_sha256=digest(report), shared_repair_cost=2,
        candidates=[v.model_dump(mode='json') for v in variants],
        scope='One uncertain inferred relation, not general route/grammar uncertainty'))
    packets = [review_packet(v) for v in variants]
    context = dict(capabilities=gate_context(contract), alternative_policy=contract['relation_alternatives'],
        preservation='Reject a weaker link if narration explicitly requires causal/motivational meaning. Do not prefer weaker meaning merely because it is easier. Context and sequence are not automatic fallbacks.')
    reviews = []
    for label, order in [('ab', (0, 1)), ('ba', (1, 0))]:
        reviews.append(await asyncio.wait_for(review_pair(script, dict(zip('AB', [packets[i] for i in order])),
            context, settings, tracker, work, review_id=f'{prefix}-{label}', model=contract['semantic_review']['model'],
            exact_quote_options=True), timeout=180))
    decision = compare_orders(*reviews)
    atomic_json(work/f'{prefix}-comparison.json', decision)
    if decision['status'] != 'CONSISTENT_PRE_RENDER_REVIEW':
        raise ValueError('relation_alternative_order_or_criteria_disagreement')
    identity = decision['winner_sha256']
    if identity is None and decision.get('preference') == 'TIE':
        # Both passed all dimensions in both orders; prefer context's retained explanatory link.
        identity = digest(packets[0])
    matches = [v for v, p in zip(variants, packets) if digest(p) == identity]
    if len(matches) != 1:
        raise ValueError('relation_alternatives_no_valid_winner')
    selected = matches[0]
    final = await review_sufficiency(selected, script, contract, settings, tracker, work,
        attempt=attempt+2, generator_model=generator_model)
    if final['status'] != 'PRE_RENDER_SEMANTICS_PASS':
        raise ValueError('relation_alternative_final_sufficiency_failed')
    atomic_json(work/f'{prefix}-selected.json', dict(status='PRE_RENDER_SEMANTICS_PASS',
        analysis=selected.model_dump(mode='json'), analysis_sha256=analysis_sha256(selected),
        comparison=decision, consumed_plan_repairs=attempt+2, human_approval=None, production_ready=False))
    return selected, attempt+2
