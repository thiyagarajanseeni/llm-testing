# AI Test Strategy for Superannuation Member AI Assistant

# Document Control:

Document Status : Draft
Document Owner : AI Test Lead
Business Owner : AI Product Manager
Reviewers : Engineering,Compliance,Legal,Security & Operations Managers
Version : 1.0
Date : 24/09/2026
Application : Superannuation Member AI Assistant
Environment : SIT / UAT
Approvers : AI Test Manager

# 1. Executive Summary
The purpose of this strategy is to establish a risk-based,enterprise-wide testing and assurance framework for LLM-powered AI assistant for
Superannuation - New and Existing Members and provide the following:
 
   1. General Superannuation Information
   2. Fund / Product Information
   3. Investment Information
   4. Retirement Information
   5. Contribution Information
   6. Insurance Information
   7. Member specific information through Authentication
   8. Human-agent escalation
 The strategy validates that solution map to applicable regulatory and organizational control framework by not treating it as one-off activity and
 should be an ongoing AI Assurance Capability

# 2. Application Overview
Application Name:                   Superannuation Member AI Assistant

Feature / Component Under Test:     Superannuation Member AI Assistant

Application Type:                   RAG Backed AI Assistant

Primary Users :                     New and Existing Members

LLM Provider:                       Open AI

Models in Use:                      GPT OSS 120B (Production) & Qwen3 0.6B (SIT)

Model Type:                         Base / Instruction Tuned

Architecture:                       Channel(Web Portal/ Mobile App) Member Interaction --> API / Security Layer --> AI Orchestration Layer --> LLM -->Response  Guardrails --> Observability & Assurance

Deployment Context:                 Customer Facing

Testing Scope:                      Functionality Testing , LLM Behavior Testing, Prompt Testing , RAG Testing ,Knowledge Base Testing , Hallucination Testing , Safety / Security / Privacy (PII) Testing,Cost Testing and Adversarial / Red-Team Testing

# 3. Testing Objectives

The primary objective of testing the LLM powered Superannuation Member AI Assistant is to establish that the solution is accurate,safe,secure,reliable,explainable,compliant and fit for production use while protecting member information and maintaining appropriate boundaries around financial guidance.

 a) Validate functional and conversational correctness across member journeys

 b) Validate LLM factual accuracy,relevance and response consistency

 c) Minimise and detect hallucinations and unsupported claims.

 d) Validate RAG retrieval accuracy and response grounding against approved fund content.

 e) Protect member PII and sensitive financial information.

 f) Test resistance to prompt injection, jailbreaks and adversarial inputs.

 g) Validate general-information vs personalised financial-advice boundaries.

 h) Verify tool/function calling, API authorisation and member-data isolation.

 i) Validate performance, scalability, resilience and cost.

 j) Establish automated LLM regression and production-monitoring controls.


 # 4. Test Approach
   Risk-Based Testing : Prioritise scenarios involving member financial information,investment/retirement questions,PII,regulatory
   obligations and high-impact decisions.

  # 4.1 Techniques to Apply for Evaluation Approach:

   Deterministic Assertion - Promptfoo

   Model-Graded Assertion -  LLM as Judge via Promptfoo / DeepEval

   Red Teaming -  Promptfoo Redteaming + PyRIT - OWASP LLM Top 10

   RAG Evaluation - RAGAS - Faithfulness,Answer Relevance & Context Recall

   Exploratory / Persona Based Testing - Black Box , Structured Session Notes

   Staleness / Data Quality Checks - If RAG - Scan for outdated documents

   Performance / Load Testing - Latency under concurrent users

   Regression Testing - Fixed Bugs Re-Run on Every Model or Prompt Update

  # 4.2 Test Approach by Layer

  Layer 1: Model Level Testing
  
  Validate the underlying LLM independently of the application,RAG pipeline and member-facing interface to establish its baseline capabilities,limitations,safety behaviour and consistency

  Test Area & Focus :

  Hallucination , Bias & Fairness , Prompt Injection , Jailbreak Resistance,Context Understanding,Factual Accuracy , Non-Determinism,Safety,Out-of-scope Handling and Long-Context Behaviour

  Layer 2: Prompt and System Prompt Testing

  Validate that the system prompt, developer instructions, prompt templates and prompt orchestration consistently enforce the AI Assistant's business, safety, privacy, security and financial guidance requirements.

The objective is to ensure that the model behaves according to approved instructions even when users provide ambiguous, adversarial, conflicting or malicious inputs.

Test Area & Focus:

Prompt Injection, Prompt Leakage , System Prompt, Jail Break Resistance , PII Protection , Prompt Versioning , Prompt Regression & Instruction Hierarchy

Layer 3: Integration Testing

Validate that the LLM AI Assistant correctly and securely integrates with RAG components, knowledge repositories, member systems, APIs, orchestration services, authentication, guardrails and external enterprise services.

The objective is to ensure that information flowing between components is accurate, authorised, complete, secure and resilient, and that integration failures do not result in misleading AI responses.

