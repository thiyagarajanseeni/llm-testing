"""
Track 2A · Module 7B · Lab 2: Cost Evaluation
==============================================
Compare cost-per-request across LLM providers.

PURPOSE:
    Understand real-world cost differences between cloud models (OpenAI, Anthropic)
    and free local models (LM Studio, Ollama) by running identical prompts through
    each provider and generating a comparative cost + latency report.

PREREQUISITES:
    1. Python packages:
          pip install openai anthropic tiktoken python-dotenv requests tabulate

    2. API keys — create a .env file in this directory with:
          OPENAI_API_KEY=sk-...
          ANTHROPIC_API_KEY=sk-ant-...

    3. Local models (optional but recommended):
          - LM Studio: download and run mistralai/mistral-7b-instruct-v0.3
            (must be listening at http://localhost:1234/v1)
          - Ollama: install ollama, then run `ollama pull gpt-oss:20b`
            (must be listening at http://localhost:11434)
          Comment out any provider in models_to_test if not available locally.

INSTRUCTIONS:
    1. Copy .env.example to .env and fill in your API keys.
    2. Start LM Studio and/or Ollama if you want local model comparisons.
    3. Run:
           python cost_comparison.py
    4. Review the printed tables — raw per-request results and the summary report.
    5. Check the saved output files:
           reports/cost-comparison.json        ← raw per-request data
           reports/cost-report-summary.json    ← aggregated model summary

WHAT TO OBSERVE:
    - Cost delta between cloud tiers (e.g. Haiku vs Sonnet vs GPT-4o-mini)
    - Local models always show $0 cost — compare their latency vs cloud
    - tiktoken estimates vs actual API-reported token counts

Homework: Fill in TODO sections and produce a cost report.
This is part of Github Exercise for Session 3 Hour 2
"""

import os
import time
import json
import requests
from dataclasses import dataclass, asdict
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# ── Cost table (USD per 1M tokens) ────────────────────────────
# Update these to current pricing from each provider's docs
PRICING = {
    # "gpt-4o":                    {"input": 5.00,   "output": 15.00},
    "gpt-4o-mini":               {"input": 0.150,  "output": 0.600},
    "phi:latest":                   {"input": 0.0,"output": 0.0},
    "llama3.2:latest":                  {"input": 0.0, "output": 0.0},
    # "claude-3-haiku-20240307":        {"input": 0.25,  "output": 1.25},
    # "claude-haiku-4-5-20251001":      {"input": 0.80,  "output": 4.00},
    # "claude-3-5-sonnet-20241022":     {"input": 3.00,  "output": 15.00},
    # "claude-sonnet-4-6":              {"input": 3.00,  "output": 15.00},
    # # Local models — zero cost
    # "mistralai/mistral-7b-instruct-v0.3:2":      {"input": 0.0, "output": 0.0},
    # "gpt-oss:20b":                               {"input": 0.0, "output": 0.0},
}

# tiktoken encoding map — fallback to cl100k_base for unknown models
TIKTOKEN_ENCODING_MAP = {
    "gpt-4o":      "o200k_base",
    "gpt-4o-mini": "o200k_base",
}

TEST_PROMPTS = [
    "What is Superannuation in Australia?",
    "What is the preservation age to access superannuation in Australia?",
    "At what age can I withdraw my superannuation in Australia without paying tax?",
    "Can I buy a property using my superannuation in Australia?",
    "Who are all my legal beneficiaries for superannuation in Australia?",
]


@dataclass
class RequestResult:
    model: str
    prompt: str
    response: str
    input_tokens: int           # tokens reported by the API
    output_tokens: int          # tokens reported by the API
    tiktoken_input: int         # tokens estimated via tiktoken
    tiktoken_output: int        # tokens estimated via tiktoken
    latency_ms: float
    input_cost_usd: float
    output_cost_usd: float
    cost_usd: float             # total = input + output
    error: Optional[str] = None


