from typing import Optional


class NetworkError(Exception):
    pass


class UnexpectedFormatError(NetworkError):
    """Base class for exceptions in this module."""

    pass


class OpenaiError(Exception):
    """Base class for exceptions in this module."""

    status_code: int
    code: str
    type: str
    message: Optional[str]
    param: Optional[str]

    def __init__(
        self,
        status_code: int,
        code: str,
        error_type: str,
        message: Optional[str] = None,
        param: Optional[str] = None,
    ):
        self.status_code = status_code
        self.code = code
        self.type = error_type
        self.message = message
        self.param = param
        super().__init__(
            f"Error Raised --code {code} --type {error_type} --message {message} --param {param}"
        )


class RateLimitError(OpenaiError):
    """Rate limit error"""

    pass


class AuthenticationError(OpenaiError):
    """Authentication error"""

    pass


class ServiceUnavailableError(OpenaiError):
    """Service unavailable error"""

    pass


class UnexpectedError(OpenaiError):
    """Unexpected error"""

    pass


def raise_error(status_code: int, error_data: dict):
    """
    Raise Error
    {'error': {'message': 'Incorrect API key provided: 123123. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_api_key'}}

    :param status_code: Status Code
    :param error_data: Error Data
    :return:
    """
    if status_code == 429:
        raise RateLimitError(
            status_code=status_code,
            code=error_data.get("code", "429"),
            error_type=error_data.get("type", "RateLimitError"),
            message=error_data.get("message", "Rate Limit Error"),
            param=error_data.get("param", None),
        )
    elif status_code == 404 and not error_data.get("message", None):
        raise ServiceUnavailableError(
            status_code=status_code,
            code=error_data.get("code", "404"),
            error_type=error_data.get("type", "ServiceUnavailableError"),
            message=error_data.get("message", "Service Unavailable Error"),
            param=error_data.get("param", None),
        )
    elif status_code == 500 or status_code != 401:
        raise ServiceUnavailableError(
            status_code=status_code,
            code=error_data.get("code", "500"),
            error_type=error_data.get("type", "ServiceUnavailableError"),
            message=error_data.get("message", "Service Unavailable Error"),
            param=error_data.get("param", None),
        )
    elif status_code == 200:
        raise UnexpectedError(
            status_code=status_code,
            code=error_data.get("code", "200"),
            error_type=error_data.get("type", "UnexpectedError"),
            message=error_data.get("message", "Unexpected Error"),
            param=error_data.get("param", None),
        )
    else:
        raise AuthenticationError(
            status_code=status_code,
            code=error_data.get("code", "401"),
            error_type=error_data.get("type", "AuthenticationError"),
            message=error_data.get("message", "Authentication Error"),
            param=error_data.get("param", None),
        )


if __name__ == "__main__":
    raise OpenaiError(status_code=100, code="100", error_type="100")
