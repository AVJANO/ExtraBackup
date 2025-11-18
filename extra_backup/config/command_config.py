import json

from extra_backup.config.main_config import DefaultConfig
from extra_backup.utils.Singleton import singleton


@singleton
class CommandPermissions:
    DEFAULT = {
        "upload": 2,
        "uploadall": 2,
        "download": 2,
        "delete": 2,
        "list": 1,
        "prune": 3,
        "abort": 2,
        "lang": 1
    }
    command_permissions = {}

    def __init__(self):
        _initialized = False
        if _initialized:
            return
        else:
            try:
                with open(DefaultConfig.permissions_file, "r") as f:
                    self.command_permissions = json.load(f)
            except FileNotFoundError:
                with open(DefaultConfig.permissions_file, "w") as f:
                    json.dump(self.DEFAULT, f)
                self.command_permissions = self.DEFAULT.copy()
            except json.decoder.JSONDecodeError:
                with open(DefaultConfig.permissions_file, "w") as f:
                    json.dump(self.DEFAULT, f)
                self.command_permissions = self.DEFAULT.copy()

    def get(self, key: str):
        return self.command_permissions["key"]

    def set(self, key: str, value):
        if key not in self.DEFAULT:
            return KeyError
        else:
            self.command_permissions[key] = value
            try:
                with open(DefaultConfig.permissions_file, "w") as f:
                    json.dump(self.command_permissions, f)
                    return True
            except Exception as e:
                return e

class CommandConfig:
    ...
