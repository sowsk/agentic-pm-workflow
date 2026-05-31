# Scoring rubric: peer-review eval

Two scoring tracks, mirroring the framework from [the Instagram video on PM evals](https://www.instagram.com/) that started this work: **quantitative** (factual / accurate) and **categorical** (behavior class). Quantitative dimensions can be checked automatically. Categorical dimensions require an LLM-as-judge or human reviewer.

The eval scores each test case in `test-cases.jsonl` against the agent's output (raw text response to the peer-review skill).

## Quantitative dimensions

Each scored 0/1 or as a percentage. Computed by [score_outputs.py](score_outputs.py) without LLM involvement.

| Dimension | How it's scored | Why it matters |
|---|---|---|
| `verdict_present` | 1 if output contains one of the 4 valid verdicts ("ready to send", "needs minor edits", "needs structural rework", "do not send"), else 0 | Skill spec requires a verdict; missing means the skill structurally failed |
| `verdict_correct` | 1 if extracted verdict equals `expected_verdict`, else 0 | The most important single quantitative signal |
| `findings_present` | 1 if output contains a "Top 3" or "by-lens findings" section, else 0 | Required by skill spec |
| `output_word_count` | Integer word count of the output | Sanity check; very short outputs often indicate failure |
| `em_dash_count` | Count of em-dash characters in output | Hard rule: skill must produce zero em dashes regardless of input |
| `quotes_from_input` | Count of quoted strings in output that appear verbatim in the input draft | Hard rule: "quote the draft when you flag something" |
| `quotes_not_in_input` | Count of quoted strings in output that do NOT appear in the input | Hallucinated quotes; should be 0 |

## Categorical dimensions (LLM-as-judge or human)

Each scored as a binary class. Judged by a different model than the system-under-test (see [judge-prompt.md](judge-prompt.md)). Validated against human scoring on 3 cases per run before being trusted.

| Class | Definition | Source |
|---|---|---|
| `hallucination` | Output cites a metric, claim, customer, date, or quote that does not exist in the input draft | Video framework: "did it hallucinate or not" |
| `policy_violation` | Output rewrote the draft instead of critiquing it, OR contains em dashes, OR ignored stakes calibration (e.g. went line-by-line on a low-stakes Slack draft, or top-line only on a critical regulatory doc) | Video framework: "policy violation"; skill hard rules |
| `wrong_lens_assignment` | Output catches a real issue but logs it under the wrong lens (e.g. a missing-context Audience issue logged under Skeptic) | Video framework: "wrong tool called" (analog) |
| `partial_answer` | Output has a verdict but is missing required sections (Top 3, by-lens findings, what's working, suggested next step) | Video framework: "partial answer" |
| `gave_up` | Output refuses to review, asks too many clarifying questions instead of proceeding, or produces a single sentence of generic feedback | Video framework: "it just gives up" |

## Per-issue scoring (subjective)

For each `seeded_issue` in a test case, the judge scores:

| Score | Meaning |
|---|---|
| `caught_correct_lens` | Issue was flagged AND logged under the correct lens |
| `caught_wrong_lens` | Issue was flagged but logged under a different lens than seeded |
| `missed` | Issue was not flagged at all |

A `caught_correct_lens` is the best outcome. A `caught_wrong_lens` counts as a partial success (the issue was found, the categorization was off). A `missed` is the worst outcome.

For each case, the judge also reports:
- `false_positives`: list of issues the output flagged that are not in the seeded issue list AND are not legitimately present in the draft (i.e. invented issues, the "do not glaze, do not invent" hard rule)

## Aggregate metrics (per run)

Reported in `runs/<timestamp>/summary.md`:

| Metric | Formula |
|---|---|
| Catch rate | (caught_correct_lens + caught_wrong_lens) / total_seeded_issues |
| Correct-lens catch rate | caught_correct_lens / total_seeded_issues |
| Verdict accuracy | sum(verdict_correct) / total_cases |
| False positive rate | total_false_positives / total_cases |
| Hallucination rate | sum(hallucination) / total_cases |
| Policy violation rate | sum(policy_violation) / total_cases |
| Em dash violation count | sum(em_dash_count) across all cases |
| Hallucinated quote count | sum(quotes_not_in_input) across all cases |
| Control case clean rate | (control cases with verdict = "ready to send" AND zero false positives) / total_control_cases |
| Judge-human agreement rate | (cases where judge score matches human score on the 3 validated cases) |

## Pass / fail thresholds

These are targets, not gates. A failing metric is signal for iteration, not for blocking publication.

| Metric | Target | Notes |
|---|---|---|
| Verdict accuracy | >= 0.80 | The most important single number |
| Catch rate | >= 0.75 | Below this means the lens framework isn't catching real issues |
| Correct-lens catch rate | >= 0.60 | Below this means the lens definitions need sharpening |
| False positive rate | <= 0.2 issues per case | Above this means the skill is inventing issues to fill slots |
| Em dash violation count | 0 | Hard rule, no tolerance |
| Hallucinated quote count | 0 | Hard rule, no tolerance |
| Control case clean rate | >= 0.67 (2 of 3) | Below this means the skill cannot tell a good draft from a bad one |
| Judge-human agreement rate | >= 0.80 | Below this, fall back to manual scoring for that run |

## Validation: judge vs. human

Before trusting LLM-as-judge scores, hand-score 3 cases per run (one control, one skeptic-focused, one strategist-focused) and compute agreement against the judge. Document the agreement rate in the run summary.

If agreement is below 80%, the run reports judge scores as "unvalidated" and the eval relies on the hand-scored subset plus all automated quantitative metrics. Lessons writeup should note which dimensions were unreliable.
