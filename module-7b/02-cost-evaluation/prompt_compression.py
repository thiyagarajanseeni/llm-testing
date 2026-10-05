"""
Prompt Compression
=====================================================================
Measure token savings from four prompt compression techniques:
1. Remove Redundant Context  (15–30% savings)
2. Bullets over Paragraphs   (20–40% savings)
3. Minimal Few-Shot          (10–25% savings)
4. Dynamic Context           (30–50% savings)

HOW IT WORKS:
    For each technique, four before/after prompt pairs are defined.
    Token counts are measured with tiktoken (cl100k_base, the tokeniser
    used by GPT-4 / Claude approximation).  Results are printed as a
    table and saved to compression_report.md.

PREREQUISITES:
    pip install tiktoken tabulate

INSTRUCTIONS:
    1. Run the script as-is to see baseline results:
    python prompt_compression.py
    2. Re-run and observe how your custom prompts compare.
"""

import textwrap
from tabulate import tabulate
import tiktoken

# ── TOKEN COUNTER ──────────────────────────────────────────────────────────────

def count_tokens(text: str, model: str = "cl100k_base") -> int:
    enc = tiktoken.get_encoding(model)
    return len(enc.encode(text))


# ══════════════════════════════════════════════════════════════════════════════
#  TECHNIQUE 1 — REMOVE REDUNDANT CONTEXT
#  Goal: strip instructions already implied by the role/task.
#  Test: does removing the text change the output? If not, cut it.
#  Expected savings: 15–30 %
# ══════════════════════════════════════════════════════════════════════════════

REDUNDANT_CONTEXT_PAIRS = [
    # Prompt compression example by reducing verbose instructions into concise rules
    {
        "label": "Superannuation assistant role",
        "before": textwrap.dedent("""\
            You are a helpful superannuation assistant. Your role is to answer
            questions from Australian superannuation members. You should provide
            accurate, clear and concise information based only on the supplied
            knowledge base. If the information is not available in the supplied
            context, do not make up an answer. Instead, tell the member that you
            don't have enough information and recommend that they contact the fund.
            You should never provide financial advice.

            Customer message: My superannuation account balance.
            
            """),
        
        "after": textwrap.dedent("""\
            You are an Australian superannuation assistant.
            Rules:
            1. Use supplied context only.
            2. Be accurate, clear and concise.
            3. If context is insufficient, say so; never guess.
            4. Do not provide personalized financial advice.
            5. Direct members to the fund when appropriate.

            Customer message: My superannuation account balance.
            
            """),
    },
    
    # Prompt compression example for summarization
    {
    "label": "Superannuation document summarization",

    "before": textwrap.dedent("""\
        You are a helpful superannuation assistant. Your role is to
        summarize information from Australian superannuation documents
        for members. You should provide an accurate, clear and concise
        summary that captures the key information from the supplied
        document. Do not introduce information that is not present in
        the source document. Preserve important dates, amounts, eligibility
        conditions, fees and limitations. If information is unclear or
        missing, state that explicitly rather than making assumptions.
        The summary should be easy for a superannuation member to understand.
        Do not provide personalized financial advice.

        Document:
        {document}
    """),

    "after": textwrap.dedent("""\
        You are an Australian superannuation summarization assistant.

        Rules:
        1. Summarize the supplied document only.
        2. Preserve key facts, dates, amounts, conditions, fees and limitations.
        3. Never invent or infer missing information.
        4. State clearly when information is missing or unclear.
        5. Use clear, concise member-friendly language.
        6. Do not provide personalized financial advice.

        Document:
        {document}
    """),
    },
        
]

# ══════════════════════════════════════════════════════════════════════════════
#  TECHNIQUE 2 — BULLETS OVER PARAGRAPHS
#  Goal: replace verbose instructions with tight bullet lists.
#  LLMs parse bullets as well as or better than paragraphs.
#  Expected savings: 20–40 %
# ══════════════════════════════════════════════════════════════════════════════

