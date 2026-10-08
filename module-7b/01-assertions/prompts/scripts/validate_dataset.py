"""
validate_dataset.py
Runs all 5 quality gates on any test dataset CSV before it enters your test suite.

Usage:
    python scripts/validate_dataset.py data/golden_augmentation/augmented_data.csv

Gates:
    1. Dedup check          — cosine-similarity-like ratio > 0.9 → flag as near-duplicate
    2. Label accuracy       — LLM judge: does expected_behavior actually match input?
    3. Distribution audit   — warn if any category > 60% of dataset
    4. Toxicity scan        — LLM judge: is this input harmful/offensive?
    5. Human review sample  — prints 10% random sample for manual spot-check
"""

import csv
import json
import os
import random
import sys
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

from openai import OpenAI

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PASS = "✅"
WARN = "⚠️ "
FAIL = "❌"


# ── GATE 1: Dedup Check ──────────────────────────────────────────────────────

def gate_dedup(rows: list[dict], threshold: float = 0.9) -> bool:
    """
    Flag any two rows whose inputs are more than `threshold` similar.
    Uses SequenceMatcher ratio — same approach as difflib's "close matches".

    threshold=0.9 means 90% character-sequence overlap.
    "Cancel my superannuation" vs "Cancel my superannuation please" = ~0.95 → flagged.
    "Cancel my superannuation" vs "How do I stop my superannuation?" = ~0.45 → fine.
    """
    print("\n── Gate 1: Dedup Check ─────────────────────────────────────────")
    inputs = [r.get("user_input", "") for r in rows]
    dupes_found = []

    for i in range(len(inputs)):
        for j in range(i + 1, len(inputs)):
            ratio = SequenceMatcher(None, inputs[i].lower(), inputs[j].lower()).ratio()
            if ratio > threshold:
                dupes_found.append((i + 2, j + 2, ratio, inputs[i], inputs[j]))

    if dupes_found:
        print(f"{WARN} {len(dupes_found)} near-duplicate pair(s) found (threshold: {threshold}):")
        for r1, r2, ratio, t1, t2 in dupes_found[:10]:
            print(f"   Row {r1} vs Row {r2}  ({ratio:.0%} similar)")
            print(f"     A: {t1[:70]}")
            print(f"     B: {t2[:70]}")
        print(f"\n   ACTION: Remove one row from each pair before using this dataset.")
        return False
    else:
        print(f"{PASS} No near-duplicates found ({len(inputs)} inputs checked)")
        return True


# ── GATE 2: Label Accuracy ───────────────────────────────────────────────────

def gate_label_accuracy(rows: list[dict], sample_size: int = 10) -> bool:
    """
    Uses OpenAI to check: does expected_behavior actually describe what a correct
    response to this input would look like?

    Augmentation can silently break labels — e.g. a paraphrase changes the intent
    but the expected_behavior column still says the original thing.

    Example of a broken label:
        input:            "How do I CLOSE my account permanently?"
        expected_behavior: "Mentions cancellation steps"   ← wrong! should say deletion

    We sample `sample_size` rows to keep API costs low.
    """
    print("\n── Gate 2: Label Accuracy ──────────────────────────────────────")

    if "expected_behavior" not in rows[0]:
        print(f"{WARN} No 'expected_behavior' column found — skipping label accuracy check")
        return True

    sample = random.sample(rows, min(sample_size, len(rows)))
    issues = []

    for row in sample:
        prompt = f"""You are a QA reviewer checking test data quality.

Input (what the user sends to the chatbot):
"{row['user_input']}"

Expected behavior (what we expect the chatbot to do):
"{row.get('expected_behavior', '')}"

Question: Does the expected behavior accurately describe what a CORRECT response to this input should do? Answer with a JSON object:
{{
"accurate": true or false,
"reason": "one sentence explanation"
}}

Return ONLY the JSON object, nothing else."""

        response = client.responses.create(
    model="gpt-4o",
    max_output_tokens=4000,
    input=prompt
)
        raw = response.output_text.strip().replace("```json", "").replace("```", "")
        result = json.loads(raw)

        if not result.get("accurate", True):
            issues.append({
                "input": row["user_input"],
                "expected_behavior": row.get("expected_behavior", ""),
                "reason": result.get("reason", "")
            })

    if issues:
        print(f"{WARN} {len(issues)}/{len(sample)} sampled rows have mismatched labels:")
        for issue in issues:
            print(f"\n   Input:    {issue['input'][:70]}")
            print(f"   Label:    {issue['expected_behavior'][:70]}")
            print(f"   Problem:  {issue['reason']}")
        print(f"\n   ACTION: Fix the expected_behavior for these rows manually.")
        return False
    else:
        print(f"{PASS} Label accuracy check passed ({len(sample)} rows sampled)")
        return True


# ── GATE 3: Distribution Audit ───────────────────────────────────────────────

def gate_distribution(rows: list[dict], max_pct: float = 0.60) -> bool:
    """
    Checks that no single category dominates the dataset.

    Why this matters: augmentation magnifies whatever you started with.
    If you had 15 happy_path and 5 adversarial rows, after 3x augmentation
    you have 45 happy_path and 15 adversarial — the imbalance got worse, not better.

    max_pct=0.60 means: warn if any category is more than 60% of the dataset.
    Ideal target: happy_path ~40%, edge_case ~35%, adversarial ~25%.
    """
    print("\n── Gate 3: Distribution Audit ──────────────────────────────────")

    if "category" not in rows[0]:
        print(f"{WARN} No 'category' column — skipping distribution check")
        return True

    dist = Counter(r["category"] for r in rows)
    total = len(rows)
    passed = True

    print(f"   Total rows: {total}")
    for cat, n in sorted(dist.items()):
        pct = n / total
        bar = "█" * int(pct * 30)
        flag = WARN if pct > max_pct else PASS
        print(f"   {flag} {cat:<20} {bar:<30} {n:3d}  ({pct:.0%})")
        if pct > max_pct:
            passed = False

    if not passed:
        print(f"\n   ACTION: Add more rows to under-represented categories,")
        print(f"   or reduce augmentation multiplier for over-represented ones.")

    return passed