# ── Token counting ─────────────────────────────────────────────

def get_token_count(text: str, model: str) -> int:
    """Estimate token count for *text* using tiktoken.

    Falls back to ``cl100k_base`` for models not in TIKTOKEN_ENCODING_MAP
    (e.g. Anthropic / Ollama models).
    """
    import tiktoken

    encoding_name = TIKTOKEN_ENCODING_MAP.get(model, "cl100k_base")
    try:
        enc = tiktoken.get_encoding(encoding_name)
    except Exception:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


# ── Cost calculation ───────────────────────────────────────────

def calculate_cost(
    model: str, input_tokens: int, output_tokens: int
) -> tuple[float, float, float]:
    """Return ``(input_cost_usd, output_cost_usd, total_cost_usd)``."""
    if model not in PRICING:
        print(f"[WARNING] No pricing found for model '{model}' — cost set to 0.0")
        return 0.0, 0.0, 0.0
    p = PRICING[model]
    input_cost  = (input_tokens  * p["input"])  / 1_000_000
    output_cost = (output_tokens * p["output"]) / 1_000_000
    return input_cost, output_cost, input_cost + output_cost


# ── Provider runners ───────────────────────────────────────────

def run_openai_request(model: str, prompt: str) -> RequestResult:
    """Run a single request against OpenAI and capture cost metrics."""
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    tiktoken_input = get_token_count(prompt, model)

    start = time.time()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=int(os.getenv("MAX_TOKENS_PER_TEST", 500)),
        )
        latency_ms    = (time.time() - start) * 1000
        input_tokens  = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        response_text = response.choices[0].message.content
        tiktoken_output = get_token_count(response_text, model)
        ic, oc, tc = calculate_cost(model, input_tokens, output_tokens)
        return RequestResult(
            model=model, prompt=prompt, response=response_text,
            input_tokens=input_tokens, output_tokens=output_tokens,
            tiktoken_input=tiktoken_input, tiktoken_output=tiktoken_output,
            latency_ms=round(latency_ms, 2),
            input_cost_usd=ic, output_cost_usd=oc, cost_usd=tc,
        )
    except Exception as e:
        return RequestResult(
            model=model, prompt=prompt, response="",
            input_tokens=0, output_tokens=0,
            tiktoken_input=tiktoken_input, tiktoken_output=0,
            latency_ms=0, input_cost_usd=0, output_cost_usd=0, cost_usd=0,
            error=str(e),
        )
        

def run_phi_request(prompt: str) -> RequestResult:
    """Run a single request against a local Ollama instance
    and capture token, latency, and cost metrics.

    Ollama must be running at OLLAMA_BASE_URL
    (default: http://localhost:11434).

    Cost is $0 for the local model.
    """
    import os
    import time
    import requests

    model = "phi:latest"

    ollama_url = os.getenv(
        "OLLAMA_BASE_URL",
        "http://localhost:11434"
    )

    # Count input tokens before sending the request
    tiktoken_input = get_token_count(prompt, model)

    start = time.time()

    try:
        resp = requests.post(
            f"{ollama_url}/api/chat",
            json={
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False,
                "options": {
                    "temperature": 0,
                    "num_predict": int(
                        os.getenv("MAX_TOKENS_PER_TEST", 500)
                    ),
                },
            },
            timeout=120,
        )

        # Raise an exception if Ollama returns HTTP 4xx/5xx
        resp.raise_for_status()

        # Calculate latency
        latency_ms = (time.time() - start) * 1000

        # Parse Ollama JSON response
        data = resp.json()

        # Extract generated response
        response_text = data["message"]["content"]

        # Get token counts reported by Ollama
        input_tokens = data.get(
            "prompt_eval_count",
            tiktoken_input
        )

        output_tokens = data.get(
            "eval_count",
            0
        )

        # Independently calculate output tokens
        tiktoken_output = get_token_count(
            response_text,
            model
        )

        # Calculate cost
        # Local phi:latest should be configured as $0
        ic, oc, tc = calculate_cost(
            model,
            input_tokens,
            output_tokens
        )

        return RequestResult(
            model=model,
            prompt=prompt,
            response=response_text,

            input_tokens=input_tokens,
            output_tokens=output_tokens,

            tiktoken_input=tiktoken_input,
            tiktoken_output=tiktoken_output,

            latency_ms=round(latency_ms, 2),

            input_cost_usd=ic,
            output_cost_usd=oc,
            cost_usd=tc,
        )

    except Exception as e:

        return RequestResult(
            model=model,
            prompt=prompt,
            response="",

            input_tokens=0,
            output_tokens=0,

            tiktoken_input=tiktoken_input,
            tiktoken_output=0,

            latency_ms=0,

            input_cost_usd=0,
            output_cost_usd=0,
            cost_usd=0,

            error=str(e),
        )


