# -*- coding: utf-8 -*-
# @Time    : 2023/10/13 下午1:25
# 探针插件加载机制 参考 nonebot2 项目设计
# https://github.com/nonebot/nonebot2/blob/99931f785a31138a2f6bac1d103551dab47d40f7/nonebot/plugin/manager.py

import importlib
import pkgutil
import sys
from importlib.abc import MetaPathFinder
from importlib.machinery import PathFinder, SourceFileLoader
from itertools import chain
from pathlib import Path
from types import ModuleType
from typing import Optional, Sequence, List, Set, Dict, Iterable

from loguru import logger

from . import (
    _managers,
    _new_plugin,
    _revert_plugin,
    _current_plugin_chain,
    _module_name_to_plugin_name,
    path_to_module_name,
)
from .error import escape_tag, OpenApiError
from .schema import Plugin, PluginMetadata


class PluginManager:
    """插件管理器。

    参数:
        plugins: 独立插件模块名集合。
        search_path: 插件搜索路径（文件夹）。
    """

    def __init__(
        self,
        plugins: Optional[Iterable[str]] = None,
        search_path: Optional[Iterable[str]] = None,
    ):
        # simple plugin not in search path
        self.plugins: Set[str] = set(plugins or [])
        self.search_path: Set[str] = set(search_path or [])

        # cache plugins
        self._third_party_plugin_names: Dict[str, str] = {}
        self._searched_plugin_names: Dict[str, Path] = {}
        self.prepare_plugins()

    def __repr__(self) -> str:
        return f"PluginManager(plugins={self.plugins}, search_path={self.search_path})"

    @property
    def third_party_plugins(self) -> Set[str]:
        """返回所有独立插件名称。"""
        return set(self._third_party_plugin_names.keys())

    @property
    def searched_plugins(self) -> Set[str]:
        """返回已搜索到的插件名称。"""
        return set(self._searched_plugin_names.keys())

    @property
    def available_plugins(self) -> Set[str]:
        """返回当前插件管理器中可用的插件名称。"""
        return self.third_party_plugins | self.searched_plugins

    def _previous_plugins(self) -> Set[str]:
        _pre_managers: List[PluginManager]
        if self in _managers:
            _pre_managers = _managers[: _managers.index(self)]
        else:
            _pre_managers = _managers[:]

        return {
            *chain.from_iterable(manager.available_plugins for manager in _pre_managers)
        }

    def prepare_plugins(self) -> Set[str]:
        """搜索插件并缓存插件名称。"""
        # get all previous ready to load plugins
        previous_plugins = self._previous_plugins()
        searched_plugins: Dict[str, Path] = {}
        third_party_plugins: Dict[str, str] = {}

        # check third party plugins
        for plugin in self.plugins:
            name = _module_name_to_plugin_name(plugin)
            if name in third_party_plugins or name in previous_plugins:
                raise RuntimeError(
                    f"Plugin already exists: {name}! Check your plugin name"
                )
            third_party_plugins[name] = plugin

        self._third_party_plugin_names = third_party_plugins
        # check plugins in search path
        for module_info in pkgutil.iter_modules(self.search_path):
            # ignore if startswith "_"
            if module_info.name.startswith("_"):
                continue

            if (
                module_info.name in searched_plugins
                or module_info.name in previous_plugins
                or module_info.name in third_party_plugins
            ):
                raise RuntimeError(
                    f"Plugin already exists: {module_info.name}! Check your plugin name"
                )
            #
            module_spec = module_info.module_finder.find_spec(module_info.name, None)
            if not module_spec:
                continue
            module_path = module_spec.origin
            if not module_path:
                continue
            searched_plugins[module_info.name] = Path(module_path).resolve()
        self._searched_plugin_names = searched_plugins
        return self.available_plugins

    def load_plugin(self, name: str) -> Optional[Plugin]:
        """加载指定插件。

        对于独立插件，可以使用完整插件模块名或者插件名称。

        参数:
            name: 插件名称。
        """

        try:
            if name in self.plugins:
                module = importlib.import_module(name)
            elif name in self._third_party_plugin_names:
                module = importlib.import_module(self._third_party_plugin_names[name])
            elif name in self._searched_plugin_names:
                module = importlib.import_module(
                    path_to_module_name(self._searched_plugin_names[name])
                )
            else:
                raise RuntimeError(f"Plugin not found: {name}! Check your plugin name")
            plugin = getattr(module, "__plugin__", None)
            if plugin is None or not isinstance(plugin, Plugin):
                raise RuntimeError(
                    f"Module {module.__name__} is not loaded as a plugin! "
                    "Make sure not to import it before loading."
                )
            logger.opt(colors=True).info(
                f'✨ Succeeded to load plugin "<y>{escape_tag(plugin.name)}</y>"'
                + (
                    f' from "<m>{escape_tag(plugin.module_name)}</m>"'
                    if plugin.module_name != plugin.name
                    else ""
                )
            )
            return plugin
        except Exception as e:
            logger.opt(colors=True, exception=e).error(
                f'<r><bg #f5f2f2>Failed to import "{escape_tag(name)}"</bg #f5f2f2></r>'
            )

    def load_all_plugins(self) -> Set[Plugin]:
        """加载所有可用插件。"""

        return set(
            filter(None, (self.load_plugin(name) for name in self.available_plugins))
        )

    @property
    def searched_plugin_names(self):
        return self._searched_plugin_names


