---
name: llm-council
description: Run any question, idea, or decision through a council of 5 AI advisors who independently analyze it, peer-review each other anonymously, and synthesize a final verdict. Adapted from Karpathy's LLM Council methodology, using Cursor subagents with different thinking lenses. MANDATORY TRIGGERS - always invoke on these phrases - "council this", "run the council", "war room this", "pressure-test this", "stress-test this", "debate this". STRONG TRIGGERS (invoke when combined with a real decision or tradeoff) - "should I X or Y", "which option", "what would you do", "is this the right move", "validate this", "get multiple perspectives", "I can't decide", "I'm torn between". Do NOT trigger on simple yes/no questions, factual lookups, or casual "should I" without meaningful tradeoff. DO trigger when the user presents a genuine decision with stakes, multiple options, and context that suggests they want it pressure-tested from multiple angles.
---

# LLM Council

You ask one AI a question, you get one answer. That answer might be great. It might be mid. You have no way to tell because you only saw one perspective.

The council fixes this. It runs the user's question through 5 independent advisor subagents, each thinking from a fundamentally different angle. Then they peer-review each other anonymously. Then a chairman (the main agent) synthesizes everything into a final recommendation.

Adapted from Andrej Karpathy's LLM Council. He dispatched queries to multiple models; this version uses Cursor subagents with different thinking lenses.

## When to invoke

**Good council questions** (genuine uncertainty, expensive to be wrong):
- "Should I launch a $97 workshop or a $497 course?"
- "Which of these 3 positioning angles is strongest?"
- "I'm thinking of pivoting from X to Y. Am I crazy?"
- "Here's my landing page copy. What's weak?"
- "Should I hire a VA or build an automation first?"

**Bad council questions** (skip and just answer):
- "What's the capital of France?" (one right answer)
- "Write me a tweet" (creation, not decision)
- "Summarize this article" (processing, not judgment)

If the user asks a council question but seems unwilling to change their mind, run it anyway. The council will tell them things they don't want to hear. That is the point.

## The 5 advisors

Each advisor is a different thinking style, not a job title. They create three natural tensions: Contrarian vs Expansionist (downside vs upside), First Principles vs Executor (rethink vs do), Outsider in the middle keeping everyone honest.

1. **The Contrarian** — actively looks for what's wrong, what will fail. Assumes a fatal flaw exists and tries to find it.
2. **The First Principles Thinker** — strips assumptions, asks "what are we actually trying to solve?" Sometimes says "you're asking the wrong question."
3. **The Expansionist** — looks for hidden upside, adjacent opportunities, what's being undervalued. Doesn't care about risk (that's the Contrarian's job).
4. **The Outsider** — has zero context about the user, field, or history. Catches the curse of knowledge.
5. **The Executor** — only cares about "can this be done, what's the fastest path?" Looks at every idea through "OK but what do you do Monday morning?"

Full advisor prompts are in [REFERENCE.md](REFERENCE.md).

## Workflow

Follow these stages in order. Track progress:

```
- [ ] Stage 1: Frame the question (with context enrichment)
- [ ] Stage 2: Convene the council (5 advisors in parallel)
- [ ] Stage 3: Anonymous peer review (5 reviewers in parallel)
- [ ] Stage 4: Chairman synthesis
- [ ] Stage 5: Generate HTML report
- [ ] Stage 6: Save markdown transcript
```

### Stage 1: Frame the question

Before framing, scan the workspace for context. Spend at most 30 seconds.

Look for and read (in priority order):
1. Files the user explicitly attached or referenced
2. `AGENTS.md` or `CLAUDE.md` in the workspace root or `~/`
3. Any `memory/` folder with audience profiles, voice docs, past decisions
4. Recent `council-transcript-*.md` files in the same directory (avoid re-counciling the same ground)
5. Topic-specific files (if pricing question → look for revenue data, past launches; if product question → recent PRDs, customer feedback)

Use Glob and quick Read calls. Stop after the 2-3 files that materially help.

Then reframe the user's raw question into a neutral prompt that includes:
1. The core decision or question
2. Key context from the user's message
3. Key context from workspace files (business stage, audience, constraints, past results, relevant numbers)
4. What's at stake (why this decision matters)

