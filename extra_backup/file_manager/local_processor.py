import os
import shutil
from pathlib import Path

from mcdreforged.api.all import *

from extra_backup.config.backup_config import BackupConfig
from extra_backup.config.main_config import DefaultConfig
from extra_backup.lang.lang_processor import tr


class LocalProcessor:
    @staticmethod
    def upload(file_path:Path, backup, backup_name, source:CommandSource):
        backup_path = backup["address"]
        try:
            if Path(file_path).name not in os.listdir(backup_path):
                source.reply(tr("upload_file_start", backup_name=backup_name))
                shutil.copy(file_path, backup_path)
                source.reply(RText(tr("upload_file_success", backup_name=backup_name), RColor.green))
                return True
            else:
                source.reply(RText(tr("upload_skip_duplicate", backup_name=backup_name), RColor.yellow))
                return None
        except Exception as e:
            source.reply(RText(tr("upload_file_failed", backup_name=backup_name, error=e), RColor.red))
            return False

    @staticmethod
    def download(filename: str, from_where : str, source:CommandSource):
        backup_path = BackupConfig().backup_list[from_where]["address"]
        try:
            if filename not in os.listdir(DefaultConfig().download_path):
                source.reply(tr("download_start", filename=filename))
                shutil.copy(os.path.join(backup_path, filename), DefaultConfig().download_path)
                source.reply(RText(tr("download_success", filename=filename), RColor.green))
                return True
            else:
                source.reply(tr("download_skip_duplicate", filename=filename))
                return None
        except Exception as e:
            source.reply(RText(tr("download_failed", filename=filename, error=e), RColor.red))
            return False

    @staticmethod
    def list(address = None, source = None):
        if address is None:
            return os.listdir(DefaultConfig().download_path)
        else:
            try:
                return os.listdir(address["address"])
            except Exception as e:
                source.reply(RText(tr("list_failed", address=address, error=e), RColor.red))
                return None

    @staticmethod
    def delete(filename: str, backup_path,backup_path_name ,source: CommandSource):
        file_path = Path(backup_path["address"]) / filename
        try:
            file_path.unlink()
            source.reply(RText(tr("delete_success", backup_path=backup_path_name, filename=filename), RColor.green))
        except FileNotFoundError:
            source.reply(RText(tr("delete_file_unfound", backup_path=backup_path_name,filename=filename), RColor.red))
        except Exception as e:
            source.reply(RText(tr("delete_failed", backup_path=backup_path_name, filename=filename, error=e), RColor.red))