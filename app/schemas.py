from typing import Generic, Optional, TypeVar, Any, Callable
from pydantic import BaseModel

T = TypeVar("T")

class APIError(BaseModel):
    """Structured error information."""
    code: str
    detail: str

class APIResponse(BaseModel, Generic[T]):
    """Central generic response schema."""
    status: bool
    message: str
    data: Optional[T] = None
    error: Optional[APIError] = None

    @classmethod
    def execute(cls, func: Callable, success_message: str, error_code: str = "INTERNAL_SERVER_ERROR", *args, **kwargs):
        """Synchronous helper to execute a function and wrap the result in an APIResponse."""
        try:
            result = func(*args, **kwargs)
            return cls(status=True, message=success_message, data=result)
        except Exception as e:
            return cls(
                status=False, 
                message=f"Operation failed", 
                error=APIError(code=error_code, detail=str(e))
            )