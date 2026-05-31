# LLM Council — Reference Templates

Templates and full advisor descriptions for `SKILL.md`. Read this file when running the council workflow.

---

## Advisor full descriptions

### 1. The Contrarian
Actively looks for what's wrong, what's missing, what will fail. Assumes the idea has a fatal flaw and tries to find it. If everything looks solid, digs deeper. The Contrarian is not a pessimist. They're the friend who saves you from a bad deal by asking the questions you're avoiding.

### 2. The First Principles Thinker
Ignores the surface-level question and asks "what are we actually trying to solve here?" Strips away assumptions. Rebuilds the problem from the ground up. Sometimes the most valuable council output is the First Principles Thinker saying "you're asking the wrong question entirely."

### 3. The Expansionist
Looks for upside everyone else is missing. What could be bigger? What adjacent opportunity is hiding? What's being undervalued? The Expansionist doesn't care about risk (that's the Contrarian's job). They care about what happens if this works even better than expected.

### 4. The Outsider
Has zero context about the user, their field, or their history. Responds purely to what's in front of them. This is the most underrated advisor. Experts develop blind spots. The Outsider catches the curse of knowledge: things that are obvious to experts but confusing to everyone else.

### 5. The Executor
Only cares about one thing: can this actually be done, and what's the fastest path to doing it? Ignores theory, strategy, and big-picture thinking. The Executor looks at every idea through the lens of "OK but what do you do Monday morning?" If an idea sounds brilliant but has no clear first step, the Executor will say so.

---

## Advisor subagent prompt template (Stage 2)

Send one Task call per advisor with this prompt, filling in `[ADVISOR_NAME]`, `[ADVISOR_DESCRIPTION]`, and `[FRAMED_QUESTION]`:

```
You are [ADVISOR_NAME] on an LLM Council.

Your thinking style: [ADVISOR_DESCRIPTION]

A user has brought this question to the council:

[FRAMED_QUESTION]

Respond from your perspective. Be direct and specific. Don't hedge or try to be balanced. Lean fully into your assigned angle. The other advisors will cover the angles you're not covering.

Keep your response between 150 and 300 words. No preamble. Go straight into your analysis.

Return only your response text — no meta-commentary, no markdown headers naming yourself. The orchestrator will label your output.
```

---

## Reviewer subagent prompt template (Stage 3)

Send one Task call per reviewer with this prompt, filling in `[FRAMED_QUESTION]` and the five anonymized responses:

```
You are reviewing the outputs of an LLM Council. Five advisors independently answered this question:

[FRAMED_QUESTION]

Here are their anonymized responses:

Response A:
[RESPONSE_A]

Response B:
[RESPONSE_B]

Response C:
[RESPONSE_C]

Response D:
[RESPONSE_D]

Response E:
[RESPONSE_E]

Answer these three questions. Be specific. Reference responses by letter.

1. Which response is the strongest? Why?
2. Which response has the biggest blind spot? What is it missing?
3. What did ALL five responses miss that the council should consider?

Keep your review under 200 words total. Be direct. No preamble.
```

Spawn 5 reviewers in parallel — they each see all 5 anonymized responses, but they review independently. Their reviews don't need different "review styles." Five independent reviews of the same anonymized set surface different gaps because each reviewer notices different things.

---

## HTML report template (Stage 5)

