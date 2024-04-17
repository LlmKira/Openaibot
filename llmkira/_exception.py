# -*- coding: utf-8 -*-
# @Time    : 2023/10/30 下午3:42


class LlmkiraException(Exception):
    pass


class SettingError(LlmkiraException):
    pass


class CacheDatabaseError(LlmkiraException):
    pass
