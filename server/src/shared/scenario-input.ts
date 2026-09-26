const TITLE = /^\s*\[시나리오\]\s*(.+?)\s*$/i;
const NON_NARRATION = /^\s*(?:장르|분량)\s*:\s*(.+?)\s*$/i;
const PRODUCTION_NOTE = /^\s*(?:(?:메모|연출|장면|화면|카메라|자막|음악|효과음|BGM|컨셉|콘셉트|시놉시스)\s*:|[\[(]\s*(?:메모|연출|장면|화면|카메라|자막|음악|효과음|BGM|나레이션)(?:\s|:|\)|\]))/i;
const HEADING = /^\s*#{1,6}\s+(.+?)\s*$/;
const SCRIPT_MARKER = /^\s*#{0,6}\s*(?:\*\*)?\s*\[(?:유튜브\s*)?\d+\s*분\s*나레이션\s*대본\]\s*(?:\*\*)?\s*$/i;
const SEPARATOR = /^\s*(?:-{3,}|_{3,}|\*{3,})\s*$/;
const NARRATION_LABEL = /^(?:나레이션|내레이션|음성|VO|V\.O\.)\s*[:：]\s*(.*)$/i;
const TIME_CUE = /^[\[(]\s*\d{1,2}(?::\d{2})?\s*[~–—-]\s*\d{1,2}(?::\d{2})?\s*(?:초|s|sec)?\s*[\])]/i;
const NAMED_TITLE = /^[^\p{L}\p{N}]*(?:(?:영상|동영상|쇼츠)\s*)?제목\s*[:：]\s*(.+?)\s*$/u;
const TABLE_LINE = /^\s*\|/;
const INLINE_TIME_CUE = /[\[(]\s*(\d{1,2}(?::\d{2})?\s*[~–—-]\s*\d{1,2}(?::\d{2})?\s*(?:초|s|sec)?)\s*[\])]/gi;
const INLINE_NARRATION = /(?:나레이션|내레이션|음성|VO|V\.O\.)\s*[:：]\s*/i;

export type VisualCue = { timeCue: string; direction: string; narration: string };

function plainMarkdown(line: string) {
  return line
    .replace(/^\s*(?:>\s*)+/, "")
    .replace(/^\s*#{1,6}\s+/, "")
    .replace(/^\s*\d+[.)]\s+/, "")
    .replace(/^\s*[-*+]\s+/, "")
    .replace(/\*\*(.+?)\*\*/g, "$1")
    .replace(/__(.+?)__/g, "$1")
    .replace(/`(.+?)`/g, "$1");
}

function spokenText(value: string) {
  const text = value.trim();
  if ((text.startsWith('"') && text.endsWith('"')) || (text.startsWith('“') && text.endsWith('”'))) {
    return text.slice(1, -1).trim();
  }
  return text;
}

