# pb_exporter.py
from __future__ import annotations
from pathlib import Path
from typing import Callable, Optional, Tuple
from datetime import datetime
import threading

from mcdreforged.api.all import ServerInterface, CommandSource, RText, RColor
from typing_extensions import override

from typing import Any

# 你自己的语言系统
from extra_backup.lang.lang_processor import tr

# —— PrimeBackup 相关 —— #
from prime_backup.action.export_backup_action_tar import ExportBackupToTarAction
from prime_backup.action.export_backup_action_zip import ExportBackupToZipAction
from prime_backup.action.get_backup_action import GetBackupAction
from prime_backup.mcdr.task.basic_task import HeavyTask
from prime_backup.mcdr.text_components import TextComponents
from prime_backup.types.tar_format import TarFormat
from prime_backup.utils.backup_id_parser import BackupIdParser
from prime_backup.utils.timer import Timer
from prime_backup.mcdr.task.backup.export_backup_task import _sanitize_file_name

from extra_backup.utils.reply import reply


def _ensure_plain_text(value: Any, default: str = "backup") -> str:
    """Convert possible Operator/Text-like objects into a plain str.

    - If value is None, return default
    - If value has .get_value(), call it to extract the underlying text
    - Fallback to str(value)
    """
    if value is None:
        return default
    # handle MCDR Operator / Text components
    if hasattr(value, "get_value"):
        try:
            value = value.get_value()
        except Exception:
            # if extraction fails, fall back to default
            return default
    # final safety: ensure string
    s = str(value)
    return s if s else default


def _fallback_source(server) -> CommandSource:
    # Prefer a real CommandSource; avoid falling back to logger objects
    if hasattr(server, 'get_self_source'):
        s = server.get_self_source()
        if isinstance(s, CommandSource):
            return s
    # As a last resort, try to obtain a console source if available in this MCDR version
    try:
        return CommandSource.console()  # type: ignore[attr-defined]
    except Exception:
        # Fallback to whatever server can provide; HeavyTask may still format output
        return getattr(server, 'get_self_source', lambda: server.get_logger())()


def _fmt_to_suffix_and_tar(fmt: str) -> Tuple[str, Optional[TarFormat], bool]:
    """返回 (扩展名, TarFormat(非zip才用), 是否zip)"""
    f = fmt.lower()
    if f == "zip":
        return ".zip", None, True
    if f in ("tar",):
        return ".tar", TarFormat.plain, False
    if f in ("tar.gz", "tgz", "gz"):
        return ".tar.gz", TarFormat.gzip, False
    if f in ("tar.zst", "zst", "tzst", "tar.zstd"):
        return ".tar.zst", TarFormat.zstd, False
    # 默认 tar
    return ".tar", TarFormat.plain, False


def _ensure_suffix(path: Path, expect_suffix: str) -> Path:
    s = str(path)
    el = expect_suffix.lower()
    if s.lower().endswith(el):
        return path
    # strip all existing suffixes (including multi-suffix like .tar.gz)
    stem = s
    p = Path(s)
    if p.suffixes:
        # iteratively remove suffix until none
        while Path(stem).suffix:
            stem = stem[: -len(Path(stem).suffix)]
    return Path(stem + expect_suffix)


def _tc_path(p: Path):
    # Compatibility shim: PrimeBackup versions differ on the method name
    if hasattr(TextComponents, 'path_name'):
        return TextComponents.path_name(p)  # newer name in some versions
    if hasattr(TextComponents, 'config_file'):
        return TextComponents.path(p)
    if hasattr(TextComponents, 'file_path'):
        return TextComponents.file_path(p)
    # Fallback: plain text
    return RText(str(p))


