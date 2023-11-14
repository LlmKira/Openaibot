# -*- coding: utf-8 -*-
# @Time    : 2023/11/13 下午3:55
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
from typing import Optional, List

from pydantic import BaseModel, Field, model_validator


class PluginExternal(BaseModel):
    class Install(BaseModel):
        shell: Optional[str] = Field(None, title="shell安装命令")
        pypi: Optional[str] = Field(None, title="pypi安装命令")
        github: Optional[str] = Field(None, title="github安装命令")

        @model_validator(mode="after")
        def available_check(self):
            if not any([self.shell, self.pypi, self.github]):
                raise ValueError("At least one of install must be available")
            return self

    plugin_name: str = Field(..., title="插件名称")
    plugin_link: str = Field(..., title="插件链接")
    plugin_desc: str = Field(..., title="插件描述")
    plugin_functions: List[str] = Field(..., title="插件功能")
    org_id: Optional[str] = Field(None, title="组织ID")
    author_id: str = Field(..., title="作者ID")
    plugin_install: Install = Field(..., title="插件安装方式")


class PluginTestResultExport(BaseModel):
    plugin: PluginExternal = Field(..., title="插件信息")
    test_pass: bool = Field(..., title="测试是否通过")
    out_date: bool = Field(..., title="是否过期")