function timedStoryboard(raw: string): { scenario: string; title?: string; metadata: string[]; visualCues: VisualCue[] } | null {
  const source = raw.replace(/\r\n/g, "\n").replace(/\\~/g, "~");
  const cues = [...source.matchAll(INLINE_TIME_CUE)];
  if (cues.length < 2) return null;
  const visualCues: VisualCue[] = [];
  const metadata: string[] = [];
  const prefix = source.slice(0, cues[0].index).trim();
  if (prefix) metadata.push(prefix);
  const heading = prefix.split("\n").map((line) => plainMarkdown(line).match(NAMED_TITLE)?.[1] ?? line.match(HEADING)?.[1]).find(Boolean);
  const title = heading ? plainMarkdown(heading).trim() : undefined;
  for (let index = 0; index < cues.length; index++) {
    const cue = cues[index];
    const section = source.slice(cue.index + cue[0].length, cues[index + 1]?.index ?? source.length)
      .replace(/\*\*/g, "").trim();
    const label = INLINE_NARRATION.exec(section);
    if (!label) {
      metadata.push(`${cue[0]} ${section}`.trim());
      continue;
    }
    const direction = section.slice(0, label.index).replace(/^[-*+]\s*/, "").trim();
    const remaining = section.slice(label.index + label[0].length).trim();
    const closing = remaining.startsWith("“") ? "”" : remaining.startsWith('"') ? '"' : null;
    const end = closing ? remaining.indexOf(closing, 1) : -1;
    const spoken = closing && end > 0 ? remaining.slice(1, end).trim()
      : closing ? "" : remaining.split("\n", 1)[0].trim();
    if (!spoken) {
      throw new Error("시간별 나레이션 문장을 확인해 주세요.");
    }
    const visualCue = { timeCue: cue[1].trim(), direction, narration: spoken };
    visualCues.push(visualCue);
    metadata.push(`${cue[0]} ${direction}`.trim());
  }
  if (!visualCues.length) {
    if (INLINE_NARRATION.test(source)) throw new Error("시간별 나레이션 문장을 확인해 주세요.");
    return null;
  }
  return { scenario: visualCues.map((cue) => cue.narration).join("\n"), title, metadata, visualCues };
}

export function prepareScenarioInput(raw: string): { scenario: string; title?: string; metadata: string[]; visualCues: VisualCue[] } {
  const storyboard = timedStoryboard(raw);
  if (storyboard) return storyboard;
  const narration: string[] = [];
  const metadata: string[] = [];
  let title: string | undefined;
  const lines = raw.replace(/\r\n/g, "\n").split("\n");
  const markerIndex = lines.findIndex((line) => SCRIPT_MARKER.test(line));
  const content = markerIndex >= 0 ? lines.slice(markerIndex + 1) : lines;
  if (markerIndex >= 0) {
    metadata.push(...lines.slice(0, markerIndex + 1).map((line) => line.trim()).filter(Boolean));
  }
  const explicitNarration = content.some((line) => NARRATION_LABEL.test(plainMarkdown(line).trim()));
  let narrationBlock = false;
  for (const line of content) {
    const plain = plainMarkdown(line).replace(/\\~/g, "~");
    const cue = TIME_CUE.test(plain.trim());
    const labeled = plain.trim().match(NARRATION_LABEL);
    if (labeled) {
      const spoken = spokenText(labeled[1]);
      if (spoken) narration.push(spoken);
      narrationBlock = !spoken;
      continue;
    }
    if (cue || TABLE_LINE.test(line)) {
      narrationBlock = false;
      metadata.push(line.trim());
      continue;
    }
    if (SEPARATOR.test(line)) {
      narrationBlock = false;
      metadata.push(line.trim());
      continue;
    }
    const titleMatch = line.match(TITLE);
    if (titleMatch && !title && narration.every((item) => !item.trim())) {
      title = titleMatch[1].trim();
      metadata.push(line.trim());
      continue;
    }
    const headingMatch = line.match(HEADING);
    if (headingMatch) {
      narrationBlock = false;
      if (!title && narration.every((item) => !item.trim())) title = plainMarkdown(headingMatch[1]).trim();
      metadata.push(line.trim());
      continue;
    }
    if (PRODUCTION_NOTE.test(plain)) {
      narrationBlock = false;
      metadata.push(line.trim());
      continue;
    }
    const namedTitle = plain.match(NAMED_TITLE);
    if (namedTitle) {
      if (!title) title = namedTitle[1].trim();
      metadata.push(line.trim());
      continue;
    }
    if (NON_NARRATION.test(plain)) {
      narrationBlock = false;
      metadata.push(line.trim());
      continue;
    }
    if (explicitNarration && !narrationBlock) {
      if (line.trim()) metadata.push(line.trim());
      continue;
    }
    narration.push(plain);
  }
  const scenario = narration.join("\n").trim();
  if (!scenario) throw new Error("내레이션 본문이 필요합니다.");
  return { scenario, title, metadata, visualCues: [] };
}
