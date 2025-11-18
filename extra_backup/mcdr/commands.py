from mcdreforged.api.all import *
from prime_backup.utils.backup_id_parser import BackupIdParser

from extra_backup.utils.chaeck_export_file import *
from extra_backup.config.backup_config import BackupConfig
from extra_backup.config.main_config import Config
from extra_backup.task.export_task import ExportTask
from extra_backup.task.upload_task import Uploader
from extra_backup.task.prune_task import Pruner
from extra_backup.lang.lang_processor import tr, Language
from extra_backup.file_manager.local_processor import LocalProcessor as LP
from extra_backup.task.download_task import Downloader


class CommandManager:
    def __init__(self, server: PluginServerInterface):
        self.server = server

    @staticmethod
    def _get_str_from_ctx(ctx: CommandContext, key: str) -> str:
        """
        兼容两种情况：
        - ctx[key] 是 Operator → 调用 get_value()
        - ctx[key] 已经是 str/int → 直接转成 str
        """
        value = ctx.get(key)

        # 如果是 Operator，就取它的值
        if hasattr(value, "get_value"):
            value = value.get_value()

        # 最后统一成 str
        return str(value) if value is not None else ""

    def cmd_upload(self, source: CommandSource, ctx: CommandContext):
        _id = self._get_str_from_ctx(ctx, "id")
        if _id=="latest":
            _id = BackupIdParser(allow_db_access=True).parse("latest")
        if get_exported_backup_path(_id) is not None:
            Uploader.upload(path= get_exported_backup_path(_id), failures=None, source=source)
        else:
            source.reply(tr("export_start",id=_id))
            ExportTask(_id).export(source, callback=Uploader.upload)

    def cmd_uploadall(self, source: CommandSource):
        ...

    def cmd_download(self, source: CommandSource, ctx: CommandContext):
        filename = ctx.get("filename")
        from_where = ctx.get("from")
        Downloader.download(filename, from_where, source)


    def cmd_prune(self, source: CommandSource, ctx: CommandContext):
        _id = ctx.get("id")
        Pruner.prune(_id, source)

    def cmd_list(self, source: CommandSource, ctx: CommandContext):
        _location = ctx.get("location", None)
        if _location is None:
            source.reply("\n")
            if LP().list(None):
                for file in LP().list(None):
                    source.reply(file+"\n")
                    return
            source.reply(tr("no_files"))
        else:
            if _location in BackupConfig().backup_list and BackupConfig().backup_list[_location]["enable"] == "true":
                backup_path = BackupConfig().backup_list[_location]
                match backup_path["mode"]:
                    case "local":
                        source.reply("\n")
                        if LP().list(backup_path, source):
                            for file in LP().list(backup_path, source):
                                source.reply(file+"\n")
                            return
                        source.reply(tr("no_files"))
                    case "ftp":
                        ...
                    case "sftp":
                        ...
                    case "smb":
                        ...
                    case _:
                        ...
            else:
                source.reply(RText(tr("unusable_backup_path", backup_path=_location), RColor.red))

    def cmd_delete(self, source: CommandSource, ctx: CommandContext):
        _location = ctx["location"]
        _id = ctx["id"]
        Pruner.delete(_id, _location, source)

    def cmd_change_language(self, source: CommandSource, ctx: CommandContext):
        _language = ctx["language"]
        try:
            Language().load(_language)
            Config().dump("language", _language)
            source.reply(RText(tr("change_language_success",language=_language), RColor.green))
        except Exception as e:
            source.reply(RText(tr("change_language_failed", language=_language), RColor.red))


    def cmd_abort(self, source: CommandSource):
        ...

    def command_register(self):
        builder = SimpleCommandBuilder()
        builder.command("!!exb upload <id>", self.cmd_upload)
        builder.command("!!exb upload <id> <tag>", self.cmd_upload)
        builder.command("!!exb download <filename>", self.cmd_download)
        builder.command("!!exb download <filename> <from>", self.cmd_download)
        builder.command("!!exb prune", self.cmd_prune)
        builder.command("!!exb prune <id>", self.cmd_prune)
        builder.command("!!exb delete <location> <id>", self.cmd_delete)
        builder.command("!!exb list", self.cmd_list)
        builder.command("!!exb list <location>", self.cmd_list)
        builder.command("!!exb lang <language>", self.cmd_change_language)
        builder.command("!!exb abort", self.cmd_abort)

        builder.arg("id", Text)
        builder.arg("location", Text)
        builder.arg("language", Text)
        builder.arg("from", Text)
        builder.arg("filename", Text)
        builder.arg("tag", GreedyText)

        builder.register(self.server)
