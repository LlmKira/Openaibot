# -*- coding: utf-8 -*-
# @Time    : 2023/8/15 下午10:29
# @Author  : sudoskys
# @File    : error.py
# @Software: PyCharm


class ValidationError(Exception):
    pass


class AuthenticationError(Exception):
    """
    Raised when the API key is invalid.
    """
    pass


class RateLimitError(Exception):
    """
    Raised when the API key has exceeded its rate limit.
    """
    pass


class ServiceUnavailableError(Exception):
    """
    Raised when the API is unavailable.
    """
    pass
