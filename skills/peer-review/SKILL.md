---
name: peer-review
description: Adversarially review an important draft document (PRD, 6-pager, leadership update, PR description, customer email, regulatory response) through three distinct reviewer lenses, then produce a prioritized change list. Use when the user asks to "peer review", "stress test this doc", "adversarial review", "review my draft", or "what would a skeptic say".
---

# Peer Review Skill

Adversarially review a draft document. Three lenses, structured output, prioritized change list.

## When to use vs. llm-council

- **peer-review**: a document already exists, the question is "is this good enough to send?"
- **llm-council**: a decision is being considered, the question is "is this the right move?"

If the user has a doc, use peer-review. If they have a choice, use llm-council.

## Inputs

The user provides one of:
- A draft pasted in chat
- A file path to a markdown/text draft
- A page URL (fetch via Confluence/Notion MCP if available)
- A ticket description (fetch via Jira/Linear MCP if available)

Ask once if not provided. Also ask:
- **Audience**: who reads this? (e.g., your manager, leadership readout, customer, engineering team, regulatory reviewer)
- **Stakes**: what is the cost if this goes wrong? (e.g., promotion conversation, customer churn risk, regulatory rejection)

These two answers calibrate the harshness of the review.

## Review lenses (run all three)

### Lens 1: The Skeptic
- Hunt for unsubstantiated claims, vague targets, undefined success criteria.
- Flag every metric, customer name, or date that isn't cited or sourced.
- Identify logical contradictions internal to the doc.
- Ask "what is the strongest version of the opposing argument?" and check if the doc addresses it.

### Lens 2: The Audience
- Read it as the named audience would. What would they not understand?
- Where is jargon used without definition? Where does the doc assume context the reader doesn't have?
- What questions will the audience ask immediately upon reading? Are those answered in the doc?
- Is the most important point in the first paragraph, or buried?

### Lens 3: The Strategist
- Does this go beyond synthesizing inputs to actually shape direction?
- Where is taste / judgment missing? Where is the doc summarizing instead of recommending?
- Is the author owning the strategic conclusion, or punting it to the reader?
- Specific patterns to flag: list-heavy with no narrative, "we'll evaluate" without commitment, no clear ask, no clear next step.

## Output format

Render as an HTML canvas when running inside Cursor (where canvas rendering is supported and the visual layout helps the user scan multi-finding output). When called via API, a notebook, or any other text-only context, render as structured markdown using the same section order. Do not produce HTML markup that won't be rendered.

Sections:
1. **Verdict** (one sentence): ready to send / needs minor edits / needs structural rework / do not send.
2. **Top 3 specific changes** (prioritized P0/P1/P2 with line-quote evidence from the draft).
3. **By-lens findings** (collapsible per lens with all issues, not just top 3).
4. **What is working** (one section, brief): so the user doesn't over-edit the good parts. Keep this honest, not glazing.
5. **Suggested next step**: revise and re-run peer-review, or send as-is.

## Hard rules

- **Be ruthless, not nice.** Default mode: lead with the flaw, do not pad with validation.
- **Quote the draft when you flag something.** "This claim on line X" beats "there's a vague claim somewhere."
- **Do not rewrite the draft.** The user owns the voice. Suggest changes, do not produce a replacement draft unless explicitly asked.
- **No em dashes** in any output. Use commas, periods, parentheses, or short sentences instead. This rule applies to your own prose even when you are critiquing a draft that itself contains em dashes. You may quote the draft's em dashes inline as evidence, but never use one in your own commentary, headings, or bullet labels.
- **If the doc is genuinely good, say so briefly and stop.** Do not invent issues to fill the lens slots.
- **Calibrate harshness to stakes.** For a low-stakes Slack draft, top-line findings only. For a high-stakes formal document (legal, regulatory, board), line-by-line.

## Source

Inspired by Zevi Arnovitz's "peer review" technique (Lenny's Newsletter, January 2026) and adapted for single-model use. Run inline using adversarial role-play to simulate the three lenses.
