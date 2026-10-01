FinGuard — Business Analysis Documentation

Purpose: BA/process/requirements artifact for the FinGuard portfolio prototype.

Documentation split: README.md is the technical and portfolio landing page. This document deliberately focuses on the business-analysis material that should not be duplicated there: stakeholders, persona, AS-IS/TO-BE analysis, requirements, user stories, acceptance criteria, UAT, traceability, KPI definitions, assumptions, risks, and BA-oriented solution rationale.

1. Document Boundary

FinGuard is a portfolio-scale AML Transaction Monitoring prototype. The README already documents the technical solution in detail, including the architecture, deterministic rule definitions, investigation-engine design, AI schema/provider implementation, audit persistence, dataset inventory, technology stack, run instructions, validation commands, illustrative ROI model, limitations, and future enhancements.

This document therefore answers the complementary BA question:

What business need is being addressed, how does the analyst workflow change, what requirements and controls define the solution, and how would the solution be evaluated?

For implementation details, refer to README.md rather than duplicating them here.

2. Business Problem

2.1 Problem Statement

Transaction-monitoring alerts require analysts to bring together several forms of information before reaching a case decision. The analyst needs to understand the alert trigger, review relevant transaction activity, consider customer context, consider historical case information, synthesize findings, document the rationale, and complete the case disposition.

The business problem is therefore not only transaction detection. It is the investigation workflow that follows alert generation.

2.2 Business Need

FinGuard is designed around four linked needs:

Reduce repetitive investigation effort by structuring the evidence-assembly process.

Improve consistency by applying a defined investigation workflow and deterministic analysis.

Use AI as an advisory interpretation layer rather than an autonomous decision-maker.

Preserve traceability between the investigation and the final human decision.

These are prototype design objectives, not claims of measured production performance.

3. Business Objectives

Objective

Intended outcome

Investigation efficiency

Reduce repetitive evidence-gathering and synthesis work.

Evidence-based investigation

Give the analyst structured context before AI interpretation.

Consistency

Use a repeatable investigation sequence and deterministic analysis.

Human decision authority

Keep final CLOSE / OVERRIDE / ESCALATE authority with the analyst.

Auditability

Retain decision metadata and rationale for later review.

Operational visibility

Provide metrics that can be used to understand completed case outcomes.

The separate ROI model in README.md provides the financial scenario analysis; its numerical assumptions are intentionally not reproduced here.

4. Stakeholder Analysis

Stakeholder

Role / interest

Primary need

Level-1 AML / Transaction Monitoring Analyst

Primary user

Fast access to relevant evidence and control over final disposition

AML Compliance Manager / Team Lead

Operational oversight

Visibility into case outcomes, overrides, escalations and trends

QA / Compliance Audit

Independent review

Traceability of evidence and decision rationale

Compliance Operations / Process Owner

Workflow ownership

Consistency, throughput and control points

Business Analyst / Product Owner

Requirements and value definition

Clear requirements, traceability, KPIs and business case

AI / System Administrator

Technical operation

Secure configuration, provider reliability and maintainability

The analyst is the primary persona; the other stakeholders are represented through controls, persistence, reporting and governance requirements.

5. Primary User Persona

Level-1 AML / Transaction Monitoring Analyst

Role: First-line analyst responsible for reviewing transaction-monitoring alerts.

Goals

Understand why an alert was generated.

Review the transactions and customer context relevant to the alert.

Consider additional indicators and historical case context.

Produce a defensible investigation rationale.

Complete the case without losing evidence traceability.

Pain points represented by the prototype

Repetitive evidence gathering.

Fragmented investigation context.

Repeated pattern interpretation.

Documentation effort.

Need to distinguish AI advice from the final analyst decision.

Desired outcome

A structured investigation workflow that takes the analyst from alert review through evidence assessment, advisory AI review, final human disposition and recorded rationale.

This is a functional role description for the portfolio prototype, not a claim about one specific bank's operating model.

6. AS-IS Process — Conceptual Baseline

The following is a BA baseline used to identify manual touchpoints. It is not a measured description of a particular bank's production process.

Alert Generated
    ↓
Analyst Opens Alert
    ↓
Find Customer / Account Context
    ↓
Review Alert Transactions
    ↓
Inspect Relevant Transaction History
    ↓
Consider Triggering Rule / Scenario
    ↓
Check Historical Customer Context
    ↓
Synthesize Findings
    ↓
Write Investigation Rationale
    ↓
Close / Override / Escalate
    ↓
