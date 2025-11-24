from mcdreforged.api.all import *

from extra_backup.lang.lang_processor import tr
from extra_backup.task.main_task import States
from extra_backup.file_manager.local_processor import LocalProcessor as LP
from extra_backup.file_manager.ftp_processor import FTPProcessor as FP
from extra_backup.config.backup_config import BackupConfig

class Downloader:
    @staticmethod
    @new_thread
    def download(filename, from_where: str | None, source:CommandSource):
        if States().Downloading:
            source.reply(RText(tr("another_downloader_is_running"), RColor.yellow))
            return
        States().Downloading = True
        try:
            if from_where is None:
                for backup_path in BackupConfig().backup_list.keys():
                    if BackupConfig().backup_list[backup_path]["enable"] == "true":
                        from_where = backup_path
                        break
            if from_where is None:
                source.reply(RText(tr("no_available_backup_path"), RColor.red))
                return
            if from_where not in BackupConfig().backup_list.keys():
                source.reply(RText(tr("unusable_backup_path", backup_path= from_where), RColor.red))
                return
            if BackupConfig().backup_list[from_where]["enable"] == "true":
                match BackupConfig().backup_list[from_where]["mode"]:
                    case "local":
                        LP.download(filename, from_where, source)
                    case "ftp":
                        ftp = FP(from_where, BackupConfig().backup_list[from_where], source)
                        try:
                            if ftp.connect():
                                ftp.download(filename)
                        finally:
                            ftp.disconnect()
                    case "smb":
                        ...
                    case "sftp":
                        ...
                    case _:
                        source.reply(RText(tr("unknown_backup_mode",
                                              mode = BackupConfig().backup_list[from_where]["mode"]),
                                           RColor.red))
            else:
                source.reply(tr("unusable_backup_path", backup_path=from_where))
        finally:
            States().Downloading = False


