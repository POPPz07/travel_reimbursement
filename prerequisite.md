JD for HCL tech company:
Job Summary
We are seeking a highly skilled Generative AI Developer to join the AI Store product team as an embedded AI expert within a squad of 7–10 traditional software engineers (backend, frontend, and full-stack developers). This is not a conventional developer role — the ideal candidate will serve as the squad's single point of contact for all things AI and Generative AI: hands-on developer, internal trainer, technical guide, and implementation lead.
Working under the guidance of the Generative AI Architect, the developer will translate architectural decisions into production-grade implementations, uplift team capabilities through training and mentorship, and independently drive the development of complex GenAI and Agentic AI features for enterprise-grade solutions.

Key Responsibilities

Act as the squad's embedded GenAI expert and single point of contact for all AI/GenAI-related decisions, implementation, and guidance.
Design, develop, and optimize production-grade GenAI and Agentic AI applications, services, and pipelines in Python.
Work under the GenAI Architect to interpret architectural blueprints and implement complex GenAI components, ensuring alignment with enterprise standards.
Integrate Large Language Models (LLMs) — including OpenAI, Azure OpenAI, Hugging Face, Anthropic, and Cohere — into enterprise workflows and products.
Design and implement Retrieval-Augmented Generation (RAG) pipelines, multi-agent orchestration systems, and Agentic AI flows.
Build, maintain, and evolve APIs, automation scripts, and AI pipelines on the AIForce platform.
Train and mentor squad members (backend, frontend, full-stack developers) on GenAI concepts, tools, frameworks, and best practices — enabling the broader team to actively contribute to AI feature development.
Conduct LLM performance evaluation, prompt optimization, and model fine-tuning as required.
Champion Safe AI, AI governance, and responsible AI development practices across the squad.
Monitor, test, and troubleshoot deployed GenAI models and services in production environments.
Stay current with emerging GenAI frameworks, LLM advances, and industry trends; proactively assess and introduce relevant innovations.
Required Skills & Qualifications

Strong proficiency in Python (2+ years), including experience building production-grade applications.
Proven hands-on experience with Agentic AI and GenAI frameworks: LangChain, LlamaIndex, Hugging Face Transformers, AutoGen, CrewAI, or similar.
Demonstrated experience designing and implementing RAG architectures, vector search pipelines, and multi-agent systems.
Familiarity with LLM APIs: OpenAI, Azure OpenAI, Anthropic, Cohere, and open-source models.
Experience with vector databases (e.g., Pinecone, Weaviate, Azure AI Search, FAISS, Chroma).
Strong knowledge of prompt engineering, chain-of-thought techniques, and LLM evaluation/observability methods.
Understanding of LLM fine-tuning approaches (RLHF, PEFT, LoRA) — practical experience will be added advantage.
Knowledge of Safe AI principles, AI security, AI governance frameworks, and responsible AI development practices.
Hands-on experience with developing AI solutions on any cloud platform
Solid software engineering fundamentals: Git, CI/CD pipelines, automated testing, API design.
Effective communication and mentoring skills — able to explain complex AI concepts to non-AI developers clearly.
Nice to Have

Experience with MLOps tooling (MLflow, Azure ML Pipelines, or equivalent).
Exposure to multimodal models (vision-language models, speech-to-text integration).
Prior experience working as an AI champion or tech lead within a cross-functional product team.
Familiarity with enterprise AI governance and compliance frameworks.


I had applied for this role at HCL tech and got assessment to submit before an internview.


Below are the assignment details, read those very carefully.
Based on these instructions we have to create a travel reimbursement approval agent.

AI Developer Candidate Assignment
Travel Reimbursement Approval Agent
Purpose: Assess hands-on ability to build a practical GenAI and Agentic AI solution, not just describe one. Business scenario
Review employee travel reimbursement claims against policy, receipts, limits, and approval rules. Build objective
Create a working AI-assisted agent that evaluates a claim and returns a structured recommendation. Expected effort
Designed to be completed in 2-3 days using free-tier, open-source, or local tools. Expected outcome
Runnable prototype, sample inputs/outputs, and a short explanation of design choices and trade-offs.
1. Assignment Overview
Build a working prototype of a Travel Reimbursement Approval Agent. The agent should accept a claim, use policy/rule context and tools, and produce a clear decision such as Approve, Partially Approve, Reject, or Manual Review. The emphasis is on clean implementation, GenAI reasoning, tool usage, and reliability in ambiguous cases.
2. Scope and Constraints

Keep the solution practical and lightweight; do not build a production-grade enterprise system.

Use Python, JavaScript/TypeScript, or another language you are comfortable with.

You may use LangChain, LlamaIndex, Semantic Kernel, CrewAI, AutoGen, direct LLM APIs, or an equivalent lightweight approach.

Use mock/sample policy documents, claims, receipts, and approval rules. No real employee or company data should be used.

A simple CLI, notebook, API endpoint, or small UI is sufficient if the demo is easy to run and understand.
3. Minimum Functional Expectations

Claim intake: Accept a reimbursement claim from JSON, CSV, form input, or API request.

Context grounding: Retrieve or reference relevant policy/rule context before making a decision.

Tool/function usage: Use at least two meaningful tools or functions, such as policy lookup, receipt completeness check, per-diem/limit checker, duplicate detector, approval threshold check, or output validator.

GenAI/Agentic workflow: Show how the LLM decides when to use tools, combines results, and handles missing or conflicting information.

Structured output: Return consistent JSON or table output with decision, approved amount, deductions/rejected amount, missing documents, policy references or rule basis, confidence, and short explanation.

Manual review handling: Route uncertain, incomplete, or policy-exception cases to Manual Review rather than forcing a decision.
4. Suggested Demo Inputs

A short travel policy file in Markdown, TXT, PDF, or JSON.

A small limit table, approval matrix, or category eligibility file.

Three to five sample reimbursement claims covering approved, partially approved, rejected, and manual review cases.

Optional mock receipts or receipt metadata, such as date, amount, category, vendor, and attachment status.
5. Deliverables

Runnable code: A Git repository, zip file, or shared folder with source code and sample data.

README: Setup steps, required environment variables, how to run the demo, and key design choices.

Sample outputs: At least three example claims with generated decisions and explanations.

Demo evidence: Screenshots, API responses, notebook output, or a short walkthrough. Be prepared to demonstrate the prototype during the interview.

Assumptions and limitations: Briefly list assumptions, simplifications, known gaps, and what you would improve next.
AI Developer Assignment - Travel Reimbursement Approval Agent
Classification: Public
6. Evaluation Criteria

Hands-on implementation quality: runnable, understandable, and reasonably organized code.

Practical use of GenAI and Agentic AI: tool calling, workflow control, prompting, and context handling.

Business correctness: sensible reimbursement decisions grounded in policy/rule context.

Reliability: structured outputs, validation, fallbacks, and manual review for uncertain cases.

Developer judgement: clear trade-offs, simple design, and avoidable over-engineering removed.
7. Optional Enhancements

Simple UI or chatbot interface.

Audit trail showing retrieved context, tools called, and intermediate checks.

Basic test cases or evaluation script for sample claims.

Confidence score or reason codes for manual review.

MCP-based tool integration, if you are comfortable implementing it within the timebox.
Submission guidance: This assignment is intentionally timeboxed to 2-3 days. A small, working, well-explained prototype is preferred over a broad but fragile implementation.