Single self-contained HTML file. Replace placeholders. Keep advisor and review sections collapsed by default.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Council Verdict — [SHORT_QUESTION_TITLE]</title>
<style>
  :root {
    --bg: #fafaf9;
    --card: #ffffff;
    --ink: #1c1917;
    --muted: #57534e;
    --border: #e7e5e4;
    --accent: #0f172a;
    --agree: #166534;
    --clash: #b45309;
    --blindspot: #7c2d12;
    --recommend: #1e3a8a;
    --first-step: #064e3b;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 32px 16px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background: var(--bg); color: var(--ink); line-height: 1.55;
  }
  .container { max-width: 880px; margin: 0 auto; }
  header { margin-bottom: 32px; }
  header .label { font-size: 12px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted); }
  header h1 { font-size: 28px; margin: 8px 0 4px; line-height: 1.25; }
  header .meta { font-size: 13px; color: var(--muted); }
  .card {
    background: var(--card); border: 1px solid var(--border); border-radius: 10px;
    padding: 24px; margin-bottom: 16px;
  }
  .card h2 { margin-top: 0; font-size: 18px; }
  .verdict h2 { display: flex; align-items: center; gap: 8px; }
  .verdict h2::before {
    content: ""; width: 6px; height: 18px; border-radius: 3px; background: var(--accent);
  }
  .section-agree h2::before { background: var(--agree); }
  .section-clash h2::before { background: var(--clash); }
  .section-blindspot h2::before { background: var(--blindspot); }
  .section-recommend h2::before { background: var(--recommend); }
  .section-first-step h2::before { background: var(--first-step); }
  .section-agree h2, .section-clash h2, .section-blindspot h2,
  .section-recommend h2, .section-first-step h2 {
    display: flex; align-items: center; gap: 8px;
  }
  .grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 8px; margin-top: 12px;
  }
  .advisor-chip {
    border: 1px solid var(--border); border-radius: 8px;
    padding: 10px 12px; font-size: 13px;
  }
  .advisor-chip .role { font-weight: 600; font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }
  .advisor-chip .stance { margin-top: 4px; }
  details { background: var(--card); border: 1px solid var(--border); border-radius: 10px; margin-bottom: 8px; }
  details summary {
    cursor: pointer; padding: 14px 18px; font-weight: 600;
    list-style: none; display: flex; justify-content: space-between; align-items: center;
  }
  details summary::after { content: "▸"; color: var(--muted); transition: transform 0.15s; }
  details[open] summary::after { transform: rotate(90deg); }
  details > div { padding: 0 18px 18px; color: var(--ink); }
  details > div p:first-child { margin-top: 0; }
  footer { margin-top: 32px; font-size: 12px; color: var(--muted); text-align: center; }
  .question-block {
    background: #f5f5f4; border-left: 3px solid var(--accent);
    padding: 14px 18px; border-radius: 6px; font-size: 14px;
  }
  .question-block .label { font-weight: 600; font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }
  .recommendation { font-size: 16px; }
  .first-step { font-size: 18px; font-weight: 600; }
</style>
</head>
<body>
<div class="container">
  <header>
    <div class="label">Council Verdict</div>
    <h1>[SHORT_QUESTION_TITLE]</h1>
    <div class="meta">[ISO_TIMESTAMP] · 5 advisors · 5 peer reviews</div>
  </header>

  <div class="card">
    <div class="question-block">
      <div class="label">Question</div>
      <div>[ORIGINAL_QUESTION]</div>
    </div>
  </div>

  <div class="card section-recommend verdict">
    <h2>The Recommendation</h2>
    <p class="recommendation">[CHAIRMAN_RECOMMENDATION]</p>
  </div>

  <div class="card section-first-step">
    <h2>The One Thing to Do First</h2>
    <p class="first-step">[ONE_THING_TO_DO_FIRST]</p>
  </div>

  <div class="card section-agree">
    <h2>Where the Council Agrees</h2>
    [AGREEMENT_BULLETS_AS_HTML_LIST]
  </div>

  <div class="card section-clash">
    <h2>Where the Council Clashes</h2>
    [CLASH_BULLETS_AS_HTML_LIST]
  </div>

  <div class="card section-blindspot">
    <h2>Blind Spots the Council Caught</h2>
    [BLINDSPOT_BULLETS_AS_HTML_LIST]
  </div>

  <div class="card">
    <h2>Advisor Stances at a Glance</h2>
    <div class="grid">
      <div class="advisor-chip"><div class="role">Contrarian</div><div class="stance">[ONE_LINE_STANCE]</div></div>
      <div class="advisor-chip"><div class="role">First Principles</div><div class="stance">[ONE_LINE_STANCE]</div></div>
      <div class="advisor-chip"><div class="role">Expansionist</div><div class="stance">[ONE_LINE_STANCE]</div></div>
      <div class="advisor-chip"><div class="role">Outsider</div><div class="stance">[ONE_LINE_STANCE]</div></div>
      <div class="advisor-chip"><div class="role">Executor</div><div class="stance">[ONE_LINE_STANCE]</div></div>
    </div>
  </div>

  <h2 style="margin: 32px 0 12px; font-size: 16px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em;">Full Advisor Responses</h2>

  <details>
    <summary>The Contrarian</summary>
    <div>[CONTRARIAN_RESPONSE_AS_HTML]</div>
  </details>
  <details>
    <summary>The First Principles Thinker</summary>
    <div>[FIRST_PRINCIPLES_RESPONSE_AS_HTML]</div>
  </details>
  <details>
    <summary>The Expansionist</summary>
    <div>[EXPANSIONIST_RESPONSE_AS_HTML]</div>
  </details>
  <details>
    <summary>The Outsider</summary>
    <div>[OUTSIDER_RESPONSE_AS_HTML]</div>
  </details>
  <details>
    <summary>The Executor</summary>
    <div>[EXECUTOR_RESPONSE_AS_HTML]</div>
  </details>

  <h2 style="margin: 32px 0 12px; font-size: 16px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em;">Peer Review Highlights</h2>
  <details>
    <summary>All 5 peer reviews</summary>
    <div>
      <h3>Reviewer 1</h3>[REVIEW_1_AS_HTML]
      <h3>Reviewer 2</h3>[REVIEW_2_AS_HTML]
      <h3>Reviewer 3</h3>[REVIEW_3_AS_HTML]
      <h3>Reviewer 4</h3>[REVIEW_4_AS_HTML]
      <h3>Reviewer 5</h3>[REVIEW_5_AS_HTML]
    </div>
  </details>

  <footer>Generated [ISO_TIMESTAMP] · LLM Council skill · Adapted from Karpathy's LLM Council</footer>
