
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from langfuse import get_client, observe, propagate_attributes
from langfuse.openai import openai

load_dotenv()

# Validate required credentials
required_vars = [
    "OPENAI_API_KEY",
    "LANGFUSE_SECRET_KEY",
    "LANGFUSE_PUBLIC_KEY",
]

missing = [key for key in required_vars if not os.getenv(key)]
if missing:
    raise ValueError(f"Missing .env variables: {', '.join(missing)}")

# Initialize Langfuse
langfuse = get_client()

# Load system prompt files
PROMPT_DIR = Path(
    "module-7b/03-prompt-management/prompts/portkey"
)

SYSTEM_PROMPT_V1 = (
    PROMPT_DIR / "system_prompt_v1.0.0.txt"
).read_text(encoding="utf-8")

SYSTEM_PROMPT_V2 = (
    PROMPT_DIR / "system_prompt_v1.1.0.txt"
).read_text(encoding="utf-8")


# PART 1: Basic traced LLM call
@observe(name="superannuation-support")
def get_support_response(
    user_message: str,
    prompt_version: str = "v1.0.0",
    session_id: str = "super-session-001",
) -> str:

    system_prompt = (
        SYSTEM_PROMPT_V1
        if prompt_version == "v1.0.0"
        else SYSTEM_PROMPT_V2
    )

    with propagate_attributes(
        session_id=session_id,
        metadata={
            "prompt_version": prompt_version,
            "use_case": "superannuation-chatbot",
        },
        tags=["superannuation", prompt_version],
    ):
        response = openai.chat.completions.create(
            name="superannuation-generation",
            model="gpt-4o-mini",
            temperature=0.1,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )

    return response.choices[0].message.content or ""


# PART 2: Compare prompt V1 and V2
def compare_prompts(user_message: str) -> None:
    print("\n--- Prompt V1 ---")
    print(get_support_response(user_message, "v1.0.0"))

    print("\n--- Prompt V2 ---")
    print(get_support_response(user_message, "v1.1.0"))


# PART 3: Track failures and propagate errors
@observe(name="superannuation-request")
def get_support_response_safe(user_message: str, session_id: str = "super-session-001") -> str:
    try:
        return get_support_response(user_message, "v1.0.0", session_id=session_id)
    except Exception:
        # The exception is recorded by the traced operation.
        # Do not expose internal exception details to the user.
        print("The LLM request failed. Check Langfuse traces.")
        raise


# PART 4: Run example test cases
if __name__ == "__main__":
    test_cases = [
        "What are concessional and non-concessional contributions?",
        "What factors affect early access to superannuation?",
        "I am frustrated and want my superannuation back now.",
    ]

    try:
        for question in test_cases:
            print("\nQuestion:", question)
            answer = get_support_response(question, "v1.0.0", session_id="super-session-001")
            print("Answer:", answer)

        compare_prompts(
            "I am frustrated and want my superannuation back now."
        )

    finally:
        langfuse.flush()
