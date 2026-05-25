class ClinicalError(Exception):
    """Base exception for all clinical data intelligence errors."""
    def __init__(self, message: str, *, code: str = "CLINICAL_ERROR",
                 details: dict | None = None, recoverable: bool = False,
                 node: str | None = None):
        self.code = code
        self.details = details or {}
        self.recoverable = recoverable
        self.node = node
        super().__init__(message)


class GraphNodeError(ClinicalError):
    """Error raised during graph node execution."""
    def __init__(self, message: str, *, node: str, code: str = "NODE_ERROR",
                 details: dict | None = None, recoverable: bool = False):
        super().__init__(message, code=code, details=details,
                         recoverable=recoverable, node=node)


class SQLExtractionError(GraphNodeError):
    """LLM failed to produce valid SQL."""
    def __init__(self, message: str = "The AI failed to generate a valid SQL query.",
                 *, node: str = "sql_tool", details: dict | None = None,
                 recoverable: bool = True):
        super().__init__(message, node=node, code="SQL_EXTRACTION_FAILED",
                         details=details, recoverable=recoverable)


class SQLExecutionError(GraphNodeError):
    """Database query execution failed."""
    def __init__(self, message: str, *, sql: str = "",
                 node: str = "sql_tool", details: dict | None = None,
                 recoverable: bool = True):
        d = {"sql": sql, "(details)": details or {}}
        super().__init__(message, node=node, code="SQL_EXECUTION_FAILED",
                         details=d, recoverable=recoverable)


class LLMProviderError(GraphNodeError):
    """LLM call failed."""
    def __init__(self, message: str, *, node: str, code: str = "LLM_PROVIDER_ERROR",
                 details: dict | None = None, recoverable: bool = True):
        super().__init__(message, node=node, code=code,
                         details=details, recoverable=recoverable)


class RateLimitError(LLMProviderError):
    """Rate limit or quota exceeded."""
    def __init__(self, message: str = "Model rate limit reached.",
                 *, node: str, details: dict | None = None,
                 recoverable: bool = True):
        super().__init__(message, node=node, code="RATE_LIMIT",
                         details=details, recoverable=recoverable)


class CacheError(GraphNodeError):
    """Cache lookup or update failed."""
    def __init__(self, message: str, *, node: str = "cache_check",
                 code: str = "CACHE_ERROR", details: dict | None = None,
                 recoverable: bool = False):
        super().__init__(message, node=node, code=code,
                         details=details, recoverable=recoverable)


class SchemaError(ClinicalError):
    """Schema introspection failed."""
    def __init__(self, message: str = "Schema introspection failed.",
                 *, code: str = "SCHEMA_ERROR", details: dict | None = None):
        super().__init__(message, code=code, details=details, recoverable=False)


class ThreadNotFoundError(ClinicalError):
    """Checkpoint thread doesn't exist."""
    def __init__(self, message: str = "Thread not found.",
                 *, code: str = "THREAD_NOT_FOUND", details: dict | None = None):
        super().__init__(message, code=code, details=details, recoverable=False)


class InvalidQueryError(ClinicalError):
    """User query rejected at validation."""
    def __init__(self, message: str, *, code: str = "INVALID_QUERY",
                 details: dict | None = None):
        super().__init__(message, code=code, details=details, recoverable=False)
