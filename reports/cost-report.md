# CI Cost Report



> Projection basis: 20 working days/month

## Cost Projections by Model

| Model | Provider | Avg Cost/Test ($) | Tests/CI Run | CI Runs/Day | Cost/CI Run ($) | Daily Cost ($) | Monthly Cost ($) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gpt-4o-mini | openai | 0.000075 | 50 | 10 | 0.003750 | 0.037500 | 0.7500 |
| phi:latest | ollama | 0.000000 | 50 | 10 | 0.000000 | 0.000000 | 0.0000 |
| llama3.2:latest | ollama | 0.000000 | 50 | 10 | 0.000000 | 0.000000 | 0.0000 |

## How costs are calculated

- **Cost per CI run** = `avg_cost_per_test � tests_per_ci_run`
- **Daily cost** = `cost_per_ci_run � ci_runs_per_day`
- **Monthly cost** = `daily_cost � 20` (working days)

> Values for `avg_cost_per_test` are sourced from the output of `cost_comparison.py`
> (the **Avg Cost/Test ($)** column in the summary report).
