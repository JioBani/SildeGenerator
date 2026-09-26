# Changelog

## 0.1.0 narrative-slide

- Fork cinematic-slide 0.6.0 without changing released renderers.
- Add typed shot intent to the actual director schema and image prompts.
- Automatically repair causal, state-continuity and repeated-shot findings.
- Preserve narration and measured timing; contract pass does not claim emotional quality.

## 0.5.0 cinematic-slide (private)

- Align camera, continuity group and renderer preference instructions with the
  actual structured director output schema; null camera means hold.
- The shared schema also exposes bounded visual labels already requested by genre
  planning, without claiming every renderer draws them.

## 0.4.0 cinematic-slide (private)

- Plan segment boundaries at cuts so outgoing dissolves are not lost in assembly.
- Core validates the partition and fingerprints the full scene contract for caching.

## 0.3.0 cinematic-slide (private)

- Respect outgoing cut/crossfade/dissolve per boundary within a segment.
- Compute each outgoing extension once consistently for FFmpeg inputs and filters.
- Reject unsupported explicit transitions during preflight instead of replacing them.
- Cross-segment transitions remain unimplemented; no public promotion.

## 0.2.0 cinematic-slide (private)

- History and documentary shots receive a visible evidence-status label.
- Explicit generated origin displays AI reconstruction; unknown or archival claims
  remain unverified. No model-supplied provenance is automatically approved.
- Narration text/timing and other genres remain unchanged.

## 0.1.0 cinematic-slide

- Private fork; replaces cut-index camera alternation with explicit camera intent.
- Zero crossfade duration compiles to true concatenation, not a zero-duration xfade.
- Holds matched-state cuts to prevent camera reset during dissolves.
- Preserves provider, subtitle, audio and assembly interfaces. No automatic approval.

## Inherited classic-slide history

## 1.1.0

- 장면 계획에서 런타임 ID와 교차참조 생성을 제거하고 결정론적 컴파일러 계약을 사용합니다.
- 모델은 중첩된 의미 구조와 장면 번호만 제안하며 source unit, hierarchy, keycut parent, continuity 참조는 Core가 생성합니다.

## 1.0.0

- 기존 24fps Ken Burns/crossfade/ASS 자막 렌더를 Core `media.py`에서 Harness로 이전했습니다.
- 임의 DAG의 subtitle/render/audio/assembly task로 실행됩니다.
