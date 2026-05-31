"""Score peer-review outputs from a run directory.

Reads outputs.jsonl produced by run_eval.py, runs automated quantitative
checks, invokes an LLM-as-judge for categorical and per-issue scoring, and
writes scores.jsonl + summary.md + failures.md to the same run directory.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python score_outputs.py --run-dir runs/2026-05-31_120000_claude-opus-4-8
    python score_outputs.py --run-dir <dir> --judge-model claude-sonnet-4-6
    python score_outputs.py --run-dir <dir> --skip-judge   # automated only
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

try:
    from anthropic import Anthropic
except ImportError:
    print("anthropic package not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import os


def _build_http_client():
    """See run_eval.py for the truststore rationale."""
    import httpx
    try:
        import ssl
        import truststore
        ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        return httpx.Client(verify=ctx, timeout=httpx.Timeout(120.0))
    except ImportError:
        return httpx.Client(timeout=httpx.Timeout(120.0))


HERE = Path(__file__).parent
TEST_CASES_PATH = HERE / "test-cases.jsonl"
JUDGE_PROMPT_PATH = HERE / "judge-prompt.md"

DEFAULT_JUDGE_MODEL = "claude-sonnet-4-6"
JUDGE_MAX_TOKENS = 4096

VALID_VERDICTS = [
    "ready to send",
    "needs minor edits",
    "needs structural rework",
    "do not send",
]

REQUIRED_SECTIONS = [
    ("verdict", [r"verdict\b", r"^\s*1\.\s*verdict"]),
    ("top_3", [r"top\s*3", r"top three", r"prioritized", r"\bP0\b"]),
    ("by_lens", [r"by[\s-]?lens", r"skeptic", r"audience", r"strategist"]),
    ("whats_working", [r"what'?s working", r"what is working", r"working well"]),
    ("next_step", [r"next step", r"suggested next", r"recommendation"]),
]

EM_DASH_CHARS = ["\u2014", "\u2015"]  # em dash, horizontal bar


def load_jsonl(path: Path) -> list[dict]:
    with path.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def find_verdict(output: str) -> str | None:
    """Find the first matching valid verdict in the output, case-insensitive."""
    lower = output.lower()
    matches = [(v, lower.find(v)) for v in VALID_VERDICTS if v in lower]
    matches = [m for m in matches if m[1] != -1]
    if not matches:
        return None
    matches.sort(key=lambda m: m[1])
    return matches[0][0]


def extract_quoted_strings(output: str) -> list[str]:
    """Find substrings the model marked as quotes.

    Catches: "text", 'text', `text`, and >text on its own line (markdown blockquotes).
    Filters quotes shorter than 4 characters (likely punctuation noise) and longer
    than 200 chars (likely an embedded code block, not a quote).
    """
    quotes: list[str] = []
    for pattern in [r'"([^"\n]{4,200})"', r'`([^`\n]{4,200})`']:
        quotes.extend(re.findall(pattern, output))
    for line in output.splitlines():
        if line.lstrip().startswith(">"):
            stripped = line.lstrip("> \t").strip()
            if 4 <= len(stripped) <= 200:
                quotes.append(stripped)
    return quotes


def quote_appears_in_input(quote: str, input_draft: str) -> bool:
    """Check if a quoted string appears verbatim in the input."""
    normalized_input = re.sub(r"\s+", " ", input_draft).lower()
    normalized_quote = re.sub(r"\s+", " ", quote).lower()
    return normalized_quote in normalized_input


def check_sections_present(output: str) -> dict[str, bool]:
    present = {}
    lower = output.lower()
    for section_name, patterns in REQUIRED_SECTIONS:
        present[section_name] = any(re.search(p, lower, re.MULTILINE) for p in patterns)
    return present


def automated_scores(case: dict, run_result: dict) -> dict:
    """All quantitative dimensions that can be checked without an LLM."""
    output = run_result.get("output") or ""
    input_draft = case["input"]

    verdict = find_verdict(output)
    verdict_correct = (verdict == case.get("expected_verdict"))

    em_dash_count = sum(output.count(c) for c in EM_DASH_CHARS)

    quotes = extract_quoted_strings(output)
    quotes_from_input = sum(1 for q in quotes if quote_appears_in_input(q, input_draft))
    quotes_not_in_input = len(quotes) - quotes_from_input

    sections = check_sections_present(output)
    sections_present_count = sum(1 for v in sections.values() if v)

    return {
        "verdict_extracted": verdict,
        "verdict_present": verdict is not None,
        "verdict_correct": verdict_correct,
        "expected_verdict": case.get("expected_verdict"),
        "em_dash_count": em_dash_count,
        "em_dash_violation": em_dash_count > 0,
        "quotes_total": len(quotes),
        "quotes_from_input": quotes_from_input,
        "quotes_not_in_input": quotes_not_in_input,
        "hallucinated_quote_violation": quotes_not_in_input > 0,
        "sections_present": sections,
        "sections_present_count": sections_present_count,
        "findings_present": sections["top_3"] or sections["by_lens"],
        "output_word_count": len(output.split()),
        "output_char_count": len(output),
    }


def load_judge_system_prompt() -> str:
    """Extract the system prompt block from judge-prompt.md.

    The doc contains the prompt inside a ``` fenced code block under "## System prompt".
    """
    text = JUDGE_PROMPT_PATH.read_text()
    match = re.search(r"## System prompt\s*\n\s*```\n(.+?)\n```", text, re.DOTALL)
    if not match:
        raise RuntimeError("Could not extract judge system prompt from judge-prompt.md")
    return match.group(1).strip()


def build_judge_user_message(case: dict, run_result: dict) -> str:
    output = run_result.get("output") or "(no output produced)"
    seeded = json.dumps(case.get("seeded_issues", []), indent=2)
    return (
        f"INPUT_DRAFT:\n{case['input']}\n\n"
        f"SEEDED_ISSUES:\n{seeded}\n\n"
        f"SKILL_OUTPUT:\n{output}\n\n"
        f"Score per the system prompt instructions. Return only JSON."
    )


def run_judge(client: Anthropic, judge_model: str, judge_system: str,
              case: dict, run_result: dict) -> dict:
    user_msg = build_judge_user_message(case, run_result)
    try:
        resp = client.messages.create(
            model=judge_model,
            max_tokens=JUDGE_MAX_TOKENS,
            system=judge_system,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw_text = "\n".join(
            b.text for b in resp.content if getattr(b, "type", None) == "text"
        )
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\n", "", cleaned)
            cleaned = re.sub(r"\n```$", "", cleaned)
        parsed = json.loads(cleaned)
        return {
            "judge_model": judge_model,
            "judge_scores": parsed,
            "judge_input_tokens": resp.usage.input_tokens,
            "judge_output_tokens": resp.usage.output_tokens,
            "judge_error": None,
        }
    except json.JSONDecodeError as exc:
        return {
            "judge_model": judge_model,
            "judge_scores": None,
            "judge_raw_output": raw_text if 'raw_text' in dir() else None,
            "judge_error": f"JSONDecodeError: {exc}",
        }
    except Exception as exc:
        return {
            "judge_model": judge_model,
            "judge_scores": None,
            "judge_error": f"{type(exc).__name__}: {exc}",
        }


