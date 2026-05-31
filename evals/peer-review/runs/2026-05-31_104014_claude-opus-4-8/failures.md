# Failures: top 5 most informative cases from this run

Surfaced by combining quantitative violations (verdict wrong, em dashes, hallucinated quotes) and judge findings (false positives, missed issues, hallucination/policy flags).

## prd-vague-targets-001

**Why it surfaced**: verdict wrong: expected 'needs structural rework', got 'do not send'; hallucinated quotes: 28; judge flagged hallucination; judge flagged policy violation

**Category**: skeptic | **Stakes**: high | **Audience**: VP Product

**Expected verdict**: needs structural rework  
**Got verdict**: do not send

**Output excerpt** (first 1500 chars):

```
Before I render the full review, one calibration note: you gave me audience (VP Product) and high stakes, so I'm running this line-by-line. Here's the analysis.

---

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Peer Review: Smart Notification Routing PRD</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    line-height: 1.6;
    color: #1a1a2e;
    background: #f4f5f7;
    padding: 32px 16px;
  }
  .container { max-width: 820px; margin: 0 auto; }
  .header {
    background: #16213e;
    color: #fff;
    padding: 24px 28px;
    border-radius: 12px 12px 0 0;
  }
  .header h1 { font-size: 20px; margin-bottom: 6px; }
  .header .meta { font-size: 13px; opacity: 0.8; }
  .verdict {
    background: #c0392b;
    color: #fff;
    padding: 20px 28px;
    font-size: 16px;
    font-weight: 600;
  }
  .verdict .label {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
    opacity: 0.85;
    display: block;
    margin-bottom: 4px;
  }
  .section {
    background: #fff;
    padding: 24px 28px;
    border-bottom: 1px solid #e1e4e8;
  }
  .section h2 {
    font-size: 15px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #16213e;
    margin-bottom: 16px;
  }
  .change {
    border-left: 4px solid #ccc;
    padding: 12px 16px;
    m...
```

---

## edge-em-dash-input-014

**Why it surfaced**: verdict wrong: expected 'needs minor edits', got 'ready to send'; em-dash violation: 4 em dashes in output; hallucinated quotes: 6; judge flagged policy violation

**Category**: edge | **Stakes**: low | **Audience**: team Slack

**Expected verdict**: needs minor edits  
**Got verdict**: ready to send

**Output excerpt** (first 1500 chars):

```
Low stakes, internal Slack, and this draft is genuinely solid. Top-line findings only.

## Verdict
**Ready to send after one small fix.** Clear phasing, clear rationale, clear ask. The structure is good.

## Top changes

**P0 — The offsite conflict needs a decision, not just a flag.**
> "the third weekend is during the team offsite. We will need two people on standby."

You flag the conflict but leave the obvious question open: why not move the third weekend? The third weekend only retires the old service (lowest risk of the three). Either say "we considered moving it and here's why we're keeping it" or "open to shifting it a week if the offsite makes standby hard." Right now a reader will ask this immediately and you've pre-empted nothing.

**P1 — Set a deadline on volunteers.**
> "Volunteers welcome — otherwise I will assign."

In Slack, "volunteers welcome" with no deadline means silence. Add "by Thursday" or similar, otherwise you'll be assigning anyway and the volunteer line was theater.

**P2 — Em dash overload (style, your call).**
You're using em dashes as the connective tissue for nearly every sentence. Six of them in a short note. It reads slightly breathless. Not wrong for Slack, but a couple could be periods.

## What is working
- The rollback rationale is the strongest part: "fully warmed and serving so we can flip back fast" tells the reader *why* phasing beats a single cutover without over-explaining.
- Read-then-write-then-retire is the right risk order and yo...
```

---

## customer-email-missing-context-005

**Why it surfaced**: verdict wrong: expected 'needs minor edits', got 'needs structural rework'; em-dash violation: 6 em dashes in output; hallucinated quotes: 16

**Category**: audience | **Stakes**: high | **Audience**: enterprise customer (CISO at Fortune 500 bank)

**Expected verdict**: needs minor edits  
**Got verdict**: needs structural rework

**Output excerpt** (first 1500 chars):

