class DomainError(Exception):
    """Base exception for the backend domain."""


class InvalidKnowledgeBaseError(DomainError):
    """Raised when the knowledge base is inconsistent."""


class InvalidPatientStateError(DomainError):
    """Raised when patient input does not satisfy the feature constraints."""


class DiagnosisNotFoundError(DomainError):
    """Raised when no diagnosis matches the patient state."""


class EntityNotFoundError(DomainError):
    """Raised when the requested knowledge base entity does not exist."""


class EntityConflictError(DomainError):
    """Raised when an entity cannot be created or renamed because of a conflict."""


class EntityInUseError(DomainError):
    """Raised when an entity is referenced by other knowledge base records."""


class InvalidEditorOperationError(DomainError):
    """Raised when an editor action violates business constraints."""
