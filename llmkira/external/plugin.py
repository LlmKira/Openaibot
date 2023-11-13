# -*- coding: utf-8 -*-
from llmkira.external.schema import PluginExternal

# ========== CHANGE FOLLOWING BLOCK TO ADD YOUR OWN PLUGIN ========== #
EXPORT = [
    PluginExternal(
        plugin_name="llmbot_plugin_bilisearch",
        plugin_link="https://github.com/LlmKira/llmbot_plugin_bilisearch",
        plugin_desc="通过自然语言调用哔哩哔哩搜索",
        plugin_functions=[
            "search_in_bilibili"
        ],
        org_id=None,
        author_id="sudoskys",
        plugin_install=PluginExternal.Install(
            shell="pip3 install llmbot_plugin_bilisearch",
            pypi="llmbot_plugin_bilisearch",
            github=None,
        )
    )
]
# ========== CHANGE ABOVE BLOCK TO ADD YOUR OWN PLUGIN ==========#