Record Case Decision

AS-IS Manual Touchpoints

Touchpoint

Analyst activity

Potential friction

Alert review

Understand the original trigger

Requires interpretation before broader review

Customer context

Locate customer information

Repeated lookup effort

Transaction review

Identify relevant activity

Filtering and comparison effort

Pattern assessment

Look for additional indicators

Repetitive analytical work

Historical review

Check prior cases

Context may be overlooked

Documentation

Write investigation rationale

Time and consistency burden

Case recording

Record the decision

Requires disciplined audit capture

7. AS-IS Pain Points and Root-Cause Analysis

Pain point

Root cause

Business effect

Fragmented evidence review

Relevant information is spread across investigation steps

Higher effort per case

Repetitive pattern checks

Similar analytical activities recur across alerts

Lower productivity

Variable documentation

Narrative creation is manual

Inconsistent investigation records

Historical context may be missed

Historical review is a separate activity

Less complete case context

AI governance risk

Unstructured AI can blur facts and interpretation

Trust and control concerns

Limited operational visibility

Outcomes must be aggregated after decisions

Harder to monitor process trends

Root-Cause Theme

The central opportunity is workflow orchestration and evidence quality first, with AI introduced only after the factual investigation context has been prepared.

8. TO-BE Process — FinGuard

Alert Queue
    ↓
Select Alert
    ↓
Customer + Alert Evidence
    ↓
Deterministic Analysis
    ↓
Investigation Context
    ↓
Historical Customer Context
    ↓
Structured Evidence Package
    ↓
AI Investigation — Advisory
    ↓
Evidence / Output Validation
    ↓
Human Analyst Review
    ↓
CLOSE / OVERRIDE / ESCALATE
    ↓
Audit Persistence
    ↓
Operational Analytics

Intended Process Improvements

Reduce manual evidence assembly.

Standardize the investigation sequence.

Separate factual evidence from AI interpretation.

Make evidence references visible to the analyst.

Keep final disposition under explicit human control.

Require a documented rationale.

Make completed outcomes available for operational reporting.

The technical implementation of this flow is already described in README.md and is not reproduced here.

9. Scope Definition

In Scope

AML transaction-monitoring alert investigation.

Customer, transaction, alert and historical context.

Deterministic rule evaluation.

Investigation-context construction.

Structured evidence packaging.

Advisory AI investigation.

AI output and evidence-reference validation.

Human-in-the-loop decisioning.

Decision rationale and audit persistence.

Operational analytics.

Illustrative business-case analysis.

Out of Scope

Real-time transaction blocking.

Autonomous alert closure.

Autonomous regulatory filing.

Live KYC / PEP / sanctions integrations.

Production core-banking integration.

Enterprise IAM / SSO.

Distributed production infrastructure.

Production-grade model-risk platform.

Real customer data.

The README contains the fuller technical scope statement.

10. Business Requirements

BR-01 — Structured Investigation

The solution should provide a consistent investigation sequence for transaction-monitoring alerts.

BR-02 — Evidence Traceability

The analyst should be able to identify the evidence supporting the investigation findings.

BR-03 — Contextual Analysis

The workflow should bring together the customer, transaction, alert and relevant historical context required for investigation.

BR-04 — Controlled AI Assistance

AI should provide advisory interpretation of prepared evidence rather than act as the final case decision-maker.

BR-05 — Human Decision Authority

The final disposition should require an explicit analyst decision.

BR-06 — Decision Rationale

The analyst should provide a rationale for the final disposition.

BR-07 — Auditability

Completed case decisions should generate persisted metadata that can support later operational review.

BR-08 — Operational Visibility

Completed investigations should support aggregate reporting on workflow outcomes.

11. Functional Requirements

ID

Requirement

Status

FR-01

The system shall present alerts for analyst selection.

Implemented

FR-02

The system shall retrieve and display the customer context associated with a selected alert.

Implemented

FR-03

The system shall evaluate deterministic transaction-monitoring indicators without relying on the LLM for calculations.

Implemented

FR-04

The system shall identify the transaction evidence associated with the alert.

Implemented

FR-05

The system shall construct a defined investigation context around the alert event.

Implemented

FR-06

The system shall provide relevant historical customer case context.

Implemented

FR-07

The system shall assemble investigation information into structured evidence for downstream review.

Implemented

FR-08

The system shall request an advisory AI investigation from the configured provider chain.

Implemented

FR-09

The system shall validate the structure of returned AI output.

Implemented

FR-10