def aggregate(scores: list[dict]) -> dict:
    """Compute aggregate metrics across all scored cases."""
    n = len(scores)
    if n == 0:
        return {}

    verdict_correct = sum(1 for s in scores if s["automated"]["verdict_correct"])
    verdict_present = sum(1 for s in scores if s["automated"]["verdict_present"])
    em_dash_total = sum(s["automated"]["em_dash_count"] for s in scores)
    hallucinated_quote_total = sum(s["automated"]["quotes_not_in_input"] for s in scores)

    total_seeded_issues = 0
    caught_correct_lens = 0
    caught_wrong_lens = 0
    false_positives = 0
    hallucinations = 0
    policy_violations = 0
    partial_answers = 0
    gave_ups = 0

    for s in scores:
        judge = s.get("judge", {}).get("judge_scores")
        case_id = s["case_id"]
        seeded_count = s.get("seeded_issue_count", 0)
        total_seeded_issues += seeded_count
        if not judge:
            continue
        for issue in judge.get("per_issue_scores", []):
            if issue.get("catch_status") == "caught_correct_lens":
                caught_correct_lens += 1
            elif issue.get("catch_status") == "caught_wrong_lens":
                caught_wrong_lens += 1
        false_positives += len(judge.get("false_positives", []))
        cat = judge.get("categorical", {})
        if cat.get("hallucination", {}).get("value"):
            hallucinations += 1
        if cat.get("policy_violation", {}).get("value"):
            policy_violations += 1
        if cat.get("partial_answer", {}).get("value"):
            partial_answers += 1
        if cat.get("gave_up", {}).get("value"):
            gave_ups += 1

    control_clean = 0
    control_total = 0
    for s in scores:
        if s.get("category") == "control":
            control_total += 1
            judge = s.get("judge", {}).get("judge_scores")
            verdict_ok = s["automated"]["verdict_extracted"] in ("ready to send", "needs minor edits")
            fp_count = len(judge.get("false_positives", [])) if judge else 0
            if verdict_ok and fp_count == 0:
                control_clean += 1

    return {
        "total_cases": n,
        "verdict_accuracy": round(verdict_correct / n, 3),
        "verdict_presence_rate": round(verdict_present / n, 3),
        "total_seeded_issues": total_seeded_issues,
        "catch_rate": round((caught_correct_lens + caught_wrong_lens) / total_seeded_issues, 3) if total_seeded_issues else None,
        "correct_lens_catch_rate": round(caught_correct_lens / total_seeded_issues, 3) if total_seeded_issues else None,
        "wrong_lens_catch_rate": round(caught_wrong_lens / total_seeded_issues, 3) if total_seeded_issues else None,
        "false_positive_count": false_positives,
        "false_positive_rate_per_case": round(false_positives / n, 3),
        "em_dash_violation_total": em_dash_total,
        "hallucinated_quote_total": hallucinated_quote_total,
        "hallucination_rate": round(hallucinations / n, 3),
        "policy_violation_rate": round(policy_violations / n, 3),
        "partial_answer_rate": round(partial_answers / n, 3),
        "gave_up_rate": round(gave_ups / n, 3),
        "control_clean_rate": round(control_clean / control_total, 3) if control_total else None,
        "control_clean_count": f"{control_clean}/{control_total}",
    }


