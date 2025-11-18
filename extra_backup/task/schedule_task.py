import re
import schedule
import time
from functools import partial
from mcdreforged.api.all import *

from extra_backup.config.main_config import Config
from extra_backup.lang.lang_processor import tr
from extra_backup.task.main_task import States

class Scheduler:
    job = None
    def __init__(self, task_name):
        self.server: PluginServerInterface = Config().server
        self.task_name = task_name

    @staticmethod
    def time_loader(s: str) -> int:
        # 把类似 "1h30m", "2d3h15m20s" 转换成总秒数
        units = {
            "s": 1,
            "m": 60,
            "h": 3600,
            "d": 86400
        }
        matches = re.findall(r"(\d+)([smhd])", s.strip().lower())
        if not matches:
            raise ValueError(tr("schedule_invalid_time", time=s))
        total_seconds = sum(int(num) * units[unit] for num, unit in matches)
        return total_seconds

    def set_schedule_thread(self, function, **kwargs):
        if States().schedule_task_state[self.task_name]=="true":
            seconds = self.time_loader(Config().get("schedule_"+self.task_name)["interval"])
            self.job = schedule.every(seconds).seconds.do(partial(function, **kwargs))
            self.server.logger.info(tr("schedule_enabled", task=tr(self.task_name)))
        else:
            self.server.logger.info(tr("schedule_disabled",task=tr(self.task_name)))

    @new_thread
    def start_schedule_thread(self):
        failures = 0
        while States().schedule_task_state[self.task_name]=="true":
            try:
                schedule.run_pending()
                failures = 0
            except Exception as e:
                failures += 1
                self.server.logger.error(tr("schedule_fail", task=tr(self.task_name), error=e))
                if failures > 3:
                    self.server.logger.error(tr("schedule_fail_stopped", task=tr(self.task_name)))
                    break
                self.server.logger.warning(tr("schedule_retry", task=tr(self.task_name)))
                time.sleep(60)
            time.sleep(0.5)
        schedule.cancel_job(self.job)
        self.server.logger.info(tr("schedule_stopped", task=tr(self.task_name)))