The system shall validate AI evidence references against available investigation evidence.

Implemented

FR-11

The system shall identify the provider used for the accepted AI result.

Implemented

FR-12

The analyst shall be able to review the alert, evidence, context and advisory AI result.

Implemented

FR-13

The analyst shall explicitly select CLOSE, OVERRIDE or ESCALATE.

Implemented

FR-14

The analyst shall provide a rationale before the HITL decision is persisted.

Implemented

FR-15

The system shall persist completed HITL decision metadata.

Implemented

FR-16

The system shall expose operational summaries of completed cases.

Implemented

FR-17

The system shall not automatically convert an AI recommendation into the final case disposition.

Implemented

Detailed module names, field definitions and implementation mechanics belong in README.md and are intentionally omitted here.

12. Non-Functional Requirements

ID

Requirement

BA rationale

NFR-01

Deterministic rule results should be repeatable for the same inputs and configuration.

Supports consistency and testability.

NFR-02

The AI recommendation shall remain separate from the final human disposition.

Supports human oversight.

NFR-03

AI findings should use controlled evidence references.

Supports traceability.

NFR-04

Secrets shall remain outside source-controlled application files.

Supports basic security hygiene.

NFR-05

The prototype should run in a lightweight local environment.

Keeps the portfolio implementation accessible and maintainable.

NFR-06

Business responsibilities should remain separated across rule, investigation, AI, HITL, persistence and analytics layers.

Supports maintainability and governance.

NFR-07

Provider failure should be surfaced rather than represented as a successful AI result.

Prevents misleading workflow states.

NFR-08

Demonstration data shall remain synthetic.

Avoids exposure of customer or confidential banking information.

NFR-09

The analyst workflow should be understandable without requiring knowledge of the underlying Python implementation.

Supports usability.

NFR-10

Performance claims should be based on measured benchmarks rather than invented targets.

Prevents unsupported operational claims.

13. User Stories

US-01 — Inspect Alert Trigger

As an AML analyst, I want to see why an alert was generated, so that I understand the original investigation focus.

US-02 — Review Customer Context

As an AML analyst, I want to see the relevant customer context, so that I can interpret transaction activity appropriately.

US-03 — Review Investigation Context

As an AML analyst, I want to see relevant activity around the alert event, so that I can distinguish an isolated event from broader activity.

US-04 — Review Deterministic Indicators

As an AML analyst, I want to see transparent rule indicators, so that I can understand the analytical basis of the investigation.

US-05 — Review Historical Context

As an AML analyst, I want to see relevant prior case context, so that I can consider the customer's investigation history.

US-06 — Use AI as an Assistant

As an AML analyst, I want to receive an AI synthesis of prepared evidence, so that I can reduce repetitive interpretation effort.

US-07 — Verify AI Evidence

As an AML analyst or reviewer, I want AI findings to reference controlled evidence, so that unsupported evidence claims can be detected.

US-08 — Make the Final Decision

As an AML analyst, I want to choose the final disposition myself, so that AI does not become the automatic case decision-maker.

US-09 — Record Decision Rationale

As an AML analyst, I want to record a reason for my decision, so that the outcome is reviewable.

US-10 — Review Case Outcomes

As a compliance or QA stakeholder, I want to review stored case outcomes and aggregate metrics, so that I can monitor workflow activity.

14. Acceptance Criteria

AC-01 — Alert Investigation

Given a valid alert, when the analyst opens it, then the alert trigger, customer context and relevant transaction evidence shall be available for review.

AC-02 — Context Construction

Given a valid alert evidence event, when investigation is executed, then the defined investigation context shall be constructed consistently.

AC-03 — Historical Context

Given a customer associated with the alert, when investigation is executed, then relevant historical case context shall be retrieved when available.

AC-04 — AI Output Structure

Given an available provider, when advisory AI analysis is requested, then the returned result shall conform to the application's structured output contract.

AC-05 — Evidence Validation

Given AI findings containing evidence references, when validation runs, then references that are unsupported by the investigation evidence shall not be accepted as valid findings.

AC-06 — Human Decision Authority

Given an AI recommendation, when the analyst reviews the case, then the system shall still require an explicit human disposition.

AC-07 — Rationale Requirement

Given a HITL decision submission, when the analyst rationale is empty, then the decision shall fail validation rather than being persisted as a completed case.

AC-08 — Audit Persistence

Given a valid HITL decision, when the case is saved, then the completed decision metadata shall be persisted.

AC-09 — Analytics Consistency