</div>
</body>
</html>
```

**Notes for filling the template:**
- `[SHORT_QUESTION_TITLE]` — 4-8 word summary of the decision (e.g. "Workshop vs. Course Launch")
- `[ORIGINAL_QUESTION]` — user's exact words
- `[ISO_TIMESTAMP]` — `YYYY-MM-DD HH:MM` UTC
- `[ONE_LINE_STANCE]` — 8-15 word distillation of each advisor's position (e.g. "Wait — your audience doesn't recognize the product name yet")
- Convert markdown bullets in advisor responses to `<p>` and `<ul><li>` HTML. Escape any `<` or `>` in user content.

---

## Markdown transcript template (Stage 6)

```markdown
# Council Transcript — [SHORT_QUESTION_TITLE]

**Run at:** [ISO_TIMESTAMP_UTC]
**Workspace:** [PATH]

---

## Original question

[ORIGINAL_QUESTION_VERBATIM]

## Context gathered

- [FILE_OR_SOURCE_1]: [WHAT_IT_PROVIDED]
- [FILE_OR_SOURCE_2]: [WHAT_IT_PROVIDED]

## Framed question

[FRAMED_QUESTION]

---

## Advisor responses

### The Contrarian
[RESPONSE]

### The First Principles Thinker
[RESPONSE]

### The Expansionist
[RESPONSE]

### The Outsider
[RESPONSE]

### The Executor
[RESPONSE]

---

## Anonymization mapping (Stage 3)

| Letter | Advisor |
|--------|---------|
| Response A | [ADVISOR] |
| Response B | [ADVISOR] |
| Response C | [ADVISOR] |
| Response D | [ADVISOR] |
| Response E | [ADVISOR] |

## Peer reviews

### Reviewer 1
[REVIEW]

### Reviewer 2
[REVIEW]

### Reviewer 3
[REVIEW]

### Reviewer 4
[REVIEW]

### Reviewer 5
[REVIEW]

---

## Chairman synthesis

### Where the Council Agrees
[CONTENT]

### Where the Council Clashes
[CONTENT]

### Blind Spots the Council Caught
[CONTENT]

### The Recommendation
[CONTENT]

### The One Thing to Do First
[CONTENT]
```

---

## Operational notes

**Parallelism in Cursor.** The Task tool runs subagents in parallel only when you place all the calls in a *single message*. Split across messages = sequential. For both Stage 2 (advisors) and Stage 3 (reviewers), batch all 5 calls together.

**Subagent type.** Use `generalPurpose` for advisors and reviewers. Set `readonly: true` so they can't accidentally write files or call MCP tools — they should think and respond, nothing else.

**Token budget.** A full council run sends 5 advisor prompts + 5 reviewer prompts (each containing all 5 advisor responses) + chairman synthesis. The reviewer step is the heaviest. Keep advisor responses under 300 words to control reviewer context.

**Anonymization.** Use a fresh random A-E mapping every run. Don't always assign Contrarian → A. Even simple deterministic patterns become reviewer cues.

**Recovery.** If a Task subagent fails or returns garbage, retry just that one. Don't restart the whole council.
