"""Authored spatial development examples; not autonomous or held-out evidence."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def cases():
    design=json.loads((ROOT/'experiments/meaning-planning-v1/film-design-candidate.json').read_text(encoding='utf-8'))
    design.update(concept_id='relative-places',central_idea='Understand explicit positions while preserving fixed referents and showing uncertainty about distances.',
        cinematic_language='No generated cinematic beat is required by these schematic examples.',
        diagram_language='Editable point markers and bounded regions, north-up orientation, sequential factual emphasis, no travel or scale claim.')
    specs=[
        ('park','공원 안 상대 위치',[('gate','정문',.22,.78),('lake','연못',.22,.16),('play','놀이터',.78,.16)],[],
         [('lake','gate','north_of','연못은 정문의 북쪽에 있습니다.'),('play','lake','east_of','놀이터는 연못의 동쪽에 있습니다.')]),
        ('campus','캠퍼스 방향 비교',[('library','도서관',.78,.16),('lab','연구실',.22,.16),('gate','후문',.22,.78)],[],
         [('lab','library','west_of','연구실은 도서관의 서쪽에 있습니다.'),('gate','lab','south_of','후문은 연구실의 남쪽에 있습니다.')]),
        ('reserve','보호구역 안과 밖',[('station','관측소',.3,.48),('parking','주차장',.82,.48)],
         [dict(id='reserve',label='보호구역',left=.02,top=.04,right=.58,bottom=.99,reveal_at=.03)],
         [('station','reserve','inside','관측소는 보호구역 안에 있습니다.'),('parking','reserve','outside','주차장은 보호구역 밖에 있습니다.')])]
    results=[]
    for identifier,title,places,regions,relations in specs:
        positions=[dict(id=i,label=label,x=x,y=y,reveal_at=.05,color=design['palette']['accents'][j]) for j,(i,label,x,y) in enumerate(places)]
        links=[dict(subject=s,target=t,relation=r,source_quote=q,show_at=.3+j*.3) for j,(s,t,r,q) in enumerate(relations)]
        narration='가상의 배치를 설명합니다. '+' '.join(r['source_quote'] for r in links)+' 실제 거리나 이동 경로를 뜻하지 않습니다.'
        spatial=dict(version='spatial-map-0.1',coordinate_mode='relative_schematic_north_up',places=positions,regions=regions,relations=links)
        hybrid=dict(version='hybrid-scene-0.6',route='diagram',reason='Explain only the stated directions and region membership while retaining each named place.',
            source_id=None,composition=None,design=design,diagram=dict(title=title,grammar='map_spatial',nodes=[],edges=[],comparison_scale_max=None,spatial_map=spatial))
        results.append(dict(id=identifier,narration=narration,hybrid=hybrid))
    return results
