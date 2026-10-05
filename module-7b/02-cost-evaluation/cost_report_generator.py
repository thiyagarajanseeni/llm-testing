"""
===================================================
CI Cost Report Generator Runs/ Day and Monthly Cost Projection

PURPOSE:
    Takes hardcoded per-model cost parameters and generates a daily/monthly
    cost projection report — both as a printed table and a saved JSON file.

    Variables per model:
        avg_cost_per_test   — average cost per individual test call (USD)
        tests_per_ci_run    — number of test calls in one CI pipeline run
        ci_runs_per_day     — how many CI runs are triggered per day

    Derived metrics:
        cost_per_ci_run     = avg_cost_per_test × tests_per_ci_run
        daily_cost          = cost_per_ci_run × ci_runs_per_day
        monthly_cost        = daily_cost × 22   (working days)

INSTRUCTIONS:
    1. Edit the MODEL_CONFIG dict below to reflect your actual observed values
       from cost_comparison.py (use avg_total_cost_usd from the summary report).
    2. Run:
           python cost_report_generator.py
    3. Review the printed table in the terminal.
    4. Check the saved report:
           reports/cost-report.md

OUTPUT FILES:
    reports/cost-report.md   ← markdown cost projection per model

This is GitHub Activity 2 of Hour 2 of Session 3 in Track 2A.
"""

import os

try:
    from tabulate import tabulate as _tabulate
except ImportError:
    _tabulate = None


# ── Hardcoded configuration ────────────────────────────────────
# Update avg_cost_per_test with values from cost_comparison.py output
# (the "Avg Cost/Test ($)" column in the summary report).

MODEL_CONFIG = [
    {
        "model":              "gpt-4o-mini",
        "provider":           "openai",
        "avg_cost_per_test":  0.000075,   # USD — from cost_comparison.py output
        "tests_per_ci_run":   50,
        "ci_runs_per_day":    10,
    },
    {
    "model": "phi:latest",
    "provider": "ollama",
    "avg_cost_per_test": 0.0,
    "tests_per_ci_run": 50,
    "ci_runs_per_day": 10,
    },
    {
    "model": "llama3.2:latest",
    "provider": "ollama",
    "avg_cost_per_test": 0.0,
    "tests_per_ci_run": 50,
    "ci_runs_per_day": 10,
    },
    # {
    #     "model":              "claude-haiku-4-5-20251001",
    #     "provider":           "anthropic",
    #     "avg_cost_per_test":  0.000090,   # USD — from cost_comparison.py output
    #     "tests_per_ci_run":   50,
    #     "ci_runs_per_day":    10,
    # },
    # {
    #     "model":              "claude-3-5-sonnet-20241022",
    #     "provider":           "anthropic",
    #     "avg_cost_per_test":  0.000850,   # USD — from cost_comparison.py output
    #     "tests_per_ci_run":   20,
    #     "ci_runs_per_day":    5,
    # },
    # {
    #     "model":              "gpt-4o",
    #     "provider":           "openai",
    #     "avg_cost_per_test":  0.001200,   # USD — from cost_comparison.py output
    #     "tests_per_ci_run":   20,
    #     "ci_runs_per_day":    5,
    # },
    # {
    #     "model":              "mistralai/mistral-7b-instruct-v0.3:2",
    #     "provider":           "lmstudio",
    #     "avg_cost_per_test":  0.000000,   # Local model — always $0
    #     "tests_per_ci_run":   100,
    #     "ci_runs_per_day":    20,
    # },
]

WORKING_DAYS_PER_MONTH = 20


# ── Computation ────────────────────────────────────────────────

def compute_projections(config: list[dict]) -> list[dict]:
    rows = []
    for m in config:
        cost_per_run  = m["avg_cost_per_test"] * m["tests_per_ci_run"]
        daily_cost    = cost_per_run * m["ci_runs_per_day"]
        monthly_cost  = daily_cost * WORKING_DAYS_PER_MONTH

        rows.append({
            "model":              m["model"],
            "provider":           m["provider"],
            "avg_cost_per_test":  round(m["avg_cost_per_test"],  8),
            "tests_per_ci_run":   m["tests_per_ci_run"],
            "ci_runs_per_day":    m["ci_runs_per_day"],
            "cost_per_ci_run":    round(cost_per_run,  8),
            "daily_cost_usd":     round(daily_cost,    8),
            "monthly_cost_usd":   round(monthly_cost,  6),
        })
    return rows