BULLETS_OVER_PARAGRAPHS_PAIRS = [
    {
    "label": "Superannuation joining guidance",

    "before": textwrap.dedent("""\
        You are a helpful superannuation assistant. Your role is to
        help Australian members understand the process of joining a
        superannuation fund. Provide accurate, clear and concise
        information based only on the supplied knowledge base.
        Explain the required steps, eligibility requirements,
        documents and information needed to join the fund. If the
        information is unavailable, do not make assumptions or
        invent an answer. Direct the member to the fund when
        appropriate. Do not provide personalized financial advice.

        Present the joining information using clear bullet points
        rather than long paragraphs.

        Customer message:
        I want to join the superannuation fund. What do I need to do?
    """),

    "after": textwrap.dedent("""\
        You are an Australian superannuation joining assistant.

        Rules:
        - Use bullet points, not paragraphs.
        - Explain joining steps clearly.
        - Include eligibility, required documents and information.
        - Use supplied context only.
        - Never invent missing information.
        - Direct members to the fund when appropriate.
        - Do not provide personalized financial advice.

        Customer message:
        I want to join the superannuation fund. What do I need to do?
    """),
    },   
]


# ══════════════════════════════════════════════════════════════════════════════
#  TECHNIQUE 3 — MINIMAL FEW-SHOT
#  Goal: use 1-shot examples instead of 3-shot.
#  1-shot often matches 3-shot accuracy at lower cost.
#  Expected savings: 10–25 %
# ══════════════════════════════════════════════════════════════════════════════

MINIMAL_FEW_SHOT_PAIRS = [
    {
    "label": "Superannuation sentiment classification",

    "before": textwrap.dedent("""\
        Classify the sentiment of each member message as Positive,
        Negative, or Neutral.

        Member: "Thanks, that was really helpful."
        Sentiment: Positive

        Member: "I've been trying to access my super account for days
        and nobody has helped me."
        Sentiment: Negative

        Member: "How can I change my contribution rate?"
        Sentiment: Neutral

        Member: "My super account keeps logging me out."
        Sentiment:
    """),

    "after": textwrap.dedent("""\
        Classify sentiment as Positive, Negative, or Neutral.

        "Thanks, that was really helpful." → Positive
        "I've been trying to access my super account for days and
        nobody has helped me." → Negative
        "How can I change my contribution rate?" → Neutral

        "My super account keeps logging me out." →
    """),
    },
    
    {
    "label": "Superannuation JSON extraction",

    "before": textwrap.dedent("""\
        Extract the member's intent, contribution amount and frequency
        from each superannuation member message and return the result
        as valid JSON.

        Only extract information explicitly provided by the member.
        Do not infer or invent missing information. If a value is not
        available, return null.

        Input: "I want to increase my super contributions to $500 a month."
        Output: {
            "intent": "change_contribution",
            "amount": 500,
            "frequency": "monthly"
        }

        Input: "Can I make an extra $1,000 contribution this year?"
        Output: {
            "intent": "additional_contribution",
            "amount": 1000,
            "frequency": "annual"
        }

        Input: "How do I change my contribution rate?"
        Output:
    """),

    "after": textwrap.dedent("""\
        Extract intent, amount and frequency as JSON.

        Rules:
        - Extract explicit information only.
        - Missing values → null.
        - Never infer or invent.
        - JSON only.

        "I want to increase my super contributions to $500 a month."
        → {
            "intent": "change_contribution",
            "amount": 500,
            "frequency": "monthly"
        }

        "How do I change my contribution rate?"
        →
    """),
    },
    
    {
    "label": "Superannuation chatbot intent classification",

    "before": textwrap.dedent("""\
        You are an AI assistant for an Australian superannuation fund.
        Classify each member message into the most appropriate intent.
        Use only the approved intent categories. Do not invent an intent.

        Intent categories:
        - balance
        - contributions
        - investment
        - withdrawal
        - retirement
        - fees
        - insurance
        - account_access
        - joining
        - other

        Member: "How much money do I have in my super?"
        Intent: balance

        Member: "How do I increase my salary sacrifice?"
        Intent: contributions

        Member: "I want to change my investment option."
        Intent: investment

        Member: "I can't log into my account."
        Intent: account_access

        Member: "How do I join the fund?"
        Intent:
    """),

    "after": textwrap.dedent("""\
        Classify the member message into one intent:

        balance | contributions | investment | withdrawal | retirement |
        fees | insurance | account_access | joining | other

        "How much money do I have in my super?" → balance
        "How do I increase my salary sacrifice?" → contributions
        "I want to change my investment option." → investment
        "I can't log into my account." → account_access

        "How do I join the fund?" →
    """),
    },
    # Member - Response Generation Task
    {
    "label": "Superannuation chatbot response generation",

    "before": textwrap.dedent("""\
        Generate a clear, concise and member-friendly response to each
        superannuation member question. Answer using only the information
        provided in the knowledge context. Do not invent facts, fees,
        eligibility rules or account information. If the answer cannot be
        determined from the supplied context, clearly state that and direct
        the member to the fund where appropriate. Do not provide personalised
        financial advice.

        Question: How can I update my personal details?
        Response: You can update your personal details through the approved
        member account channel. If you need assistance, please contact the
        fund.

        Question: How can I make additional contributions?
        Response: You can make additional contributions using the options
        available through the fund. Please check the applicable fund
        information for the available methods and requirements.

        Question: I can't log into my account. What should I do?
        Response:
    """),

    "after": textwrap.dedent("""\
        Answer the member clearly and concisely.

        Rules:
        - Use supplied context only.
        - Never invent facts or account information.
        - If information is unavailable, say so and direct the member
        to the fund.
        - Do not provide personalised financial advice.

        "How can I update my personal details?" →
        "How can I make additional contributions?" →
        "I can't log into my account. What should I do?" →
    """),
    },
]

