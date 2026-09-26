"""Local mixed-track timing evidence. Never infer words, speech pauses or SFX labels."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
import numpy as np


def envelope(samples, rate=16000, step_seconds=.02):
    samples = np.asarray(samples, dtype=np.float64)
    if samples.ndim != 2 or not samples.shape[0] or rate <= 0:
        raise ValueError('Expected nonempty frames x channels PCM')
    if not np.isfinite(samples).all():
        raise ValueError('PCM contains nonfinite samples')
    step = max(1, round(rate*step_seconds))
    rows = []
    for start in range(0, len(samples), step):
        block = samples[start:start+step]
        # Energy across channels, not a mono sum that can cancel antiphase sound.
        rms = float(np.sqrt(np.mean(block*block)))
        peak = float(np.max(np.abs(block)))
        rows.append({'start': start/rate, 'end': min(start+step,len(samples))/rate,
                     'rms_dbfs': round(20*np.log10(max(rms,1e-6)),3),
                     'peak_dbfs': round(20*np.log10(max(peak,1e-6)),3)})
    return rows


def quiet_intervals(rows, threshold=-38, minimum=.12):
    out=[]
    start=end=None
    for row in rows+[{'start':rows[-1]['end'],'end':rows[-1]['end'],'rms_dbfs':0}]:
        if row['rms_dbfs'] < threshold:
            if start is None: start=row['start']
            end=row['end']
        elif start is not None:
            if end-start >= minimum-1e-9: out.append([start,end])
            start=end=None
    return out


def summarize(rows, partitions):
    result=[]
    for part in partitions:
        start,end=part['range']
        matched=[r for r in rows if r['end']>start and r['start']<end]
        if not matched: raise ValueError('Partition outside decoded audio')
        low=sum(max(0,min(end,r['end'])-max(start,r['start'])) for r in matched if r['rms_dbfs'] < -38)
        result.append({'range':[start,end],'scene_function':part['function'],
                       'median_rms_dbfs':float(np.median([r['rms_dbfs'] for r in matched])),
                       'low_energy_seconds':round(low,4),
                       'max_peak_dbfs':max(r['peak_dbfs'] for r in matched)})
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument('source',type=Path)
    p.add_argument('reference_id')
    p.add_argument('output',type=Path)
    p.add_argument('--atlas',type=Path,default=Path('docs/reference-director-atlas.json'))
    a=p.parse_args()
    if a.output.exists(): p.error('Use new evidence output')
    atlas=json.loads(a.atlas.read_text(encoding='utf-8'))
    ref=next(r for r in atlas['references'] if r['id']==a.reference_id)
    probe=subprocess.run(['ffprobe','-v','error','-select_streams','a:0','-show_entries',
                          'stream=start_time','-of','json',str(a.source)],capture_output=True,
                         text=True,check=True,timeout=30)
    streams=json.loads(probe.stdout)['streams']
    if not streams or abs(float(streams[0].get('start_time','nan')))>.001 or not np.isfinite(float(streams[0].get('start_time','nan'))):
        raise ValueError('Audio timestamp origin not verified as zero; explicit alignment required')
    raw=subprocess.run(['ffmpeg','-v','error','-i',str(a.source),'-map','0:a:0','-vn',
                        '-ac','2','-ar','16000','-f','f32le','pipe:1'],capture_output=True,check=True,timeout=120).stdout
    pcm=np.frombuffer(raw,dtype='<f4').reshape(-1,2)
    rows=envelope(pcm)
    if abs(rows[-1]['end']-ref['duration'])>.15:
        raise ValueError('Audio/video duration mismatch; review timestamp origin')
    candidates=[]
    for i in range(3,len(rows)):
        rise=rows[i]['rms_dbfs']-min(r['rms_dbfs'] for r in rows[i-3:i])
        if rise>=12 and rows[i]['rms_dbfs']>-30 and (not candidates or rows[i]['start']-candidates[-1]['time']>=.2):
            candidates.append({'time':rows[i]['start'],'rise_db':round(rise,3),'semantic_label':None})
    report={'reference_id':a.reference_id,'source_sha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),
            'atlas_sha256':hashlib.sha256(a.atlas.read_bytes()).hexdigest(),
            'analyzer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'audio_start_seconds':0,
            'duration_seconds':rows[-1]['end'],'decoded_rate':16000,'channels':2,'window_seconds':.02,
            'scope':'Mixed-track RMS and peak dBFS. Not LUFS, speech recognition, musical beat detection or sound-event identity.',
            'quiet_threshold_dbfs':-38,'quiet_minimum_seconds':.12,'low_energy_intervals':quiet_intervals(rows),
            'energy_rise_candidates':candidates,'partitions':summarize(rows,ref['partitions']),'envelope':rows,
            'human_audio_review':False,'audio_reuse_authorized':False,'paid_calls':0}
    a.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'reference':a.reference_id,'duration':report['duration_seconds'],
                      'windows':len(rows),'partitions':len(report['partitions']),
                      'quiet_intervals':len(report['low_energy_intervals']),'rise_candidates':len(candidates)}))


if __name__=='__main__':main()
