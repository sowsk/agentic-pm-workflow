---
name: evals
description: Design and run an evaluation suite for a production AI feature. Use when the user says "design an eval", "set up evals for", "we need to evaluate this AI feature", "how do I test the LLM part of this", or wants to systematically measure whether an AI feature is doing what it's supposed to. Produces a test case set, a scoring rubric, an optional LLM-as-judge prompt, and a runnable evaluation plan grounded in real failure modes rather than synthetic edge cases.
---

# Evals Skill

For PMs shipping AI features. The eval is the PRD. The success criteria you'd write for a deterministic feature don't survive contact with a probabilistic model. This skill walks you through building the eval that catches what your shipping AI feature actually breaks on.

A worked example lives at [evals/peer-review/](../../evals/peer-review/) in this repo. Read it after this skill to see what the output actually looks like.

## When to use

- An AI feature is about to ship and the only measurement plan is "we'll watch for complaints"
- An AI feature is already in production and you don't know if it's getting better or worse over time
- The team is iterating on prompts and there's no way to know if a change improved or regressed behavior
- You're about to compare two models (or two prompts) and want data instead of vibes

## When not to use

- The feature is not actually using an LLM (no point in an LLM-eval framework)
- You're at the prototype demo stage and the goal is excitement, not measurement (yet)
- The feature is fully deterministic with traditional unit-test coverage already

## Source framing

This skill is grounded in three sources and one demonstrated application:

- An Instagram talk by a PM-side practitioner on the demo-vs-production gap, quantitative + categorical scoring, the "golden dataset," and the CI-like continuous loop (this is what motivated the methodology)
- Hamel Husain's [eval writing](https://hamel.dev/blog/posts/evals/) for the failure analysis pattern, the test case design, and the judge-validation-against-human discipline
- OpenAI's [evals cookbook](https://github.com/openai/evals) for the JSONL + runner + scoring pattern
- Andrej Karpathy's "evals are everything" framing: success criteria over step-by-step instructions, build the eval first

The worked example at [evals/peer-review/](../../evals/peer-review/) is a real eval suite applied to one of the skills in this repo, with run results.

## The PM angle that separates this from a generic eval explainer

The eval IS the PRD for an AI feature. Specifically:

- **Success criteria** become quantitative scores (verdict matches expected, hard-rule violations = 0, response within latency budget)
- **Failure modes that matter to your customer** become categorical scores (hallucination, policy violation, gave up, wrong tool called, partial answer)
- **Edge cases that came up in user research** become test cases
- **Hard product policies** become assertions in the automated layer
- **Subjective quality** is where LLM-as-judge comes in, but only after you've validated the judge against humans on a small sample

If you can't write the eval, you don't have a PRD; you have a demo wish.

## The 4-step process

### Step 1: Failure analysis first (read 20 real outputs)

Before designing a single test case, look at 20 real outputs from the feature. Read them. Categorize what's already breaking.

For each output, write:
- What the user asked
- What the AI produced
- What's wrong (if anything)
- Which category of wrong (hallucination, off-topic, wrong format, refused, partial, factually incorrect, etc.)

After 20, you'll see 3-5 failure categories repeat. Those become your eval's failure modes. The categories you invent in a conference room rarely match what users actually surface.

If you can't get 20 real outputs (pre-production), generate 20 production-realistic prompts and run them through the system manually. The point is to look at outputs before designing scoring.

This is the part most teams skip. It's also the highest leverage step.

### Step 2: Test cases mirror real use, not synthetic edge cases

Start with cases that look like real production traffic. Add edge cases only after you have the baseline coverage.

A balanced test set has:
- **~60% production-realistic**: drafts/inputs that look like what users actually send
- **~20% control cases**: inputs that should pass cleanly (this catches the model inventing problems to look smart)
- **~10% seeded failure cases**: inputs you deliberately broke to test specific failure detection
- **~10% edge cases**: testing the hard rules and policy boundaries

Each case is one JSONL line:

```json
{
  "id": "unique-id",
  "category": "what kind of case this is",
  "context": {"stakes": "high", "audience": "VP"},
  "input": "<the actual input>",
  "seeded_issues": [
    {"type": "...", "severity": "P0", "description": "...", "expected_substring": "..."}
  ],
  "expected_output_class": "<a categorical expectation>"
}
```

Aim for 15-30 cases for the first run. Below 10 is too few to see patterns. Above 50 is over-engineering before you've learned anything.

### Step 3: Scoring on two tracks (quant + categorical)

Every eval should score on two tracks: Quantitative and Categorical.

**Quantitative** (scriptable, no LLM needed):
- Hard rule assertions (no banned phrases, no banned characters, response within token budget)
- Structural assertions (required sections present, expected schema)
- Exact match on categorical labels (verdict was X, classifier output was Y)
- Counts (number of citations, number of false claims)