Integration & Test Focus:

Chat UI --> AI API , AI --> Authentication/Identity, AI --> Human Escalation,AI --> Guardrails,RAG --> Vector Database , RAG --> Knowledge Base , Orchestrator --> LLM & Orchestrator --> RAG

Layer 4: End to End Application Testing

Validate the complete member-to-AI-to-response journey across the production-like application ecosystem to demonstrate that the LLM Superannuation AI Assistant delivers an accurate, secure, safe, reliable and usable member experience.

E2E testing validates the interaction of UI, authentication, orchestration, prompts, guardrails, RAG, LLM, member APIs, business rules, escalation and observability as one integrated solution.

End to End Test Scope & Coverage:

Member Access , Member-Specific Queries , RAG,LLM,Guardrails,Security,Escalation,Error Handling & Performance

# 5. Test Scope

5.1 In Scope

Model-Level Testing , Prompt & System Prompt Testing , RAG & Knowledge Testing, Integration Testing , End to End Application Testing, Security & Privacy Testing , Responsible AI & Safety , Performance,Cost & Regression Testing

5.2 Out of Scope

Testing the underlying foundation model's training infrastructure , Development or Retraining of LLM , Testing unrelated fund applications, Business processes unrelated to chatbot & Unapproved external data sources

# 6. Acceptance Criteria

The LLM Superannuation AI Assistant will be considered ready for production release only when the following quality, AI assurance, security, privacy, performance and business acceptance criteria have been satisfied.

1. Functional & Business Acceptance  ≥ 98% of critical business scenarios pass

2. Escalation ≥ 95% correct escalation for defined scenarios

3. LLM Factual Accuracy ≥ 95–98% for approved test dataset

4. LLM Response Consistency ≥ 95% for critical scenarios

5. RAG ≥ 95% retrieval relevance for approved test queries

6. RAG ≥ 95% response grounding against authoritative sources

7. Prompt & System Prompt injection must not bypass controls

8. PII Protection instructions must be maintained

9. PII Leakage and Unauthorised Member-data access should be 0

10. Correct Tool / API function selected for ≥ 99% of critical scenarios

11. Token consumption cost must remain within agreed limits

12. No unacceptable degradation under peak load must meet P95 response time

13. Regression Acceptance - No release may proceed if there is unacceptable degradation in Accuracy , Grounding,Safety,Privacy,Security,Advice Boundary & Escalation

14. Defect Acceptance :
    
    1. Must have Zero Unresolved Critical Defects
    2. High Severity Defects require risk acceptance documented from appropriate team owner before release
    3. Medium / Low Defects may be accepted with Impact / Risk understood & documented with appropriate owner approves the residual risk usually agreed upon Defect Triage meetings

# 7. Test Data Strategy

   The objective of the Test Data Strategy is to provide representative, secure, diverse and controlled test data to validate the LLM Superannuation AI Assistant across functional, AI/LLM, RAG, security, privacy, safety, performance and end-to-end scenarios.

   Test data must enable realistic testing without exposing genuine member information or creating unnecessary privacy, security or financial risk.

   1. Synthetic Dataset - Create controlled synthetic data using Golden Dataset
   2. Golden Dataset - Maintain curated data containing high-value member questions and expected evaluation criteria
   3. RAG Test Data - Include both Positive & Negative
   4. Security and Privacy Test Data
   5. Adversarial Test Data - Prompt Injection , Jail Break Red-Team Dataset
   6. Boundary & Edge Case Test Data
   7. Non Determinism Test Data
   8. Persona Based Test Data

# 8. Tool Chain

The LLM Superannuation AI Assistant will use a layered testing toolchain combining LLM evaluation, RAG validation, security testing, performance testing and production observability.

1. Automated Eval + Assertions - Promptfoo

2. Model Grade Assertions - Promptfoo / Deepeval

3. Redteaming - Promptfoo Redteam / PyRIT

4. RAG Evaluation - RAGAS / TruLens

5. Tracing & Observability - Langfuse

6. Local Model Testing - Ollama

7. CI / CD Integration - GitHub Actions

8. Load / Performance Testing - k6 / Locust

9. Observability - to capture Quality,Safety,Security,Performance & Cost

Also maintain Toolchain governance to have Approved Version,Owner & Purpose


# 9. Test Execution Plan

The Test Execution Plan defines the approach for executing, monitoring and reporting testing for the LLM-powered Superannuation AI Assistant across model, prompt, integration and end-to-end application layers.

Testing will follow a risk-based, shift-left and continuous evaluation approach, with critical AI, security, privacy and financial-guidance scenarios prioritised.

1. Requirements & Risk Assessment 
2. Test Data setup
3. Layer 1 - Model in Isolation
4. Layer 2 - Prompt
5. Layer 3 - Integration
6. Layer 4 - E2E Application
7. Security / Performance
8. Regression Suite
9. Business Validation (UAT)
10. Release Readiness ( Go /No-Go) Decision

