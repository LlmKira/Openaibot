# 用于在输出输入的时候，替换输入输出的数据，达成多媒体的目的。附加媒体文件查询，等等。
from abc import abstractmethod
from enum import Enum
from typing import Type, Set, TypeVar

from loguru import logger
from pydantic import BaseModel

T = TypeVar("T")


class Trigger(Enum):
    SENDER = "sender"
    RECEIVER = "receiver"


class Hook(BaseModel):
    trigger: Trigger = Trigger.RECEIVER
    priority: int = 0

    @abstractmethod
    async def trigger_hook(self, *args, **kwargs) -> bool:
        return True

    @abstractmethod
    async def hook_run(self, *args, **kwargs) -> T:
        pass


__hook__: Set[Type[Hook]] = set()


def resign_hook():
    def decorator(cls: Type[Hook]):
        if issubclass(cls, Hook):
            logger.success(f"📦 [Resign Hook] {type(cls)}")
            __hook__.add(cls)
        else:
            raise ValueError(f"Resign Hook Error for unknown cls {type(cls)} ")

        return cls

    return decorator


async def run_hook(trigger: Trigger, *args: T, **kwargs) -> T:
    hook_instances = [hook_cls() for hook_cls in __hook__]
    sorted_hook_instances = sorted(
        hook_instances, key=lambda x: x.priority, reverse=True
    )
    for hook_instance in sorted_hook_instances:
        if hook_instance.trigger == trigger:
            if await hook_instance.trigger_hook(*args, **kwargs):
                try:
                    args, kwargs = await hook_instance.hook_run(*args, **kwargs)
                except Exception as ex:
                    logger.exception(f"Hook Run Error {ex}")
    return args, kwargs
