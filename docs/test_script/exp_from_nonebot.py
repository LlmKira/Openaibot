# -*- coding: utf-8 -*-
import importlib
import pkgutil
import sys
from contextvars import ContextVar
from dataclasses import dataclass, field
from importlib.abc import MetaPathFinder
from importlib.machinery import PathFinder, SourceFileLoader
from itertools import chain
from pathlib import Path
from types import ModuleType
from typing import Optional, Sequence, List, Set, Type, Dict, Tuple, Any, Union, Iterable

from loguru import logger
from pydantic import BaseModel

_plugins: Dict[str, "Plugin"] = {}
_managers: List["PluginManager"] = []
_current_plugin_chain: ContextVar[Tuple["Plugin", ...]] = ContextVar(
    "_current_plugin_chain", default=tuple()
)


def path_to_module_name(path: Path) -> str:
    rel_path = path.resolve().relative_to(Path("").resolve())
    if rel_path.stem == "__init__":
        return ".".join(rel_path.parts[:-1])
    else:
        return ".".join(rel_path.parts[:-1] + (rel_path.stem,))


@dataclass(eq=False)
class PluginMetadata:
    """插件元信息，由插件编写者提供"""

    name: str
    """插件名称"""
    description: str
    """插件功能介绍"""
    usage: str
    """插件使用方法"""
    type: Optional[str] = None
    """插件类型，用于商店分类"""
    homepage: Optional[str] = None
    """插件主页"""
    config: Optional[Type[BaseModel]] = None
    """插件配置项"""
    supported_adapters: Optional[Set[str]] = None
    """插件支持的适配器模块路径
    格式为 `<module>[:<Adapter>]`，`~` 为 `nonebot.adapters.` 的缩写。
    `None` 表示支持**所有适配器**。
    """
    extra: Dict[Any, Any] = field(default_factory=dict)
    """插件额外信息，可由插件编写者自由扩展定义"""


@dataclass(eq=False)
class Plugin:
    """存储插件信息"""

    name: str
    """插件索引标识，Bot 使用 文件/文件夹 名称作为标识符"""
    module: ModuleType
    """插件模块对象"""
    module_name: str
    """点分割模块路径"""
    manager: "PluginManager"
    """导入该插件的插件管理器"""
    parent_plugin: Optional["Plugin"] = None
    """父插件"""
    metadata: Optional[PluginMetadata] = None


def load_all_plugins(
        module_path: Iterable[str], plugin_dir: Iterable[str]
) -> Set[Plugin]:
    """导入指定列表中的插件以及指定目录下多个插件，以 `_` 开头的插件不会被导入!

    参数:
        module_path: 指定插件集合
        plugin_dir: 指定文件夹路径集合
    """
    manager = PluginManager(module_path, plugin_dir)
    _managers.append(manager)
    return manager.load_all_plugins()


def load_plugins(*plugin_dir: str) -> Set[Plugin]:
    """导入文件夹下多个插件，以 `_` 开头的插件不会被导入!

    参数:
        plugin_dir: 文件夹路径
    """
    manager = PluginManager(search_path=plugin_dir)
    _managers.append(manager)
    return manager.load_all_plugins()


def load_builtin_plugin(name: str) -> Optional[Plugin]:
    """导入 Bot 内置插件。

    参数:
        name: 插件名称
    """
    return load_plugin(f"nonebot.plugins.{name}")


def load_builtin_plugins(*plugins: str) -> Set[Plugin]:
    """导入多个 Bot 内置插件。

    参数:
        plugins: 插件名称列表
    """
    return load_all_plugins([f"nonebot.plugins.{p}" for p in plugins], [])


def load_plugin(module_path: Union[str, Path]) -> Optional[Plugin]:
    """加载单个插件，可以是本地插件或是通过 `pip` 安装的插件。

    参数:
        module_path: 插件名称 `path.to.your.plugin`
            或插件路径 `pathlib.Path(path/to/your/plugin)`
    """
    module_path = (
        path_to_module_name(module_path)
        if isinstance(module_path, Path)
        else module_path
    )
    manager = PluginManager([module_path])
    _managers.append(manager)
    return manager.load_plugin(module_path)


