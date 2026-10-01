import json
import os

from openai import OpenAI
from pydantic import ValidationError

from app.ai_schema import AIInvestigationResult
from app.ai_providers.base import AIProvider, AIProviderError


# ---------------------------------------------------------------------------
# NVIDIA Configuration
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "z-ai/glm-5.3-flash"

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"


# ---------------------------------------------------------------------------
# System Instruction
# ---------------------------------------------------------------------------

SYSTEM_INSTRUCTION = """
You are the AI Investigation Assistant for FinGuard,
a human-in-the-loop AML transaction monitoring system.

Your role is to synthesize a deterministic Evidence Package
into a concise, evidence-based investigation assessment for
a Level-1 AML analyst.

The AI is an ASSISTANT, not the final decision maker.

============================================================
CORE PRINCIPLES
============================================================

1. The supplied Evidence Package is the ONLY source of truth.

2. Use only information contained in the Evidence Package.

3. Never invent:
   - alert IDs
   - customer IDs
   - transaction IDs
   - rule IDs
   - case IDs
   - amounts
   - dates
   - counterparties
   - thresholds
   - customer attributes

4. Do not recalculate deterministic monitoring rules.

5. Do not change, override, or reinterpret deterministic
   rule results.

6. Clearly distinguish:
   - primary alert trigger
   - contextual rule indicators
   - customer profile context
   - historical case context

7. Historical information is contextual evidence only.

8. Never claim that money laundering has been proven.

9. Recommend an investigative next step, not a final
   regulatory or legal conclusion.

10. The human analyst retains final decision authority.


============================================================
EVIDENCE REFERENCE CONTRACT
============================================================

Every evidence reference MUST use one of the following
reference types.


------------------------------------------------------------
TRANSACTION
------------------------------------------------------------

Use:

    reference_type = "TRANSACTION"

The reference_id MUST be an actual transaction ID
contained in the Evidence Package.

Example:

{
    "reference_type": "TRANSACTION",
    "reference_id": "TXN-11988",
    "statement": "Primary transaction that triggered the alert."
}


------------------------------------------------------------
RULE
------------------------------------------------------------

Use:

    reference_type = "RULE"

The reference_id MUST be an actual deterministic rule ID
contained in the Evidence Package.

Valid examples include:

    RL-01
    RL-02
    RL-03
    RL-04
    RL-05

Example:

{
    "reference_type": "RULE",
    "reference_id": "RL-02",
    "statement": "Baseline deviation rule triggered the alert."
}


------------------------------------------------------------
CUSTOMER_CONTEXT
------------------------------------------------------------

Use:

    reference_type = "CUSTOMER_CONTEXT"

The reference_id MUST be the customer ID.

Example:

{
    "reference_type": "CUSTOMER_CONTEXT",
    "reference_id": "CUST-0001",
    "statement": "Customer profile indicates a low-risk customer."
}

IMPORTANT:

A CUSTOMER ID such as CUST-0001 MUST NEVER be used as
HISTORICAL_CONTEXT.


------------------------------------------------------------
HISTORICAL_CONTEXT
------------------------------------------------------------

Use:

    reference_type = "HISTORICAL_CONTEXT"

The ONLY valid reference IDs are:

    CUSTOMER_PROFILE
    CASE_HISTORY

Examples:

{
    "reference_type": "HISTORICAL_CONTEXT",
    "reference_id": "CUSTOMER_PROFILE",
    "statement": "Customer profile provides historical risk context."
}

or:

{
    "reference_type": "HISTORICAL_CONTEXT",
    "reference_id": "CASE_HISTORY",
    "statement": "Historical case records show no prior cases."
}


IMPORTANT:

NEVER produce:

{
    "reference_type": "HISTORICAL_CONTEXT",
    "reference_id": "CUST-0001"
}

That is INVALID.

If you want to refer to customer CUST-0001,
use:

{
    "reference_type": "CUSTOMER_CONTEXT",
    "reference_id": "CUST-0001"
}

If you want to refer to the customer's historical
profile information, use:

{
    "reference_type": "HISTORICAL_CONTEXT",
    "reference_id": "CUSTOMER_PROFILE"
}


============================================================
CANONICAL SCENARIO INTERPRETATION
============================================================

For an isolated baseline-deviation alert, consider the
following evidence pattern:

- the primary alert is caused by one transaction
- RL-01 is not triggered
- RL-03 is not triggered
- RL-04 is not triggered
- RL-05 is not triggered
- the customer has low-risk historical context
- there are no prior cases or escalations
- there is no corroborating suspicious transaction pattern

When this pattern is present and supported by the Evidence
Package, the assessment should normally be:

    risk_assessment = "LOW"

and:

    recommended_next_step = "CLOSE_REVIEW"

Do NOT recommend FURTHER_REVIEW solely because optional
information such as counterparty details, payment purpose,
or an itemized baseline calculation is absent.

Those limitations may be documented under evidence_gaps.

However, if the Evidence Package contains material
corroborating indicators, assess those indicators normally.

For example:

- multiple transactions
- amount clustering
- rapid inbound/outbound movement
- high transaction velocity
- multiple counterparties
- significant contextual rule triggers

should be considered when determining the appropriate
investigative next step.

Do not automatically classify an alert as HIGH merely
because an alert exists.

Do not automatically close an alert merely because the
customer has a low-risk profile.


============================================================
OUTPUT REQUIREMENTS
============================================================

Return ONLY valid JSON.

Do not return Markdown.

Do not use ```json fences.

Do not include commentary before or after the JSON.

The output must conform exactly to the supplied
AIInvestigationResult schema.

Keep the response concise.

Use only a small number of material key findings.

Every evidence reference MUST obey the evidence-reference
contract above.

Before returning the JSON, internally verify:

1. Every TRANSACTION reference_id is a real transaction ID.
2. Every RULE reference_id is a real rule ID.
3. Every CUSTOMER_CONTEXT reference_id is a real customer ID.
4. Every HISTORICAL_CONTEXT reference_id is exactly one of:
       CUSTOMER_PROFILE
       CASE_HISTORY
5. Never use a customer ID as HISTORICAL_CONTEXT.
6. Never invent evidence identifiers.
7. The response is complete valid JSON.
"""


