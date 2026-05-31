# Peer-review eval

This directory contains a reproducible eval suite for the [`peer-review` skill](../../skills/peer-review/SKILL.md).

The point isn't to score `peer-review` once. The point is to demonstrate the workflow: when you ship an AI tool, you build an eval for it. The skill is the artifact. The eval is the discipline.

## What's here

| File | What it is |
|---|---|
| [`test-cases.jsonl`](test-cases.jsonl) | 15 test cases: 10 with seeded failure modes (by lens), 3 controls that should pass clean, 2 edge cases for the skill's hard rules. |
| [`scoring-rubric.md`](scoring-rubric.md) | Quantitative + categorical dimensions. The quant track maps to scriptable checks; the categorical track maps to LLM-as-judge. |
| [`judge-prompt.md`](judge-prompt.md) | System prompt for the judge model, plus the SUT/judge pairing rules to avoid same-model bias. |
| [`run_eval.py`](run_eval.py) | Runs the SUT model against every test case. Saves raw outputs to `runs/<timestamp>_<model>/outputs.jsonl`. |
| [`score_outputs.py`](score_outputs.py) | Runs automated scoring (verdict extraction, em-dash count, quote verification) + LLM-as-judge subjective scoring. Writes scores, summary, failures. |
| [`requirements.txt`](requirements.txt) | Pinned: `anthropic==0.42.0`, `python-dotenv==1.0.1`. |
| [`LESSONS.md`](LESSONS.md) | What the runs revealed about `peer-review`. The PM artifact. |
| `runs/<timestamp>_<model>/` | One directory per run. Contains `outputs.jsonl`, `scores.jsonl`, `summary.md`, `failures.md`. |

## How to run

```bash
# from the repo root
python3 -m venv .venv
source .venv/bin/activate
pip install -r evals/peer-review/requirements.txt

export ANTHROPIC_API_KEY=sk-ant-...

# 1. run the eval
python evals/peer-review/run_eval.py

# 2. score the outputs (judge invocation included)
python evals/peer-review/score_outputs.py --run-dir evals/peer-review/runs/<timestamp>_<model>

# automated-only (skip the LLM judge):
python evals/peer-review/score_outputs.py --run-dir <dir> --skip-judge
```

A full run takes ~5 minutes and costs roughly $1-2 against Opus 4.8 + Sonnet 4.6 judge.

## Reading a run

Open the run's `summary.md` first. It contains the headline metrics (verdict accuracy, catch rate, em-dash violations, judge agreement). Then open `failures.md` for the 5 most informative failures with quoted output excerpts.

`scores.jsonl` is the raw scoring data, one JSON object per case, for any deeper analysis.

## Validation

LLM-as-judge is not trusted by default. For each run, hand-score the three cases listed in `summary.md` and compute agreement against the judge. If agreement falls below 80%, the judge scores are reported as unvalidated and the run relies on automated + hand-scored metrics only.

This follows the validation pattern from Hamel Husain's eval methodology.

## Adding test cases

Each test case is a JSON object on a single line in `test-cases.jsonl`:

```json
{
  "id": "unique-id",
  "category": "skeptic" | "audience" | "strategist" | "multi-lens" | "control" | "edge",
  "document_type": "PRD",
  "stakes": "low" | "medium" | "high" | "critical",
  "audience": "<who reads this>",
  "input": "<the full draft text>",
  "seeded_issues": [
    {
      "lens": "Skeptic" | "Audience" | "Strategist",
      "severity": "P0" | "P1" | "P2",
      "description": "<what the issue is>",
      "expected_quote_substring": "<a substring from the input that the skill should quote>"
    }
  ],
  "expected_verdict": "ready to send" | "needs minor edits" | "needs structural rework" | "do not send",
  "rule_check": "<optional: name of a hard-rule check this case targets>"
}
```

When adding cases, keep the distribution balanced: don't pile up control cases (the eval will look better than it is) or pile up critical-stakes cases (the eval will look harsher than it is).

## When to re-run

- After editing `skills/peer-review/SKILL.md`. Compare new run's `summary.md` against the previous one.
- When swapping models. Each model gets its own run directory; the SUT model is in the directory name.
- Before publishing a public update to the skill.

## What this doesn't cover

This eval tests the **skill prompt** as a standalone system prompt against the Anthropic API. It does not test:

- Cursor's skill activation logic (whether the description triggers correctly on user phrasing)
- The HTML canvas rendering specified in the skill output format (the runner captures the text, not the rendered canvas)
- Multi-turn behavior (peer-review is a single-shot transform, so this is by design)

Those would need different test harnesses. They're listed in `LESSONS.md` as future work.
