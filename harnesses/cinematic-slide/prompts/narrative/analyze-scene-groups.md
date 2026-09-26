# Scene group 분석

각 sequence 안에서 같은 국소 목적을 수행하는 scene 묶음을 순서대로 제안한다.

- group ID, sequence ID, scene ID, source unit 범위를 만들지 않는다.
- 각 group은 scenes를 직접 포함한다.
- 배열 순서와 하위 scene의 source_unit_count를 바탕으로 컴파일러가 범위를 계산한다.
