import type { RunnerStage } from "../metrics/metrics.service";

const STAGE_LABELS: Record<string, string> = {
  prompt_loading: "프롬프트 준비",
  scene_planning: "장면 구성",
  image_generation: "이미지 생성",
  voice_generation: "음성 생성",
  subtitle_generation: "자막 생성",
  audio_assembly: "음성 조립",
  video_render: "영상 렌더링",
  deterministic_validation: "결과 검증",
};

export function failedStage(stages: RunnerStage[] | undefined) {
  return [...(stages ?? [])].reverse().find((stage) => stage.status === "failed")?.stage;
}

export function userFacingRunnerError(error: unknown, stage?: string) {
  const raw = error instanceof Error ? error.message : String(error);
  const label = stage ? STAGE_LABELS[stage] ?? stage : "영상 생성";
  if (/aborted|aborterror/i.test(raw)) {
    return `${label} 단계가 설정된 최대 작업 시간을 초과했습니다.`;
  }
  if (/fetch failed|ECONNRESET|socket hang up|EPIPE|ECONNREFUSED/i.test(raw)) {
    return `${label} 단계에서 렌더러 연결이 끊겼습니다. 잠시 후 다시 시도해 주세요.`;
  }
  if (raw === "runner reported failure") {
    return `${label} 단계에서 렌더러가 작업을 완료하지 못했습니다.`;
  }
  if (/scene narration must preserve|source units must preserve|source units must be used exactly once/i.test(raw)) {
    return `${label} 단계에서 대본 일부가 누락되어 안전 검증에 실패했습니다.`;
  }
  if (/invalid scene plan/i.test(raw)) {
    return `${label} 단계에서 장면 의미 구조를 처리하지 못했습니다.`;
  }
  return `${label} 단계 실패: ${raw}`;
}
