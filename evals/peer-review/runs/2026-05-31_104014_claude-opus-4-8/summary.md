# Run summary

- **Date**: 2026-05-31_104014_claude-opus-4-8
- **System-under-test**: `claude-opus-4-8`
- **Judge**: `claude-sonnet-4-6`
- **Cases run**: 15

## Headline metrics

| Metric | Value | Target |
|---|---|---|
| Verdict accuracy | 0.4 | >= 0.80 |
| Catch rate | 1.0 | >= 0.75 |
| Correct-lens catch rate | 0.975 | >= 0.60 |
| False positive rate (per case) | 0.0 | <= 0.2 |
| Em dash violations | 31 | 0 |
| Hallucinated quotes | 194 | 0 |
| Control case clean rate | 1.0 (3/3) | >= 0.67 |
| Hallucination rate | 0.067 | low |
| Policy violation rate | 0.133 | low |
| Partial answer rate | 0.0 | low |
| Gave up rate | 0.0 | 0 |

## Per-case results

| Case | Category | Verdict (expected) | Verdict (got) | Correct? | Em-dash | Hallucinated quotes | Judge issues caught |
|---|---|---|---|---|---|---|---|
| `prd-vague-targets-001` | skeptic | needs structural rework | do not send | no | 0 | 28 | 4/4 |
| `6pager-internal-contradiction-002` | skeptic | do not send | do not send | yes | 0 | 15 | 4/4 |
| `leadership-update-jargon-003` | audience | needs structural rework | needs structural rework | yes | 3 | 5 | 5/5 |
| `leadership-update-buried-lede-004` | audience | needs minor edits | needs minor edits | yes | 0 | 8 | 2/2 |
| `customer-email-missing-context-005` | audience | needs minor edits | needs structural rework | no | 6 | 16 | 3/3 |
| `strategy-doc-list-heavy-006` | strategist | needs structural rework | needs structural rework | yes | 0 | 5 | 4/4 |
| `roadmap-no-commitment-007` | strategist | needs structural rework | do not send | no | 0 | 21 | 4/4 |
| `prd-no-ask-008` | strategist | needs minor edits | needs structural rework | no | 0 | 20 | 2/2 |
| `mixed-failures-009` | multi-lens | needs structural rework | do not send | no | 0 | 23 | 4/4 |
| `regulatory-vague-claims-010` | skeptic | do not send | do not send | yes | 0 | 19 | 5/5 |
| `control-good-prd-011` | control | ready to send | needs minor edits | no | 4 | 11 | 0/0 |
| `control-good-leadership-update-012` | control | ready to send | needs minor edits | no | 5 | 6 | 0/0 |
| `control-good-customer-email-013` | control | ready to send | needs minor edits | no | 3 | 6 | 0/0 |
| `edge-em-dash-input-014` | edge | needs minor edits | ready to send | no | 4 | 6 | 1/1 |
| `edge-asks-for-rewrite-015` | edge | needs structural rework | needs structural rework | yes | 6 | 5 | 2/2 |

## Cost

- **SUT tokens**: 24848 in, 31745 out
- **Judge tokens**: 49049 in, 16373 out
- **Estimated cost**: $1.3106

## Validation against human scoring

Per [scoring-rubric.md](../../scoring-rubric.md), 3 cases should be hand-scored and compared against the judge.
Hand-score these cases and document the agreement rate here:

- `control-good-prd-011` (control case, expect zero issues)
- `prd-vague-targets-001` (skeptic-focused, 4 seeded issues)
- `roadmap-no-commitment-007` (strategist-focused, 4 seeded issues)

If agreement < 80%, mark judge scores as unvalidated and rely on automated metrics + hand-scored subset only.

## Files

- `outputs.jsonl`: raw model outputs
- `scores.jsonl`: per-case automated + judge scores
- `failures.md`: detailed look at the most interesting failure modes
- `summary.md`: this file
