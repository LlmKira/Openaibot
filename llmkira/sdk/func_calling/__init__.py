# -*- coding: utf-8 -*-
# 探针插件加载机制 参考 nonebot2 项目设计
# https://github.com/nonebot/nonebot2/blob/99931f785a31138a2f6bac1d103551dab47d40f7/nonebot/plugin/manager.py

from contextvars import ContextVar
from itertools import chain
from pathlib import Path
from types import ModuleType
from typing import Optional, List, Set, Dict, Tuple, Any

from pydantic import BaseModel

from .error import OpenApiError

_plugins: Dict[str, "Plugin"] = {}
_managers: List["PluginManager"] = []
_current_plugin_chain: ContextVar[Tuple["Plugin", ...]] = ContextVar(
    "_current_plugin_chain", default=tuple()
)


class FrameworkInfo(BaseModel):
    support: bool
    exception: Optional[str] = None


_current_openapi_version_: str = "20231017"
_openapi_version_: Dict[str, "FrameworkInfo"] = {
    _current_openapi_version_: FrameworkInfo(
        support=True,
        exception=None
    ),
    "20231013": FrameworkInfo(
        support=False,
        exception="Chain Manager changed in ver.20231017"
    )
}


def verify_openapi_version(name: str, openapi_version: str):
    """
    验证框架接口版本
    """
    if not openapi_version:
        return None
    frame = _openapi_version_.get(openapi_version, None)
    if not frame:
        raise OpenApiError(
            f"OpenApiError:Plugin<{name}> --error {openapi_version} not support")
    if not frame.support:
        raise OpenApiError(
            f"OpenApiError:Plugin<{name}> --error {frame.exception}")


def path_to_module_name(path: Path) -> str:
    rel_path = path.resolve().relative_to(Path("").resolve())
    if rel_path.stem == "__init__":
        return ".".join(rel_path.parts[:-1])
    else:
        return ".".join(rel_path.parts[:-1] + (rel_path.stem,))


def get_plugin(name: str) -> Optional["Plugin"]:
    """获取已经导入的某个插件。

    如果为 `load_plugins` 文件夹导入的插件，则为文件(夹)名。

    参数:
        name: 插件名，即 {ref}`extra.plugin.model.Plugin.name`。
    """
    return _plugins.get(name)


def get_loaded_plugins() -> Set["Plugin"]:
    """获取当前已导入的所有插件。"""
    return set(_plugins.values())


def get_entrypoint_plugins(group="llmkira.extra.plugin") -> Set[str]:
    import importlib_metadata
    hook = importlib_metadata.entry_points().select(group=group)
    plugins = [item.module for item in hook]
    return {*plugins}


def get_available_plugin_names() -> Set[str]:
    """获取当前所有可用的插件名（包含尚未加载的插件）。"""
    return {*chain.from_iterable(manager.available_plugins for manager in _managers)}


def _find_manager_by_name(name: str) -> Optional[Any]:
    for manager in reversed(_managers):
        if name in manager.plugins or name in manager.searched_plugins:
            return manager


def _module_name_to_plugin_name(module_name: str) -> str:
    return module_name.rsplit(".", 1)[-1]


def _new_plugin(module_name: str, module: ModuleType, manager: "PluginManager") -> "Plugin":
    """
    Create a new plugin
    """
    plugin_name = _module_name_to_plugin_name(module_name)
    if plugin_name in _plugins:
        raise RuntimeError("Plugin already exists! Check your plugin name.")
    plugin = Plugin(plugin_name, module, module_name, manager)
    _plugins[plugin_name] = plugin
    return plugin


def _revert_plugin(plugin: "Plugin") -> None:
    """
    Revert a plugin
    删除创建的链
    :param plugin: Plugin to revert
    """
    if plugin.name not in _plugins:
        raise RuntimeError("Plugin not found!")
    del _plugins[plugin.name]
    parent_plugin = plugin.parent_plugin
    if parent_plugin:
        parent_plugin.sub_plugins.remove(plugin)


from .loader import PluginManager
from .schema import Plugin as Plugin, BaseTool
from .loader import require as require
from .loader import load_plugin as load_plugin
from .loader import load_plugins as load_plugins
from .loader import load_all_plugins as load_all_plugins
from .loader import load_builtin_plugin as load_builtin_plugin
from .loader import load_builtin_plugins as load_builtin_plugins
from .loader import load_from_entrypoint as load_from_entrypoint
from .loader import PluginManager as PluginManager

from .model import Plugin as Plugin
from .model import PluginMetadata as PluginMetadata

from .register import ToolRegister as ToolRegister