def get_plugin(name: str) -> Optional["Plugin"]:
    """获取已经导入的某个插件。

    如果为 `load_plugins` 文件夹导入的插件，则为文件(夹)名。

    参数:
        name: 插件名，即 {ref}`nonebot.plugin.model.Plugin.name`。
    """
    return _plugins.get(name)


def get_loaded_plugins() -> Set["Plugin"]:
    """获取当前已导入的所有插件。"""
    return set(_plugins.values())


def get_available_plugin_names() -> Set[str]:
    """获取当前所有可用的插件名（包含尚未加载的插件）。"""
    return {*chain.from_iterable(manager.available_plugins for manager in _managers)}


def _find_manager_by_name(name: str) -> Optional[Any]:
    for manager in reversed(_managers):
        if name in manager.plugins or name in manager.searched_plugins:
            return manager


def require(name: str) -> ModuleType:
    """获取一个插件的导出内容。

    如果为 `load_plugins` 文件夹导入的插件，则为文件(夹)名。

    参数:
        name: 插件名，即 {ref}`nonebot.plugin.model.Plugin.name`。

    异常:
        RuntimeError: 插件无法加载
    """
    plugin = get_plugin(_module_name_to_plugin_name(name))
    # if plugin not loaded
    if not plugin:
        # plugin already declared
        if manager := _find_manager_by_name(name):
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

            if not (
                    module_spec := module_info.module_finder.find_spec(
                        module_info.name, None
                    )
            ):
                continue
            if not (module_path := module_spec.origin):
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

            logger.info(
                f'Succeeded to import "<y>{(name)}</y>"'
            )
            if (plugin := getattr(module, "__plugin_meta__", None)) is None:
                raise RuntimeError(
                    f"Module {module.__name__} is not loaded as a plugin! "
                    "Make sure not to import it before loading."
                )
            return plugin
        except Exception as e:
            logger.exception(
                f'Failed to import "{(name)} {e}"'
            )

    def load_all_plugins(self) -> Set[Plugin]:
        """加载所有可用插件。"""

        return set(
            filter(None, (self.load_plugin(name) for name in self.available_plugins))
        )


def _module_name_to_plugin_name(module_name: str) -> str:
    return module_name.rsplit(".", 1)[-1]


def _new_plugin(
        module_name: str, module: ModuleType, manager: "PluginManager"
) -> "Plugin":
    plugin_name = _module_name_to_plugin_name(module_name)
    if plugin_name in _plugins:
        raise RuntimeError("Plugin already exists! Check your plugin name.")
    plugin = Plugin(plugin_name, module, module_name, manager)
    _plugins[plugin_name] = plugin
    return plugin


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
                        or module_path in manager._searched_plugin_names.values()
                ):
                    # print("find_spec",manager, fullname, module_origin)
                    print(f"module_origin:{module_origin}")
                    module_spec.loader = PluginLoader(manager, fullname, module_origin)
                    return module_spec
        return


def _revert_plugin(plugin: "Plugin") -> None:
    if plugin.name not in _plugins:
        raise RuntimeError("Plugin not found!")
    del _plugins[plugin.name]
    if parent_plugin := plugin.parent_plugin:
        parent_plugin.sub_plugins.remove(plugin)


class PluginLoader(SourceFileLoader):
    def __init__(self,
                 manager: PluginManager, fullname: str, path) -> None:
        self.manager = manager
        self.loaded = False
        super().__init__(fullname, path)

    def create_module(self, spec) -> Optional[ModuleType]:
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
        setattr(module, "plugin", plugin)

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
        except Exception:
            _revert_plugin(plugin)
            raise
        finally:
            # leave plugin context
            _current_plugin_chain.reset(_plugin_token)

        # get plugin metadata
        metadata: Optional[PluginMetadata] = getattr(module, "plugin_meta", None)
        plugin.metadata = metadata

        return


load_all_plugins([], ["test_plugin"])

sys.meta_path.insert(0, PluginFinder())
load_plugin("test_plugin")

print(get_plugin("arg"))
print(_managers)
print(_plugins)
print(get_loaded_plugins())
