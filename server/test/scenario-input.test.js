const test = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const path = require('node:path');
const { prepareScenarioInput } = require('../dist/shared/scenario-input');

test('scenario heading, genre and duration are metadata rather than narration', () => {
  const prepared = prepareScenarioInput(`[시나리오] 우주에서 가장 차가운 곳
장르: 과학 가설 / SF 다큐멘터리
분량: 약 1분 (나레이션 기준)

우주에서 가장 차가운 곳은 어디일까요?
절대영도는 영하 273.15도입니다.`);
  assert.equal(prepared.title, '우주에서 가장 차가운 곳');
  assert.equal(prepared.metadata.length, 3);
  assert.equal(prepared.scenario, '우주에서 가장 차가운 곳은 어디일까요?\n절대영도는 영하 273.15도입니다.');
});

test('ordinary body lines containing colons remain narration', () => {
  const prepared = prepareScenarioInput('관찰 결과: 빛이 느려집니다.\n다음 현상을 봅니다.');
  assert.equal(prepared.scenario, '관찰 결과: 빛이 느려집니다.\n다음 현상을 봅니다.');
  assert.deepEqual(prepared.metadata, []);
});

test('chat-style narration wrapper and markdown are not spoken', () => {
  const prepared = prepareScenarioInput(`1분 분량의 나레이션 전용 대본입니다.
말하기 속도를 고려해 구성했습니다.

---

### **[유튜브 1분 나레이션 대본]**

**제목:** 나이가 들수록 시간이 빨리 가는 진짜 이유

뇌과학이 밝혀낸 **'새로운 자극의 부재'** 때문입니다.
오늘부터 새로운 길로 걸어보세요.`);

  assert.equal(prepared.title, '나이가 들수록 시간이 빨리 가는 진짜 이유');
  assert.equal(prepared.scenario, "뇌과학이 밝혀낸 '새로운 자극의 부재' 때문입니다.\n오늘부터 새로운 길로 걸어보세요.");
  assert.ok(prepared.metadata.some((line) => line.includes('나레이션 대본')));
});

test('headings, numbered lines and production notes do not leak into narration', () => {
  const prepared = prepareScenarioInput(`# 별을 잃은 밤
1. 밤하늘을 올려다보세요.
## 도시의 불빛
(연출: 창밖 가로등이 켜진다)
메모: 약 1분 분량
2) 별이 하나씩 사라집니다.
[자막: 별이 보이지 않는 이유]
물은 H2O(물 분자)로 이루어집니다.`);
  assert.equal(prepared.title, '별을 잃은 밤');
  assert.equal(prepared.scenario, '밤하늘을 올려다보세요.\n별이 하나씩 사라집니다.\n물은 H2O(물 분자)로 이루어집니다.');
  assert.ok(prepared.metadata.some((line) => line.includes('가로등')));
});

test('timed storyboard speaks only explicitly labeled narration', () => {
  const prepared = prepareScenarioInput(`### [옵션 2] 영화·미디어 비하인드 쇼츠: <영화 속 프레임의 비밀>

> **컨셉:** 연출과 영상미에 관한 쇼츠.

- **[00\\~03초] 후킹 (화면: 유명 영화의 대칭 장면 세 개)**
  - **나레이션:** "감독들이 당신을 조종하기 위해 영상 속에 숨겨둔 치사한 속임수."
- **[03\\~20초] 문제 제기 (화면: 빨간 가이드라인 overlay)**
  - **나레이션:** "어떤 영화는 편안하고, 어떤 영화는 불안하죠? 당신의 시선을 고정했기 때문입니다."
- **[20\\~40초] 시각적 증명 (화면: 인물의 눈에 격자선)**
  - **나레이션:** "감독은 인물의 눈을 화면 상단 3분의 1 지점에 둡니다."
- **[40\\~50초] 반전/비교 (화면: 의도적 틸트 샷)**
  - **나레이션:** "반대로 불안감을 주고 싶을 땐 프레임을 비틀어 균형을 깨버립니다."
- **[50\\~60초] 엔딩 (화면: 스마트폰을 보는 시청자)**
  - **나레이션:** "지금 보고 있는 이 프레임도 전부 계산된 거라면 믿으시겠습니까?"
|
|`);
  assert.equal(prepared.scenario, [
    '감독들이 당신을 조종하기 위해 영상 속에 숨겨둔 치사한 속임수.',
    '어떤 영화는 편안하고, 어떤 영화는 불안하죠? 당신의 시선을 고정했기 때문입니다.',
    '감독은 인물의 눈을 화면 상단 3분의 1 지점에 둡니다.',
    '반대로 불안감을 주고 싶을 땐 프레임을 비틀어 균형을 깨버립니다.',
    '지금 보고 있는 이 프레임도 전부 계산된 거라면 믿으시겠습니까?',
  ].join('\n'));
  assert.ok(prepared.metadata.some((line) => line.includes('가이드라인')));
  assert.equal(prepared.scenario.includes('화면:'), false);
  assert.equal(prepared.scenario.includes('후킹'), false);
  assert.equal(prepared.visualCues.length, 5);
  assert.match(prepared.visualCues[1].direction, /가이드라인/);
});

