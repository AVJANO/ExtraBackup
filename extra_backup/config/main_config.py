import os
import json

from mcdreforged.api.all import *

from extra_backup.utils.Singleton import singleton
from extra_backup.lang.lang_processor import tr

class DefaultConfig:
    main_config = {
                        "enable":"false",
                        "language":"zh_cn",
                        "max_thread":"-1",
                        "schedule_backup":{
                            "enable":"false",
                            "interval":"30m"
                        },
                        "schedule_prune":{
                            "enable":"false",
                            "interval":"1d",
                            "max_lifetime":"3d",
                            "prune_downloads":"true",
                            "prune_exports":"true"
                        }
                      }
    config_folder = os.path.join(os.path.join(os.getcwd(), "backup_path"), "extra_backup")
    config_file = os.path.join(config_folder, "backup_path.json")
    permissions_file = os.path.join(config_folder, "permissions.json")
    backup_config_file = os.path.join(config_folder, "backup_path.json")
    download_path = os.path.join(os.getcwd(), "exb_downloads")
    pb_export_path = os.path.join(os.path.join(os.getcwd(), "pb_files"), "export")

@singleton
class Config:
    _initialized = False
    default_config = DefaultConfig.main_config
    temp_config = {}
    server: PluginServerInterface = None
    def __init__(self, server: PluginServerInterface):
        if self._initialized:
            return
        try:
            os.mkdir(DefaultConfig().download_path)
        except FileExistsError:
            pass
        except Exception as e:
            server.logger.error(tr("mkdir_downloads_failed", error = e))
        try:
            with open(DefaultConfig.config_file, "r") as config_file:
                self.config = json.load(config_file)
        except FileNotFoundError as e:
            self.config = DefaultConfig.main_config
            if os.path.exists(DefaultConfig.config_folder):
                with open(DefaultConfig.config_file, "w") as config_file:
                    json.dump(self.config , config_file, indent=4 , ensure_ascii=False)
            else:
                os.makedirs(DefaultConfig.config_folder)
                with open(DefaultConfig.config_file, "w") as config_file:
                    json.dump(self.config , config_file , indent=4 , ensure_ascii=False)
        finally:
            self.server = server
            self._initialized = True

    def get(self, key: str):
        """获取指定定配置项"""
        try:
            if key in self.temp_config:
                return self.temp_config[key]
            else:
                return self.config[key]
        except KeyError:
            self.config[key] = self.default_config[key]
            with open(DefaultConfig.config_file, "w") as config_file:
                json.dump(self.config, config_file, indent=4 , ensure_ascii=False)
            return self.default_config[key]

    def set(self, key: str, value):
        """设置配置项（临时，重启无效）"""
        self.temp_config[key] = value

    def dump(self, key: str, value):
        """设置配置项（永久，写入配置文件）"""
        self.config[key] = value
        try:
            with open(DefaultConfig.config_file, "w") as config_file:
                json.dump(self.config, config_file, indent=4 , ensure_ascii=False)
            return None
        except Exception as e:
            return e



