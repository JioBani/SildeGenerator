"""Authored test scripts, explicitly not held-out automatic director results."""


def cases():
    specs = [
        ("comparison", "quantitative_comparison", "같은 목적지, 다른 이동 시간", "예시입니다. 같은 목적지까지 버스는 20분, 자전거는 35분, 도보는 50분 걸립니다. 같은 눈금으로 비교하면 시간 차이가 보입니다.",
         [("버스", "20분", 20), ("자전거", "35분", 35), ("도보", "50분", 50)], "분", 60),
        ("accumulation", "cumulative_change", "책은 하루씩 쌓입니다", "작은 도서관의 예시입니다. 첫날 2권, 둘째 날 3권, 셋째 날 5권을 받았습니다. 받은 책을 차례로 더하면 모두 10권입니다.",
         [("첫날", "2권", 2), ("둘째 날", "3권", 3), ("셋째 날", "5권", 5)], "권", 10),
        ("procedure", "step_sequence", "자료에서 발행까지", "안내문을 만드는 순서입니다. 먼저 자료를 모읍니다. 다음으로 내용을 정리합니다. 마지막으로 안내문을 발행합니다. 모으기, 정리하기, 발행하기의 순서를 지킵니다.",
         [("자료 모으기", "자료 확보", None), ("내용 정리", "내용 확정", None), ("안내문 발행", "발행 완료", None)], None, None),
    ]
    result = []
    for identifier, grammar, title, narration, entries, unit, scale in specs:
        nodes = []
        for j, (label, after, quantity) in enumerate(entries):
            nodes.append(dict(id=f"item-{j}",label=label,before="대기",after=after,x=.2+j*.3,y=.4,
                color=["#287887", "#b94d48", "#79622c"][j],reveal_at=0,change_at=[.15,.38,.62][j],
                quantity=quantity,unit=unit,source_quote=after if quantity is not None else None))
        edges = [] if grammar != "step_sequence" else [
            dict(source="item-0",target="item-1",label="다음",start_at=.22,end_at=.36),
            dict(source="item-1",target="item-2",label="다음",start_at=.45,end_at=.60)]
        result.append(dict(id=identifier,narration=narration,hybrid=dict(version="hybrid-scene-0.3",route="diagram",
            reason="Render the script's explicit relationship with editable objects and distinct geometry.",source_id=None,composition=None,
            diagram=dict(title=title,grammar=grammar,nodes=nodes,edges=edges,comparison_scale_max=scale))))
    return result