def run_llama_request(model: str, prompt: str) -> RequestResult:
    """Run Llama 3.2 locally using Ollama."""

    base_url = os.getenv(
        "OLLAMA_BASE_URL",
        "http://localhost:11434"
    )

    start = time.time()

    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json={
                "model": "llama3.2:latest",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False,
                "options": {
                    "temperature": 0
                }
            },
            timeout=120
        )

        response.raise_for_status()

        data = response.json()

        latency_ms = (time.time() - start) * 1000

        input_tokens = data.get("prompt_eval_count", 0)
        output_tokens = data.get("eval_count", 0)

        response_text = data["message"]["content"]

        ic, oc, tc = calculate_cost(
            "llama3.2:latest",
            input_tokens,
            output_tokens
        )

        return RequestResult(
            model="llama3.2:latest",
            prompt=prompt,
            response=response_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            tiktoken_input=input_tokens,
            tiktoken_output=output_tokens,
            latency_ms=round(latency_ms, 2),
            input_cost_usd=ic,
            output_cost_usd=oc,
            cost_usd=tc,
        )

    except Exception as e:
        return RequestResult(
            model="llama3.2:latest",
            prompt=prompt,
            response="",
            input_tokens=0,
            output_tokens=0,
            tiktoken_input=0,
            tiktoken_output=0,
            latency_ms=0,
            input_cost_usd=0,
            output_cost_usd=0,
            cost_usd=0,
            error=str(e),
        )        
        
        
        
                


# def run_anthropic_request(model: str, prompt: str) -> RequestResult:
#     """Run a single request against Anthropic and capture cost metrics."""
#     import anthropic

#     client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
#     tiktoken_input = get_token_count(prompt, model)

#     start = time.time()
#     try:
#         response = client.messages.create(
#             model=model,
#             max_tokens=int(os.getenv("MAX_TOKENS_PER_TEST", 500)),
#             messages=[{"role": "user", "content": prompt}],
#         )
#         latency_ms    = (time.time() - start) * 1000
#         input_tokens  = response.usage.input_tokens
#         output_tokens = response.usage.output_tokens
#         response_text = response.content[0].text
#         tiktoken_output = get_token_count(response_text, model)
#         ic, oc, tc = calculate_cost(model, input_tokens, output_tokens)
#         return RequestResult(
#             model=model, prompt=prompt, response=response_text,
#             input_tokens=input_tokens, output_tokens=output_tokens,
#             tiktoken_input=tiktoken_input, tiktoken_output=tiktoken_output,
#             latency_ms=round(latency_ms, 2),
#             input_cost_usd=ic, output_cost_usd=oc, cost_usd=tc,
#         )
#     except Exception as e:
#         return RequestResult(
#             model=model, prompt=prompt, response="",
#             input_tokens=0, output_tokens=0,
#             tiktoken_input=tiktoken_input, tiktoken_output=0,
#             latency_ms=0, input_cost_usd=0, output_cost_usd=0, cost_usd=0,
#             error=str(e),
#         )


