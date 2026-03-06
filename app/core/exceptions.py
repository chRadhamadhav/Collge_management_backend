"""
Domain-level exception classes.
Services raise these; the exception handlers in main.py transform them
into consistent JSON error responses for the client.
"""
from http import HTTPStatus


class AppException(Exception):
    """Base for all application-level exceptions."""

    def __init__(self, message: str, error_code: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code


class NotFoundError(AppException):
    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(
            message=f"{resource} not found with identifier: {identifier}",
            error_code=f"{resource.upper().replace(' ', '_')}_NOT_FOUND",
            status_code=HTTPStatus.NOT_FOUND,
        )


class UnauthorizedError(AppException):
    def __init__(self, detail: str = "Not authenticated") -> None:
        super().__init__(
            message=detail,
            error_code="UNAUTHORIZED",
            status_code=HTTPStatus.UNAUTHORIZED,
        )


class ForbiddenError(AppException):
    def __init__(self, detail: str = "Insufficient permissions") -> None:
        super().__init__(
            message=detail,
            error_code="FORBIDDEN",
            status_code=HTTPStatus.FORBIDDEN,
        )


class ConflictError(AppException):
    def __init__(self, resource: str, field: str, value: str) -> None:
        super().__init__(
            message=f"{resource} with {field} '{value}' already exists",
            error_code=f"{resource.upper().replace(' ', '_')}_CONFLICT",
            status_code=HTTPStatus.CONFLICT,
        )


class ValidationError(AppException):
    def __init__(self, detail: str) -> None:
        super().__init__(
            message=detail,
            error_code="VALIDATION_ERROR",
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )


class FileTooLargeError(AppException):
    def __init__(self, max_mb: int) -> None:
        super().__init__(
            message=f"File exceeds the maximum allowed size of {max_mb} MB",
            error_code="FILE_TOO_LARGE",
            status_code=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
        )
