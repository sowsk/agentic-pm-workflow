"""Run the peer-review eval against a configured Anthropic model.

Loads test cases from test-cases.jsonl, the peer-review skill from
../../skills/peer-review/SKILL.md, and invokes the model once per case.
Writes raw outputs to runs/<timestamp>_<model>/outputs.jsonl.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python run_eval.py                          # default: claude-opus-4-8
    python run_eval.py --model claude-sonnet-4-6
    python run_eval.py --cases prd-vague-targets-001,control-good-prd-011

The runner is intentionally simple: one model call per case, no retries on
content errors, no streaming. Scoring lives in score_outputs.py so that the
two stages can be run independently and outputs can be re-scored without
re-running the model.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
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


def _build_http_client():
    """Build an httpx client that trusts the OS keychain.

    On corporate networks that do SSL inspection (Cisco Secure Access, Zscaler,
    Netskope, etc.), Python's bundled CA list doesn't include the corporate root,
    causing CERTIFICATE_VERIFY_FAILED. truststore makes Python use the system
    keychain instead, which already trusts the corporate CA. Harmless otherwise.
    """
    import httpx
    try:
        import ssl
        import truststore
        ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        return httpx.Client(verify=ctx, timeout=httpx.Timeout(120.0))
    except ImportError:
        return httpx.Client(timeout=httpx.Timeout(120.0))


HERE = Path(__file__).parent
REPO_ROOT = HERE.parent.parent
SKILL_PATH = REPO_ROOT / "skills" / "peer-review" / "SKILL.md"
TEST_CASES_PATH = HERE / "test-cases.jsonl"
RUNS_DIR = HERE / "runs"

DEFAULT_MODEL = "claude-opus-4-8"
MAX_TOKENS = 4096


def load_test_cases(path: Path, case_ids: list[str] | None = None) -> list[dict]:
    cases = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            cases.append(json.loads(line))
    if case_ids:
        wanted = set(case_ids)
        cases = [c for c in cases if c["id"] in wanted]
        missing = wanted - {c["id"] for c in cases}
        if missing:
            print(f"Warning: requested cases not found in test-cases.jsonl: {sorted(missing)}")
    return cases


def load_skill(path: Path) -> str:
    """Return the peer-review skill body, stripped of YAML frontmatter."""
    text = path.read_text()
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            text = text[end + 3:].lstrip()
    return text


def build_user_message(case: dict) -> str:
    return (
        f"Audience: {case['audience']}\n"
        f"Stakes: {case['stakes']}\n"
        f"Document type: {case['document_type']}\n\n"
        f"Please peer-review the following draft.\n\n"
        f"---\n\n"
        f"{case['input']}"
    )


def run_one_case(client: Anthropic, model: str, skill_body: str, case: dict) -> dict:
    user_msg = build_user_message(case)
    start = time.time()
    try:
        resp = client.messages.create(
            model=model,
            max_tokens=MAX_TOKENS,
            system=skill_body,
            messages=[{"role": "user", "content": user_msg}],
        )
        elapsed_ms = int((time.time() - start) * 1000)
        output_text = "\n".join(
            block.text for block in resp.content if getattr(block, "type", None) == "text"
        )
        return {
            "case_id": case["id"],
            "model": model,
            "output": output_text,
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens,
            "elapsed_ms": elapsed_ms,
            "stop_reason": resp.stop_reason,
            "error": None,
        }
    except Exception as exc:
        return {
            "case_id": case["id"],
            "model": model,
            "output": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def estimate_cost_usd(input_tokens: int, output_tokens: int, model: str) -> float:
    """Pricing snapshot as of May 2026. Update when Anthropic publishes new tiers."""
    pricing = {
        "claude-opus-4-8":     {"in": 5.0,  "out": 25.0},
        "claude-opus-4-7":     {"in": 15.0, "out": 75.0},
        "claude-sonnet-4-6":   {"in": 3.0,  "out": 15.0},
        "claude-haiku-4-5-20251001": {"in": 0.8, "out": 4.0},
    }
    rates = pricing.get(model)
    if not rates:
        return 0.0
    return (input_tokens / 1_000_000) * rates["in"] + (output_tokens / 1_000_000) * rates["out"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run peer-review eval against an Anthropic model.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model ID (default: %(default)s)")
    parser.add_argument("--cases", default=None, help="Comma-separated case IDs to run (default: all)")
    parser.add_argument("--out-dir", default=None, help="Output directory (default: runs/<timestamp>_<model>)")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY not set. Export it or add it to a .env file at the repo root.")
        return 2

    case_ids = [c.strip() for c in args.cases.split(",")] if args.cases else None
    cases = load_test_cases(TEST_CASES_PATH, case_ids)
    skill_body = load_skill(SKILL_PATH)

    timestamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir = Path(args.out_dir) if args.out_dir else RUNS_DIR / f"{timestamp}_{args.model}"
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs_path = out_dir / "outputs.jsonl"

    print(f"Running {len(cases)} cases against {args.model}")
    print(f"Skill loaded from {SKILL_PATH} ({len(skill_body)} chars)")
    print(f"Writing to {outputs_path}")

    client = Anthropic(api_key=api_key, http_client=_build_http_client())

    total_input_tokens = 0
    total_output_tokens = 0
    failures = 0

    with outputs_path.open("w") as f:
        for i, case in enumerate(cases, 1):
            print(f"  [{i}/{len(cases)}] {case['id']} ... ", end="", flush=True)
            result = run_one_case(client, args.model, skill_body, case)
            f.write(json.dumps(result) + "\n")
            f.flush()
            if result["error"]:
                print(f"ERROR: {result['error']}")
                failures += 1
            else:
                total_input_tokens += result["input_tokens"]
                total_output_tokens += result["output_tokens"]
                print(f"ok ({result['output_tokens']} out tokens, {result['elapsed_ms']} ms)")

    cost = estimate_cost_usd(total_input_tokens, total_output_tokens, args.model)
    print()
    print(f"Done. {len(cases) - failures}/{len(cases)} cases succeeded.")
    print(f"Total tokens: {total_input_tokens} in, {total_output_tokens} out")
    print(f"Estimated cost: ${cost:.4f}")
    print(f"Outputs: {outputs_path}")
    print()
    print(f"Next: python score_outputs.py --run-dir {out_dir}")

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
