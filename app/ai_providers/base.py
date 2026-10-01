"""
FinGuard — AI Provider Contract

Defines the common interface that every AI provider must implement.

The investigation layer should depend on this interface rather than
depending directly on Gemini or NVIDIA.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.ai_schema import AIInvestigationResult


class AIProviderError(RuntimeError):
    """Base exception for provider-level failures."""


class AIProvider(ABC):
    """
    Common interface for all FinGuard AI providers.

    Every provider receives the same deterministic Evidence Package
    and must return the same AIInvestigationResult schema.
    """

    provider_name: str

    @abstractmethod
    def generate_investigation(
        self,
        evidence_package: dict,
    ) -> AIInvestigationResult:
        """
        Generate an AI-assisted investigation from an Evidence Package.

        Providers must:
        - analyze only the supplied evidence,
        - return the common Pydantic schema,
        - raise AIProviderError on provider/API failures.
        """
        raise NotImplementedError