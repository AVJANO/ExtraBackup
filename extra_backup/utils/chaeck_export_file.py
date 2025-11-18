from pathlib import Path
from typing import Optional


def get_exported_backup_path(
        backup_id: int,
        export_dir: Path = Path("pb_files/export"),
        prefix: str = "backup_",
        suffixes: tuple[str, ...] = (".tar", ".tar.gz", ".tar.zst", ".zip"),
) -> Optional[Path]:
    """
    检查导出目录下是否存在指定备份 ID 的导出文件。
    如果存在，返回该文件的路径；如果不存在，返回 None。

    Args:
        backup_id (int): 要检查的备份ID
        export_dir (Path): 导出目录（默认 pb_files/export）
        prefix (str): 文件名前缀（默认 backup_）
        suffixes (tuple): 可接受的文件扩展名

    Returns:
        Optional[Path]: 已存在的备份路径，或 None（未导出）
    """
    if not export_dir.exists():
        return None

    for file in export_dir.iterdir():
        if not file.is_file():
            continue
        # 文件名以 backup_<id> 开头或包含 backup_<id>_
        if f"{prefix}{backup_id}" in file.name:
            if any(file.name.endswith(ext) for ext in suffixes):
                return file.resolve()
    return None