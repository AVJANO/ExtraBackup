import json
import os

from extra_backup.config.main_config import DefaultConfig
from extra_backup.utils.Singleton import singleton


@singleton
class BackupConfig:
    _initialized = False
    default = True
    backup_list = {}
    example_backup_list = {
        "Name1_example":
        {
            "enable":"false",
            "mode":"ftp",
            "address":"ftp://example.com/folder",
            "username":"username",
            "password":"123456"
        },
        "Name2_example":
        {
            "enable":"false",
            "mode":"local",
            "address":"/folder/example",
            "username":"",
            "password":""
        }
    }
    config_file = DefaultConfig.backup_config_file
    def __init__(self):
        if self._initialized:
            return
        try:
            with open(self.config_file, 'r') as f:
                self.backup_list = json.load(f)
            self.default = False
        except FileNotFoundError:
            with open(self.config_file, 'w') as f:
                json.dump(self.example_backup_list, f, indent=4 , ensure_ascii=False)
        except json.decoder.JSONDecodeError:
            with open(self.config_file, 'w') as f:
                json.dump(self.example_backup_list, f, indent=4 , ensure_ascii=False)
        self._initialized = True
