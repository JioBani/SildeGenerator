"""Evidence-bound research packets. Never authorize production or human approval."""
import hashlib
import importlib.util
import json
from pathlib import Path


def compiler_effects(root):
    path=root/'harnesses/astra-motion/src/astra_motion/scene_program.py'
    spec=importlib.util.spec_from_file_location('study_scene_program',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return set(module.EFFECTS)


def packet(ledger, root, effects):
    root=Path(root).resolve()
    cases=[]
    seen=set()
    for case in ledger['cases']:
        if case['id'] in seen:
            raise ValueError('Duplicate learning case')
        seen.add(case['id'])
        for key in ('conditions','counterexamples','failure','correction','required_effects','next_experiment'):
            if not case.get(key):
                raise ValueError(f'Missing learning contract field: {key}')
        issues=[]
        if not case.get('evidence'):
            issues.append('NO_EVIDENCE')
        for evidence in case.get('evidence',[]):
            path=(root/evidence['path']).resolve()
            if not path.is_relative_to(root):
                raise ValueError('Evidence path escapes repository')
            if not path.is_file():
                issues.append('MISSING:'+evidence['path'])
            elif hashlib.sha256(path.read_bytes()).hexdigest()!=evidence['sha256'].lower():
                issues.append('STALE:'+evidence['path'])
        missing=sorted(set(case['required_effects'])-effects)
        cases.append({**case,'evidence_issues':issues,
                      'retrievable':not issues,'missing_compiler_effects':missing,
                      'compiler_compatible':not missing,'production_authorized':False,
                      'status':'EVIDENCE_INVALID' if issues else 'EXPERIMENT_ONLY',
                      'human_review_required':True})
    return {'schema_version':1,'cases':cases,
            'scope':'Director research advisory, not runtime enforcement or production approval. '
                    'Code effects are capabilities, not proof of quality. Transfer requires independent review.'}


def retrieve(report, scene_function):
    return [case for case in report['cases'] if case['retrievable'] and scene_function in case['scene_functions']]


QUALITY_AXES=('meaning','design','layout','motion','transition','rhythm','audio')


def iteration_checkpoint(history):
    """Advisory only: count experiments, never infer success from missing records."""
    seen=set()
    counts={}
    missing=[]
    for attempt in history:
        identity=attempt.get('id')
        if not isinstance(identity,str) or not identity.strip() or identity in seen:
            raise ValueError('Iteration IDs must be nonempty and unique')
        seen.add(identity)
        for field in ('hypothesis','changed_variables','observation','next_action'):
            if not attempt.get(field):missing.append(identity+':'+field)
        failures=attempt.get('unresolved_failures',[])
        if not isinstance(failures,list) or any(not isinstance(f,str) or not f.strip() for f in failures):
            raise ValueError('Failure families must be nonempty strings')
        # Count each family once per attempt, and only consecutive observations.
        counts={family:counts.get(family,0)+1 for family in set(failures)}
    repeated=sorted(f for f,n in counts.items() if n>=3)
    status=('CAUSE_REVIEW_REQUIRED' if repeated else
            'RECORD_INCOMPLETE' if missing or not history else 'NEXT_EXPERIMENT_REVIEW')
    return {'status':status,'attempts':len(history),'repeated_failure_families':repeated,
            'missing_records':missing,'automatic_retry_authorized':False,
            'scope':'Offline advisory; does not pause or approve production.'}


def assess_experiment(experiment, root):
    """Separate measured gates from human quality; never replace a best artifact."""
    root=Path(root).resolve()
    def verified(item):
        path=(root/item['path']).resolve()
        if not path.is_relative_to(root):raise ValueError('Evidence path escapes repository')
        if not path.is_file():return None
        if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256'].lower():return None
        return path
    artifact=verified(experiment['candidate'])
    outcomes=[]
    for check in experiment.get('checks',[]):
        path=verified(check['evidence'])
        if path is None:
            outcomes.append({'id':check['id'],'status':'EVIDENCE_INVALID'})
            continue
        data=json.loads(path.read_text(encoding='utf-8'))
        actual=data.get(check['field'])
        if check['op']=='eq':passed=type(actual)==type(check['expected']) and actual==check['expected']
        elif check['op']=='lte':
            import math
            passed=type(actual) in (int,float) and math.isfinite(actual) and actual<=check['expected']
        else:raise ValueError('Unsupported measurement comparison')
        outcomes.append({'id':check['id'],'status':'PASS' if passed else 'FAIL','actual':actual})
    technical=bool(artifact and outcomes and all(o['status']=='PASS' for o in outcomes))
    # Review requests are not approvals. Existing external human approval is a separate system.
    axes={axis:experiment.get('quality_questions',{}).get(axis,'Review required') for axis in QUALITY_AXES}
    regression=experiment.get('known_regressions',[])
    if not artifact or any(o['status']=='EVIDENCE_INVALID' for o in outcomes):decision='EVIDENCE_INVALID'
    elif not technical or regression:decision='REWORK_PRESERVE_BEST'
    else:decision='HUMAN_QUALITY_REVIEW_REQUIRED'
    return {'id':experiment['id'],'decision':decision,'technical_pass':technical,'checks':outcomes,
            'iteration_checkpoint':iteration_checkpoint(experiment.get('iterations',[])),
            'quality_review_questions':axes,'known_regressions':regression,
            'production_authorized':False,'replace_best':False,
            'best_version':experiment.get('best_version'),
            'next_action':experiment['next_action']}