# ---------------------------------------------------------------------------
# NVIDIA Provider
# ---------------------------------------------------------------------------


class NVIDIAProvider(AIProvider):
    """
    NVIDIA-backed implementation of the FinGuard AI provider.
    """

    provider_name = "nvidia"

    def __init__(self) -> None:

        api_key = os.getenv("NVIDIA_API_KEY")

        if not api_key:
            raise AIProviderError(
                "NVIDIA_API_KEY is not configured."
            )

        self.model_name = os.getenv(
            "NVIDIA_MODEL",
            DEFAULT_MODEL,
        )

        try:

            self.client = OpenAI(
                api_key=api_key,
                base_url=NVIDIA_BASE_URL,
            )

        except Exception as exc:

            raise AIProviderError(
                "Failed to initialize NVIDIA AI client."
            ) from exc

    # -----------------------------------------------------------------------
    # Prompt construction
    # -----------------------------------------------------------------------

    def _build_prompt(
        self,
        evidence_package: dict,
    ) -> str:
        """
        Convert the deterministic Evidence Package into
        the canonical LLM input.
        """

        evidence_json = json.dumps(
            evidence_package,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

        schema_json = json.dumps(
            AIInvestigationResult.model_json_schema(),
            indent=2,
            ensure_ascii=False,
        )

        return f"""
Analyze the following FinGuard Evidence Package.

The Evidence Package contains:

- immutable alert information
- primary alert evidence
- investigation context
- contextual deterministic rule indicators
- historical customer context

Your task is to produce an analyst-facing investigation
assessment.


ANALYSIS REQUIREMENTS
=====================

1. Identify the primary alert trigger.

2. Identify material contextual findings.

3. Explain why those findings matter.

4. Use historical customer context only as contextual
   evidence.

5. Distinguish triggered and non-triggered rules accurately.

6. Use only evidence contained in the package.

7. Cite evidence references from the supplied package.

8. Do not invent identifiers or facts.

9. Do not recalculate deterministic rules.

10. Do not change deterministic rule results.

11. Do not claim that money laundering is proven.

12. Recommend a next investigative action for the
    human analyst.

13. The human analyst retains final decision authority.

14. Mention meaningful evidence gaps where appropriate.

15. Keep the output concise.


IMPORTANT SCN_001 INTERPRETATION
================================

If the Evidence Package represents an isolated
baseline-deviation alert where:

- one transaction caused the primary alert,
- RL-01 is not triggered,
- RL-03 is not triggered,
- RL-04 is not triggered,
- RL-05 is not triggered,
- the customer has low-risk historical context,
- there are no prior cases or escalations,

then treat the pattern as an explainable isolated
deviation when supported by the supplied evidence.

In that situation:

- risk_assessment should normally be LOW
- recommended_next_step should normally be CLOSE_REVIEW

Do NOT recommend FURTHER_REVIEW solely because the package
does not contain optional counterparty details, transaction
purpose, or a fully itemized baseline calculation.

Such missing information can still be recorded under
evidence_gaps.

However, if the Evidence Package contains corroborating
transactional patterns or materially triggered contextual
rules, evaluate those findings normally.


EVIDENCE REFERENCE RULES
========================

When creating evidence_references:

TRANSACTION:
- reference_id must be an actual transaction ID from the package.

RULE:
- reference_id must be an actual rule ID from the package.

CUSTOMER_CONTEXT:
- reference_id must be the actual customer ID.

HISTORICAL_CONTEXT:
- reference_id MUST be exactly:
    CUSTOMER_PROFILE
  or:
    CASE_HISTORY

NEVER use a customer ID such as CUST-0001
as HISTORICAL_CONTEXT.

If you want to reference CUST-0001 directly,
use CUSTOMER_CONTEXT.

If you want to reference historical customer profile
information, use HISTORICAL_CONTEXT with:

    CUSTOMER_PROFILE

If you want to reference historical case information,
use HISTORICAL_CONTEXT with:

    CASE_HISTORY


OUTPUT FORMAT
=============

Return ONLY valid JSON.

Do not use Markdown.

Do not use ```json fences.

Do not include commentary before or after the JSON.

The response MUST conform to this schema:

{schema_json}


EVIDENCE PACKAGE
================

{evidence_json}
"""

    # -----------------------------------------------------------------------
    # Generate investigation
    # -----------------------------------------------------------------------

    def generate_investigation(
        self,
        evidence_package: dict,
    ) -> AIInvestigationResult:
        """
        Generate a structured AI investigation result.
        """

        prompt = self._build_prompt(
            evidence_package
        )

        try:

            response = (
                self.client
                .chat
                .completions
                .create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": SYSTEM_INSTRUCTION,
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    temperature=0.2,
                    max_tokens=2500,
                    reasoning_effort="low",
                    extra_body={
                        "chat_template_kwargs": {
                            "clear_thinking": True,
                        }
                    },
                )
            )

        except Exception as exc:

            raise AIProviderError(
                "NVIDIA AI request failed."
            ) from exc

        # -------------------------------------------------------------------
        # Validate response structure
        # -------------------------------------------------------------------

        try:

            if not response.choices:

                raise AIProviderError(
                    "NVIDIA returned no response choices."
                )

            content = (
                response
                .choices[0]
                .message
                .content
            )

            if not content:

                raise AIProviderError(
                    "NVIDIA returned an empty response."
                )

            content = content.strip()

            # Defensive handling in case the model ignores
            # the no-Markdown instruction.
            if content.startswith("```json"):

                content = (
                    content[len("```json"):]
                    .strip()
                )

            elif content.startswith("```"):

                content = (
                    content[len("```"):]
                    .strip()
                )

            if content.endswith("```"):

                content = (
                    content[:-3]
                    .strip()
                )

            result = (
                AIInvestigationResult
                .model_validate_json(content)
            )

        except ValidationError as exc:

            raise AIProviderError(
                "NVIDIA returned JSON that does not "
                "match the FinGuard investigation schema."
            ) from exc

        except AIProviderError:

            raise

        except Exception as exc:

            raise AIProviderError(
                "Failed to parse NVIDIA investigation response."
            ) from exc

        return result