"""
FinGuard — AI Investigation Orchestrator

Coordinates the configured AI providers.

Architecture:
    Evidence Package
          ↓
    Primary AI Provider
          ↓
       success
          ↓
    Validate Evidence
          ↓
    Stamp Provider
          ↓
       AI Result

       OR

       failure
          ↓
    Fallback AI Provider
          ↓
       success
          ↓
    Validate Evidence
          ↓
    Stamp Provider
          ↓
       AI Result

The orchestrator is responsible for:
- loading environment configuration,
- selecting the configured providers,
- handling provider-level failures,
- rejecting invalid AI-generated evidence references,
- falling back when the primary provider fails,
- recording which provider generated the final result,
- returning the common AIInvestigationResult schema.

The providers themselves are responsible for communicating with
their respective AI APIs.

Important:
Provider API failures and invalid provider outputs are both treated
as provider failures. Invalid evidence references are never allowed
to pass through to the analyst-facing result.

The Evidence Package remains the deterministic source of truth.
The AI layer interprets and summarizes that evidence; it does not
replace the deterministic investigation engine.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

from app.ai_schema import (
    AIInvestigationResult,
    validate_evidence_references,
)

from app.ai_providers.base import (
    AIProvider,
    AIProviderError,
)

from app.ai_providers.gemini_provider import (
    GeminiProvider,
)

from app.ai_providers.nvidia_provider import (
    NVIDIAProvider,
)


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

# Load variables from the project's .env file.
#
# This means the application can automatically access:
#
#     NVIDIA_API_KEY
#     GEMINI_API_KEY
#     AI_PRIMARY_PROVIDER
#     AI_FALLBACK_PROVIDER
#     NVIDIA_MODEL
#     GEMINI_MODEL
#
# without requiring PowerShell environment variables to be manually
# configured every time a new terminal is opened.
load_dotenv()


# ---------------------------------------------------------------------------
# Provider defaults
# ---------------------------------------------------------------------------

# NVIDIA is currently the validated primary provider for FinGuard.
#
# Gemini remains available as the fallback provider.
#
# These values can still be overridden through .env:
#
# AI_PRIMARY_PROVIDER=nvidia
# AI_FALLBACK_PROVIDER=gemini
#
DEFAULT_PRIMARY_PROVIDER = "nvidia"
DEFAULT_FALLBACK_PROVIDER = "gemini"


# ---------------------------------------------------------------------------
# Provider factory
# ---------------------------------------------------------------------------

def _create_provider(
    provider_name: str,
) -> AIProvider:
    """
    Create the configured AI provider.

    Supported providers:
    - gemini
    - nvidia
    """

    provider_name = provider_name.strip().lower()

    if provider_name == "gemini":
        return GeminiProvider()

    if provider_name == "nvidia":
        return NVIDIAProvider()

    raise ValueError(
        f"Unsupported AI provider: {provider_name}. "
        "Supported providers are: gemini, nvidia."
    )


# ---------------------------------------------------------------------------
# Provider execution helper
# ---------------------------------------------------------------------------

def _run_provider(
    provider: AIProvider,
    evidence_package: dict,
) -> AIInvestigationResult:
    """
    Run one AI provider and validate its result.

    A provider execution is considered unsuccessful if:

    1. The provider/API raises AIProviderError.
    2. The returned investigation contains unsupported
       evidence references.

    Evidence validation errors are converted into
    AIProviderError so that the orchestrator can treat
    malformed or unsupported AI output in the same way
    as other provider-level failures.

    The provider provenance field is stamped only after
    the result successfully passes evidence validation.
    """

    try:

        # ---------------------------------------------------------------
        # Call the provider.
        # ---------------------------------------------------------------

        result = provider.generate_investigation(
            evidence_package
        )

        # ---------------------------------------------------------------
        # Validate all evidence references returned by the AI.
        #
        # The AI is not allowed to introduce evidence that does not
        # exist in the deterministic Evidence Package.
        # ---------------------------------------------------------------

        validate_evidence_references(
            result,
            evidence_package,
        )

    except AIProviderError:

        # Provider already raised a controlled provider-level
        # exception. Preserve it unchanged so the orchestrator
        # can attempt the fallback provider.
        raise

    except ValueError as validation_error:

        # Evidence-reference validation deliberately raises
        # ValueError when the AI cites unsupported evidence.
        #
        # Convert it into AIProviderError so the orchestrator
        # can treat invalid AI output as a provider failure.
        raise AIProviderError(
            f"Provider '{provider.provider_name}' returned "
            "an invalid investigation result: "
            f"{validation_error}"
        ) from validation_error

    # -----------------------------------------------------------------------
    # Provider provenance
    # -----------------------------------------------------------------------

    # The application stamps provider provenance.
    #
    # The LLM is NOT trusted to identify which provider
    # generated the result.
    return result.model_copy(
        update={
            "provider": provider.provider_name,
        }
    )


# ---------------------------------------------------------------------------
# Main orchestration function
# ---------------------------------------------------------------------------

def generate_ai_investigation(
    evidence_package: dict,
) -> AIInvestigationResult:
    """
    Generate an AI-assisted investigation from a deterministic
    Evidence Package.

    Provider flow:

        Primary provider
              ↓
           generate
              ↓
        validate evidence
              ↓
        stamp provenance
              ↓
         return result

              OR

           provider/API failure
              OR
        invalid AI evidence
              ↓
        Fallback provider
              ↓
           generate
              ↓
        validate evidence
              ↓
        stamp provenance
              ↓
         return result

              OR

           provider/API failure
              OR
        invalid AI evidence
              ↓
        raise combined error

    The Evidence Package remains the deterministic source of truth.

    AI-generated evidence references must pass validation before
    any investigation result is returned to the caller.

    Provider provenance is assigned by the application only after
    successful validation.
    """

    # -----------------------------------------------------------------------
    # Read provider configuration.
    #
    # .env values take precedence.
    # If they are not present, the validated defaults are used.
    # -----------------------------------------------------------------------

    primary_name = os.getenv(
        "AI_PRIMARY_PROVIDER",
        DEFAULT_PRIMARY_PROVIDER,
    )

    fallback_name = os.getenv(
        "AI_FALLBACK_PROVIDER",
        DEFAULT_FALLBACK_PROVIDER,
    )

    primary_name = primary_name.strip().lower()
    fallback_name = fallback_name.strip().lower()

    # -----------------------------------------------------------------------
    # Configuration safety check
    # -----------------------------------------------------------------------

    if fallback_name == primary_name:

        raise RuntimeError(
            "AI provider configuration is invalid: "
            f"primary provider '{primary_name}' and fallback "
            f"provider '{fallback_name}' are the same."
        )

    # -----------------------------------------------------------------------
    # Primary provider
    # -----------------------------------------------------------------------

    try:

        primary_provider = _create_provider(
            primary_name
        )

        return _run_provider(
            primary_provider,
            evidence_package,
        )

    except AIProviderError as primary_error:

        # -------------------------------------------------------------------
        # Primary provider failed.
        #
        # Try the configured fallback provider.
        # -------------------------------------------------------------------

        try:

            fallback_provider = _create_provider(
                fallback_name
            )

            return _run_provider(
                fallback_provider,
                evidence_package,
            )

        except AIProviderError as fallback_error:

            # ---------------------------------------------------------------
            # Both providers failed.
            #
            # Preserve both errors so the user/developer can see which
            # provider failed and why.
            # ---------------------------------------------------------------

            raise RuntimeError(
                "Both configured AI providers failed. "
                f"Primary '{primary_name}' error: "
                f"{primary_error}. "
                f"Fallback '{fallback_name}' error: "
                f"{fallback_error}."
            ) from fallback_error