Given stored audit records, when operational analytics are calculated, then the reported totals shall be consistent with the underlying completed-case records.

AC-10 — Provider Failure Handling

Given that the configured AI providers fail, when AI analysis is requested, then the application shall surface an error rather than represent an unsuccessful AI call as a successful AI result.

15. UAT Scenarios

The UAT layer validates business behavior. Detailed rule parameters and canonical dataset values are intentionally kept in README.md rather than duplicated here.

UAT-01 — Standard Alert Investigation

Given: An alert exists in the queue.

When: The analyst selects the alert and begins investigation.

Then: The workflow presents the alert context, customer context, investigation evidence and relevant historical context.

Acceptance: The analyst can reach the review stage using a consistent evidence-driven process.

UAT-02 — AI-Assisted Investigation

Given: A valid structured investigation package and an available provider.

When: The analyst requests AI assistance.

Then: A structured advisory result is returned and validated before presentation.

Acceptance: AI assistance is presented as advisory analysis rather than as the final disposition.

UAT-03 — Evidence-Reference Control

Given: An AI result contains evidence references.

When: the application validates the result.

Then: each accepted reference must correspond to an allowed evidence type and available investigation evidence.

Acceptance: unsupported evidence references are rejected from the accepted result.

UAT-04 — Human Decision Control

Given: An AI recommendation is displayed.

When: The analyst selects CLOSE, OVERRIDE or ESCALATE and provides a rationale.

Then: the analyst's choice becomes the final human disposition and the decision metadata is persisted.

Acceptance: the AI recommendation cannot silently become the final disposition.

UAT-05 — Override Path

Given: The analyst reaches a conclusion different from the AI recommendation.

When: the analyst selects OVERRIDE and provides a rationale.

Then: both the advisory recommendation and human outcome remain distinguishable in the stored case information.

Acceptance: the workflow supports disagreement with the AI result without breaking the audit process.

UAT-06 — AI Provider Failure

Given: configured AI providers are unavailable.

When: the analyst requests AI assistance.

Then: the application surfaces the provider failure rather than creating a false successful AI result.

Acceptance: the failure is visible and does not create an invalid AI decision state.

16. Requirements Traceability Matrix

Business objective

Requirement

User story

Acceptance / UAT

Outcome

Investigation efficiency

FR-05, FR-07

US-03

AC-02, UAT-01

Structured investigation context

Evidence-based investigation

FR-04, FR-10

US-05, US-07

AC-05, UAT-03

Traceable evidence use

Consistency

FR-03

US-04

AC-01, UAT-01

Repeatable deterministic analysis

Controlled AI assistance

FR-08, FR-09

US-06

AC-04, UAT-02

Structured advisory AI

Human decision authority

FR-13, FR-17

US-08

AC-06, UAT-04

Explicit human disposition

Decision accountability

FR-14, FR-15

US-09

AC-07, AC-08

Rationale + persisted decision

Operational visibility

FR-16

US-10

AC-09

Aggregate workflow metrics

Controlled failure

FR-08

US-06

AC-10, UAT-06

Visible AI failure state

17. KPI & Success-Metric Framework

The prototype contains operational analytics. The BA perspective is to define what those metrics mean, while avoiding unsupported claims about real-world performance.

Investigation Efficiency

Potential measures:

average investigation time per alert;

evidence-assembly time;

number of alerts completed per analyst period; and

proportion of investigation steps supported by the structured workflow.

Investigation Quality / Control

Potential measures:

percentage of cases with complete analyst rationale;

percentage of accepted AI findings with valid evidence references;

AI recommendation versus human outcome; and

override and escalation rates.

Operational Monitoring

Potential measures:

completed case volume;

decision distribution;

risk-assessment distribution;

provider usage distribution; and

case volume by period.

These should be interpreted as process metrics, not standalone measures of analyst quality or regulatory effectiveness.

18. Governance, Risk & Control Considerations

Risk / control concern

Why it matters

FinGuard control / design response

AI hallucinated evidence

Could distort an investigation

Evidence-reference validation

Automation bias

Analyst could accept AI without sufficient review

Explicit HITL disposition

Rule-calculation error

Could produce incorrect indicators

Deterministic rule layer separated from AI

Incomplete context

Could weaken investigation quality

Structured customer, transaction, alert and historical context

Provider outage

AI assistance may be unavailable

Configured provider fallback and explicit failure handling

Weak auditability

Difficult post-case review

Persisted HITL decision metadata

Schema mismatch

