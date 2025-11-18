from mcdreforged.api.all import *

from extra_backup.pb.export import PBExporter
from extra_backup.config.main_config import Config

class ExportTask:
    def __init__(self, id):
        self.server: PluginServerInterface= Config().server
        self.id = id

    def export(self, source: CommandSource, callback):
        PBExporter(self.server, source).export(
            ident=self.id,
            fmt='tar',
            verify_blob=False,
            async_run=True,
            callback=callback  # 导出完成后回调
        )