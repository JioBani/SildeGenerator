# 연속성 에셋 선택

반복되는 모든 명사를 에셋으로 만들지 말고, 외형 불일치가 서사를 훼손하는 주요 인물·장소·사물만 보수적으로 선택한다.

- asset ID를 만들지 않는다. `category`와 배열 순서로 컴파일러가 ID를 생성한다.
- `appearing_scene_numbers`에는 에셋이 실제 등장하는 전역 scene 번호를 1부터 시작해 기록한다.
- 두 scene 이상 등장하지 않으면 컴파일러가 에셋을 제거한다.
- category는 character, object, location, vehicle, graphic, phenomenon 중 하나다.