class PBExporterTask(HeavyTask[None]):
    """
    复制 ExportBackupTask 的核心流程，但改造成“可编程调用 + 回调”的形态。
    """

    def __init__(
        self,
        source: CommandSource,
        backup_id: int,
        *,
        fmt: str = "tar",
        output: Optional[Path] = None,   # 目录 或 文件；None 则自动放到 pb_files/export/
        verify_blob: bool = False,
        fail_soft: bool = False,
        overwrite_existing: bool = True,
        create_meta: bool = True,
        callback: Optional[Callable[[Optional[Path], Optional[list], Any], None]] = None,
    ):
        # 先设置在 id 属性中会用到的字段，避免父类构造期间访问未初始化属性
        self.backup_id = backup_id
        self.fmt = fmt
        self.output = output
        self.verify_blob = verify_blob
        self.fail_soft = fail_soft
        self.overwrite_existing = overwrite_existing
        self.create_meta = create_meta
        self.callback = callback
        # 再调用父类构造，父类可能会读取 self.id
        super().__init__(source)

    @property
    @override
    def id(self) -> str:
        suffix, _, _ = _fmt_to_suffix_and_tar(self.fmt)
        return f"export_backup:{self.backup_id}:{suffix}"

    def _resolve_output_path(self, comment: str | None, creator: str | None) -> Path:
        # 不再使用 comment / creator 来参与命名，只用备份 id
        suffix, _, _ = _fmt_to_suffix_and_tar(self.fmt)

        # 默认：pb_files/export/backup_<id>.<ext>
        def default_path() -> Path:
            return Path("pb_files/export") / f"backup_{self.backup_id}{suffix}"

        # 没有指定 output：用默认目录
        if self.output is None:
            return default_path()

        # output 是已经存在的目录：目录下生成 backup_<id>.<ext>
        if self.output.exists() and self.output.is_dir():
            return self.output / f"backup_{self.backup_id}{suffix}"

        # output 以 / 或 \ 结尾，当成目录来处理
        if str(self.output).endswith(("/", "\\")):
            return Path(str(self.output)) / f"backup_{self.backup_id}{suffix}"

        # output 指向具体文件名：只负责补后缀
        return _ensure_suffix(self.output, suffix)

    @override
    def run(self) -> None:
        out_path: Optional[Path] = None
        failures: list = []
        try:
            # 1) 获取备份信息
            backup = GetBackupAction(self.backup_id).run()

            # 2) 计算输出路径
            out_path = self._resolve_output_path(backup.comment, backup.creator)
            out_path_parent = out_path.parent
            out_path_parent.mkdir(parents=True, exist_ok=True)
            if out_path.exists() and not self.overwrite_existing:
                # 已存在且不允许覆盖：直接返回，由 finally 调用回调
                return

            # 3) 选择 Action
            _, tar_format, is_zip = _fmt_to_suffix_and_tar(self.fmt)
            if is_zip:
                action = ExportBackupToZipAction(
                    backup_id=backup.id,
                    output_path=out_path,
                    fail_soft=self.fail_soft,
                    verify_blob=self.verify_blob,
                    create_meta=self.create_meta,
                )
            else:
                action = ExportBackupToTarAction(
                    backup_id=backup.id,
                    output_dest=out_path,
                    tar_format=tar_format,
                    fail_soft=self.fail_soft,
                    verify_blob=self.verify_blob,
                    create_meta=self.create_meta,
                )

            # 4) 执行 + 计时 + 输出（仅使用 export_start 语言键来构造提示）
            timer = Timer()
            failures = self.run_action(action)   # HeavyTask 会做异常处理/记录
            elapsed = round(timer.get_elapsed(), 2)

            ok = out_path is not None and out_path.is_file()
            # 计算失败条目数量（若失败对象不支持 len，则记为 0）
            try:
                fail_count = len(failures)
            except TypeError:
                fail_count = 0

            if ok and fail_count == 0:
                self.source.reply(RText(tr("export_success", id=self.backup_id, time=elapsed, path=out_path),RColor.green))
            else:
                msg = tr("export_failed", id=self.backup_id, failures=fail_count)
                self.source.reply(RText(msg, RColor.red))

                # 输出具体错误信息（如果有）
                if failures:
                    try:
                        lines = failures.to_lines()
                    except AttributeError:
                        # 退化处理：如果没有 to_lines，就按可迭代或字符串处理
                        try:
                            lines = list(failures)
                        except TypeError:
                            lines = [str(failures)]
                    for line in lines:
                        self.reply(RText(str(line), RColor.red))

        except Exception as e:
            msg = tr("export_failed", id=getattr(self, "backup_id", "?"), failures="1", error=e)
            self.reply(RText(msg, RColor.red))

        finally:
            if self.callback:
                try:
                    ok = (out_path is not None) and Path(out_path).exists()
                    self.callback(out_path if ok else None, list(failures), self.source)
                except Exception as e:
                    self.reply(RText(f"[PBExporter] callback error: {e}", RColor.red))


class PBExporter:
    """
    面向业务的简单封装：
    - 自动解析 'latest' / '~2' / 具体ID
    - 同步/异步两种执行方式
    """

    def __init__(self, server: ServerInterface, source: CommandSource | None = None):
        self.server = server
        # 尽量拿一个可用的 CommandSource（用于 HeavyTask 的输出）
        self.source = source or _fallback_source(server)

    def _parse_backup_id(self, ident: str | int) -> int:
        if isinstance(ident, int):
            return ident
        return BackupIdParser(allow_db_access=True).parse(str(ident))

    def export(
        self,
        ident: str | int,
        *,
        fmt: str = "tar",
        output: Optional[Path] = None,
        verify_blob: bool = True,
        fail_soft: bool = False,
        overwrite_existing: bool = True,
        create_meta: bool = True,
        callback: Optional[Callable[[Optional[Path], Optional[list], Any], None]] = None,
        async_run: bool = False,
    ) -> Optional[Path]:
        """
        ident: 备份标识（如 'latest' / '~2' / 4175）
        callback(out_path|None, failures): 导出完成后回调
        async_run: 是否在新线程中执行（不阻塞）
        返回：同步模式下返回导出文件路径（失败或未生成则为 None）；异步模式返回 None
        """
        backup_id = self._parse_backup_id(ident)

        result_holder = {"config_file": None}

        def _inner_cb(p: Optional[Path], fails: list, source):
            # 捕获同步结果
            result_holder["config_file"] = p
            # 透传给用户回调（若提供）
            if callback is not None:
                callback(p, fails, self.source)

        task = PBExporterTask(
            source=self.source,  # 用于 HeavyTask 的友好输出
            backup_id=backup_id,
            fmt=fmt,
            output=output,
            verify_blob=verify_blob,
            fail_soft=fail_soft,
            overwrite_existing=overwrite_existing,
            create_meta=create_meta,
            callback=_inner_cb if not async_run or callback is not None else None,
        )

        if async_run:
            threading.Thread(target=task.run, name=f"PBExporter-{backup_id}-{fmt}", daemon=True).start()
            return None
        else:
            task.run()
            return result_holder["config_file"]