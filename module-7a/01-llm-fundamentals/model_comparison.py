import os
import sys
import time
import json
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DEFAULT_PROMPT = (
    "Explain API testing to a junior developer in 3 bullet points. Be concise."
)

PROVIDERS = []

def get_openai_response(prompt: str) -> dict:
    from openai import OpenAI
    key = os.getenv("OPENAI_API_KEY")
    if not key or "..." in key:
        return None
    client = OpenAI(api_key=key)
    start = time.time()
    r = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return {
        "provider": "OpenAI",
        "model": "gpt-4o-mini",
        "response": r.choices[0].message.content,
        "latency_ms": round((time.time() - start) * 1000),
        "tokens": r.usage.total_tokens if r.usage else None
    }

def get_anthropic_response(prompt: str) -> dict:
    import anthropic
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key or "..." in key:
        return None
    client = anthropic.Anthropic(api_key=key)
    start = time.time()
    msg = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    return {
        "provider": "Anthropic",
        "model": "claude-3-haiku",
        "response": msg.content[0].text,
        "latency_ms": round((time.time() - start) * 1000),
        "tokens": msg.usage.input_tokens + msg.usage.output_tokens
    }

def get_gemini_response(prompt: str) -> dict:
    import google.generativeai as genai
    key = os.getenv("GOOGLE_API_KEY")
    if not key or "..." in key:
        return None
    genai.configure(api_key=key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    start = time.time()
    r = model.generate_content(prompt)
    return {
        "provider": "Google Gemini",
        "model": "gemini-1.5-flash",
        "response": r.text,
        "latency_ms": round((time.time() - start) * 1000),
        "tokens": None
    }

def get_ollama_response(prompt: str) -> dict:
    from openai import OpenAI
    model = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434") + "/v1"
    client = OpenAI(base_url=base_url, api_key="ollama")
    start = time.time()
    r = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return {
        "provider": "Ollama (Local)",
        "model": model,
        "response": r.choices[0].message.content,
        "latency_ms": round((time.time() - start) * 1000),
        "tokens": None
    }

def get_lm_studio_response(prompt: str) -> dict:
    from openai import OpenAI
    base_url = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
    model = os.getenv("LM_STUDIO_MODEL", "local-model")
    client = OpenAI(base_url=base_url, api_key="lm-studio")
    start = time.time()
    r = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return {
        "provider": "LM Studio (Local)",
        "model": model,
        "response": r.choices[0].message.content,
        "latency_ms": round((time.time() - start) * 1000),
        "tokens": None
    }


PROVIDER_FNS = [
    ("OpenAI",      get_openai_response),
    # ("Anthropic",   get_anthropic_response),
    # # ("Gemini",      get_gemini_response),
    # ("Ollama",      get_ollama_response),
    # ("LM Studio",   get_lm_studio_response),
]


def run_comparison(prompt: str, runs: int = 1) -> list:
    results = []
    print(f"\n{'='*60}")
    print(f"  PROMPT: {prompt[:80]}{'...' if len(prompt)>80 else ''}")
    print(f"  RUNS PER PROVIDER: {runs}")
    print(f"{'='*60}\n")

    for name, fn in PROVIDER_FNS:
        provider_results = []
        for run_num in range(runs):
            try:
                result = fn(prompt)
                if result is None:
                    if run_num == 0:
                        print(f"  [SKIP] {name} — API key not configured")
                    break
                provider_results.append(result)
                latency = result['latency_ms']
                preview = result['response'][:120].replace('\n', ' ')
                if run_num == 0:
                    print(f"  [✓] {name} ({result['model']}) — {latency}ms")
                    print(f"      {preview}{'...' if len(result['response'])>120 else ''}")
                    if runs > 1:
                        print(f"      (run 1/{runs} complete, checking consistency...)")
                else:
                    print(f"      run {run_num+1}/{runs} — {latency}ms")
            except Exception as e:
                if run_num == 0:
                    print(f"  [✗] {name} — {str(e)[:80]}")
                break

        if provider_results:
            entry = {
                "provider": provider_results[0]["provider"],
                "model": provider_results[0]["model"],
                "runs": provider_results,
                "avg_latency_ms": round(sum(r["latency_ms"] for r in provider_results) / len(provider_results)),
                "consistent": len(set(r["response"] for r in provider_results)) == 1 if runs > 1 else None
            }
            results.append(entry)
        print()

    return results


def save_report(prompt: str, results: list, runs: int):
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = reports_dir / f"cross_model_{timestamp}.md"

    lines = [
        "# Cross-Model Comparison Report",
        f"\n**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  ",
        f"**Runs per provider:** {runs}  ",
        f"\n## Prompt\n\n> {prompt}\n",
        "## Results\n"
    ]

    for r in results:
        lines.append(f"### {r['provider']} ({r['model']})\n")
        lines.append(f"- **Avg Latency:** {r['avg_latency_ms']}ms")
        if r['consistent'] is not None:
            lines.append(f"- **Consistent across {runs} runs:** {'Yes ✓' if r['consistent'] else 'No ✗'}")
        lines.append(f"\n**Response (run 1):**\n\n```\n{r['runs'][0]['response']}\n```\n")

    lines.append("## Observations\n")
    lines.append("Fill in your notes here — refer to the cross-model-observations section of the setup guide.\n")
    lines.append("\n| Dimension | Observation |\n|-----------|-------------|")
    lines.append("| Latency ranking |  |")
    lines.append("| Best instruction following |  |")
    lines.append("| Most verbose |  |")
    lines.append("| Most concise |  |")
    lines.append("| Most consistent |  |")
    lines.append("| Would you trust for production? |  |")

    report_path.write_text("\n".join(lines))
    print(f"\n📄 Report saved: {report_path}")
    return report_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cross-model comparison tool")
    parser.add_argument("--prompt", type=str, default=DEFAULT_PROMPT)
    parser.add_argument("--runs", type=int, default=1, help="Runs per provider (use 3 to check consistency)")
    args = parser.parse_args()

    results = run_comparison(args.prompt, args.runs)

    if not results:
        print("No providers returned results. Run verify_setup.py first.")
        sys.exit(1)

    save_report(args.prompt, results, args.runs)

    # Summary
    print("\n" + "="*60)
    print("  SUMMARY")
    print("="*60)
    sorted_results = sorted(results, key=lambda r: r["avg_latency_ms"])
    for i, r in enumerate(sorted_results):
        rank = f"#{i+1}"
        consistency = ""
        if r["consistent"] is not None:
            consistency = "  consistent ✓" if r["consistent"] else "  inconsistent ✗"
        print(f"  {rank}  {r['provider']:<22} {r['avg_latency_ms']}ms{consistency}")
    print()