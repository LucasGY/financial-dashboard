class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class InvalidParameterError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__("INVALID_PARAMETER", message, 400)


class NotFoundError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__("NOT_FOUND", message, 404)


class DataUnavailableError(AppError):
    def __init__(self, message: str = "data source is unavailable") -> None:
        super().__init__("DATA_UNAVAILABLE", message, 503)


class InternalError(AppError):
    def __init__(self, message: str = "internal server error") -> None:
        super().__init__("INTERNAL_ERROR", message, 500)


class ConflictError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__("CONFLICT", message, 409)
