# Reaction reading interval: V11/V12

Status: rendered experimental comparison; no human winner or production
promotion. Both clips use the same generated actor and articulated arm assets.
No new image generation or separate paid API call was made.

## Reference evidence

Source: https://www.youtube.com/watch?v=bHB5iiDDJ-s

The existing local source SHA-256 was revalidated as
`957f4678239327abaf5d2079067d7802f178e923d3f67f10c449911d0a0029b6`.
All 144 decoded frames of the 176-182 second window were inspected by the
measurement script; selected frames were visually reviewed as a labeled sheet.

Frame 90 (179.721208s) has narrow eyes and a grin. Frame 91 (179.762917s)
has wide eyes and a downturned mouth. The registered face crop's average RGB
change is 19.95284/255 while the rounded blue-body center is unchanged.
That center remains unchanged through frame 96 (179.971458s); translation is
measured again at frame 97 (180.013167s). This supports a short facial-reading
interval before renewed body movement in this particular shot.

It does not prove an exact physical stop: HSV segmentation, integer center
rounding and compressed pixels limit precision. Nor does it establish a
universal 0.25-second human reaction rule. A further facial change occurs at
frame 127 (181.264417s), confirmed in the sheet. The source's anthropomorphic
agent and our human character have different expressive needs.

Evidence: `output/layered-motion-reference-timing/source-frame-observations.json`
and `source-reaction-timing-sheet.jpg`. Reproduce with
`python experiments/layered-motion/analyze_reference_reaction.py`.

The official timing/spacing lesson at
https://ed.ted.com/lessons/animation-basics-the-art-of-timing-and-spacing-ted-ed
was read, but new continuous playback was unavailable because the browser
control runtime failed to initialize. Do not label that lesson as newly
analyzed frame by frame. The measured frames above belong to the locally
available bird-flu lesson.

## Authored comparison

All times below are local to the five-second reaction shot, which starts at
3 seconds in the complete eight-second clip.

| Event | V11 | V12 |
| --- | --- | --- |
| Smile transition | 1.15-1.65 | unchanged |
| Posture release ends | 2.20 | unchanged |
| Hand lifts | 1.80-2.55 | 2.40-3.15 |
| Hand remains raised | 2.55-3.60 | 3.15-3.60 |
| Hand returns | 3.60-4.70 | unchanged |

V12 shifts the 0.75-second lift later by 0.6 seconds. This leaves 0.2 seconds
between posture release and gesture onset. Keeping the return and total clip
duration fixed also shortens the held hand pose from 1.05 to 0.45 seconds.
That tradeoff may hurt the gesture's readability; it must be evaluated, not
hidden in a claim that every behavior is unchanged.

The hypothesis is that the smile reads before the additional gesture. The
counter-hypothesis is that V11 feels more coordinated and V12 unnecessarily
separates the reaction into steps. No automatic preference is assigned.

## Verification

- Rendered 8 seconds, 1920 x 1080, 30 fps, 240 frames in MP4 and WebM.
- Both delivery formats decode to identical frames.
- The face and monitor match V11 exactly at all 11 screenshot checkpoints.
- Geometry checks preserve planted feet and gaze. Generated sleeve anchors
  are checked in rendered coordinates across all 240 frames.
- Face/body channels and the still mode match the baseline in sampled states.
- Hand travel duration, target and return interval are retained; the lifting
  phase is retimed. No opacity crossfade is introduced.

Review URL: http://127.0.0.1:18771/?compare=timing

The review asks the viewer to describe the perceived emotion/action and choose
the more natural version. Only an actual human review may select a winner.
Do not promote this timing as a global director rule or begin workflow
optimization on the strength of these technical checks.
