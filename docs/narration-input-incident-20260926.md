# Narration extraction incident: parenthesized timestamps

## Confirmed cause

Completed job `a6bda8ed-ac37-4392-9df3-e84e01b45ce1` used classic-slide@1.2.0,
dystopian style. Its original input had an emoji-prefixed `영상 제목:` and
unlabelled narration under `(00:00~00:08) 도입부 (Hook)` and four other sections.

The intake parser recognized square-bracket timestamps and explicitly labelled
narration, but not parenthesized timestamp headers or the prefixed title. Both
the stored production scenario and scene-plan narrations contained these lines.
The first scene was the title. This was an intake error, not a playback-cache bug.
Previous acceptance coverage was insufficient for this script format.

## Correction and validation

- Recognize square and round timestamp headers, with seconds or mm:ss values.
- Treat emoji/markdown-prefixed video titles as metadata.
- Preserve ordinary parentheses and spoken numbers, including Antimatter.
- Reject malformed explicitly labelled timed narration instead of dropping it.
- Production renderer rejects residual title, timing and direction headers before
  provider calls. Research requests retain their separate compatibility contract.
- Server tests: 47 pass. New renderer boundary tests: 4 pass.
- Existing subtitle timing/transcript tests: 3 pass.
- Main-service estimate endpoint now returns 458 narration characters for the
  incident input, excluding title and all five timed section headings.
- API, worker and runner rebuilt and deployed after confirming no active jobs.

The original MP4 and job records are preserved. The existing rendered audio and
captions do not change when the parser is updated. A new creation or remake is
required to produce a corrected video. No new paid/subscription generation was
triggered during this repair. The supplied narration's factual claims were not
changed or fact-checked as part of this parsing fix.