class PluginFinder(MetaPathFinder):
    def find_spec(
        self,
        fullname: str,
        path: Optional[Sequence[str]],
        target: Optional[ModuleType] = None,
    ):
        if _managers:
            module_spec = PathFinder.find_spec(fullname, path, target)
            if not module_spec:
                return
            module_origin = module_spec.origin
            if not module_origin:
                return
            module_path = Path(module_origin).resolve()

            for manager in reversed(_managers):
                # use path instead of name in case of submodule name conflict
                if (
                    fullname in manager.plugins
                    or module_path in manager.searched_plugin_names.values()
                ):
                    # print("find_spec",manager, fullname, module_origin)
                    # print(f"module_origin:{module_origin}")
                    module_spec.loader = PluginLoader(manager, fullname, module_origin)
                    return module_spec
        return


class PluginLoader(SourceFileLoader):
    def __init__(self, manager: PluginManager, fullname: str, path) -> None:
        self.manager = manager
        self.loaded = False
        super().__init__(fullname, path)

    def create_module(self, spec) -> Optional[ModuleType]:
        # check self.name in sys.modules to avoid import loop
        if self.name in sys.modules:
            self.loaded = True
            return sys.modules[self.name]
        # return None to use default module creation
        return super().create_module(spec)

    def exec_module(self, module: ModuleType) -> None:
        if self.loaded:
            return

        # create plugin before executing
        plugin = _new_plugin(self.name, module, self.manager)
        setattr(module, "__plugin__", plugin)

        # detect parent plugin before entering current plugin context
        parent_plugins = _current_plugin_chain.get()
        for pre_plugin in reversed(parent_plugins):
            # ensure parent plugin is declared before current plugin
            if _managers.index(pre_plugin.manager) < _managers.index(self.manager):
                plugin.parent_plugin = pre_plugin
                pre_plugin.sub_plugins.add(plugin)
                break

        # enter plugin context
        _plugin_token = _current_plugin_chain.set(parent_plugins + (plugin,))

        try:
            super().exec_module(module)
        except OpenApiError as e:
            _revert_plugin(plugin)
            logger.error(f"\n🔧{e}")
            raise
        except Exception:
            _revert_plugin(plugin)
            raise
        except SystemExit:
            _revert_plugin(plugin)
            raise RuntimeError(
                f"Plugin {self.name} exited with status 0. "
                "Plugins should not call sys.exit()!"
            )
        finally:
            # leave plugin context
            _current_plugin_chain.reset(_plugin_token)
        # get plugin metadata
        metadata: Optional[PluginMetadata] = getattr(module, "__plugin_meta__", None)
        # 校验
        if not metadata:
            raise RuntimeError(
                f"Plugin {self.name} does not provide metadata! "
                "Make sure to declare it before importing."
            )

        plugin.metadata = metadata
        return


sys.meta_path.insert(0, PluginFinder())
