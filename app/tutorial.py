# -*- coding: utf-8 -*-
# @Time    : 2023/10/28 下午4:19
# @Author  : sudoskys
# @File    : tutorial.py
# @Software: PyCharm
import pathlib
from time import sleep

import elara
from rich.console import Console

elara_client = elara.exe(
    path=pathlib.Path(__file__).parent / ".tutorial.db", commitdb=True
)

tutorial = [
    {
        "cn": "接下来进行一些说明，如果您不想看到这些说明，请使用 --no-tutorial 参数运行入口文件。",
        "en": "Next, some instructions will be given. "
        "If you don’t want to see these instructions, please run the entry file with the --no-tutorial flag.",
    },
    {
        "cn": "请您在 .env 文件中填写您的配置信息。"
        "您可以通过 `docker-compose up -f docker-compose.yml` 来测试服务。",
        "en": "Please fill in your configuration information in the .env file. "
        "You can test the service by `docker-compose up -f docker-compose.yml`.",
    },
    {
        "cn": "数据库 RabbitMQ 的默认端口为 5672，Redis 的默认端口为 6379，MongoDB 的默认端口为 27017。"
        "请您考虑是否需要添加防火墙配置。其中，RabbitMQ 和 MongoDB 均使用默认配置了密码。请查看 .env 文件进行修改。",
        "en": "The default port of the database RabbitMQ is 5672, "
        "the default port of Redis is 6379, and the default port of MongoDB is 27017."
        "Please consider whether to add firewall configuration. "
        "Among them, RabbitMQ and MongoDB use the default configuration password. "
        "Please check the .env file for modification.",
    },
    {
        "cn": "请当心您的 .env 文件，其中包含了您的敏感信息。请不要将 .env 文件上传到公共仓库。",
        "en": "Please be careful with your .env file, "
        "which contains your sensitive information. "
        "Please do not upload the .env file to the public repository.",
    },
    {
        "cn": "请当心您的 日志文件，其中包含了您的敏感信息。请不要将 日志文件上传到公共仓库。",
        "en": "Please be careful with your log file, which contains your sensitive information. "
        "Please do not upload the log file to the public repository.",
    },
    {
        "cn": "如果您在使用过程中遇到了问题，可以在 GitHub 上提出 issue 来完善测试。",
        "en": "If you encounter any problems during use, you can raise an issue on GitHub to improve the test.",
    },
]
tutorial_len = len(tutorial)


def show_tutorial(
    skip_existing: bool = False, pre_step_stop: int = 5, database_key: str = "55123"
):
    global tutorial, elara_client, tutorial_len
    lens = elara_client.get(database_key)
    if skip_existing and str(lens) == str(len(tutorial)):
        return None
    # 截取未读的条目
    tutorial = tutorial[lens:] if skip_existing else tutorial
    console = Console()
    print("\n")
    with console.status("[bold green]Working on tasks...[/bold green]") as status:
        index = 0
        while tutorial:
            info = tutorial.pop(0)
            index += 1
            console.print(info["cn"], style="bold cyan")
            console.print(info["en"], style="bold green", end="\n\n")
            for i in range(pre_step_stop):
                status.update(
                    f"[bold green]({index}/{tutorial_len})Remaining {pre_step_stop - i} "
                    f"seconds to next info... [/bold green] "
                )
                sleep(1)

    # 更新进度
    elara_client.set(database_key, tutorial_len)
    sleep(3)
