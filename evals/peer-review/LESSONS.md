# What the eval revealed about peer-review

One run, 15 test cases, Claude Opus 4.8 as system-under-test, Claude Sonnet 4.6 as judge. Total cost: $1.31. Full results in [runs/2026-05-31_104014_claude-opus-4-8/](runs/2026-05-31_104014_claude-opus-4-8/).

This is the document the eval was for. Headline metrics in [summary.md](runs/2026-05-31_104014_claude-opus-4-8/summary.md). What follows is the interpretation: what worked, what didn't, what changed about the skill as a result.

## 1. The catch rate is the headline. Don't get distracted by the verdict number.

| Metric | Value |
|---|---|
| **Catch rate (seeded issues caught)** | **100% (39/39)** |
| **Correct-lens catch rate** | **97.5% (38/39)** |
| Verdict accuracy (vs. my expected) | 40% (6/15) |

At first glance the 40% verdict accuracy looks bad. It isn't. When I dug into the cases where the verdict diverged from my expectation, the judge confirmed that the model found 3-7 additional legitimate issues per case that I hadn't seeded. The model was going harsher because there was genuinely more to flag, not because it was overcalibrated.

This is a **calibration problem in my ground truth**, not a flaw in the skill. My "needs minor edits" expectation for a PRD with 4 unsourced metrics was too soft. The model was right to call it "do not send."

Concrete example from [prd-vague-targets-001](runs/2026-05-31_104014_claude-opus-4-8/failures.md):

> Expected verdict: "needs structural rework"
> Got verdict: "do not send"
> Judge: caught all 4 seeded issues correctly under Skeptic, plus 5 unseeded legitimate findings including "Notification suppression carries unaddressed safety/compliance risk (security alerts, payment failures, legal notices)."

That safety/compliance issue is a real one I missed when seeding. "Do not send" is the defensible call.

**Lesson for eval design**: hand-score every test case for ALL legitimate issues, not just the ones you wanted to test. Otherwise the verdict targets drift and you wrongly attribute the gap to the system under test.

## 2. The lens framework works. The lens definitions are tight.

97.5% correct-lens assignment (38 of 39 caught issues went to the right lens, with only 1 going to Skeptic when I expected Audience). This is the strongest signal in the whole run.

The single wrong-lens case is [edge-asks-for-rewrite-015](runs/2026-05-31_104014_claude-opus-4-8/scores.jsonl):

> Seeded issue (Audience): "Missing context: which top 10 customers, what specifically they said about search quality"
> Model assigned: Skeptic ("'customers say' as unsupported")

