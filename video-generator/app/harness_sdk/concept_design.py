"""Pre-render concept candidates and independent, counterbalanced judgments."""
from copy import deepcopy
import hashlib
import json
from typing import Annotated, Literal
from pydantic import Field, model_validator
from .direction import DirectionModel
from .film_design import FilmDesignContract, design_sha256, shared_design

Text = Annotated[str, Field(min_length=12, max_length=500)]
Capability = Literal['cinematic_still', 'editable_diagram', 'registered_source_image', 'hold', 'push', 'pull']
Verdict = Literal['PASS', 'FAIL', 'UNKNOWN']
CRITERIA = ('script_fidelity','route_coverage','source_integrity','executable',
    'originality','korean_readability','whole_film_coherence')


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


class Concept(DirectionModel):
    design: FilmDesignContract
    script_quote: str = Field(min_length=1,max_length=240)
    viewer_journey: Text
    visual_metaphor: Text
    world_description: Text
    lighting_language: Text
    camera_language: Text
    motion_personality: Text
    shared_motifs: list[Text] = Field(min_length=2,max_length=3)
    forbidden_variations: list[Text] = Field(min_length=2,max_length=4)
    required_capabilities: list[Capability] = Field(min_length=1,max_length=6)


def anonymous(concept):
    value = concept.model_dump(mode='json')
    value['design'].pop('concept_id')
    return value


class ConceptBatch(DirectionModel):
    version: Literal['film-concepts-0.1']
    candidates: list[Concept] = Field(min_length=3,max_length=3)

    @model_validator(mode='after')
    def distinct(self):
        if len({c.design.concept_id for c in self.candidates}) != 3:
            raise ValueError('concept_ids_must_differ')
        # Mere color/name changes do not constitute three concepts.
        signatures = [digest({**{key:anonymous(c)[key] for key in
            ('viewer_journey','visual_metaphor','world_description','lighting_language','camera_language')},
            'snapshot_layout':getattr(c.design,'snapshot_layout',None),
            'comparison_layout':getattr(c.design,'comparison_layout',None)})
            for c in self.candidates]
        if len(set(signatures)) != 3:
            raise ValueError('concepts_need_more_than_palette_changes')
        return self


class ConceptJudgment(DirectionModel):
    label: Literal['A','B','C']
    script_fidelity: Verdict
    route_coverage: Verdict
    source_integrity: Verdict
    executable: Verdict
    originality: Verdict
    korean_readability: Verdict
    whole_film_coherence: Verdict
    script_quote: str = Field(min_length=1,max_length=240)
    reason: Text
    repair_target: str | None


class ConceptReview(DirectionModel):
    candidates: list[ConceptJudgment] = Field(min_length=3,max_length=3)
    genuinely_distinct: Verdict
    distinctness_reason: Text
    # Multiple labels mean a genuine tie, never a ranking with an unpassed member.
    preferred: list[Literal['A','B','C']] = Field(max_length=3)
    preference_reason: Text


def validate_batch(batch, script):
    findings = []
    for i,candidate in enumerate(batch.candidates):
        if not candidate.script_quote.strip() or candidate.script_quote not in script:
            findings.append(f'candidate-{i}:quote_not_grounded')
        if len(set(candidate.required_capabilities)) != len(candidate.required_capabilities):
            findings.append(f'candidate-{i}:duplicate_capability')
    return findings


def validate_review(review, script):
    findings = []
    if {c.label for c in review.candidates} != {'A','B','C'}:
        findings.append('concept_review_coverage_not_exact')
    passing = set()
    for candidate in review.candidates:
        if candidate.script_quote not in script or not candidate.script_quote.strip():
            findings.append(f'{candidate.label}:review_quote_not_grounded')
        if all(getattr(candidate,key)=='PASS' for key in CRITERIA):
            passing.add(candidate.label)
        elif not candidate.repair_target:
            findings.append(f'{candidate.label}:repair_target_missing')
    if len(set(review.preferred)) != len(review.preferred):
        findings.append('duplicate_concept_preference')
    if set(review.preferred)-passing:
        findings.append('unpassed_concept_preferred')
    if review.genuinely_distinct != 'PASS' and review.preferred:
        findings.append('indistinct_concepts_cannot_be_selected')
    if review.genuinely_distinct=='PASS' and passing and not review.preferred:
        findings.append('passing_concepts_without_preference')
    return findings