From 3 to 8 Test Results / Findings will be published to the project team

# 10. Failure Attribution Framework

The Failure Attribution Framework provides a structured approach for determining the root cause and responsible system layer when the LLM Superannuation AI Assistant produces an incorrect, unsafe, incomplete, misleading or unexpected response.

The objective is to distinguish between failures originating from:

Model → Prompt → Retrieval → Context → Tool/API → Guardrail → Application → Test Data

This prevents incorrect attribution of all AI failures to the LLM itself.

10.1 Bug Report & Failure Tree to be followed

a) Is the retrieved context wrong - RAG / Retrieval Bug (Inspect top-N Chunks , Check Staleness)

b) Context Correct but model reason wrong - Model / Prompt Bug ( Re-run Layer 1 in isolation & inspect system prompt)

c) Tool / Function returned bad output - Integration Bug (Check API Contract,schema,tool implementation)

d) Escalation / Routing Behaved Wrong - Prompt Engineering Bug (Check threshold instructions in system prompt)

e) UI / Parser Mangled the Output - Application Bug (Check output parser,format assumptions,rendering)

Every Bug Reported must include below details:

Attribution Layer in the Title

Model Name , Version & Temperature

Exact Prompt plus Retrieved Context (if its RAG)

Reproduction Rate ie No of runs

Map the Bug to one or more of the 7 Challenges

Severity Critical / High / Medium / Low

Owner Team


# 11. CI / CD Quality Gates

CI/CD Quality Gates ensure that changes to the application, LLM/model, system prompt, RAG configuration, knowledge base, guardrails, tools or APIs do not introduce unacceptable functional, AI, security, privacy, safety or performance risks.

A release must automatically pass defined quality gates before progressing to the next environment.


Gate 1: Build and Conventional QA - Block deployment if critical build, code-quality or security checks fail.

Gate 2: Prompt Regression - No critical behavioural regression compared with the approved baseline.

Gate 3: LLM Evaluation - A model should not be promoted simply because its average evaluation score improves if it introduces a critical failure in a high-risk scenario.

Gate 4: RAG Evaluation - Any outdated document usage blocks deployment.

Gate 5: Security and Privacy - Any critical failure blocks deployment.

Gate 6: AI Safety - High-risk scenarios should have deterministic release gates wherever possible, rather than relying exclusively on an LLM judge.

Gate 7: E2E Regression - 100% of critical member journeys must pass.

Gate 8: Performance - Must remain within approved SLA & Budget

Gate 9: Regression Comparison - Current Version vs Approved Baseline in critical scenarios Metrics should Pass.


# 12. Risks and Mitigations

Identify, assess and mitigate risks that could result in incorrect member information, financial harm, privacy breaches, security compromise, unsafe AI behaviour, regulatory/compliance issues, service disruption or loss of member trust.

Risks should be assessed using:

Likelihood × Impact = Risk Rating

Critical risks require preventive controls, dedicated test scenarios and explicit release gates.

1. LLM Hallucination - The LLM generates plausible but unsupported superannuation information.

Mitigation: RAG with authoritative sources , Golden DataSet , Hig-Risk Human escalation

Likelihood - Medium

Acceptance: Zero unresolved critical hallucinations

2. Member PII Leakage - The AI exposes member information to an unauthorised user or another member.

Mitigation: Strong Authentication, Server-side Authorisation,PII Detection

Likelihood - High

Acceptance: Zero unresolved critical PII Leakage

3. Prompt Injection - A malicious user or document attempts to override system instructions.

Mitigation: Input / Output Guardrails , Red-Team Testing

Likelihood - High

Acceptance: Zero critical security-control bypasses

4. Incorrect RAG Retrieval - The correct knowledge exists but the system retrieves irrelevant or outdated information.

Mitigation: Grounding Checks , Retrieval Evaluation , Document Version Control

Likelihood - Medium

Acceptance: Retrieval and grounding meet approved thresholds.

5. Financial Advice Boundary - The AI provides personalised financial recommendations when it is intended only to provide general information.

Mitigation: Advice-boundary classifier/guardrail , Escalation to appropriate human channels

Likelihood - Medium

Acceptance: No unresolved critical advice-boundary violations


# 13. Reporting

The objective of test reporting is to provide transparent, evidence-based visibility of the AI Assistant's quality, risk, test coverage, defects and release readiness.

Reporting should enable Product, Engineering, QA, Risk, Security, Compliance and AI Governance stakeholders to make informed release decisions.


# 14. Definition of Done

The LLM Superannuation AI Assistant is considered Done when all agreed functional, AI quality, security, privacy, safety, performance, integration and business acceptance criteria have been satisfied, with sufficient evidence to support production release.


# 15. Sign - Off

Formal sign-off confirms that the LLM Superannuation AI Assistant has met the agreed functional, AI quality, security, privacy, safety, performance, business and operational acceptance criteria and that any residual risks have been appropriately assessed and accepted.

Sign-off must be based on documented test evidence rather than test completion alone.


































  
