# ══════════════════════════════════════════════════════════════════════════════
#  TECHNIQUE 4 — DYNAMIC CONTEXT
#  Goal: inject only the schema/tools needed for this specific request,
#        not the entire config.
#  Expected savings: 30–50 %
# ══════════════════════════════════════════════════════════════════════════════

DYNAMIC_CONTEXT_PAIRS = [
    {
        "label": "Superannuation tool selection",
        "before": textwrap.dedent("""\
            You are a superannuation AI assistant with access to:
            - get_member_profile(member_id)
            - get_account_balance(member_id)
            - get_contribution_history(member_id)
            - get_investment_options(member_id)
            - get_insurance_details(member_id)
            - get_beneficiary_details(member_id)
            - get_transaction_history(member_id)
            - get_statement(member_id, date_range)
            - get_retirement_information(member_id)
            - create_service_request(member_id, request_type)

            Use the minimum tools required to answer the member's question.

            Member question:
            How much is in my super account?
        """),
        "after": textwrap.dedent("""\
            Available tool:
            - get_account_balance(member_id)

            Member question:
            How much is in my super account?
        """),
    },

    {
        "label": "Superannuation RAG context compression",
        "before": textwrap.dedent("""\
            Use the approved superannuation knowledge base to answer
            the member's question.

            [Contributions]
            Members may make voluntary contributions subject to applicable
            rules and contribution limits.

            [Investment]
            Members can select from the investment options available
            under their superannuation product.

            [Insurance]
            Eligible members may have insurance cover associated with
            their superannuation account.

            [Retirement]
            Access to super is subject to preservation rules and
            applicable conditions of release.

            [Fees]
            Fees may apply depending on the member's product and
            investment option.

            [Account Access]
            Members can view their account balance through the
            approved member portal.

            Member question:
            How can I check my super balance?
        """),
        "after": textwrap.dedent("""\
            Relevant knowledge:

            [Account Access]
            Members can view their account balance through the
            approved member portal.

            Member question:
            How can I check my super balance?
        """),
    },

    {
        "label": "Superannuation member context",
        "before": textwrap.dedent("""\
            Member information:
            - Member ID
            - Name
            - Date of birth
            - Email
            - Phone
            - Address
            - Employer
            - Employment status
            - Account balance
            - Contribution rate
            - Contribution history
            - Investment option
            - Insurance cover
            - Beneficiaries
            - Transaction history
            - Account status

            Member question:
            What investment option am I currently invested in?
        """),
        "after": textwrap.dedent("""\
            Relevant member information:
            - Investment option

            Member question:
            What investment option am I currently invested in?
        """),
    },

    {
        "label": "Superannuation joining context",
        "before": textwrap.dedent("""\
            Use the following approved information to answer the member.

            [Joining]
            Members can join the fund through the approved application
            process.

            [Eligibility]
            Eligibility depends on the member's circumstances and
            applicable fund rules.

            [Documents]
            Identification and other required information may be
            required during the joining process.

            [Contributions]
            Members can make contributions using the available
            contribution methods.

            [Investment]
            Members can select from available investment options.

            [Insurance]
            Eligible members may have insurance options.

            Member question:
            How do I join the superannuation fund?
        """),
        "after": textwrap.dedent("""\
            Relevant knowledge:

            [Joining]
            Members can join the fund through the approved application
            process.

            [Eligibility]
            Eligibility depends on the member's circumstances and
            applicable fund rules.

            [Documents]
            Identification and other required information may be
            required during the joining process.

            Member question:
            How do I join the superannuation fund?
        """),
    },
]


