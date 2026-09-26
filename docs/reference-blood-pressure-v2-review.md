# Blood wall measurement V2

Experimental astra-motion@0.3.0 example only; Core and production defaults unchanged. V1 preserved. No paid calls. Docker Mock E2E remains unverified; this is the local GSAP/Chrome study path.

## Objective and evidence

Replace the constant invented traveling wave over source 65-78s with measured cream vessel centerlines. Labels, heart, typography, narrative order and 30-second output duration are unchanged. Source native PTS, source SHA and individual frame hashes are recorded in blood-wall-measurement-v1.json. 312 source frames are sampled at 77 horizontal positions on each lining; all corresponding SVG control points match the extracted values in output coordinates. This is not a rendered-silhouette or physiology approval.

At first, center expansion appeared to be the only behavior. Later frames show traveling crests too. Peak locations span 16-576 analysis pixels; measured amplitude spans 1-16 pixels. A stationary or constant traveling oscillator alone cannot represent both. Keep the source-aligned state track, not a single guessed period.

## Extraction failures

- Source 63s still contains the split-heart panel, so the full-width ROI was invalid. Start the reviewed measurement at 65s instead.
- A broad cream threshold admitted yellow arrows; a blue/green ratio separates the reviewed colors.
- Sampling at the extreme image edge missed dashed cream lining. The reviewed range is x=16..624 with a 13-pixel horizontal window. Outside that range, the candidate extends endpoint height; it is not measured evidence.
- Reject missing or ambiguous samples instead of silently substituting zero. Tests cover a known line, missing lining and disconnected candidates.

## Boundaries

Before the measured interval the curve remains approximate. After it, the last geometry holds until the panel leaves; source motion there is unverified. Eighteen out-of-order seeks pass. Original control-point matching is narrower than full spatial fidelity: threshold bias, stroke thickness, dashes, transition timing and heart/body proportions still need review. Audio absent. No human approval or automatic grammar promotion.

Do not use constant per-frame change as a quality criterion: legitimate source holds can be static. A measurement-aligned track must be checked against source events and hold intervals, not encouraged to move constantly.

## Render review

The 30-second V2 MP4 decodes without errors. The rebuilt source/candidate sheet at the measured interval shows central expansion, a flat hold and subsequent traveling crests in corresponding positions. Candidate stroke thickness, lining pattern, smaller type and oversized arrowheads remain visibly different. The source aligned control points improve this one motion layer, not the whole scene. Keep visual status REVISE, audio NOT_IMPLEMENTED and human approval false. Existing 81-second V1 remains separate; this candidate has not been promoted into it.
