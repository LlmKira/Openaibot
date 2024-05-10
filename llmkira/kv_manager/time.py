import datetime

from llmkira.kv_manager._base import KvManager


def hours_difference(timestamp1: int, timestamp2: int) -> float:
    """
    Calculate the difference between two timestamps in hours
    :param timestamp1: timestamp 1
    :param timestamp2: timestamp 2
    :return: difference in hours
    """
    # convert timestamp to datetime object
    dt_object1 = datetime.datetime.fromtimestamp(timestamp1)
    dt_object2 = datetime.datetime.fromtimestamp(timestamp2)

    # calculate the difference
    time_diff = dt_object1 - dt_object2

    # return the difference in hours
    return round(abs(time_diff.total_seconds() / 3600), 2)


class TimeFeelManager(KvManager):
    def __init__(self, user_id: str):
        self.user_id = str(user_id)

    def prefix(self, key: str) -> str:
        return f"time_feel:{key}"

    async def get_leave(self) -> str:
        now_timestamp = int(datetime.datetime.now().timestamp())
        try:
            hours = await self.read_data(self.user_id)
            if isinstance(hours, bytes):
                hours = hours.decode("utf-8")
            if not hours:
                raise LookupError("No data")
            last_timestamp = int(hours)
        except LookupError:
            last_timestamp = now_timestamp
        finally:
            # 存储当前时间戳
            await self.save_data(self.user_id, str(now_timestamp))
        # 计算时间小时差，如果大于 1 小时，返回小时，否则返回None
        diff = hours_difference(now_timestamp, last_timestamp)
        if diff > 1:
            return f"{diff} hours"
