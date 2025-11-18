from pathlib import Path
from unittest import case

from mcdreforged.api.all import *

from extra_backup.task.main_task import States
from extra_backup.config.backup_config import BackupConfig
from extra_backup.file_manager.local_processor import LocalProcessor as LP
from extra_backup.lang.lang_processor import tr

class Uploader:
    @staticmethod
    @new_thread
    def upload(path: Path | None, failures, source: CommandSource):
        if States().Uploading:
            source.reply(RText(tr("another_uploader_is_running"), RColor.yellow))
            return
        States().Uploading = True
        success_backup_count = 0
        success_backups = []
        failure_backup_count = 0
        failure_backups = []
        skipped_backup_count = 0
        skipped_backups = []
        if path is not None:
            backup_list= BackupConfig().backup_list
            total_backups = len(backup_list)
            for backup_path in backup_list:
                backup = backup_list[backup_path]
                if backup["enable"]=="true":
                    match backup["mode"]:
                        case "local":
                            match LP.upload(path, backup, backup_path, source):
                                case True:
                                    success_backup_count+=1
                                    success_backups.append(backup_path)
                                case None:
                                    skipped_backup_count += 1
                                    skipped_backups.append(backup_path)
                                case False:
                                    failure_backup_count+=1
                                    failure_backups.append(backup_path)
                        case "ftp":
                            ...
                        case "smb":
                            ...
                        case "sftp":
                            ...
                        case _:
                            source.reply(RText(tr("backup_config_wrong_mode", mode=backup_path["mode"]), RColor.red))
                else:
                    skipped_backup_count+=1
                    skipped_backups.append(backup_path)
            source.reply(RText(tr("upload_complete",
                                  total_count     = total_backups,
                                  success_count   = success_backup_count,
                                  success_backups = success_backups,
                                  failure_count   = failure_backup_count,
                                  failure_backups = ", ".join(map(str, failure_backups)) if failure_backups else "",
                                  skipped_count = skipped_backup_count,
                                  skipped_backups = ", ".join(map(str, skipped_backups)),),
                                RColor.blue))


        else:
            source.reply(RText(tr("upload_failed", error= tr("export_failed")), RColor.red))
        States().Uploading = False