def write_summary(out_dir: Path, run_meta: dict, aggregate_metrics: dict, scores: list[dict]) -> None:
    lines = [
        f"# Run summary",
        "",
        f"- **Date**: {run_meta['date']}",
        f"- **System-under-test**: `{run_meta['sut_model']}`",
        f"- **Judge**: `{run_meta['judge_model']}`" if run_meta.get('judge_model') else "- **Judge**: skipped",
        f"- **Cases run**: {aggregate_metrics.get('total_cases', 0)}",
        "",
        "## Headline metrics",
        "",
        "| Metric | Value | Target |",
        "|---|---|---|",
        f"| Verdict accuracy | {aggregate_metrics.get('verdict_accuracy', 'n/a')} | >= 0.80 |",
        f"| Catch rate | {aggregate_metrics.get('catch_rate', 'n/a')} | >= 0.75 |",
        f"| Correct-lens catch rate | {aggregate_metrics.get('correct_lens_catch_rate', 'n/a')} | >= 0.60 |",
        f"| False positive rate (per case) | {aggregate_metrics.get('false_positive_rate_per_case', 'n/a')} | <= 0.2 |",
        f"| Em dash violations | {aggregate_metrics.get('em_dash_violation_total', 'n/a')} | 0 |",
        f"| Hallucinated quotes | {aggregate_metrics.get('hallucinated_quote_total', 'n/a')} | 0 |",
        f"| Control case clean rate | {aggregate_metrics.get('control_clean_rate', 'n/a')} ({aggregate_metrics.get('control_clean_count', 'n/a')}) | >= 0.67 |",
        f"| Hallucination rate | {aggregate_metrics.get('hallucination_rate', 'n/a')} | low |",
        f"| Policy violation rate | {aggregate_metrics.get('policy_violation_rate', 'n/a')} | low |",
        f"| Partial answer rate | {aggregate_metrics.get('partial_answer_rate', 'n/a')} | low |",
        f"| Gave up rate | {aggregate_metrics.get('gave_up_rate', 'n/a')} | 0 |",
        "",
        "## Per-case results",
        "",
        "| Case | Category | Verdict (expected) | Verdict (got) | Correct? | Em-dash | Hallucinated quotes | Judge issues caught |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for s in scores:
        a = s["automated"]
        judge = s.get("judge", {}).get("judge_scores")
        if judge:
            caught = sum(1 for i in judge.get("per_issue_scores", []) if i.get("catch_status") != "missed")
            total = len(judge.get("per_issue_scores", []))
            judge_summary = f"{caught}/{total}"
        else:
            judge_summary = "n/a"
        lines.append(
            f"| `{s['case_id']}` | {s.get('category', 'n/a')} | {a['expected_verdict']} | "
            f"{a['verdict_extracted'] or '(none)'} | "
            f"{'yes' if a['verdict_correct'] else 'no'} | "
            f"{a['em_dash_count']} | {a['quotes_not_in_input']} | {judge_summary} |"
        )

    lines.extend([
        "",
        "## Cost",
        "",
        f"- **SUT tokens**: {run_meta.get('sut_input_tokens', 0)} in, {run_meta.get('sut_output_tokens', 0)} out",
        f"- **Judge tokens**: {run_meta.get('judge_input_tokens', 0)} in, {run_meta.get('judge_output_tokens', 0)} out",
        f"- **Estimated cost**: ${run_meta.get('total_cost_usd', 0):.4f}",
        "",
        "## Validation against human scoring",
        "",
        "Per [scoring-rubric.md](../../scoring-rubric.md), 3 cases should be hand-scored and compared against the judge.",
        "Hand-score these cases and document the agreement rate here:",
        "",
        "- `control-good-prd-011` (control case, expect zero issues)",
        "- `prd-vague-targets-001` (skeptic-focused, 4 seeded issues)",
        "- `roadmap-no-commitment-007` (strategist-focused, 4 seeded issues)",
        "",
        "If agreement < 80%, mark judge scores as unvalidated and rely on automated metrics + hand-scored subset only.",
        "",
        "## Files",
        "",
        "- `outputs.jsonl`: raw model outputs",
        "- `scores.jsonl`: per-case automated + judge scores",
        "- `failures.md`: detailed look at the most interesting failure modes",
        "- `summary.md`: this file",
    ])

    (out_dir / "summary.md").write_text("\n".join(lines) + "\n")


def write_failures(out_dir: Path, scores: list[dict], cases_by_id: dict, outputs_by_id: dict) -> None:
    """Pick the most informative failures and write a deep-dive doc."""
    interesting = []
    for s in scores:
        a = s["automated"]
        judge = s.get("judge", {}).get("judge_scores")
        score_for_interest = 0
        notes = []
        if not a["verdict_correct"]:
            score_for_interest += 2
            notes.append(f"verdict wrong: expected '{a['expected_verdict']}', got '{a['verdict_extracted']}'")
        if a["em_dash_count"] > 0:
            score_for_interest += 3
            notes.append(f"em-dash violation: {a['em_dash_count']} em dashes in output")
        if a["quotes_not_in_input"] > 0:
            score_for_interest += 3
            notes.append(f"hallucinated quotes: {a['quotes_not_in_input']}")
        if judge:
            fps = len(judge.get("false_positives", []))
            missed = sum(1 for i in judge.get("per_issue_scores", []) if i.get("catch_status") == "missed")
            if fps > 0:
                score_for_interest += fps
                notes.append(f"{fps} false positive(s)")
            if missed > 0:
                score_for_interest += missed
                notes.append(f"{missed} missed seeded issue(s)")
            if judge.get("categorical", {}).get("hallucination", {}).get("value"):
                score_for_interest += 3
                notes.append("judge flagged hallucination")
            if judge.get("categorical", {}).get("policy_violation", {}).get("value"):
                score_for_interest += 3
                notes.append("judge flagged policy violation")
        if score_for_interest > 0:
            interesting.append((score_for_interest, s, notes))

    interesting.sort(key=lambda t: -t[0])
    top = interesting[:5]

    lines = [
        "# Failures: top 5 most informative cases from this run",
        "",
        "Surfaced by combining quantitative violations (verdict wrong, em dashes, hallucinated quotes) and judge findings (false positives, missed issues, hallucination/policy flags).",
        "",
    ]
    if not top:
        lines.append("No failures of note. Either the skill is solid or the eval is undercalibrated.")
    for score, s, notes in top:
        case = cases_by_id[s["case_id"]]
        output = outputs_by_id.get(s["case_id"], "(missing)")
        lines.extend([
            f"## {s['case_id']}",
            "",
            f"**Why it surfaced**: {'; '.join(notes)}",
            "",
            f"**Category**: {case.get('category')} | **Stakes**: {case.get('stakes')} | **Audience**: {case.get('audience')}",
            "",
            f"**Expected verdict**: {case.get('expected_verdict')}  ",
            f"**Got verdict**: {s['automated']['verdict_extracted']}",
            "",
            "**Output excerpt** (first 1500 chars):",
            "",
            "```",
            output[:1500] + ("..." if len(output) > 1500 else ""),
            "```",
            "",
            "---",
            "",
        ])

    (out_dir / "failures.md").write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Score peer-review eval outputs.")
    parser.add_argument("--run-dir", required=True, help="Directory containing outputs.jsonl")
    parser.add_argument("--judge-model", default=DEFAULT_JUDGE_MODEL)
    parser.add_argument("--skip-judge", action="store_true", help="Skip LLM-as-judge, automated scoring only")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    outputs_path = run_dir / "outputs.jsonl"
    if not outputs_path.exists():
        print(f"Outputs file not found: {outputs_path}")
        return 2

    cases = load_jsonl(TEST_CASES_PATH)
    cases_by_id = {c["id"]: c for c in cases}
    outputs = load_jsonl(outputs_path)
    outputs_by_id = {o["case_id"]: (o.get("output") or "") for o in outputs}

    judge_client = None
    judge_system = None
    if not args.skip_judge:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("ANTHROPIC_API_KEY not set. Use --skip-judge for automated-only scoring.")
            return 2
        judge_client = Anthropic(api_key=api_key, http_client=_build_http_client())
        judge_system = load_judge_system_prompt()

    scores = []
    sut_input_tokens = sum(o.get("input_tokens", 0) for o in outputs)
    sut_output_tokens = sum(o.get("output_tokens", 0) for o in outputs)
    judge_input_tokens = 0
    judge_output_tokens = 0

    print(f"Scoring {len(outputs)} cases from {run_dir}")
    for i, run_result in enumerate(outputs, 1):
        case_id = run_result["case_id"]
        case = cases_by_id.get(case_id)
        if not case:
            print(f"  [{i}/{len(outputs)}] {case_id} — no matching test case, skipping")
            continue
        auto = automated_scores(case, run_result)
        entry = {
            "case_id": case_id,
            "category": case.get("category"),
            "seeded_issue_count": len(case.get("seeded_issues", [])),
            "automated": auto,
        }
        if judge_client:
            print(f"  [{i}/{len(outputs)}] {case_id} — auto ok, calling judge ... ", end="", flush=True)
            judge = run_judge(judge_client, args.judge_model, judge_system, case, run_result)
            entry["judge"] = judge
            judge_input_tokens += judge.get("judge_input_tokens", 0) or 0
            judge_output_tokens += judge.get("judge_output_tokens", 0) or 0
            if judge.get("judge_error"):
                print(f"JUDGE ERROR: {judge['judge_error']}")
            else:
                print("ok")
        else:
            print(f"  [{i}/{len(outputs)}] {case_id} — auto only")
        scores.append(entry)

    scores_path = run_dir / "scores.jsonl"
    with scores_path.open("w") as f:
        for s in scores:
            f.write(json.dumps(s) + "\n")

    sut_model = outputs[0]["model"] if outputs else "unknown"
    sut_cost = (sut_input_tokens / 1_000_000) * 5.0 + (sut_output_tokens / 1_000_000) * 25.0
    judge_cost = (judge_input_tokens / 1_000_000) * 3.0 + (judge_output_tokens / 1_000_000) * 15.0

    run_meta = {
        "date": run_dir.name,
        "sut_model": sut_model,
        "judge_model": args.judge_model if not args.skip_judge else None,
        "sut_input_tokens": sut_input_tokens,
        "sut_output_tokens": sut_output_tokens,
        "judge_input_tokens": judge_input_tokens,
        "judge_output_tokens": judge_output_tokens,
        "total_cost_usd": sut_cost + judge_cost,
    }

    metrics = aggregate(scores)
    write_summary(run_dir, run_meta, metrics, scores)
    write_failures(run_dir, scores, cases_by_id, outputs_by_id)

    print()
    print(f"Wrote {scores_path}")
    print(f"Wrote {run_dir / 'summary.md'}")
    print(f"Wrote {run_dir / 'failures.md'}")
    print()
    print(f"Verdict accuracy: {metrics.get('verdict_accuracy')}")
    print(f"Catch rate: {metrics.get('catch_rate')}")
    print(f"Em dash violations: {metrics.get('em_dash_violation_total')}")
    print(f"Total estimated cost: ${run_meta['total_cost_usd']:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
