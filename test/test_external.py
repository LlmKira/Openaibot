# -*- coding: utf-8 -*-
# @Time    : 2023/11/14 上午10:09
# @Author  : sudoskys
# @File    : test_external.py
# @Software: PyCharm
import sys

sys.path.append("..")

from pydantic import ValidationError

from llmkira.external.schema import PluginExternal, PluginTestResultExport


def test_install():
    try:
        _install = PluginExternal.Install()
    except ValidationError as e:
        print("Cant init from empty")
    _install = PluginExternal.Install(pypi="test")
    _install = PluginExternal.Install(github="https://github.com/llmkira/")
    _install = PluginExternal.Install(shell="pip install llmkira")


def test_schema():
    _install = PluginExternal.Install(
        shell="pip install llmkira"
    )
    _external = PluginExternal(
        author_id="test",
        plugin_name="test.test.plugin",
        plugin_link="https://test.com",
        plugin_desc="desc",
        plugin_functions=[
            "test_func"
        ],
        org_id="test_org",
        plugin_install=_install
    )
    _result = PluginTestResultExport(plugin=_external, test_pass=True, out_date=True)
    assert _result
