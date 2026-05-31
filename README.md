# agentic-pm-workflow

Cursor skills I use as a senior PM at [ThousandEyes](https://www.thousandeyes.com) (part of Cisco) to turn Cursor into a real PM workspace.

Five skills. Each one solves a workflow I was previously doing by hand or with shallow chatbot prompts. They live alongside the agent and trigger automatically based on what I'm asking, so I'm not re-prompting the same setup every session.

## What's inside

| Skill | What it does | When to use |
|---|---|---|
| [llm-council](skills/llm-council/) | Runs a decision through 5 AI advisors with different thinking lenses, peer-reviews them anonymously, then synthesizes a verdict | When you're torn between options and want it pressure-tested |
| [peer-review](skills/peer-review/) | Adversarial review of a draft document through 3 reviewer lenses (skeptic, audience, strategist) with prioritized findings | Before sending an important doc (PRD, leadership update, customer email, regulatory response) |
| [pm-presentation](skills/pm-presentation/) | Builds or critiques slide decks using 7 PM-specific narrative templates (roadmap, exec update, QBR, strategy, pitch, PRD readout, customer demo) | Building a deck or asking "make my deck better" |
| [6pager](skills/6pager/) | Walks you through a 6-pager interactively, section by section, asking targeted questions instead of dumping a draft | When you need to write a 6-pager and don't want a wall of generic AI prose |
| [continual-learning](skills/continual-learning/) | Mines your transcript history for recurring preferences and project facts, routes them to global rules vs. workspace-specific memory | When your AI doesn't remember things you've already told it five times |

## Install

Cursor loads skills from `~/.cursor/skills/`. To install all of them:

```bash
git clone https://github.com/sowsk/agentic-pm-workflow.git
cp -r agentic-pm-workflow/skills/* ~/.cursor/skills/
```

Or pick the ones you want:

```bash
cp -r agentic-pm-workflow/skills/llm-council ~/.cursor/skills/
```

Restart Cursor (or open a new chat). The skills will surface automatically when their trigger conditions are met. You can also invoke them explicitly, e.g., "council this" or "peer review my draft."

## How Cursor skills work

A Cursor skill is a markdown file with YAML frontmatter. The `description` field tells the agent when to invoke the skill. Once installed, the agent reads the description and decides whether the current request matches. If yes, it loads the full `SKILL.md` and follows the instructions inside.

The advantage over a system prompt: skills only load when relevant, so they don't bloat every conversation. The advantage over re-prompting: the methodology stays consistent across sessions.

## Attribution

A few of these build on prior work:

- **llm-council** adapts Andrej Karpathy's [LLM Council](https://github.com/karpathy/llm-council) idea. Karpathy dispatched queries to multiple models; this version uses Cursor subagents with different thinking lenses, plus anonymized peer review and a chairman synthesis stage.
- **peer-review** is inspired by Zevi Arnovitz's "peer review" technique (Lenny's Newsletter, January 2026), adapted for single-model use with three named lenses.
- **6pager** uses Amazon's 6-pager document structure. The contribution here is the interactive workflow (section-by-section question prompts instead of bulk drafts) and the rule against generating prose before the user has actually thought through each section.

The other two (`pm-presentation`, `continual-learning`) are original.

## License

MIT. Use them, fork them, improve them. If you build something better, send it over.

## About

I'm a senior PM at [ThousandEyes](https://www.thousandeyes.com) (part of Cisco) where I own the alerts, integrations, and visualization platforms and the AI / agentic strategy across them. These skills came out of trying to make Cursor behave like a real PM workspace, not a generic chatbot.

If you're building PM tooling on top of Cursor, or thinking about AI for IT and operations, I'd be interested to compare notes.

[LinkedIn](https://www.linkedin.com/in/sowmya-krishnamoorthy)
