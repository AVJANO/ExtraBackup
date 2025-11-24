import ftplib
# import socket
# import chardet
import os
from typing import Optional
from mcdreforged.api.all import *

from extra_backup.config.main_config import DefaultConfig
from extra_backup.lang.lang_processor import tr

def parse_ftp_url(url: str) -> tuple[str, str]:
    """
    返回 (ip, path)
    """
    if not url.startswith("ftp://"):
        raise ValueError(tr("URL_format_error"))

    stripped = url[len("ftp://"):]  # 去掉 ftp://

    # 找第一个斜杠 —— 分割 IP 和路径
    if "/" in stripped:
        ip, path = stripped.split("/", 1)
        path = "/" + path  # 确保路径以 / 开头
    else:
        ip = stripped
        path = "/"  # 没有路径则设为根目录

    return ip, path

class FTPProcessor:
    def __init__(self, backup_name, backup_path: dict, source: CommandSource):
        self.source = source
        self.ftp_client: Optional[ftplib.FTP] = None
        self.encoding = 'utf-8'
        self.port = 21
        self.username = backup_path["username"]
        self.password = backup_path["password"]
        self.ip, self.path = parse_ftp_url(backup_path["address"])
        self.backup_name = backup_name

    def connect(self) -> bool:
        try:
            self.ftp_client = ftplib.FTP()
            self.ftp_client.encoding = self.encoding
            self.ftp_client.connect(self.ip, self.port, timeout=10)
            self.ftp_client.login(self.username, self.password)
            self.source.reply(tr("ftp_connected", backup_name=self.backup_name))
            return True
        except Exception as e:
            self.source.reply(RText(tr("ftp_connection_error", backup_name=self.backup_name, error=str(e)), RColor.red))
            return False

    def upload(self, file_path: str):
        if self.ftp_client is None:
            self.source.reply(RText(tr("ftp_not_connected"), RColor.yellow))
            return False

        try:
            remote_filename = os.path.basename(file_path)
            remote_dir = self.path.strip("/")

            # 确保远程目录存在
            try:
                self.ftp_client.cwd("/")
                for folder in remote_dir.split("/"):
                    if folder:
                        try:
                            self.ftp_client.cwd(folder)
                        except:
                            self.ftp_client.mkd(folder)
                            self.ftp_client.cwd(folder)
            except Exception as e:
                self.source.reply(RText(tr("folder_switch_or_generate_failed", backup_name=self.backup_name, error=str(e)), RColor.red))
                return False


            if remote_filename in self.list():
                self.source.reply(RText(tr("upload_skip_duplicate", backup_name=self.backup_name), RColor.yellow))
                return None

            # 上传文件
            with open(file_path, "rb") as f:
                self.ftp_client.storbinary(f"STOR {remote_filename}", f)

            self.source.reply(RText(tr("upload_file_success", backup_name=self.backup_name), RColor.green))
            return True

        except Exception as e:
            self.source.reply(RText(tr("upload_file_failed", backup_name=self.backup_name, error=str(e)), RColor.red))
            return False

    def download(self, file_name: str) -> bool:
        """
        从 FTP 远程目录下载指定文件 file_name
        下载到本地 self.local_download_path
        """
        if self.ftp_client is None:
            self.source.reply(RText(tr("ftp_not_connected"), RColor.yellow))
            return False

        try:
            # 切换到远程目录
            remote_dir = (self.path or "/")
            self.ftp_client.cwd(remote_dir)
        except Exception as e:
            self.source.reply(f"切换目录失败: {e}")
            return False

        # 确保本地下载目录存在
        os.makedirs(DefaultConfig().download_path, exist_ok=True)
        local_file_path = os.path.join(DefaultConfig().download_path, file_name)

        try:
            with open(local_file_path, "wb") as f:
                self.ftp_client.retrbinary(f"RETR {file_name}", f.write)

            self.source.reply(RText(tr("download_success", file_name=file_name), RColor.green))
            return True

        except Exception as e:
            self.source.reply(RText(tr("download_failed", file_name=file_name, error = e), RColor.red))
            return False

    def list(self) -> list[str]:
        """
        列出 FTP 远程目录下的所有文件，返回文件名列表（不包含目录）
        """
        remote_dir = self.path
        if self.ftp_client is None:
            self.source.reply(RText(tr("ftp_not_connected"), RColor.yellow))
            return []

        try:
            # 切换目录
            if remote_dir:
                self.ftp_client.cwd(remote_dir)

            files = []
            items = []

            # 获取目录内容（每一行都是字符串，如 "-rw-r--r-- 1 user group 1234 Jan 1 00:00 filename.zip"）
            self.ftp_client.retrlines("LIST", items.append)

            for line in items:
                # 判断开头第一个字符：
                # '-' = 文件
                # 'd' = 目录
                # 'l' = 链接
                if line.startswith('-'):  # 文件
                    parts = line.split(maxsplit=8)
                    filename = parts[-1]
                    files.append(filename)

            return files

        except Exception as e:
            self.source.reply(f"列出目录失败: {e}")
            return []

    def disconnect(self):
        if self.ftp_client:
            try:
                self.ftp_client.quit()
            except Exception as e:
                self.ftp_client.close()
            self.ftp_client = None