Don't add opinion. Don't steer. But DO ensure each advisor has enough context to give specific, grounded advice rather than generic takes.

If the question is too vague ("council this: my business"), ask exactly ONE clarifying question, then proceed.

Save the framed question for Stages 2-6.

### Stage 2: Convene the council

Spawn ALL 5 advisor subagents **in a single message with 5 parallel Task tool calls**. Sequential spawning wastes time and lets earlier responses bleed into later ones.

For each advisor:
- `subagent_type: "generalPurpose"`
- `readonly: true` (advisors think and respond, they don't modify state)
- `description`: short title like "Council: Contrarian"
- `prompt`: the advisor prompt template from [REFERENCE.md](REFERENCE.md), filled with the framed question

Each advisor produces 150-300 words. They do not see each other's responses.

### Stage 3: Anonymous peer review

Collect all 5 advisor responses. **Anonymize them as Response A through E with a randomized mapping** — do not keep advisors in their original 1-5 order. Save the mapping privately for Stage 4 and the transcript.

Spawn 5 reviewer subagents **in a single message with 5 parallel Task tool calls**. Each reviewer:
- `subagent_type: "generalPurpose"`
- `readonly: true`
- `prompt`: the reviewer template from [REFERENCE.md](REFERENCE.md), with all 5 anonymized responses

Each reviewer answers three questions in under 200 words:
1. Which response is the strongest? Why?
2. Which response has the biggest blind spot? What is it missing?
3. What did ALL five responses miss that the council should consider?

Question 3 is the most valuable output. Most council sessions surface the highest-leverage insight in the gaps between advisors.

### Stage 4: Chairman synthesis

The main agent (you) is the chairman. De-anonymize the responses and produce the verdict using this exact structure:

**Where the Council Agrees** — points multiple advisors converged on independently. High-confidence signals.

**Where the Council Clashes** — genuine disagreements. Don't smooth them over. Present both sides and explain why reasonable advisors disagree.

**Blind Spots the Council Caught** — things that only emerged through peer review. Things individual advisors missed that others flagged.

**The Recommendation** — a clear, direct recommendation. Not "it depends." Not "consider both sides." A real answer with reasoning. The chairman can disagree with the majority if the dissenter's reasoning is strongest — say so explicitly.

**The One Thing to Do First** — a single concrete next step. Not a list. One thing.

### Stage 5: Generate the HTML report

Generate a self-contained HTML file using the template in [REFERENCE.md](REFERENCE.md).

**File location** (in priority order):
1. If a workspace is open, save to the workspace root
2. Otherwise, save to `~/Documents/council-sessions/` (create if missing)

**Filename**: `council-report-YYYYMMDD-HHMMSS.html` (UTC timestamp, no spaces)

After writing, tell the user the path and how to open it.

### Stage 6: Save the full transcript

Write `council-transcript-YYYYMMDD-HHMMSS.md` (matching timestamp) to the same directory. Use the transcript template in [REFERENCE.md](REFERENCE.md). Include:
- Original question
- Framed question
- All 5 advisor responses (de-anonymized)
- All 5 peer reviews with the A-E mapping revealed
- Chairman's full synthesis

The transcript is the artifact. Future council runs on the same question can reference it to see how thinking evolved.

## Important rules

- **Always spawn all 5 advisors in parallel.** Single message, 5 Task calls. Same for peer review.
- **Always anonymize for peer review** with a random mapping. If reviewers know who said what, they defer to thinking styles instead of evaluating on merit.
- **The chairman can disagree with the majority.** Best reasoning wins, not most popular position.
- **Don't council trivial questions.** If there's one right answer, just answer it.
- **Don't soften.** Each advisor leans fully into their angle. The synthesis comes later.
- **The HTML report is what the user actually reads.** Make it scannable. Verdict at top, advisor details collapsed by default.

## Final output to chat

After Stages 5 and 6, briefly tell the user:
1. The chairman's recommendation (1-2 sentences)
2. The one thing to do first
3. Path to the HTML report and transcript

Keep the chat reply short — the artifacts hold the detail.
