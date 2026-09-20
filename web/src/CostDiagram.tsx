import { buildCostBreakdown } from "./cost-breakdown";

const won = (value: number) => `${value.toLocaleString("ko-KR", { maximumFractionDigits: 2 })}원`;

export function CostDiagram({ inferenceCostKrw, imageCostKrw, voiceCostKrw, actualExternalCostKrw }: {
  inferenceCostKrw: number;
  imageCostKrw: number;
  voiceCostKrw: number;
  actualExternalCostKrw: number;
}) {
  const model = buildCostBreakdown({ inferenceCostKrw, imageCostKrw, voiceCostKrw });
  return <div className="cost-diagram">
    <div className="cost-donut" role="img" aria-label={`총 환산 비용 ${won(model.total)}`} style={{ background: model.gradient }}>
      <div><strong>{won(model.total)}</strong><span>총 환산 비용</span></div>
    </div>
    <div className="cost-legend">
      {model.slices.map((slice) => <div key={slice.key}>
        <i style={{ background: slice.color }} />
        <span>{slice.label}</span>
        <strong>{won(slice.value)}</strong>
        <b>{slice.percent.toFixed(1)}%</b>
      </div>)}
      <p>실제 외부 결제 {won(actualExternalCostKrw)} · Codex와 이미지는 API 가격 환산값이며, OAuth 이미지의 실제 청구액은 별도입니다.</p>
    </div>
  </div>;
}
