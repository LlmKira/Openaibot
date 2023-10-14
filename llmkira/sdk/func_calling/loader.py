# -*- coding: utf-8 -*-

from pathlib import Path
from types import ModuleType
from typing import Optional, Set, Iterable, Union

from . import (
    _managers,
    _current_plugin_chain,
    _module_name_to_plugin_name,
    path_to_module_name, _find_manager_by_name, get_plugin,
)
from .model import PluginManager
from .schema import Plugin


def load_all_plugins(module_path: Iterable[str], plugin_dir: Iterable[str]) -> Set[Plugin]:
    """
    导入指定列表中的插件以及指定目录下多个插件，以 `_` 开头的插件不会被导入!
    :param module_path: 指定插件集合
    :param plugin_dir: 指定文件夹路径集合
    """
    manager = PluginManager(module_path, plugin_dir)
    _managers.append(manager)
    return manager.load_all_plugins()


def load_plugins(*plugin_dir: str) -> Set[Plugin]:
    """
    导入文件夹下多个插件，以 `_` 开头的插件不会被导入!
    :param plugin_dir: 文件夹路径
    :return: 插件集合
    """
    manager = PluginManager(search_path=plugin_dir)
    _managers.append(manager)
    return manager.load_all_plugins()


def load_builtin_plugin(name: str) -> Optional[Plugin]:
    """导入 Bot 内置插件。
    :param name: 插件名称
    :return: 插件
    """
    return load_plugin(f"extra.plugins.{name}")


def load_builtin_plugins(*plugins: str) -> Set[Plugin]:
    """导入多个 Bot 内置插件。
    :param plugins: 插件名称集合
    """
    return load_all_plugins([f"extra.plugins.{p}" for p in plugins], [])


def load_plugin(module_path: Union[str, Path]) -> Optional[Plugin]:
    """
    加载单个插件，可以是本地插件或是通过 `pip` 安装的插件。
    :param module_path: 插件名称 `path.to.your.plugin`
            或插件路径 `pathlib.Path(path/to/your/plugin)`
    :return: 插件
    """
    module_path = (
        path_to_module_name(module_path)
        if isinstance(module_path, Path)
        else module_path
    )
    manager = PluginManager([module_path])
    _managers.append(manager)
    return manager.load_plugin(module_path)


def load_from_entrypoint(group="llmkira.extra.plugin") -> Set[Plugin]:
    import importlib_metadata
    hook = importlib_metadata.entry_points().select(group=group)
    plugins = [item.module for item in hook]
    return load_all_plugins(plugins, [])


def require(name: str) -> ModuleType:
    """
    获取一个插件的导出内容。
    如果为 `load_plugins` 文件夹导入的插件，则为文件(夹)名。
    :param name: 插件名称 即 {ref}`extra.plugin.model.Plugin.name`。
    :exception RuntimeError: 插件无法加载
    :return: 插件导出内容
    """
    plugin = get_plugin(_module_name_to_plugin_name(name))
    # if plugin not loaded
    if not plugin:
        # plugin already declared
        manager = _find_manager_by_name(name)
        if manager:
            plugin = manager.load_plugin(name)
        # plugin not declared, try to declare and load it
        else:
            # clear current plugin chain, ensure plugin loaded in a new context
            _t = _current_plugin_chain.set(())
            try:
                plugin = load_plugin(name)
            finally:
                _current_plugin_chain.reset(_t)
    if not plugin:
        raise RuntimeError(f'Cannot load plugin "{name}"!')
    return plugin.module
