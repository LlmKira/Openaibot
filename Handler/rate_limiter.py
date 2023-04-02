# -*- coding: utf-8 -*-
# @Time    : 2023/3/30 下午5:23
# @Author  : sudoskys
# @File    : rate_limiter.py
# @Software: PyCharm
import time


# RateLimiter is a simple rate limiter that allows a maximum number of requests
# within a given interval. It is not thread-safe.
# Example usage:
# limiter = RateLimiter(5, 60)
# if limiter.allow_request():
#     print("Request allowed")
# else:
#     print("Request denied")


class RateLimiter(object):
    def __init__(self, max_requests, interval):
        self.max_requests = max_requests
        self.interval = interval
        self.requests = []

    def allow_request(self):
        now = int(time.time())
        cutoff = now - self.interval

        # Remove any requests that fall outside the interval window
        self.requests = [r for r in self.requests if r > cutoff]

        # Check if the number of remaining requests is less than the allowed maximum
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        else:
            return False


class UsageLimiter:
    def __init__(self, limit_usage, limit_time=1):
        self.usage_dict = {}
        self.limit_time = limit_time
        self.limit_usage = limit_usage

    async def check_usage(self, uid, usage):
        current_time = int(time.time())
        if uid not in self.usage_dict:
            self.usage_dict[uid] = {"usage": 0, "last_time": current_time}
        elif current_time - self.usage_dict[uid]["last_time"] >= self.limit_time:
            self.usage_dict[uid]["usage"] = 0
            self.usage_dict[uid]["last_time"] = current_time
        if self.usage_dict[uid]["usage"] + usage <= self.limit_usage:
            self.usage_dict[uid]["usage"] += usage
            return True
        else:
            return False
