# Documentary disclosure probe

Private cinematic-slide 0.2.0 adds visible evidence status for history/documentary
scenes. Generated assets explicitly identified in fixture metadata show AI reconstruction;
unknown origin (including unsupported archival claims) shows source verification needed.
This is not independent verification of planner metadata or archival licensing.

Verified:
- Harness validation passed.
- Three unit tests passed: per-shot timing, untrusted archive claim, other genres unchanged.
- Actual local graph render: output/documentary-disclosure-v1/delivery/cinematic.mp4,
  10.033333 seconds, 1920x1080, 30fps, H.264/AAC.
- Existing images and matched voice reused; no paid API calls.
- Frame at 2 seconds inspected: upper-left disclosure is readable and does not cover
  the face, screen result or bottom narration in this composition.

Limits: this short modern computer illustration is a disclosure test, not proof of
historical accuracy or documentary storytelling. Label placement still needs checking
for other compositions. Scene origin must eventually come from a trusted asset ledger,
not merely planner assertions. No public renderer routing was changed; service-wide
adoption and human quality review remain pending. Original narration is unchanged.
