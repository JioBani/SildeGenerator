"""Build an auditable reconstruction backlog; never infer approval from render success."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from reference_learning import compiler_effects, packet, assess_experiment

AXES = ('design', 'layout', 'motion', 'transition', 'rhythm', 'audio', 'meaning')


def intervals(rows, duration):
    result = []
    for start, end in sorted(rows):
        if not (math.isfinite(start) and math.isfinite(end) and 0 <= start < end <= duration + .001):
            raise ValueError('Invalid source interval')
        end = min(end, duration)
        if result and start <= result[-1][1]:
            result[-1][1] = max(result[-1][1], end)
        else:
            result.append([start, end])
    return result


def seconds(rows, duration):
    return sum(end-start for start, end in intervals(rows, duration))


def resolve(root, value):
    if not value:
        return None
    result = (root / value).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError('Evidence path must stay inside evidence root')
    return result


def read(root, value):
    path = resolve(root, value)
    return json.loads(path.read_text(encoding='utf-8')) if path and path.is_file() else None


def accepted_review(root, value, expected_source_hash):
    review = read(root, value)
    if not review or review.get('decision') != 'PASS' or review.get('reviewer_type') != 'human':
        return None
    if not review.get('reviewer') or review.get('source_sha256') != expected_source_hash:
        return None
    if any(review.get('axes', {}).get(axis) != 'PASS' for axis in AXES):
        return None
    artifact = resolve(root, review.get('artifact'))
    if not artifact or not artifact.is_file():
        return None
    if hashlib.sha256(artifact.read_bytes()).hexdigest() != review.get('artifact_sha256'):
        return None
    return review


def build_reference(ref, root):
    source = resolve(root, ref.get('source'))
    overview = read(root, ref.get('overview'))
    result = {'id': ref['id'], 'label': ref['label'], 'url': f"https://www.youtube.com/watch?v={ref['id']}",
              'status': 'SOURCE_NOT_REGISTERED', 'source_available': bool(source and source.is_file()),
              'quality_approved': False, 'transfer_passed': False, 'tasks': []}
    if not result['source_available'] or not overview:
        return result
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    duration = float(overview['probe']['format']['duration'])
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError('Source duration must be positive')
    motion_windows, decoded = [], 0
    issues = []
    for filename in ref.get('motion', []):
        motion = read(root, filename)
        if not motion:
            continue
        if motion.get('source_sha256') != source_hash:
            issues.append(f'Stale motion evidence: {filename}')
            continue
        frames = motion.get('frames', [])
        # Extraction metadata is evidence of sampling, not evidence of semantic analysis.
        if not frames or any(not (resolve(root, str(Path(filename).parent/'frames'/f['file'])).is_file()) for f in frames):
            issues.append(f'Missing frames: {filename}')
            continue
        motion_windows.append([motion['start'], motion['start']+motion['duration']])
        decoded += len(frames)
    study_windows = []
    for study in ref.get('studies', []):
        if study.get('status', '').startswith('REJECTED'):
            issues.append(f"Rejected study excluded from coverage: {study['file']}")
            continue
        artifact = resolve(root, study['file'])
        if artifact and artifact.is_file():
            study_windows.extend(study.get('source_windows', []))
    approved = []
    approved_artifact_hashes = set()
    for filename in ref.get('approved_reviews', []):
        review = accepted_review(root, filename, source_hash)
        if review:
            approved.extend(review.get('source_windows', []))
            approved_artifact_hashes.add(review['artifact_sha256'])
        else:
            issues.append(f'Invalid or incomplete approval: {filename}')
    reviewed_seconds = seconds(approved, duration)
    full_approved = reviewed_seconds >= duration - .001
    transfer = accepted_review(root, ref.get('transfer_review'), source_hash)
    script = resolve(root, transfer.get('script')) if transfer else None
    transferred = bool(transfer and transfer.get('different_script') is True
                       and script and script.is_file()
                       and hashlib.sha256(script.read_bytes()).hexdigest() == transfer.get('script_sha256')
                       and transfer['artifact_sha256'] not in approved_artifact_hashes)
    boundaries = {0., duration}
    for segment in overview['segments']:
        for key in ('start', 'end'):
            value = float(segment[key])
            if 0 < value < duration:
                boundaries.add(value)
    boundaries = sorted(boundaries)
    tasks = []
    for i, (start, end) in enumerate(zip(boundaries, boundaries[1:])):
        tasks.append({'id': f"{ref['id']}-{i+1:03}", 'source_start': start, 'source_end': end,
                      'boundary_status': 'AUTO_CANDIDATE_REQUIRES_REVIEW',
                      'scene_function': None, 'design_rules': None, 'layout': None,
                      'object_states': None, 'motion': None, 'transition': None, 'rhythm': None,
                      'audio_events': None, 'source_object_tracks': None,
                      'native_frames_required': 'PENDING_MOTION_TRIAGE',
                      'candidate_version': None, 'best_version': None,
                      'review_axes': dict.fromkeys(AXES, 'UNREVIEWED'),
                      'status': 'ANNOTATION_REQUIRED'})
    result.update({'status': 'COMPLETE' if full_approved and transferred else 'IN_PROGRESS',
                   'source_sha256': source_hash, 'duration': duration,
                   'overview_samples': len(overview.get('per_second', [])),
                   'decoded_frames': decoded, 'native_sampled_seconds': round(seconds(motion_windows, duration), 3),
                   'partial_study_seconds': round(seconds(study_windows, duration), 3),
                   'approved_seconds': round(reviewed_seconds, 3), 'quality_approved': full_approved,
                   'transfer_passed': transferred, 'issues': issues, 'tasks': tasks})
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--manifest', type=Path, default=Path('docs/reference-curriculum.json'))
    p.add_argument('--root', type=Path, default=Path('.runtime/reference-study'))
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--learning-ledger', type=Path, default=Path('docs/director-learning-ledger.json'))
    p.add_argument('--learning-experiments', type=Path, default=Path('docs/director-learning-experiments.json'))
    a = p.parse_args()
    if a.output.exists():
        p.error('Use a new snapshot path; do not overwrite reviewed annotations')
    config = json.loads(a.manifest.read_text(encoding='utf-8'))
    refs = [build_reference(ref, a.root) for ref in config['references']]
    result = {'schema_version': 1, 'references': refs,
              'limitations': 'Overview sampling is not shot interpretation; partial study seconds are not fidelity or approval percentages.'}
    a.output.mkdir(parents=True)
    (a.output/'backlog.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    if a.learning_ledger.is_file():
        repository=Path(__file__).resolve().parents[1]
        learning=packet(json.loads(a.learning_ledger.read_text(encoding='utf-8')),repository,compiler_effects(repository))
        (a.output/'director-learning.json').write_text(json.dumps(learning,ensure_ascii=False,indent=2),encoding='utf-8')
    if a.learning_experiments.is_file():
        repository=Path(__file__).resolve().parents[1]
        experiments=json.loads(a.learning_experiments.read_text(encoding='utf-8'))['experiments']
        decisions=[assess_experiment(e,repository) for e in experiments]
        (a.output/'quality-decisions.json').write_text(json.dumps(decisions,ensure_ascii=False,indent=2),encoding='utf-8')
    lines = ['# Reference reconstruction coverage', '', '| Reference | Duration | Native sampled | Partial study | Approved | Status |', '|---|---:|---:|---:|---:|---|']
    for ref in refs:
        lines.append(f"| {ref['label']} ({ref['id']}) | {ref.get('duration', '?')} | {ref.get('native_sampled_seconds', 0)} | {ref.get('partial_study_seconds', 0)} | {ref.get('approved_seconds', 0)} | {ref['status']} |")
    lines.extend(['', 'Units: seconds. Unknown source mappings receive no study coverage credit.',
                  'Generated task boundaries need review. No model weights were trained.',
                  'Do not publish reference excerpts as original production assets.'])
    (a.output/'coverage.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(json.dumps({'references': len(refs), 'tasks': sum(len(r['tasks']) for r in refs),
                      'complete': sum(r['status']=='COMPLETE' for r in refs)}))


if __name__ == '__main__':
    main()
