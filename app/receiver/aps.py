# -*- coding: utf-8 -*-
# @Time    : 2023/8/18 下午8:34
# @Author  : sudoskys
# @File    : aps.py
# @Software: PyCharm
from pathlib import Path

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from pytz import utc
from tzlocal import get_localzone
Path(".cache").mkdir(exist_ok=True)
jobstores = {"default": SQLAlchemyJobStore(url="sqlite:///.cache/aps.db")}
executors = {"default": ThreadPoolExecutor(20)}
job_defaults = {"coalesce": False, "max_instances": 3}

SCHEDULER = AsyncIOScheduler(
    job_defaults=job_defaults, timezone=get_localzone(), executors=executors, jobstores=jobstores
)


async def aps_start():
    logger.success("Receiver Runtime:APS Timer start")
    SCHEDULER.start()
