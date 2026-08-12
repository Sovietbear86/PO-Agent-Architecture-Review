"""Core error classes for PO Agent Platform v2."""


class POAgentError(Exception):
    """Base exception for all PO Agent Platform errors."""


class ConfigurationError(POAgentError):
    """Configuration-related errors."""


class AuthenticationError(POAgentError):
    """Authentication failures."""


class AdapterUnavailableError(POAgentError):
    """External adapter service unavailable."""


class AdapterTimeoutError(POAgentError):
    """Adapter service timeout."""


class NotFoundError(POAgentError):
    """Resource not found."""


class InvalidExternalDataError(POAgentError):
    """Invalid data from external source."""


class ContractViolationError(POAgentError):
    """Contract violation with external service."""


class CapabilityExecutionError(POAgentError):
    """Capability execution failure."""


class LLMUnavailableError(POAgentError):
    """LLM service unavailable."""


class EvaluationError(POAgentError):
    """Evaluation-related errors."""


class VersionPromotionError(POAgentError):
    """Version promotion failure."""


class MemoryPolicyError(POAgentError):
    """Memory policy violation."""
