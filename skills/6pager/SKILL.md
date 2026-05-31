---
name: 6pager
description: Run an interactive 6-pager drafting session, section by section. Asks targeted questions instead of generating a full draft, so the doc reflects what you actually think. Use when the user asks for "6-pager", "six pager", "draft a 6-pager for [topic]", or "start a 6-pager session for [initiative]".
---

# 6-Pager Skill

Run an interactive 6-pager drafting session. Never generate the whole doc in one shot. Work section-by-section with targeted questions, then synthesize what the user actually says.

The 6-pager format originated at Amazon as an alternative to slide decks for product reviews. Most teams that use it have adapted the structure. This skill works with either the standard structure or a custom team template.

## Setup (do once at start)

1. Ask the user:
   - **Initiative name** — what you're writing the doc about
   - **Doc type** — **major** initiative (needs Business Case + PR-FAQ sections) or **minor** (skip those)
   - **Template source** — using the standard structure below, or do you have a team template (URL, file path, or pasted structure)?
2. If using a custom template, fetch and confirm the section list with the user before starting. Do not assume the structure.
3. If using the standard structure, confirm the section list:
   - Elevator Pitch
   - Problem Alignment
   - Discovery Findings
   - High-level Approach
   - Business Case (major only)
   - Product Requirements / Acceptance Criteria
   - Objectives & Success Metrics
   - PR-FAQ (major only)
   - Launch Readiness (when needed)

## Workflow per section

For each section, in order:

1. **State the section name and purpose** in one sentence based on the template.
2. **Pull existing context** from workspace docs, recent transcripts, and linked tickets/pages. If there is prior relevant content, summarize it for the user before asking questions.
3. **Ask 2-4 targeted questions** to get the input you need. Examples:
   - Problem Alignment: "Who is hurting today, what does the pain look like in their workflow, and what data backs that up?"
   - Discovery Findings: "What's the top 1-2 customer quotes or data points that changed your thinking? Any contradicting signals?"
   - High-level Approach: "What's the smallest viable change that makes the problem visibly better? What's explicitly out of scope?"
   - Success Metrics: "How will you know this worked in 30 / 90 / 365 days? What signal is most leading?"
4. **Capture the user's answer verbatim**, then offer a tightened version in their voice. Do not invent customer names, metrics, or quotes.
5. **Confirm before moving on**: "Ready to move to [next section] or want to refine this more?"

## Hard rules

- **One section at a time.** Do not generate the whole doc. The whole point of this skill is question-by-question drafting, not bulk output.
- **Capability and outcome level only.** Do not prescribe specific cadences, tech stack names, data identifiers, or class/function names. Keep requirements at the user-visible / platform-visible level.
- **No em dashes** anywhere in drafted prose.
- **Cite sources** for every claim (ticket key, doc URL, customer call note, message permalink).
- **Mark gaps explicitly**: `[needs verification]` or `[guess]` for anything not sourced.

## End-of-session output

After all sections are walked, produce ONE consolidated draft. Ask the user where to save it. Common options:

1. **Confluence / Notion page draft** (if your team uses one): structured to paste into a new page under the team template.
2. **Markdown file in workspace**: save to `<workspace>/six-pagers/<initiative-name>-<YYYY-MM-DD>.md`.
3. **Google Doc** or whatever your team's standard doc tool is.

## Why this exists

Most "draft me a 6-pager" prompts return generic prose that doesn't reflect what the PM actually thinks. The PM then rewrites the whole doc anyway, which wastes time. This skill inverts the flow: the LLM is a research assistant and a structure-keeper, not a ghostwriter. The user does the thinking in small chunks. Result: a doc that sounds like the PM, not like ChatGPT, written faster because the PM isn't fighting hallucinations.
