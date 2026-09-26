import type { ImageStyle } from "./image-style";

export const MOTION_STYLE_IDS = ["narrative", "educational_info"] as const;
export type MotionStyleId = typeof MOTION_STYLE_IDS[number];
export type MotionStyleSnapshot = {
  id: MotionStyleId;
  version: "1.0.0";
  imagePreset: ImageStyle;
  storyContract: string[];
  assetContract: string[];
  productionRoute?: "local_graphic";
};

const STYLES: Record<MotionStyleId, MotionStyleSnapshot> = {
  narrative: {
    id: "narrative", version: "1.0.0", imagePreset: "editorial_illustration",
    storyContract: ["대본에 맞는 사람·물체·현상 중 한 주체를 선택", "주체 정체성 유지", "국소 변화", "큰 맥락", "결과"],
    assetContract: ["동일 주체의 장면 간 식별자와 디자인 앵커", "움직일 대상의 사전 분리 계획", "배우 연기·접촉은 승인 자산 없이는 차단"],
  },
  educational_info: {
    id: "educational_info", version: "1.0.0", imagePreset: "graphic_explainer",
    storyContract: ["질문", "원리", "단계·비교·수치의 시각화", "이해 확인"],
    assetContract: ["레이블·도식·경로를 편집 가능한 객체로 저작", "설명과 무관한 움직임 제외", "수치와 인과 관계는 대본 근거 확인"],
  },
};

export function motionStyleSnapshot(id: MotionStyleId, localProduction = false): MotionStyleSnapshot {
  const snapshot = structuredClone(STYLES[id]);
  if (localProduction) snapshot.productionRoute = "local_graphic";
  return snapshot;
}