test('compact timed storyboard keeps visual directions out of voice and subtitles', () => {
  const input = '### [옵션 2] 영화·미디어 비하인드 쇼츠: <영화 속 프레임의 비밀>'
    + '컨셉: 연출/영상미에 관심 있는 시청자층의 호기심을 자극하는 쇼츠.'
    + '[00~03초] 후킹 (화면: 대칭 장면 3개)나레이션: "감독들이 당신을 조종하기 위해 숨겨둔 속임수."'
    + '[03~20초] 문제 제기 (화면: 빨간 십자가 가이드라인)나레이션: "어떤 영화는 편안하고 어떤 영화는 불안하죠?"'
    + '[20~40초] 시각적 증명 (화면: 인물 눈에 격자선)나레이션: "인물의 눈을 화면 상단 3분의 1에 둡니다."'
    + '[40~50초] 반전 (화면: 틸트 샷)나레이션: "프레임을 비틀어 균형을 깨버립니다."'
    + '[50~60초] 엔딩 (화면: 스마트폰)나레이션: "이 쇼츠의 프레임도 계산된 거라면 믿으시겠습니까?"';
  const prepared = prepareScenarioInput(input);
  assert.equal(prepared.visualCues.length, 5);
  assert.equal(prepared.scenario.split('\n').length, 5);
  assert.equal(prepared.scenario.includes('화면:'), false);
  assert.equal(prepared.scenario.includes('컨셉:'), false);
  assert.equal(prepared.scenario.includes('후킹'), false);
  assert.match(prepared.visualCues[2].direction, /격자선/);
  assert.match(prepared.visualCues[2].narration, /눈을 화면/);
});

test('the frame-secret production script yields only its five narration lines', () => {
  const input = readFileSync(path.join(__dirname, 'fixtures/frame-secret-storyboard.md'), 'utf8');
  for (const candidate of [input, input.replace(/\s*\n\s*/g, '')]) {
    const prepared = prepareScenarioInput(candidate);
    assert.equal(prepared.visualCues.length, 5);
    assert.equal(prepared.scenario.split('\n').length, 5);
    assert.equal(prepared.scenario.includes('화면:'), false);
    assert.equal(prepared.scenario.includes('가이드라인 overlay'), false);
    assert.ok(prepared.scenario.startsWith('감독들이 당신을'));
    assert.ok(prepared.scenario.endsWith('믿으시겠습니까?'));
  }
});

test('explicit narration fails closed when only visual directions contain text', () => {
  assert.throws(() => prepareScenarioInput('화면: 붉은 격자선\n나레이션:\n화면: 눈 위치를 강조'), /내레이션 본문/);
  assert.equal(prepareScenarioInput('나레이션:\n첫 번째 문장입니다.\n- **화면:** 벽을 따라 이동\n두 번째 제작 메모').scenario, '첫 번째 문장입니다.');
});

test('unlabelled parenthesized timed script excludes emoji title and section headings', () => {
  const input = readFileSync(path.join(__dirname, 'fixtures/antimatter-timed-script.md'), 'utf8');
  const expected = input.split('\n').filter(line => !line.startsWith('🎬') && !/^\(\d/.test(line)).join('\n').replace(/\*\*/g, '').trim();
  for (const candidate of [input, input.replaceAll('\n', '\r\n'), input.replace(/\((\d{2}:\d{2}~\d{2}:\d{2})\)/g, '[$1]')]) {
    const prepared = prepareScenarioInput(candidate);
    assert.equal(prepared.title, '세상에서 가장 비싼 물질 top 1 (1g에 8경 원?!)');
    assert.equal(prepared.scenario, expected);
    assert.equal(prepared.metadata.length, 6);
    assert.doesNotMatch(prepared.scenario, /영상 제목|00:00|본론|Hook|Call to Action/);
    assert.match(prepared.scenario, /반물질\(Antimatter\)/);
    assert.match(prepared.scenario, /댓글로 남겨주세요!/);
  }
});

test('parenthesized cues also support explicitly labelled and compact narration', () => {
  const input = '영상 제목: 시험\n(00:00~00:03) 후킹\n나레이션: "첫 문장입니다."\n(00:03~00:08) 설명\n나레이션: "두 번째 문장입니다."';
  for (const candidate of [input, input.replaceAll('\n', '')]) {
    const prepared = prepareScenarioInput(candidate);
    assert.equal(prepared.scenario, '첫 문장입니다.\n두 번째 문장입니다.');
    assert.equal(prepared.visualCues.length, 2);
  }
});

test('a malformed explicit narration block cannot silently disappear', () => {
  assert.throws(() => prepareScenarioInput('[00~03초] 나레이션: "정상 문장."\n[03~08초] 나레이션: "닫히지 않은 문장'), /나레이션 문장/);
});

test('ordinary parentheses and times inside spoken sentences are preserved', () => {
  const narration = '반물질(Antimatter)은 어렵습니다.\n지금 시간은 00:08입니다.\n가격(1g 기준)을 살펴봅니다.\n결론은 아직 모른다는 것입니다.';
  assert.equal(prepareScenarioInput(narration).scenario, narration);
});
