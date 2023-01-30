from apscheduler.schedulers.background import BackgroundScheduler

class Trigger: # Trigger Class
    def __init__(self):
        import pytz
        self.tz = pytz.timezone("Asia/Shanghai")
    def parse_time(self, time_str):
        from apscheduler.triggers.interval import IntervalTrigger
        result = {"s": 0, "m": 0, "h": 0, "d": 0}
        for unit in ("d", "h", "m", "s"):
            if unit in time_str:
                pos = time_str.find(unit)
                result[unit] = int(time_str[:pos])
                time_str = time_str[pos + 1:]
        return IntervalTrigger(seconds=result['s'],
                               minutes=result['m'],
                               hours=result['h'],
                               days=result['d'],
                               timezone=self.tz
                               )

class Schedule:
    def __init__(self):
        self.schedule = BackgroundScheduler()
        self.currentTaskID = 0
        self.trigger = Trigger()
        self.schedule.start()
    def add_job(self, target, parameter, time_str):
        job = self.schedule.add_job(target,
                                    trigger=self.trigger.parse_time(time_str),
                                    args=(parameter,),
                                    id=self.currentTaskID,
                                    replace_existing=True)
        self.currentTaskID += 1
        return job, self.currentTaskID - 1  #老id
    def remove_job(self, job_id):
        self.schedule.remove_job(job_id)