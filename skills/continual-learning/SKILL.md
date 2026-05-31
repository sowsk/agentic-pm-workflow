---
name: continual-learning
description: Incrementally extract recurring user corrections and durable workspace facts from transcript changes. Routes global preferences to ~/.cursor/rules/global-preferences.mdc and workspace-specific facts to AGENTS.md. Use when the user asks to mine previous chats, maintain AGENTS.md memory, or build a self-learning preference loop.
---

# Continual Learning

Keep memory current using transcript deltas. Split output between global preferences and workspace facts.

## Inputs

- Transcript root: `~/.cursor/projects/<workspace-slug>/agent-transcripts/`
- Global preferences file: `~/.cursor/rules/global-preferences.mdc`
- Workspace memory file: `AGENTS.md` (in current workspace root)
- Incremental index: `.cursor/hooks/state/continual-learning-index.json`

## Workflow

1. Read existing `~/.cursor/rules/global-preferences.mdc` and workspace `AGENTS.md`.
2. Load incremental index if present.
3. Discover transcript files and process only:
   - new files not in index, or
   - files whose mtime is newer than indexed mtime.
4. Extract high-signal, reusable information and classify each item:
   - **Global preference** if it applies regardless of project (see Classification below)
   - **Workspace fact** if it is specific to the current project or context
5. Merge global preferences into `~/.cursor/rules/global-preferences.mdc`:
   - update matching bullets in place under existing sections
   - add net-new bullets under the correct section
   - deduplicate semantically similar bullets
6. Merge workspace facts into `AGENTS.md`:
   - update matching bullets in place
   - add only net-new bullets
   - deduplicate semantically similar bullets
7. Write back the incremental index.

## Classification: Global vs Workspace

**Route to `~/.cursor/rules/global-preferences.mdc`** when the item is about:
- Communication style (tone, formatting, what to avoid in writing)
- Response format expectations (one draft not multiple, direct answers, etc.)
- Tool usage preferences (which tools to prefer, when to use Shell vs Read/Grep)
- Who the user is, their role, and what tools/MCPs they have access to
- Workflow habits that apply to any project (how to structure emails, PR reviews, etc.)

**Route to workspace `AGENTS.md`** when the item is about:
- Project timelines, launch dates, milestones
- Specific stakeholders on a project
- Technical specifics of a feature being built
- Customer counts, segment data, file paths tied to this project
- Jira/Confluence/GitHub IDs relevant to this project

**Rule of thumb**: Ask "Would this preference make sense in a completely different project?" If yes → global. If only meaningful in this project's context → workspace.

## Output Contracts

### `~/.cursor/rules/global-preferences.mdc`
Keep these sections, adding to them as needed:
- `## User Preferences` — communication style, response format, workflow habits
- `## Tool Usage Preferences` — which tools to use and when
- `## User Context` — who the user is, role, available tools/MCPs

Do not add project-specific facts here.

### Workspace `AGENTS.md`
Keep only these sections:
- `## Learned User Preferences` — only preferences not already captured globally
- `## Learned Workspace Facts` — project-specific facts

## Inclusion Bar

Keep an item only if all are true:
- actionable in future sessions
- stable across sessions
- repeated in multiple transcripts, or explicitly stated as a broad rule
- non-sensitive

## Exclusions

Never store:
- secrets, tokens, credentials, private personal data
- one-off task instructions
- transient details (branch names, commit hashes, temporary errors)

## Incremental Index Format

```json
{
  "version": 1,
  "transcripts": {
    "/abs/path/to/file.jsonl": {
      "mtimeMs": 1730000000000,
      "lastProcessedAt": "2026-02-18T12:00:00.000Z"
    }
  }
}
```