This is ambiguous. "Customers say X" is both an audience problem (the reader doesn't know who or what) AND a skeptic problem (the claim is unsupported). I'd call this a fair categorization either way. Not a real failure.

**No SKILL.md change needed for the lens definitions.**

## 3. The em-dash hard rule is violated 40% of the time.

| Cases with em dashes in output | 6 of 15 (40%) |
| Total em-dash violations across run | 31 |

The skill says explicitly: "**No em dashes** in any output." The model doesn't follow this consistently. Worst offenders:

- [`edge-em-dash-input-014`](runs/2026-05-31_104014_claude-opus-4-8/failures.md) (low-stakes Slack memo): 4 em dashes, including (per judge) "'P0 — The offsite conflict', 'P1 — Set a deadline', 'P2 — Em dash overload'". The model used em dashes to bullet-format its own findings while critiquing the draft for em-dash overuse. Ironic.
- [`customer-email-missing-context-005`](runs/2026-05-31_104014_claude-opus-4-8/failures.md) (high stakes, financial customer CISO): 6 em dashes.
- All 3 control cases: 3-5 em dashes each.

The judge flagged 2 of these as policy violations. The automated scorer caught all 6.

**Action: SKILL.md was updated** to make the em-dash rule more emphatic and to specify what to use instead. See the [diff](#changes-made-to-peer-review-as-a-result).

## 4. The skill doesn't invent issues. Control cases are clean.

| False positive count across 15 cases (per judge) | 0 |
| Control case clean rate (no false positives) | 100% (3/3) |

This is the most important defensive metric. The skill could fail in two directions: missing real issues (caught above), or inventing fake ones to fill lens slots. The eval shows it doesn't do the second one.

The 7-8 "additional findings" per control case turn out to be **legitimate** issues per the judge, not invented ones. Quoting the judge on [`control-good-leadership-update-012`](runs/2026-05-31_104014_claude-opus-4-8/scores.jsonl):

> "every finding it flags is a legitimate, substantive observation grounded in the actual draft text. The skill did not invent phantom problems to fill lens slots; instead, it identified real weaknesses (unsourced 'binding,' unaddressed failure mode of Option B, buried deadline, ambiguous open items)."

My controls weren't as clean as I thought. The skill is honest about what it finds. **No SKILL.md change needed for false-positive avoidance.**

## 5. The HTML canvas instruction is hit-or-miss in API contexts.

The skill says: "Render as an HTML canvas". In Cursor that triggers canvas rendering. Over the API, it produces 5-10KB of HTML markup wrapping the actual critique. Some cases produced full HTML (case 001 at 9,995 chars, case 002 at 7,000+ chars). Other cases the model decided to produce markdown instead.

Case 005 had this explicit preamble:

> "A note before the findings: I'd normally render this as an HTML canvas, but the review is compact enough that inline serves you better here. Flagging that I'm deviating from the default format intentionally."

That's good adaptive judgment, but it means the output format is unpredictable. For API consumers, you can't reliably parse the response.

**Action: SKILL.md was updated** to make canvas-vs-inline conditional on the runtime context.

## 6. The automated quote-extraction scorer is unreliable on HTML output.

| Reported "hallucinated quotes" total | 194 |
| Real hallucinations per judge | 0 |

The automated scorer extracts anything in `"..."` as a quote and checks if it appears in the input. When the output is HTML, this picks up CSS color codes (`"#16213e"`), HTML attribute values (`"en"`, `"UTF-8"`), and font family strings as "quotes." None of these are claims about the draft.

The judge correctly identified zero actual hallucinations across all 15 cases (the judge's reasoning on case 001 explicitly debunks the automated flag: "no metrics, customer names, or quotes are invented from the INPUT_DRAFT").

**Action: scorer needs to strip HTML before quote extraction, or skip the check when output is HTML-dominant. Tracked as future work below. Not blocking on this run because the judge correctly caught the real signal.**

## Judge validation

Per the [scoring-rubric.md](scoring-rubric.md) requirement, three cases were hand-scored against the judge:

| Case | Hand-scored issues | Judge issues | Agreement |
|---|---|---|---|
| `prd-vague-targets-001` | 4/4 caught_correct_lens, 0 false positives, 5 legitimate unseeded findings | Same | 100% |
| `roadmap-no-commitment-007` | 4/4 caught_correct_lens, 0 false positives, 3 legitimate unseeded findings | Same | 100% |
| `control-good-prd-011` | 0 false positives, 7 legitimate unseeded findings | Same | 100% |

**Judge agreement: 100% (above the 80% trust threshold).** Judge scores are treated as validated for this run.

## Changes made to peer-review as a result

1. **Em-dash rule strengthened.** Added concrete alternatives (commas, periods, parentheses, short sentences) and an explicit note that the rule applies to your own prose even when critiquing a draft that contains em dashes.
2. **Canvas instruction made context-aware.** HTML canvas when running inside Cursor, structured markdown otherwise. Removes the "render full HTML over the API" failure mode.

Diff in [skills/peer-review/SKILL.md](../../skills/peer-review/SKILL.md). One re-run after these changes should drop em-dash violations to zero and produce parseable markdown output. Tracked as next-run work below.

## What this eval doesn't cover

- **Cursor's skill activation logic.** The description field in the skill frontmatter triggers the skill when user phrasing matches. The eval bypasses this by invoking the skill body as a system prompt directly.
- **Canvas rendering.** The eval captures the text payload. In Cursor, that text becomes a rendered canvas. The eval can't tell whether the canvas looks good visually.
- **Multi-turn behavior.** `peer-review` is a single-shot transform. If we wanted to test "user asks for clarification after the review," that's a separate harness.
- **Cross-model comparison.** Only run against Opus 4.8. Future work: re-run against Sonnet 4.6 and a non-Anthropic model to see which performs best per dollar.

## Future work

| Priority | Item |
|---|---|
| **P0** | Re-run after SKILL.md edits. Verify em-dash violations drop to 0 and HTML output disappears. |
| **P1** | Fix the automated quote-extraction scorer to handle HTML. Strip tags before extraction, or skip when output is HTML-dominant. |
| **P1** | Add 5-10 more control cases, this time genuinely scrubbed for hidden gaps. Current controls were under-cleaned and gave a misleading "ready to send" target. |
| **P2** | Run against Sonnet 4.6 and one non-Anthropic model. Build a model-comparison table. |
| **P2** | Add a "regression suite" of cases from real production drafts (anonymized) so the eval reflects actual use, not just synthetic patterns. |
| **P3** | Test multi-turn: "review this, then incorporate the feedback into a revised version" type follow-ups. Different harness needed. |

## What this proved about evals as a practice

Three things worth carrying forward into other skills:

1. **Build the eval before trusting the skill.** I'd been using `peer-review` for months on real drafts. The eval showed it violates its own em-dash rule 40% of the time. I hadn't noticed because I read for content, not policy compliance. Manual use isn't a substitute for systematic measurement.

2. **The judge needs validation against humans, but it's worth it.** 3 hand-scored cases (~15 min) gave high confidence in the other 12. Without that validation step, the judge's confident-sounding output is just plausible vibes.

3. **The eval data forces ground-truth recalibration.** My "expected verdicts" were softer than what the model produces. The skill is calibrated tighter than I was scoring it. That's a useful correction, but I only got there because the eval forced me to look at every case side-by-side.

The methodology generalizes. See [`skills/evals/SKILL.md`](../../skills/evals/SKILL.md) for the reusable version.
