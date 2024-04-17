from llmkira.openapi.hook import resign_hook, Hook, Trigger, run_hook


@resign_hook()
class TestHook(Hook):
    trigger: Trigger = Trigger.SENDER

    async def trigger_hook(self, *args, **kwargs) -> bool:
        print(f"Trigger {args} {kwargs}")
        return True

    async def hook_run(self, *args, **kwargs):
        print(f"Running {args} {kwargs}")
        return args, kwargs


@resign_hook()
class TestHook2(Hook):
    trigger: Trigger = Trigger.SENDER
    priority: int = 1

    async def trigger_hook(self, *args, **kwargs) -> bool:
        print(f"Trigger {args} {kwargs}")
        return True

    async def hook_run(self, *args, **kwargs):
        print(f"Running {args} {kwargs}")
        return args, kwargs


async def run_test():
    print("Before running hook")
    arg, kwarg = await run_hook(Trigger.SENDER, 2, 3, a=4, b=5)
    print(f"After running hook {arg} {kwarg}")


import asyncio  # noqa

asyncio.run(run_test())