# ══════════════════════════════════════════════════════════════════════════════
#  MEASUREMENT & REPORTING
# ══════════════════════════════════════════════════════════════════════════════

TECHNIQUES = [
    ("Remove Redundant Context",  "15–30 %",  REDUNDANT_CONTEXT_PAIRS),
    ("Bullets over Paragraphs",   "20–40 %",  BULLETS_OVER_PARAGRAPHS_PAIRS),
    ("Minimal Few-Shot",          "10–25 %",  MINIMAL_FEW_SHOT_PAIRS),
    ("Dynamic Context",           "30–50 %",  DYNAMIC_CONTEXT_PAIRS),
]


def analyse_pairs(pairs: list[dict]) -> list[dict]:
    results = []
    for p in pairs:
        before = count_tokens(p["before"])
        after  = count_tokens(p["after"])
        saved  = before - after
        pct    = (saved / before * 100) if before else 0
        results.append({
            "label":  p["label"],
            "before": before,
            "after":  after,
            "saved":  saved,
            "pct":    pct,
        })
    return results


def build_table_rows(results: list[dict]) -> list[list]:
    rows = []
    for r in results:
        rows.append([
            r["label"],
            r["before"],
            r["after"],
            r["saved"],
            f"{r['pct']:.1f} %",
        ])
    # Totals row
    tot_before = sum(r["before"] for r in results)
    tot_after  = sum(r["after"]  for r in results)
    tot_saved  = sum(r["saved"]  for r in results)
    tot_pct    = (tot_saved / tot_before * 100) if tot_before else 0
    rows.append(["TOTAL", tot_before, tot_after, tot_saved, f"{tot_pct:.1f} %"])
    return rows


HEADERS = ["Prompt", "Tokens (before)", "Tokens (after)", "Saved", "% Reduction"]


def print_report(technique_name: str, expected_range: str,
                 results: list[dict]) -> None:
    rows = build_table_rows(results)
    print(f"\n{'═' * 72}")
    print(f"  {technique_name}  (expected savings: {expected_range})")
    print(f"{'═' * 72}")
    print(tabulate(rows, headers=HEADERS, tablefmt="github"))


def save_markdown_report(all_results: list[tuple]) -> None:
    lines = [
        "# Prompt Compression Report",
        "",
        "Generated by `prompt_compression.py`  ",
        "Tokens counted with `tiktoken` (`cl100k_base`).",
        "",
    ]

    grand_before = grand_after = 0

    for technique_name, expected_range, results in all_results:
        lines += [
            f"## {technique_name}",
            f"**Expected savings:** {expected_range}",
            "",
        ]
        rows = build_table_rows(results)
        lines.append(tabulate(rows, headers=HEADERS, tablefmt="github"))
        lines.append("")

        grand_before += sum(r["before"] for r in results)
        grand_after  += sum(r["after"]  for r in results)

    grand_saved = grand_before - grand_after
    grand_pct   = (grand_saved / grand_before * 100) if grand_before else 0

    lines += [
        "---",
        "## Overall Summary",
        "",
        tabulate(
            [["All techniques combined",
        grand_before, grand_after, grand_saved, f"{grand_pct:.1f} %"]],
            headers=HEADERS,
            tablefmt="github",
        ),
        "",
        "---",
        "_Add your own prompts in the `── STUDENT PROMPTS ──` sections of_",
        "_`prompt_compression.py` and re-run to see your personal savings._",
    ]

    report_path = "compression_report.md"
    with open(report_path, "w",encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nReport saved to {report_path}")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    print("\nPrompt Compression — Token Analysis")
    print("====================================")

    all_results = []
    for technique_name, expected_range, pairs in TECHNIQUES:
        results = analyse_pairs(pairs)
        print_report(technique_name, expected_range, results)
        all_results.append((technique_name, expected_range, results))

    # Overall totals
    grand_before = sum(r["before"] for _, _, rs in all_results for r in rs)
    grand_after  = sum(r["after"]  for _, _, rs in all_results for r in rs)
    grand_saved  = grand_before - grand_after
    grand_pct    = (grand_saved / grand_before * 100) if grand_before else 0

    print(f"\n{'═' * 72}")
    print("  OVERALL SUMMARY (all techniques)")
    print(f"{'═' * 72}")
    print(tabulate(
        [["All techniques combined",
        grand_before, grand_after, grand_saved, f"{grand_pct:.1f} %"]],
        headers=HEADERS,
        tablefmt="github",
    ))

    save_markdown_report(all_results)


if __name__ == "__main__":
    main()