# ── GATE 4: Toxicity Scan ────────────────────────────────────────────────────

def gate_toxicity(rows: list[dict]) -> bool:
    """
    Scans all inputs for content that shouldn't be in a professional test suite:
    offensive language, hate speech, explicit content, real PII.

    Note: adversarial test cases (prompt injections, jailbreak attempts) are FINE —
    they're supposed to be in there. We're only catching accidentally generated
    offensive content that slipped through.

    We batch inputs to reduce API calls — send up to 20 at a time.
    """
    print("\n── Gate 4: Toxicity Scan ───────────────────────────────────────")

    inputs = [r.get("user_input", "") for r in rows]
    batch_size = 20
    toxic_found = []

    for batch_start in range(0, len(inputs), batch_size):
        batch = inputs[batch_start : batch_start + batch_size]
        numbered = "\n".join(f"{i+1}. {inp}" for i, inp in enumerate(batch))

        prompt = f"""You are checking test inputs for a professional software QA test suite.

Review these {len(batch)} inputs and identify any that contain:
- Hate speech or slurs
- Explicit sexual content  
- Real personal information (actual names + contact details)
- Content that would embarrass a professional organization

NOTE: Prompt injection attempts, jailbreak tests, and adversarial security tests 
are NOT toxic — they are expected and should NOT be flagged.

Inputs:
{numbered}

Return a JSON array of objects for ONLY the problematic inputs:
[{{"index": 1, "input": "...", "reason": "..."}}]

If none are problematic, return an empty array: []
Return ONLY the JSON, nothing else."""

        response = client.responses.create(
    model="gpt-4o",
    max_output_tokens=4000,
    input=prompt
)

        raw = response.output_text.strip().replace("```json", "").replace("```", "")
        results = json.loads(raw)

        for item in results:
            global_index = batch_start + item["index"]
            toxic_found.append({
                "row": global_index + 1,
                "input": item["input"],
                "reason": item["reason"]
            })

    if toxic_found:
        print(f"{FAIL} {len(toxic_found)} problematic input(s) found:")
        for item in toxic_found:
            print(f"\n   Row {item['row']}: {item['input'][:70]}")
            print(f"   Reason:  {item['reason']}")
        print(f"\n   ACTION: Remove these rows before using this dataset.")
        return False
    else:
        print(f"{PASS} No toxic content found ({len(inputs)} inputs scanned)")
        return True


# ── GATE 5: Human Review Sample ──────────────────────────────────────────────

def gate_human_review(rows: list[dict], sample_pct: float = 0.10) -> bool:
    """
    Prints a random 10% sample for the human to read through.
    Automated gates catch systematic problems; human eyes catch subtle ones —
    a variant that technically passes all checks but tests the wrong thing.

    This gate always 'passes' automatically — it just prints the sample.
    The human marks it as reviewed in BASELINE.md.
    """
    print("\n── Gate 5: Human Review Sample ─────────────────────────────────")

    n = max(1, int(len(rows) * sample_pct))
    sample = random.sample(rows, n)

    print(f"   Review these {n} rows manually ({sample_pct:.0%} of {len(rows)} total):")
    print(f"   Ask yourself: Does this input test what I think it tests?\n")

    for i, row in enumerate(sample, 1):
        print(f"   [{i:02d}] Category: {row.get('category', 'N/A'):<15}  "
            f"Source: {row.get('source', 'original')}")
        print(f"        Input:    {row['user_input'][:80]}")
        eb = row.get('expected_behavior', row.get('__expected__', 'N/A'))
        print(f"        Expected: {eb[:80]}")
        print()

    print(f"   {WARN} Human review required — mark as complete in BASELINE.md")
    return True


# ── Runner ───────────────────────────────────────────────────────────────────

def run_all_gates(filepath: str):
    print(f"\n{'='*65}")
    print(f" Dataset Quality Validator")
    print(f" File: {filepath}")
    print(f"{'='*65}")

    with open(filepath, encoding="cp1252", newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        print(f"{FAIL} File is empty or has no data rows.")
        return

    print(f" Rows loaded: {len(rows)}")
    print(f" Columns:     {', '.join(rows[0].keys())}")

    results = {
        "Dedup":        gate_dedup(rows),
        "Label accuracy": gate_label_accuracy(rows, sample_size=min(10, len(rows))),
        "Distribution": gate_distribution(rows),
        "Toxicity":     gate_toxicity(rows),
        "Human review": gate_human_review(rows),
    }

    print(f"\n{'='*65}")
    print(" Summary")
    print(f"{'='*65}")
    all_passed = True
    for gate, passed in results.items():
        icon = PASS if passed else WARN
        print(f" {icon} {gate}")
        if not passed:
            all_passed = False

    print(f"\n{'='*65}")
    if all_passed:
        print(f" {PASS} All gates passed. Dataset is ready for use.")
    else:
        print(f" {WARN} One or more gates failed. Fix issues before committing.")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    path = (
    sys.argv[1]
    if len(sys.argv) > 1
    else "module-7b/data/golden_augmentation/augmented_data.csv"
)
    if not Path(path).exists():
        print(f"File not found: {path}")
        sys.exit(1)
    run_all_gates(path)