```
I'll review this now. Given the audience (CISO at a Fortune 500 bank) and high stakes, I'm calibrating to a strict, near line-by-line review.

A note before the findings: I'd normally render this as an HTML canvas, but the review is compact enough that inline serves you better here. Flagging that I'm deviating from the default format intentionally.

---

## Verdict

**Needs structural rework.** This reads as an internal status update, not an accountability communication to a regulated financial customer after an outage.

---

## Top 3 specific changes

**P0 — No acknowledgment of impact, no apology, no accountability framing.**
The email opens with "Thanks for raising the concern." A CISO whose institution was affected by your outage did not raise a "concern," they experienced a service failure with potential downstream impact on their operations. There is no "we're sorry," no acknowledgment of the disruption, no ownership. For a bank, an outage may be a reportable event to their own risk and compliance teams. This email gives them nothing to bring upstream.

**P1 — Internal jargon throughout makes this unreadable to the audience.**
Five acronyms the customer almost certainly does not know: "EBC," "TIPv2," "CEA team," "PE team," and arguably "RCA" depending on their familiarity. Quote: *"the issue was traced to a misconfiguration in our TIPv2 deployment"* and *"schedule a follow-up with the PE team."* The reader does not care about your internal team names. This signals the e...
```

---

## control-good-prd-011

**Why it surfaced**: verdict wrong: expected 'ready to send', got 'needs minor edits'; em-dash violation: 4 em dashes in output; hallucinated quotes: 11

**Category**: control | **Stakes**: high | **Audience**: VP Product

**Expected verdict**: ready to send  
**Got verdict**: needs minor edits

**Output excerpt** (first 1500 chars):

```
This is a strong draft. Before I render the full canvas, let me give you the honest read: this PRD is in good shape and my findings are mostly sharpening, not rescue. I'll flag the real gaps clearly.

---

## Verdict
**Needs minor edits.** This is close to send-ready for a VP audience. The logic chain holds, metrics are specific, and the ask is concrete. Two findings need addressing before sign-off because they affect the guardrail credibility and the resourcing ask.

---

## Top 3 changes (prioritized)

### P0 — The guardrail metric has no measurement mechanism
> "Guardrail: No increase in alert-related SEV1 incidents traced to suppression (zero is the bar)."

You set zero as the bar but never say how you detect a suppressed incident. If auto-snooze hides a genuine SEV1, by definition nobody acked it, so what triggers the trace-back? This is the single most likely question a VP asks and the answer "we'll know it when we see it" sinks the approval. State the detection mechanism: shadow-logging every snoozed alert, a delayed-fire audit, post-incident review tagging, or similar. Without this, the guardrail is aspirational, not measurable.

### P1 — The 60% hypothesis target and the 4.6 success target don't reconcile
> Hypothesis: "reduce manual snooze actions by 60%"
> Success metric: "current baseline 11.4 actions; target less than 4.6"

11.4 reduced by 60% is 4.56, so the math works, but you present two numbers the reader has to reconcile themselves. More importantly: the sur...
```

---

## control-good-leadership-update-012

**Why it surfaced**: verdict wrong: expected 'ready to send', got 'needs minor edits'; em-dash violation: 5 em dashes in output; hallucinated quotes: 6

**Category**: control | **Stakes**: medium | **Audience**: your manager (Director PM)

**Expected verdict**: ready to send  
**Got verdict**: needs minor edits

**Output excerpt** (first 1500 chars):

```
Quick calibration before the review: this is a tight, well-structured update. The harshness here is dialed to medium stakes and a competent audience, so I'm flagging real gaps but not inventing problems.

---

## Verdict
**Needs minor edits**: strong decision-forcing structure, but the central ask leans on an unsourced "binding" claim and omits the risk profile of your recommended path.

---

## Top 3 specific changes

**P0 — Substantiate "binding"**
> "I lean toward B because the changelog commitment is binding"

"Binding" is doing all the load-bearing work in your recommendation and it is asserted, not shown. Binding to whom, and what is the actual consequence of missing it? A customer contract? A public-facing promise with reputational cost? If your Director pushes back with "changelogs slip all the time, why is this one different," you have no answer in the doc. One clause fixes it.

**P1 — Option B has an unstated risk, not just a cost**
> "Cost: technical debt, requires manual account-level config."

You frame B's downside as cost (debt, manual config). But the real question is: does the feature flag actually work? You are suppressing streaming for your *top 3 customers*. If the suppression is buggy or the manual config is fat-fingered, those same top customers get a worse experience than option A's delay. You are asking for a Wednesday decision while underselling the failure mode of the path you recommend. Name it.

**P1 — The two open items have no owner-of-consequenc...
```

---

