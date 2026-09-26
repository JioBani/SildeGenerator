"""Compile observed reference partitions into gated director research records."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess


def validate(atlas):
    ids = set()
    for ref in atlas['references']:
        if ref['id'] in ids:
            raise ValueError('Duplicate reference ID')
        ids.add(ref['id'])
        if ref['design'] not in atlas['designs']:
            raise ValueError('Unknown design profile')
        cursor = 0
        for part in ref['partitions']:
            start, end = part['range']
            if not all(isinstance(x, (float, int)) and math.isfinite(x) for x in (start, end)):
                raise ValueError('Non-finite interval')
            if abs(start-cursor) > 1e-6 or end <= start:
                raise ValueError('Gap, overlap or reversed partition')
            for field in ('function', 'layout', 'states', 'motion'):
                if not part.get(field):
                    raise ValueError(f'Missing {field}')
            if not isinstance(part['requires'], list):
                raise ValueError('Capabilities must be a list')
            cursor = end
        if abs(cursor-ref['duration']) > 1e-6:
            raise ValueError('Reference tail is unaccounted for')


def contained_file(root, relative):
    target = (root / relative).resolve()
    if not target.is_relative_to(root.resolve()) or not target.is_file():
        raise ValueError(f'Missing or out-of-root evidence: {relative}')
    return target


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def scene_record(ref, part, index, design):
    return {
        'id': f"{ref['id']}-research-{index:03}",
        'source_window': part['range'],
        'boundary_status': 'ANALYSIS_PARTITION_NOT_VERIFIED_CUT',
        'scene_function': part['function'],
        'design_rules': design,
        'layout': part['layout'],
        'object_states': part['states'],
        'motion': {'hypothesis': part['motion'], 'measured_trajectory': None},
        'transition': {'status': 'NATIVE_FRAME_REVIEW_REQUIRED'},
        'rhythm': {'status': 'AUDIO_AND_FRAME_REVIEW_REQUIRED'},
        'renderer_requirements': {'capabilities_needed': part['requires'], 'selected_renderer': None},
        'rights': part.get('rights', 'INDEPENDENT_ASSETS_REQUIRED'),
        'fact_check': part.get('fact_check', 'VERIFY_NARRATION_BEFORE_TRANSFER'),
        'knowledge_layer': 'OBSERVED_GRAMMAR_HYPOTHESIS',
        'render_authorized': False,
        'human_approved': False,
        'production_promotion': False,
    }


def attach_audio(records, report, source_hash, atlas_hash, evidence):
    if report.get('source_sha256') != source_hash or report.get('atlas_sha256') != atlas_hash:
        raise ValueError('Audio evidence source or atlas hash mismatch')
    if len(report.get('partitions', [])) != len(records):
        raise ValueError('Audio evidence partition count mismatch')
    for scene, audio in zip(records, report['partitions']):
        if scene['source_window'] != audio['range'] or scene['scene_function'] != audio['scene_function']:
            raise ValueError('Audio evidence partition alignment mismatch')
        scene['rhythm'] = {
            'status': 'MIXED_AUDIO_MEASURED_SEMANTIC_REVIEW_REQUIRED',
            'evidence': evidence,
            'measurements': audio,
            'limitations': report['scope'],
            'speech_alignment': None,
            'sound_event_identity': None,
            'audio_reuse_authorized': False,
        }


def attach_semantics(records, observations, source_hash, root):
    for item in observations:
        if item.get('source_sha256', '').lower() != source_hash.lower():
            raise ValueError('Semantic observation source mismatch')
        matches = [r for r in records if r['source_window'] == item.get('scene_window')]
        if len(matches) != 1:
            raise ValueError('Semantic observation scene scope mismatch')
        scene = matches[0]
        when = item.get('observed_at')
        start, end = scene['source_window']
        if not isinstance(when, (int, float)) or not math.isfinite(when) or not start <= when < end:
            raise ValueError('Observation timestamp outside scene')
        if item.get('required_scene_state') not in scene['object_states']:
            raise ValueError('Scene contradicts corrected semantic state')
        if not item.get('evidence') or not item.get('discriminating_cues'):
            raise ValueError('Missing semantic evidence or visible cues')
        for evidence in item['evidence']:
            actual = digest(contained_file(root, evidence['file']))
            if actual != evidence.get('sha256', '').lower():
                raise ValueError('Semantic evidence file changed')
        scene.setdefault('semantic_observations', []).append({
            'id': item['id'], 'status': 'MODEL_OBSERVATION_HUMAN_REVIEW_PENDING',
            'observed_at': when, 'evidence': item['evidence'],
            'visible_identity': item['visible_identity'], 'cues': item['discriminating_cues'],
            'rejected_hypothesis': item['rejected_hypothesis'],
            'story_function_hypothesis': item['story_function_hypothesis'],
            'narration_claim': None, 'production_promotion': False,
            'transfer_limits': item['transfer_limits'],
        })


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--atlas', type=Path, default=Path('docs/reference-director-atlas.json'))
    p.add_argument('--manifest', type=Path, default=Path('docs/reference-curriculum.json'))
    p.add_argument('--root', type=Path, default=Path('.runtime/reference-study'))
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--audio', nargs='*', default=[], help='Audio reports relative to evidence root')
    p.add_argument('--observations', type=Path, help='Evidence-linked semantic observations; not approval')
    args = p.parse_args()
    if args.output.exists():
        p.error('Use a new output directory; preserve previous evidence')
    atlas = json.loads(args.atlas.read_text(encoding='utf-8'))
    validate(atlas)
    registry = {r['id']: r for r in json.loads(args.manifest.read_text(encoding='utf-8'))['references']}
    observations = json.loads(args.observations.read_text(encoding='utf-8'))['observations'] if args.observations else []
    known_ids = {r['id'] for r in atlas['references']}
    if any(o.get('reference_id') not in known_ids for o in observations):
        raise ValueError('Observation references unknown atlas entry')
    if len({o['id'] for o in observations}) != len(observations):
        raise ValueError('Duplicate semantic observation ID')
    result = []
    audio_reports = {}
    for name in args.audio:
        file = contained_file(args.root, name)
        report = json.loads(file.read_text(encoding='utf-8'))
        key = report['reference_id']
        if key in audio_reports:
            raise ValueError('Duplicate audio evidence for reference')
        if key not in registry:
            raise ValueError('Unknown audio reference')
        audio_reports[key] = (report, {'file': name, 'sha256': digest(file)})
    for ref in atlas['references']:
        source = contained_file(args.root, registry[ref['id']]['source'])
        probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                '-of', 'json', str(source)], capture_output=True, text=True,
                               check=True, timeout=30)
        actual_duration = float(json.loads(probe.stdout)['format']['duration'])
        if abs(actual_duration-ref['duration']) > .05:
            raise ValueError(f"Duration does not match source: {ref['id']}")
        evidence = [{'file': name, 'sha256': digest(contained_file(args.root, name))}
                    for name in ref['evidence']]
        result.append({'id': ref['id'], 'source_sha256': digest(source),
                       'source_duration': actual_duration, 'evidence': evidence,
                       'scenes': [scene_record(ref, part, i+1, atlas['designs'][ref['design']])
                                  for i, part in enumerate(ref['partitions'])]})
        if ref['id'] in audio_reports:
            report, audio_evidence = audio_reports[ref['id']]
            attach_audio(result[-1]['scenes'], report, digest(source), digest(args.atlas), audio_evidence)
            result[-1]['evidence'].append(audio_evidence)
        attach_semantics(result[-1]['scenes'], [o for o in observations if o['reference_id']==ref['id']],
                         digest(source), args.root)
    args.output.mkdir(parents=True)
    record = {'atlas_sha256': digest(args.atlas), 'status': 'RESEARCH_NOT_PRODUCTION',
              'limitations': atlas['interval_semantics'], 'references': result}
    if args.observations:
        record['semantic_observations_sha256'] = digest(args.observations)
    (args.output/'director-records.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    capabilities = {}
    for ref in result:
        for scene in ref['scenes']:
            for capability in scene['renderer_requirements']['capabilities_needed']:
                capabilities.setdefault(capability, []).append(scene['id'])
    (args.output/'capability-backlog.json').write_text(json.dumps(capabilities, indent=2), encoding='utf-8')
    print(json.dumps({'references': len(result), 'partitions': sum(len(r['scenes']) for r in result),
                      'capability_requirements': len(capabilities), 'production_approved': 0}))


if __name__ == '__main__':
    main()