# def run_lmstudio_request(model: str, prompt: str) -> RequestResult:
#     """Run a single request against a local LM Studio instance and capture metrics.

#     LM Studio exposes an OpenAI-compatible API at LMS_BASE_URL
#     (default: http://localhost:1234/v1).  Cost is always $0 for local models.
#     """
#     from openai import OpenAI

#     lms_url        = os.getenv("LMS_BASE_URL", "http://localhost:1234/v1")
#     client         = OpenAI(base_url=lms_url, api_key="lm-studio")
#     tiktoken_input = get_token_count(prompt, model)

#     start = time.time()
#     try:
#         response = client.chat.completions.create(
#             model=model,
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0,
#             max_tokens=int(os.getenv("MAX_TOKENS_PER_TEST", 500)),
#         )
#         latency_ms    = (time.time() - start) * 1000
#         input_tokens  = response.usage.prompt_tokens
#         output_tokens = response.usage.completion_tokens
#         response_text = response.choices[0].message.content
#         tiktoken_output = get_token_count(response_text, model)
#         ic, oc, tc = calculate_cost(model, input_tokens, output_tokens)
#         return RequestResult(
#             model=model, prompt=prompt, response=response_text,
#             input_tokens=input_tokens, output_tokens=output_tokens,
#             tiktoken_input=tiktoken_input, tiktoken_output=tiktoken_output,
#             latency_ms=round(latency_ms, 2),
#             input_cost_usd=ic, output_cost_usd=oc, cost_usd=tc,
#         )
#     except Exception as e:
#         return RequestResult(
#             model=model, prompt=prompt, response="",
#             input_tokens=0, output_tokens=0,
#             tiktoken_input=tiktoken_input, tiktoken_output=0,
#             latency_ms=0, input_cost_usd=0, output_cost_usd=0, cost_usd=0,
#             error=str(e),
#         )


# def run_ollama_request(model: str, prompt: str) -> RequestResult:
#     """Run a single request against a local Ollama instance and capture metrics.

#     Ollama must be running at OLLAMA_BASE_URL (default: http://localhost:11434).
#     Cost is always $0 for local models.
#     """
#     import requests

#     ollama_url     = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
#     tiktoken_input = get_token_count(prompt, model)

#     start = time.time()
#     try:
#         resp = requests.post(
#             f"{ollama_url}/api/chat",
#             json={
#                 "model": model,
#                 "messages": [{"role": "user", "content": prompt}],
#                 "stream": False,
#                 "options": {
#                     "temperature": 0,
#                     "num_predict": int(os.getenv("MAX_TOKENS_PER_TEST", 500)),
#                 },
#             },
#             timeout=120,
#         )
#         resp.raise_for_status()
#         latency_ms    = (time.time() - start) * 1000
#         data          = resp.json()
#         response_text = data["message"]["content"]
#         # Ollama reports prompt_eval_count and eval_count; fall back to tiktoken
#         input_tokens  = data.get("prompt_eval_count", tiktoken_input)
#         output_tokens = data.get("eval_count", 0)
#         tiktoken_output = get_token_count(response_text, model)
#         ic, oc, tc = calculate_cost(model, input_tokens, output_tokens)
#         return RequestResult(
#             model=model, prompt=prompt, response=response_text,
#             input_tokens=input_tokens, output_tokens=output_tokens,
#             tiktoken_input=tiktoken_input, tiktoken_output=tiktoken_output,
#             latency_ms=round(latency_ms, 2),
#             input_cost_usd=ic, output_cost_usd=oc, cost_usd=tc,
#         )
#     except Exception as e:
#         return RequestResult(
#             model=model, prompt=prompt, response="",
#             input_tokens=0, output_tokens=0,
#             tiktoken_input=tiktoken_input, tiktoken_output=0,
#             latency_ms=0, input_cost_usd=0, output_cost_usd=0, cost_usd=0,
#             error=str(e),
#         )


