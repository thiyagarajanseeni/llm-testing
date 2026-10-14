"""
Portkey Lab — Session 3 Hour 4
Track 2A: LLM & GenAI Testing Essentials

Use case: Superannuation Chatbot with observability, version tagging, and automatic provider fallback.

Setup:
1. pip install portkey-ai python-dotenv
2. Sign up at app.portkey.ai
3. Go to Model Catalog → Add Provider → OpenAI (name it: openai-super)
3. → your slug becomes: openai-super
4. Do the same for Anthropic (name it: anthropic-super)
5. Add to .env:
PORTKEY_API_KEY=pk-...
OPENAI_SLUG=openai-super      ← the slug you chose in Model Catalog
ANTHROPIC_SLUG=anthropic-super
"""

import os
from dotenv import load_dotenv
from portkey_ai import Portkey

load_dotenv()

PORTKEY_API_KEY  = os.getenv("PORTKEY_API_KEY")
OPENAI_SLUG      = os.getenv("OPENAI_SLUG", "openai-super")
ANTHROPIC_SLUG   = os.getenv("ANTHROPIC_SLUG", "anthropic-super")

SYSTEM_PROMPT_V1 = open("module-7b/03-prompt-management/prompts/portkey/system_prompt_v1.0.0.txt").read()
SYSTEM_PROMPT_V2 = open("module-7b/03-prompt-management/prompts/portkey/system_prompt_v1.1.0.txt").read()

# ─── PART 1: Basic client — just Portkey API key, no virtual key needed ──────

client = Portkey(api_key=PORTKEY_API_KEY)

# Model format: @<your-slug>/<model-name>
# Slug comes from your Model Catalog provider name in the dashboard


# ─── PART 2: Make a basic call and see it in the dashboard ───────────────────

def get_support_response(user_message: str, prompt_version: str = "v1.0.0") -> str:
    """Basic call — every request auto-logged in Portkey dashboard."""
    system_prompt = SYSTEM_PROMPT_V1 if prompt_version == "v1.0.0" else SYSTEM_PROMPT_V2

    response = client.chat.completions.create( # portkey client is called from line 34
        model=f"@{OPENAI_SLUG}/gpt-4o-mini",   # @slug/model-name
        temperature=0.1,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message}
        ]
    )
    return response.choices[0].message.content


# ─── PART 3: Tag by prompt version — filter in dashboard ─────────────────────

def get_response_tagged(user_message: str, prompt_version: str = "v1.0.0") -> str:
    """
    Adds metadata + trace_id so you can filter by prompt version in dashboard.
    Go to: app.portkey.ai → Logs → Filter → metadata.prompt_version = v1.0.0
    """
    system_prompt = SYSTEM_PROMPT_V1 if prompt_version == "v1.0.0" else SYSTEM_PROMPT_V2

    tagged_client = Portkey(
        api_key=PORTKEY_API_KEY,
        metadata={
            "prompt_version":   prompt_version,
            "use_case":        "superannuation chatbot",
            "session":         "track-2a-s3h4",
        },
        trace_id=f"support-{prompt_version}"   # groups related calls in one trace
    )

    response = tagged_client.chat.completions.create(
        model=f"@{OPENAI_SLUG}/gpt-4o-mini",
        temperature=0.1,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message}
        ]
    )
    return response.choices[0].message.content


# ─── PART 4: Fallback — OpenAI fails → automatically use Claude ──────────────

def get_response_with_fallback(user_message: str) -> str:
    """
    If OpenAI fails (429, 500, 503), Portkey automatically retries with Claude.
    Your app never sees the error.

    Model format for fallback targets: @slug/model-name
    """
    fallback_client = Portkey(
        api_key=PORTKEY_API_KEY,
        config={
            "strategy": {
                "mode": "fallback",
                "on_status_codes": [404,429, 500, 503]
            },
            "targets": [
                {
                    "override_params": {
                        "model": f"@{OPENAI_SLUG}/gpt-4o-mini"    # try first
                    }
                },
                {
                    "override_params": {
                        "model": f"@{ANTHROPIC_SLUG}/claude-sonnet-4-6"  # fallback
                    }
                }
            ]
        }
    )

    response = fallback_client.chat.completions.create(
        temperature=0.1,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_V1},
            {"role": "user",   "content": user_message}
        ]
    )
    return response.choices[0].message.content


# ─── PART 5: Retry on rate limit ─────────────────────────────────────────────

def get_response_with_retry(user_message: str) -> str:
    """Automatically retries up to 3 times on 429 (rate limit) errors."""
    retry_client = Portkey(
        api_key=PORTKEY_API_KEY,
        config={
            "retry": {
                "attempts": 3,
                "on_status_codes": [429, 503]
            }
        }
    )

    response = retry_client.chat.completions.create(
        model=f"@{OPENAI_SLUG}/gpt-4o-mini",
        temperature=0.1,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_V1},
            {"role": "user",   "content": user_message}
        ]
    )
    return response.choices[0].message.content


# ─── MAIN: Run all parts in sequence ─────────────────────────────────────────

if __name__ == "__main__":
    test_cases = [
        "I'm considering making additional contributions to my super fund before retirement—what factors and tax caps do I need to take into account?",
        "What is the difference between a pre-tax (concessional) and post-tax (non-concessional) super contribution?",
        "This is ridiculous! I want my superannuation back NOW.",
    ]


    # ── Part 2: Basic logging ─────────────────────────────────────────────────
    print("=" * 60)
    print("PART 2 — Basic calls (check dashboard → Logs)")
    print("=" * 60)
    for question in test_cases:
        answer = get_support_response(question, prompt_version="v1.0.0")
        print(f"Q: {question}")
        print(f"A: {answer}\n")

    # ── Part 3: Compare versions with tags ────────────────────────────────────
    print("=" * 60)
    print("PART 3 — Tagged calls (filter by metadata.prompt_version in dashboard)")
    print("=" * 60)
    angry = "This is ridiculous! I want my superannuation back NOW."

    print("--- v1.0.0 (Formal) ---")
    print(get_response_tagged(angry, prompt_version="v1.0.0"))

    print("\n--- v1.1.0 (Empathy-first) ---")
    print(get_response_tagged(angry, prompt_version="v1.1.0"))

    # ── Part 4: Fallback ──────────────────────────────────────────────────────
    print("=" * 60)
    print("PART 4 — Fallback (OpenAI → Claude if OpenAI fails)")
    print("=" * 60)
    print(get_response_with_fallback("What is your refund policy?"))
    print("(check dashboard → Logs to see which provider was used)")

    # ── Part 5: Retry ─────────────────────────────────────────────────────────
    print("=" * 60)
    print("PART 5 — Retry (auto-retries 3x on rate limit)")
    print("=" * 60)
    print(get_response_with_retry("How do I make additional contributions to my super fund?"))
