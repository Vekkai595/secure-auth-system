class DomainError(Exception):
    code = 'domain_error'
    status_code = 400

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class UserAlreadyExistsError(DomainError):
    code = 'user_already_exists'
    status_code = 400


class InvalidCredentialsError(DomainError):
    code = 'invalid_credentials'
    status_code = 401


class InvalidRefreshTokenError(DomainError):
    code = 'invalid_refresh_token'
    status_code = 401


class SessionOwnershipError(DomainError):
    code = 'session_not_found'
    status_code = 400


class RateLimitExceeded(DomainError):
    code = 'rate_limited'
    status_code = 429


class InvalidTokenError(DomainError):
    code = 'invalid_token'
    status_code = 401
