import asyncio
import json
import pathlib
import tzlocal
import tempfile
import time
from collections import deque
from typing import Optional, Union, Callable, Awaitable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from App import Event
from utils import Setting, Sticker
from utils.Blip import BlipServer, FileReader
from utils.Chat import Utils, PhotoRecordUtils, ConfigUtils
from utils.Data import DefaultData, User_Message, create_message, PublicReturn, Service_Data
from utils.Frequency import Vitality

from nakuru import (
    CQHTTP,
    GroupMessage,
    PrivateMessage,
    FriendRequest
)
from nakuru.entities.components import Plain

_service = Service_Data.get_key()