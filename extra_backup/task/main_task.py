from extra_backup.utils.Singleton import singleton
from extra_backup.config.main_config import Config

@singleton
class States:
    _initialized = False

    schedule_task_state = {}


    Uploading = False
    Downloading = False

    task_queue = {}


    def __init__(self):
        if self._initialized:
            return
        self.schedule_task_state["backup"]=Config().get("schedule_backup")["enable"]
        self.schedule_task_state["prune"]=Config().get("schedule_prune")["enable"]
        self._initialized = True