# ── Display ────────────────────────────────────────────────────

def print_table(rows: list[dict]) -> None:
    headers = [
        "Model",
        "Provider",
        "Avg Cost/Test ($)",
        "Tests/CI Run",
        "CI Runs/Day",
        "Cost/CI Run ($)",
        "Daily Cost ($)",
        "Monthly Cost ($)",
    ]

    table_rows = [
        [
            r["model"],
            r["provider"],
            f"{r['avg_cost_per_test']:.6f}",
            r["tests_per_ci_run"],
            r["ci_runs_per_day"],
            f"{r['cost_per_ci_run']:.6f}",
            f"{r['daily_cost_usd']:.6f}",
            f"{r['monthly_cost_usd']:.4f}",
        ]
        for r in rows
    ]

    total_daily   = sum(r["daily_cost_usd"]   for r in rows)
    total_monthly = sum(r["monthly_cost_usd"] for r in rows)

    print("\n" + "=" * 120)
    print("CI COST REPORT — Track 2A · Session 3 · Hour 2 · GitHub Activity 2")
    print(f"Projection basis: {WORKING_DAYS_PER_MONTH} working days/month")
    print("=" * 120)

    if _tabulate:
        print(_tabulate(table_rows, headers=headers, tablefmt="grid"))
    else:
        col_w = [
            max(len(str(h)), max((len(str(r[i])) for r in table_rows), default=0))
            for i, h in enumerate(headers)
        ]
        sep = "+-" + "-+-".join("-" * w for w in col_w) + "-+"
        fmt = "| " + " | ".join(f"{{:<{w}}}" for w in col_w) + " |"
        print(sep)
        print(fmt.format(*headers))
        print(sep)
        for row in table_rows:
            print(fmt.format(*[str(v) for v in row]))
        print(sep)

    print("=" * 120)


# ── Entry point ────────────────────────────────────────────────

if __name__ == "__main__":
    rows = compute_projections(MODEL_CONFIG)

    print_table(rows)

    # Save JSON report alongside the other reports
    script_dir  = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(script_dir, "..", "..", "reports")
    os.makedirs(reports_dir, exist_ok=True)

    headers = [
        "Model", "Provider", "Avg Cost/Test ($)", "Tests/CI Run",
        "CI Runs/Day", "Cost/CI Run ($)", "Daily Cost ($)", "Monthly Cost ($)",
    ]
    table_rows = [
        [
            r["model"], r["provider"],
            f"{r['avg_cost_per_test']:.6f}",
            r["tests_per_ci_run"],
            r["ci_runs_per_day"],
            f"{r['cost_per_ci_run']:.6f}",
            f"{r['daily_cost_usd']:.6f}",
            f"{r['monthly_cost_usd']:.4f}",
        ]
        for r in rows
    ]

    # Build markdown table
    md_header = "| " + " | ".join(headers) + " |"
    md_sep    = "| " + " | ".join("---" for _ in headers) + " |"
    md_rows   = "\n".join(
        "| " + " | ".join(str(v) for v in row) + " |"
        for row in table_rows
    )
    md_content = f"""# CI Cost Report

**Track 2A · Session 3 · Hour 2 · GitHub Activity 2**

> Projection basis: {WORKING_DAYS_PER_MONTH} working days/month

## Cost Projections by Model

{md_header}
{md_sep}
{md_rows}

## How costs are calculated

- **Cost per CI run** = `avg_cost_per_test × tests_per_ci_run`
- **Daily cost** = `cost_per_ci_run × ci_runs_per_day`
- **Monthly cost** = `daily_cost × {WORKING_DAYS_PER_MONTH}` (working days)

> Values for `avg_cost_per_test` are sourced from the output of `cost_comparison.py`
> (the **Avg Cost/Test ($)** column in the summary report).
"""

    out_path = os.path.join(reports_dir, "cost-report.md")
    with open(out_path, "w") as f:
        f.write(md_content)

    print(f"\nMarkdown report saved to: {out_path}")