**Categorical** (subjective, LLM-as-judge or human):
- Hallucination (cited a fact that doesn't exist)
- Policy violation (rewrote when asked to critique, ignored stakes calibration)
- Partial answer (started but didn't finish)
- Gave up (refused or asked too many clarifying questions instead of proceeding)
- Wrong tool called (in agentic settings)

**Quantitative dimensions never need a judge.** Run them on every case, every run.

**Categorical dimensions need a judge**, OR human scoring, OR both. Default to human if the stakes are high. LLM-as-judge is the practical compromise for scale, but only after validation.

### Step 4: Validate the judge against humans (and wire into the dev loop)

LLM-as-judge is appealing because it's cheap and scales. It's also confidently wrong in ways that look right. Hamel's discipline: hand-score 3-5 cases per run and compare to the judge. If agreement is below ~80%, treat judge scores as unvalidated and fall back to humans for the unreliable dimensions.

Pick cases for hand-scoring deliberately:
- 1 control case
- 1 case with the most seeded issues (high-signal)
- 1 case where the model produced unexpected output (instructive)

Document the agreement rate in the run summary. Re-validate every time you change the judge model or the judge prompt.

**Wiring into the dev loop**: every change to the prompt re-runs the eval. The summary.md compares against the previous run. Drift detection. CI-like cadence.

In the worked example, this is what [evals/peer-review/score_outputs.py](../../evals/peer-review/score_outputs.py) does: produces a per-run summary.md you can diff against previous runs.

## What the eval will teach you (real findings from the worked example)

From the peer-review eval at [evals/peer-review/LESSONS.md](../../evals/peer-review/LESSONS.md):

- **Your ground-truth expectations will be wrong.** The model found 5-7 legitimate issues per case that the PM hadn't seeded. The model was right; the expected verdicts were too soft. Cost: re-calibrate the eval. Benefit: a more accurate skill.
- **Hard rules get violated more than you'd expect.** A "no em dashes" rule was violated in 40% of outputs. The PM hadn't noticed during months of manual use because she read for content, not policy.
- **The skill avoided inventing issues (0 false positives) but always found something on "good" controls.** Turned out the "good" controls had real gaps the PM missed during design. The eval forced a higher bar on ground truth itself.
- **LLM-as-judge agreed with hand scoring on 3 of 3 cases.** Judge validated. But also: hand-scoring takes ~15 min and saves you from trusting confidently-wrong automated output. Always do it.

These are typical patterns. Yours will be different but rhyme.

## Templates

### Failure analysis worksheet (Step 1)

```
Output 1 of 20
  User prompt:
  AI response (first 500 chars):
  What's wrong (if anything):
  Failure category:

[repeat 20 times]

Failure category counts:
  - hallucination: 
  - off-topic:
  - wrong format:
  - refused:
  - partial:
  - other:
```

After 20 outputs, the categorical counts are your eval's categorical dimensions.

### Test case JSONL schema (Step 2)

See [evals/peer-review/test-cases.jsonl](../../evals/peer-review/test-cases.jsonl) for the worked version. Adapt the fields to your domain.

### Scoring rubric template (Step 3)

See [evals/peer-review/scoring-rubric.md](../../evals/peer-review/scoring-rubric.md) for the worked version. Two tables: quantitative dimensions (one per row, formula), categorical dimensions (one per row, definition).

### Judge prompt template (Step 4)

See [evals/peer-review/judge-prompt.md](../../evals/peer-review/judge-prompt.md). Key components: system prompt with clear "what to score" + structured JSON output schema, user message template with inputs, and the SUT/judge pairing rules (judge model should differ from system-under-test to avoid same-model bias).

## Hard rules

- **Never write a SKILL.md for an eval you haven't run.** The eval methodology has to be informed by actually running it on something. If you find yourself drafting an eval skill from theory, stop and run a tiny one (5 cases) on a real feature first.
- **Validate the judge before trusting it.** No exceptions. Even for "easy" eval tasks.
- **Don't ship test cases with hand-coded answers that are wrong.** Spend time on ground truth. The eval is only as good as the answer key.
- **Track every run.** One directory per run, with the model name and timestamp. Never overwrite. Diffs over time are the actual signal.
- **Re-run after every prompt change.** Cheap to run, expensive to ship a regression.

## What to produce

When this skill is invoked, produce in order:

1. **A failure analysis output** (or a worksheet for the user to fill in if 20 real outputs aren't accessible yet)
2. **A draft test case set** (5-10 cases to start, structured per the template, written for the user's specific feature)
3. **A draft scoring rubric** (quant dimensions that can be checked without an LLM, categorical dimensions that need a judge)
4. **A judge prompt** (only if categorical dimensions exist; pair with a different model than SUT)
5. **A runnable plan** (what commands to run, what the artifacts look like, how to validate)

Do not produce all 5 in a single dump. Walk the user through one at a time. Each step has decisions; rushing past them produces the generic eval that doesn't catch what their feature actually breaks on.

## Source

Adapted from Hamel Husain's [eval writing](https://hamel.dev/blog/posts/evals/), OpenAI's [evals cookbook](https://github.com/openai/evals), Karpathy's "evals are everything" framing, and an Instagram talk that motivated the quantitative + categorical + CI-loop pattern. Demonstrated end-to-end in [evals/peer-review/](../../evals/peer-review/).
