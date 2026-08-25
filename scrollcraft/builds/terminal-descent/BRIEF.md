# BRIEF · terminal-descent · GLLMS landing page

Interviewed (not self-authored). One amendment logged below under **Pivot**.

## The eight answers, verbatim

1. **Vibe:** "Terminal noir"
2. **Scroll journey:** "Threat → proof → try it"
3. **Energy curve:** "Calm open, intense middle"
4. **Feeling + peak:** "Intrigue → unease → control" · peak: "watching the injection actually break the model"
5. **One thing no site does:** "Scroll hijacks a chatbot" (as you scroll, a fake LLM chat visibly gets prompt-injected; the page demonstrates the attack on itself)
6. **Range from premium-minimal:** "Retro" (terminal/CRT nostalgia)
7. **Structure:** "One unbroken world"
8. **Assets:** "Nothing yet"

Follow-ups, verbatim:

- **Belief by end:** "This threat is real"
- **Next action:** "Run a scenario" (one label, used everywhere)
- **Art direction:** "Photographic"

## Pivot (user decision, post-interview)

Generation spend was declined ("No generation at all"), so the photographic
world is replaced by a **code-drawn vector-phosphor world** (SVG/CSS, zero API
cost). Everything else in the brief stands. The world change strengthens the
retro/terminal-noir answers rather than fighting them: the page reads as a
1980s vector display rendering the attack live.

## What this is

Landing page for GLLMS: an education lab for OWASP LLM Top 10 attacks where you
read an attack script, press Run, and watch a real agent execute it (scenario
s1: indirect prompt injection in RAG). Visitor must leave believing **this
threat is real**, and click **Run a scenario** (links to the app at `/`).

## Journey

```
1  Threat      they see how much of their AI's knowledge arrives untrusted
2  Tension     the query leaves their hands into the machine
3  Proof       five documents come back; four are policies
4  PEAK        one of them lies, and the model obeys it
5  Turn        the boundary marks it untrusted and the model refuses
6  Commitment  arrival at a terminal: run the scenario yourself
```

## Feeling curve (curve first, legs second)

| # | Leg (place) | Emotion | What on screen causes it |
|---|---|---|---|
| 1 | Entry hall | Calm intrigue | Night facility rendered as phosphor line art; one console glowing; the scale of the place |
| 2 | Fiber spine | Dread, recognition | The visitor's own question travelling away from them as light pulses down cables |
| 3 | Archive vault | Unease | Rows of retrieved documents at three depths; one slab sits slightly out of alignment |
| 4 | Poisoned page | Alarm (PEAK) | A hidden instruction surfaces inside a document as inverse-video text and grows; the chat panel breaks and obeys |
| 5 | Trust boundary | Relief | A gate of light bars; the injected block stamped UNTRUSTED behind quarantine lines; the chat replays the same exchange, refused |
| 6 | Terminal arrival | Resolve | Desk-level terminal, cursor blinking, the prompt line waiting |

No two adjacent legs share an emotion.

## Peak

In the visitor's words: *"I was scrolling a security site and its own demo chat
got hijacked by a note hidden inside a document."*

Lives in leg 4. Gets the largest weight (1.6vh) plus linger dwell, the silence
in front of it, and the only inverse-video state change on the page.

## Authored silence

The last third of leg 3 is deliberately sparse: layer motion slows, copy thins
to one short line ("One of them is lying."), nothing new arrives for roughly a
third of a viewport-height. This is the quiet before the drop, not dead scroll.

The same applies to every copy plateau and to the final hold: each block reaches
full opacity and *stays* while it is read — a window that only touches 1 for one
instant is the defect, not the hold. The shoot harness counts clip time /
crossfades / cue-opacity deltas; this build has no clips, so every plateau
(0–3%, 22–25%, 37–40%, 75–81%) and the resolution hold (94–100%) report as
"dead scroll" there by construction. The motion those samples cannot see is real
and asserted locally: `--sc-segp` advances inside every leg and the scene layers
translate with it (`lab/assert-local.mjs`).

## Verification record

- `lab/assert-local.mjs`: 21 passed / 0 failed on desktop (1440×900) and under
  reduced motion — spacer/stage/flow geometry, seam handoff (outgoing releases
  only once covered), copy translate cap, per-leg full opacity, layer motion,
  chat phase ladder (idle → query → search → docs → hijack/guard → prompt),
  depth readout, verify-state publication, finale hold, no console errors.
- Contact sheets (desktop / mobile 375×812 / reduced motion): every leg paints a
  real frame; contrast ≥4.5:1 at worst frame on all three after widening the
  band scrim (the relief block measured 4.45:1 over its reduced-motion poster).
- The one true dead stretch found (relief → finale, ~86–91%) was closed by
  starting the finale ramp early (`data-sc-window="0.872 1 0.38 0"`).

## Tell-someone sentence

"It's the site where scrolling flies you down into an AI's pipeline and the
chat window gets prompt-injected right in front of you."

## Grammar

**Continuous world** (worldflight mode), chosen by the interview answer "One
unbroken world", not by default. Why the other seven lost: filmic one-shot is
the default drift and cuts the world into pinned blocks; chaptered editorial
contradicts "unbroken"; live surface bans full-frame imagery that carries the
descent; typographic poster has no world to fly through; gallery, split stage
and cutlist all impose section boundaries the brief forbids.

## Signature move

**The hijacked transcript**: a fixed chat panel accumulates a labelled,
simulated s1 transcript as waypoints pass (user query → assistant cites docs),
breaks at leg 4 (retrieved document speaks as inverse-video instruction;
assistant starts leaking policy text marked UNTRUSTED OUTPUT), replays the same
exchange protected at leg 5, and resolves to the Run-a-scenario prompt at leg 6.
Real markup computing state from scroll (`sc:waypoint` + track progress);
labelled on its face as a simulation. It merges with the peak rather than
competing with it.

## Score table

| Beat | Leg scene | Within-leg treatment (variety axis) | Why this one |
|---|---|---|---|
| Threat | Entry hall | Perspective grid parallax, doorway pulse | Establishing position inside the world |
| Tension | Fiber spine | Packet glyphs drifting toward the viewer off leg progress | Travel = transmission |
| Proof | Archive vault | Three shelf depths, misaligned slab foreshadow | Breadth of retrieval |
| Peak | Poisoned page | Inverse-video block growing out of the document + chat break | Macro change of state |
| Turn | Trust boundary | Gate bars wipe across; quarantine stamps land | A wipe is a change of state |
| Commitment | Terminal arrival | Blinking cursor, prompt-line CTA as object in the place | Resolve and hold |

Six distinct treatments, none repeated consecutively. Nav is the map the
grammar requires: clickable waypoint trace + depth readout, driven by
`sc:waypoint`. No clips exist, so every leg ships its scene as static layers
moved by `--sc-segp`; reduced motion drops the transforms and keeps the story.
