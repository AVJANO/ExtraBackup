import os
import time

from mcdreforged.api.all import *

from extra_backup.config.backup_config import BackupConfig
from extra_backup.config.main_config import Config
from extra_backup.config.main_config import DefaultConfig
from extra_backup.lang.lang_processor import tr
from extra_backup.task.schedule_task import Scheduler
from extra_backup.file_manager.local_processor import LocalProcessor as LP

class Pruner:
    @staticmethod
    @new_thread
    def prune(id: str | None, source: CommandSource):
        source.reply(tr("prune_start", id = "" if id is None else id))
        if Config().get("schedule_prune")["prune_downloads"] == "true":
            for file in os.listdir(DefaultConfig().download_path):
                if time.time() - os.path.getmtime(os.path.join(DefaultConfig().download_path, file)) > Scheduler.time_loader(Config().get("schedule_prune")["max_lifetime"]):
                    LP.delete(file,
                              {"address":DefaultConfig().download_path},
                              tr("exb_downloads"),
                              source)
        if Config().get("schedule_prune")["prune_exports"] == "true":
            for file in os.listdir(DefaultConfig().pb_export_path):
                if time.time() - os.path.getmtime(os.path.join(DefaultConfig().pb_export_path, file)) > Scheduler.time_loader(Config().get("schedule_prune")["max_lifetime"]):
                    LP.delete(file,
                              {"address":DefaultConfig().pb_export_path},
                              tr("pb_exports"),
                              source)
        for backup_path in BackupConfig().backup_list:
            if BackupConfig().backup_list[backup_path]["enable"] == "true":
                match BackupConfig().backup_list[backup_path]["mode"]:
                    case "local":
                        if id is None:
                            for file in os.listdir(BackupConfig().backup_list[backup_path]["address"]):
                                if time.time() - os.path.getmtime(os.path.join(BackupConfig().backup_list[backup_path]["address"],file)) > Scheduler.time_loader(Config().get("schedule_prune")["max_lifetime"]):
                                    LP.delete(file,
                                              BackupConfig().backup_list[backup_path],
                                              backup_path,
                                              source)
                        else:
                            LP.delete(f"backup_{id}.tar",
                                      BackupConfig().backup_list[backup_path],
                                      backup_path,
                                      source)
                    case "ftp":
                        ...
                    case "smb":
                        ...
                    case "sftp":
                        ...
                    case _:
                        ...
        source.reply(RText(tr("prune_complete"), RColor.green))

    @staticmethod
    @new_thread
    def delete(id, backup_path, source: CommandSource):
        source.reply(tr("delete_start", id = id, backup_path = backup_path))
        if backup_path in BackupConfig().backup_list.keys():
            if BackupConfig().backup_list[backup_path]["enable"] == "true":
                match BackupConfig().backup_list[backup_path]["mode"]:
                    case "local":
                        LP.delete(f"backup_{id}.tar",
                                  BackupConfig().backup_list[backup_path],
                                  backup_path,
                                  source)
                    case "ftp":
                        ...
                    case "smb":
                        ...
                    case "sftp":
                        ...
                    case _:
                        ...
            else:
                source.reply(RText(tr("unusable_backup_path", backup_path = backup_path), RColor.red))
        else:
            source.reply(RText(tr("unusable_backup_path", backup_path = backup_path), RColor.red))