def compare_concept_orders(first, second, batch):
    base = dict(status='CONCEPT_SELECTION_INCOMPLETE', selection_policy='concept-consensus-0.2', selected_sha256=None, human_approval=None, production_ready=False)
    if any(r.get('status')!='VALID_REVIEW' for r in (first,second)):
        return base
    if any(first.get(k)!=second.get(k) for k in ('script_sha256','context_sha256','model','evaluator_version')):
        return {**base,'status':'CONCEPT_REVIEW_POLICY_MISMATCH'}
    a,b = first['candidate_hashes'],second['candidate_hashes']
    if len(set(a.values()))!=3 or [a[k] for k in 'ABC'] != [b[k] for k in 'CBA']:
        return {**base,'status':'CONCEPT_COUNTERBALANCE_INVALID'}
    if not first.get('response_id') or first['response_id']==second.get('response_id'):
        return {**base,'status':'CONCEPT_REVIEW_PROVENANCE_INVALID'}
    expected = {digest(anonymous(c)):c for c in batch.candidates}
    if set(a.values())!=set(expected):
        return {**base,'status':'CONCEPT_REVIEW_INPUT_MISMATCH'}
    def normalize(report):
        verdict = report['verdict']
        return (verdict['genuinely_distinct'],
            {report['candidate_hashes'][c['label']]:{k:c[k] for k in CRITERIA} for c in verdict['candidates']},
            {report['candidate_hashes'][label] for label in verdict['preferred']})
    left,right=normalize(first),normalize(second)
    agreements=sum(left[1][h][key]==right[1][h][key] for h in expected for key in CRITERIA)
    total=len(expected)*len(CRITERIA)
    consistent={h for h in expected if left[1][h]==right[1][h]}
    policy={'criteria_agreement':{'matching':agreements,'total':total,'fraction':agreements/total,'minimum':.9},
            'quarantined_sha256':sorted(set(expected)-consistent)}
    # The goal requires >=90% evaluator agreement, and zero critical disagreement
    # on the actual winner. Disagreement on a losing candidate is not approval.
    if left[0]!=right[0] or agreements/total<.9:
        return {**base,**policy,'status':'CONCEPT_ORDER_DISAGREEMENT'}
    if left[0]!='PASS':
        return {**base,**policy,'status':'NO_PASSING_CONCEPT'}
    winners = left[2] & right[2] & consistent
    winners={h for h in winners if all(left[1][h][k]=='PASS' for k in CRITERIA)}
    if not winners:
        return {**base,**policy,'status':'CONCEPT_ORDER_DISAGREEMENT' if left[2] or right[2] else 'NO_PASSING_CONCEPT'}
    # Runtime cost is comparable for these bounded capabilities. This is only a
    # deterministic complexity tie-break, not measured production cost/superiority.
    selected = min(winners,key=lambda h:(len(expected[h].required_capabilities),len(expected[h].design.palette.accents),h))
    return {**base,**policy,'status':'CONSISTENT_CONCEPT_SELECTION','selected_sha256':selected,
        'selected_design_sha256':design_sha256(expected[selected].design),
        'tie_break':'fewest declared capabilities, fewest accents, stable hash' if len(winners)>1 else None}


def concept_extension(*, graphic_design=False, directed_graphics=False):
    return {'version':'concept-selection-0.3' if directed_graphics else 'concept-selection-0.2' if graphic_design else 'concept-selection-0.1',
            'candidate_count':3,'review_model':'gpt-5.6-terra','orders':['ABC','CBA']}


def concept_enabled(contract):
    extension = (contract or {}).get('concept_selection')
    if extension is None: return False
    graphic = extension.get('version') == 'concept-selection-0.2'
    directed = extension.get('version') == 'concept-selection-0.3'
    if extension!=concept_extension(graphic_design=graphic, directed_graphics=directed): raise ValueError('unsupported_concept_selection_contract')
    if (graphic or directed) and (contract.get('hybrid_direction') or {}).get('version') != 'hybrid-scene-0.6':
        raise ValueError('graphic_concepts_require_scene_version_06')
    if (contract.get('hybrid_direction') or {}).get('version') not in {'hybrid-scene-0.4','hybrid-scene-0.5','hybrid-scene-0.6'}:
        raise ValueError('concept_selection_requires_shared_design')
    return True


def bind_selected_concept(scenes, concept):
    selected = design_sha256(concept.design)
    findings = []
    for scene in scenes:
        try:
            actual = shared_design([scene])
            if actual is None or design_sha256(actual)!=selected:
                findings.append(f'{scene.id}:selected_concept_design_changed')
                continue
            scene.layout['selected_concept'] = {'sha256':digest(anonymous(concept)),
                'design_sha256':selected,'blueprint':concept.model_dump(mode='json'),
                'scope':'independent pre-render concept selection, not film approval'}
        except ValueError:
            findings.append(f'{scene.id}:selected_concept_design_invalid')
    return findings