# ── Report helpers ─────────────────────────────────────────────

def build_report(results: list[RequestResult]) -> dict:
    """Aggregate per-model stats and return a structured report dict."""
    by_model: dict[str, list[RequestResult]] = {}
    for r in results:
        by_model.setdefault(r.model, []).append(r)

    model_summaries = []
    grand_total = 0.0

    for model, reqs in by_model.items():
        valid  = [r for r in reqs if not r.error]
        errors = len(reqs) - len(valid)
        if not valid:
            model_summaries.append({"model": model, "error": "all requests failed"})
            continue
        n = len(valid)
        avg_in          = sum(r.input_tokens    for r in valid) / n
        avg_out         = sum(r.output_tokens   for r in valid) / n
        avg_tik_in      = sum(r.tiktoken_input  for r in valid) / n
        avg_tik_out     = sum(r.tiktoken_output for r in valid) / n
        avg_lat         = sum(r.latency_ms      for r in valid) / n
        total_in_cost   = sum(r.input_cost_usd  for r in valid)
        total_out_cost  = sum(r.output_cost_usd for r in valid)
        total_cost      = sum(r.cost_usd        for r in valid)
        grand_total    += total_cost

        avg_cost = total_cost / n

        model_summaries.append({
            "model":                   model,
            "requests":                n,
            "errors":                  errors,
            "avg_input_tokens":        round(avg_in, 1),
            "avg_output_tokens":       round(avg_out, 1),
            "avg_tiktoken_input":      round(avg_tik_in, 1),
            "avg_tiktoken_output":     round(avg_tik_out, 1),
            "avg_latency_ms":          round(avg_lat, 1),
            "total_input_cost_usd":    round(total_in_cost,  8),
            "total_output_cost_usd":   round(total_out_cost, 8),
            "total_cost_usd":          round(total_cost,     8),
            "avg_total_cost_usd":      round(avg_cost,       8),
        })

    return {
        "models":              model_summaries,
        "grand_total_cost_usd": round(grand_total, 8),
    }


def print_raw_results_table(results: list[RequestResult]) -> None:
    """Print every individual request result in a tabular format."""
    try:
        from tabulate import tabulate
        _tabulate = tabulate
    except ImportError:
        _tabulate = None

    print("\n" + "=" * 130)
    print("RAW REQUEST RESULTS")
    print("=" * 130)

    headers = [
        "Model", "Prompt (truncated)",
        "In Tok", "Out Tok", "tiktoken In", "tiktoken Out",
        "Latency", "In Cost ($)", "Out Cost ($)", "Total Cost ($)", "Error",
    ]
    rows = []
    for r in results:
        rows.append([
            r.model,
            r.prompt[:45] + "…" if len(r.prompt) > 45 else r.prompt,
            r.input_tokens,
            r.output_tokens,
            r.tiktoken_input,
            r.tiktoken_output,
            f"{r.latency_ms:.0f}ms",
            f"{r.input_cost_usd:.6f}",
            f"{r.output_cost_usd:.6f}",
            f"{r.cost_usd:.6f}",
            r.error or "",
        ])

    if _tabulate:
        print(_tabulate(rows, headers=headers, tablefmt="grid"))
    else:
        col_w = [
            max(len(str(h)), max((len(str(r[i])) for r in rows), default=0))
            for i, h in enumerate(headers)
        ]
        sep = "+-" + "-+-".join("-" * w for w in col_w) + "-+"
        fmt = "| " + " | ".join(f"{{:<{w}}}" for w in col_w) + " |"
        print(sep)
        print(fmt.format(*headers))
        print(sep)
        for row in rows:
            print(fmt.format(*[str(v) for v in row]))
        print(sep)

    print("=" * 130)


