export type CostBreakdownInput = {
  inferenceCostKrw: number;
  imageCostKrw: number;
  voiceCostKrw: number;
};

export type CostSlice = {
  key: "inference" | "image" | "voice";
  label: string;
  value: number;
  percent: number;
  color: string;
};

export function buildCostBreakdown(input: CostBreakdownInput) {
  const values = [
    { key: "inference" as const, label: "Codex 추론", value: Math.max(0, Number(input.inferenceCostKrw) || 0), color: "#7867d8" },
    { key: "image" as const, label: "이미지 API 환산", value: Math.max(0, Number(input.imageCostKrw) || 0), color: "#2f6fdb" },
    { key: "voice" as const, label: "음성", value: Math.max(0, Number(input.voiceCostKrw) || 0), color: "#18a078" },
  ];
  const total = values.reduce((sum, item) => sum + item.value, 0);
  const slices: CostSlice[] = values.map((item) => ({
    ...item,
    percent: total > 0 ? item.value / total * 100 : 0,
  }));
  let cursor = 0;
  const gradient = slices.map((slice) => {
    const start = cursor;
    cursor += slice.percent;
    return `${slice.color} ${start.toFixed(4)}% ${cursor.toFixed(4)}%`;
  }).join(", ");
  return { total, slices, gradient: total > 0 ? `conic-gradient(${gradient})` : "#e7ebf1" };
}
