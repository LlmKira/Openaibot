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

"""
from apscheduler.jobstores.redis import RedisJobStore
from redis.connection import ConnectionPool
import os
redis_url = os.getenv('REDIS_DSN', 'redis://localhost:6379/0')
job_store = RedisJobStore(
    connection_pool=ConnectionPool().from_url(redis_url)
)
"""
Path("config_dir").mkdir(exist_ok=True)
jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///config_dir/aps.db')
}
executors = {
    'default': ThreadPoolExecutor(20)
}
job_defaults = {
    'coalesce': False,
    'max_instances': 3
}
from pytz import utc

SCHEDULER = AsyncIOScheduler(job_defaults=job_defaults,
                             timezone=utc,
                             executors=executors,
                             jobstores=jobstores
                             )


async def aps_start():
    logger.success("Receiver Runtime:APS Timer start")
    SCHEDULER.start()