def print_report(results: list[RequestResult]) -> dict:
    """Print a tabular cost comparison report and return the report dict."""
    try:
        from tabulate import tabulate
        _tabulate = tabulate
    except ImportError:
        _tabulate = None

    report = build_report(results)

    print("\n" + "=" * 130)
    print("COST COMPARISON REPORT — Track 2A Module 7B")
    print("=" * 130)

    headers = [
        "Model", "Reqs",
        "Avg In Tok", "Avg Out Tok",
        "Avg tiktoken In", "Avg tiktoken Out",
        "Avg Latency",
        "Input Cost ($)", "Output Cost ($)", "Total Cost ($)", "Avg Cost/Test ($)",
    ]
    rows = []
    for m in report["models"]:
        if "error" in m:
            rows.append([m["model"], "ERROR"] + ["-"] * 9)
        else:
            rows.append([
                m["model"],
                m["requests"],
                m["avg_input_tokens"],
                m["avg_output_tokens"],
                m["avg_tiktoken_input"],
                m["avg_tiktoken_output"],
                f"{m['avg_latency_ms']:.0f}ms",
                f"{m['total_input_cost_usd']:.6f}",
                f"{m['total_output_cost_usd']:.6f}",
                f"{m['total_cost_usd']:.6f}",
                f"{m['avg_total_cost_usd']:.6f}",
            ])

    if _tabulate:
        print(_tabulate(rows, headers=headers, tablefmt="grid"))
    else:
        # Manual tabular fallback
        col_w = [
            max(len(str(h)), max((len(str(r[i])) for r in rows), default=0))
            for i, h in enumerate(headers)
        ]
        sep = "+-" + "-+-".join("-" * w for w in col_w) + "-+"
        fmt = "| " + " | ".join(f"{{:<{w}}}" for w in col_w) + " |"
        print(sep)
        print(fmt.format(*headers))
        print(sep)
        for row in rows:
            print(fmt.format(*[str(v) for v in row]))
        print(sep)

    print(f"\nGrand total cost for this run: ${report['grand_total_cost_usd']:.6f}")
    print("=" * 130)

    return report


# ── Entry point ────────────────────────────────────────────────

if __name__ == "__main__":
    results: list[RequestResult] = []

    models_to_test = [
        ("openai",     "gpt-4o-mini"),
        ("ollama",     "phi:latest"),
        ("ollama",     "llama3.2:latest"),
        # ("anthropic",  "claude-haiku-4-5-20251001"),
        # ("anthropic",  "claude-sonnet-4-6"),
        # ("lmstudio",   "mistralai/mistral-7b-instruct-v0.3:2"),
        #("ollama",     "gpt-oss:20b"),
    ]

    print("Running cost comparison across models...")
    for provider, model in models_to_test:
        for prompt in TEST_PROMPTS:
            print(f"  [{provider}] {model} — {prompt[:50]}...")
            if provider == "openai":
                result = run_openai_request(model, prompt)
            elif provider == "anthropic":
                result = run_anthropic_request(model, prompt)
            elif provider == "lmstudio":
                result = run_lmstudio_request(model, prompt)
            elif provider == "ollama":
                if model == "llama3.2:latest":
                    result = run_llama_request(model, prompt)
                else:
                    result = run_phi_request(prompt)
            else:
                continue
            results.append(result)

    print_raw_results_table(results)
    report = print_report(results)

    # Save outputs — path is relative to the repo root, resolved from this file's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(script_dir, "..", "..", "reports")
    os.makedirs(reports_dir, exist_ok=True)

    raw_path     = os.path.join(reports_dir, "cost-comparison.json")
    summary_path = os.path.join(reports_dir, "cost-report-summary.json")

    with open(raw_path, "w") as f:
        json.dump([asdict(r) for r in results], f, indent=2)
    print(f"\nRaw results saved to      {raw_path}")

    with open(summary_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Summary report saved to   {summary_path}")
