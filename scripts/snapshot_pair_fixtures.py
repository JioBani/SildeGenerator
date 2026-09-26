"""Authored development inputs, never held-out director evaluation."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def cases():
    design=json.loads((ROOT/'experiments/meaning-planning-v1/film-design-candidate.json').read_text(encoding='utf-8'))
    specs=[
        ('battery','같은 배터리','충전량','%',100,'출발 전',80,'도착 후',35),
        ('queue','같은 창구','대기 인원','명',40,'오전',12,'오후',28),
        ('stock','같은 창고','재고','개',60,'월요일',45,'금요일',45),
    ]
    result=[]
    for identifier,entity,metric,unit,maximum,t1,v1,t2,v2 in specs:
        before=f'{t1} {entity}의 {metric}은 {v1}{unit}였습니다.'
        after=f'{t2} {entity}의 {metric}은 {v2}{unit}였습니다.'
        narration=f'가상의 측정 예시입니다. {before} {after} 두 시점의 값만 비교하며, 중간 변화나 원인을 뜻하지 않습니다.'
        pair=dict(version='snapshot-pair-0.1',entity=entity,metric=metric,unit=unit,scale_max=maximum,
            color=design['palette']['accents'][0],before=dict(time_label=t1,value=v1,source_quote=before,show_at=.15),
            after=dict(time_label=t2,value=v2,source_quote=after,show_at=.5))
        hybrid=dict(version='hybrid-scene-0.5',route='diagram',reason='Compare two explicitly stated measurements of the same entity without inferring a cause.',
            source_id=None,composition=None,design=design,diagram=dict(title=f'{metric}의 전후 비교',grammar='before_after',
                nodes=[],edges=[],comparison_scale_max=None,snapshot_pair=pair))
        result.append(dict(id=identifier,narration=narration,hybrid=hybrid))
    return result