New data source may not fit the workflow

Canonical schema plus validation requirement

Overstated business value

Could create unrealistic expectations

ROI clearly labelled as illustrative

Core Governance Principle

Facts / Calculations
        ↓
Evidence
        ↓
AI Interpretation
        ↓
Human Decision
        ↓
Audit Record

The AI layer is therefore downstream of the factual evidence layer and upstream of the human disposition.

19. Assumptions

The prototype operates on the application's defined canonical AML data concepts.

Demonstration data is synthetic.

Deterministic transaction-monitoring analysis is available before AI interpretation.

AI providers are external dependencies and may fail.

A human analyst remains responsible for the final disposition.

Operational analytics represent prototype case data, not production KPIs.

Financial benefit estimates require real organizational baselines before being used for an investment decision.

A generalized data-ingestion/schema-mapping layer would be required to support arbitrary external source schemas.

20. BA-Oriented Future Enhancements

The README contains the full technical roadmap. From a BA perspective, future work can be grouped into these capability themes:

Data Integration

formal source-to-canonical mapping;

data-quality rules and exception handling; and

onboarding workflow for new source systems.

Investigation Operations

configurable investigation policies;

broader customer segmentation;

additional transaction-pattern indicators; and

richer network/counterparty analysis.

AI Governance

structured evaluation criteria;

prompt/model version tracking;

provider health monitoring;

human-feedback capture; and

AI quality monitoring.

Enterprise Controls

identity and access management;

retention requirements;

stronger audit controls;

approval workflows; and

production model-risk governance.

These are roadmap themes rather than claims that the current prototype already provides the capabilities.

21. BA Deliverables Demonstrated

The project demonstrates a complete BA-to-prototype chain:

Business Problem
      ↓
Stakeholders
      ↓
Persona
      ↓
AS-IS Process
      ↓
Pain Points
      ↓
TO-BE Process
      ↓
Scope
      ↓
Requirements
      ↓
User Stories
      ↓
Acceptance Criteria / UAT
      ↓
Traceability
      ↓
Controls / Governance
      ↓
KPIs
      ↓
Prototype Implementation

This demonstrates BA capability across problem framing, process analysis, requirements thinking, solution design, AI governance, human oversight, KPI definition and business-case framing.

22. Interview-Relevant Design Rationale

Why not let the LLM make the final AML decision?

Because the prototype deliberately separates AI advisory analysis from the human disposition. The analyst remains responsible for the final CLOSE, OVERRIDE or ESCALATE choice.

Why use deterministic analysis before AI?

Because calculations and transaction-pattern indicators need to be repeatable, transparent and testable. AI is then used for a different task: synthesis and explanation of prepared evidence.

Why synthetic data?

Because the portfolio project needs realistic relational investigation flows without relying on confidential or real customer data.

What would be required to support another dataset?

The source fields would need to be mapped and validated against the canonical AML data contract used by the application. A generalized ingestion and schema-mapping capability is a logical future enhancement.

Is this production-ready?

No. It is intentionally a portfolio-scale prototype. Production implementation would require enterprise integration, security, resilience, identity/access controls, data governance, model governance, monitoring, retention and regulatory controls.

23. Documentation Ownership Rule

To prevent duplication and documentation drift:

Information type

Primary document

Project overview

README.md

Architecture / Mermaid

README.md + docs/architecture.mmd

Exact deterministic rule logic

README.md

Dataset inventory and canonical scenarios

README.md

AI provider/model/schema implementation

README.md

Audit persistence implementation

README.md

Technical run / validation commands

README.md

ROI assumptions and calculations

README.md

Business problem

BA_DOCUMENTATION.md

Stakeholders / persona

BA_DOCUMENTATION.md

AS-IS / TO-BE process

BA_DOCUMENTATION.md

Requirements / user stories

BA_DOCUMENTATION.md

Acceptance criteria / UAT

BA_DOCUMENTATION.md

Traceability

BA_DOCUMENTATION.md

KPI definitions from a BA perspective

BA_DOCUMENTATION.md

BA governance / risks / assumptions

BA_DOCUMENTATION.md

This split is intentional: README = what the system is and how it works technically; BA document = why the solution exists and how the business/process requirements are defined and evaluated.

24. Document Status

Project: FinGuard — AI-Assisted AML Transaction Monitoring & Human-in-the-Loop Investigation System
Artifact: Business Analysis Documentation
Status: v1.0 working-prototype documentation

The document complements README.md; it is not intended to reproduce the technical project description.