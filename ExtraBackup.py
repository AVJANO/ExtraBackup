#Open Source License: GNU General Public License v3.0

import mcdreforged.api.all as mcdr
from pathlib import Path
import threading
import schedule
import ftplib
import shutil
import time
import json
import os
import re

PLUGIN_METADATA = {
    'id': 'extra_backup',
    'version': '0.1.2',
    'name': 'Extra Backup',
    'description': {
        "zh_cn":"全新分布式备份插件，为您的珍贵存档增添一份安心！",
        "en_us":"A new distributed backup plugin which adds peace of mind to your valuable archives!"
    },
    'author': 'avjano',
    'link': 'https://github.com/AVJANO/ExtraBackup',
    'dependencies': {
        'mcdreforged': '>=2.14.7'
    }
}

default_config = {
                    "enable":"true",
                    "mode":"pb",
                    "localfolder":"",
                    "multithreading":"true",
                    "schedule_backup":{"enable":"true",
                                "interval":"3m"}
                  }
config=default_config.copy()
backup_path={
    "Name1":
    {
        "enable":"false",
        "mode":"ftp",
        "address":"ftp://example.com/folder",
        "username":"username",
        "password":"123456"
    },
    "Name2":
    {
        "enable":"true",
        "mode":"local",
        "address":"/folder/example",
        "username":"",
        "password":""
    }
}

uploading = False
downloading = False

config_path=os.path.join(os.getcwd(),"config")
config_folder=os.path.join(config_path,"extra_backup")
config_file=os.path.join(config_folder,"config.json")
backup_config_path=os.path.join(config_folder,"backup_path.json")

def time_str(s: str) -> int:
    """
    把类似 "1h30m", "2d3h15m20s" 转换成总秒数
    """
    units = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400
    }
    matches = re.findall(r"(\d+)([smhd])", s.strip().lower())
    if not matches:
        raise ValueError(f"无效的时间格式: {s}")

    total_seconds = sum(int(num) * units[unit] for num, unit in matches)
    return total_seconds


def config_loader():
    if os.path.exists(config_folder):
        if os.path.isfile(config_file):
            with open(config_file) as f:
                return json.load(f)
        else:
            with open(config_file , "w") as f:
                json.dump(default_config , f , indent=4 , ensure_ascii=False)
            return default_config
    else:
        os.makedirs(config_folder)
        with open(config_file , "w") as f:
            json.dump(default_config , f , indent=4 , ensure_ascii=False)
        return default_config


def backup_path_loader():
    if os.path.exists(backup_config_path):
        with open(backup_config_path) as f:
            return json.load(f)
    else:
        with open(backup_config_path , "w") as f:
            json.dump(backup_path , f , indent=4 , ensure_ascii=False)
            return backup_path
        

@mcdr.new_thread
def upload(backup_name , _backup_path , local_file):
    global uploading
    mode=_backup_path["mode"]
    if mode=="ftp":
        uploading = True
        print("开始向"+backup_name+"上传备份...")
        try:
            uploader = ftplib.FTP()
            pass
        except Exception as e:
            print("向"+backup_name+"上传备份失败！原因是：")
            print(e)
        finally:
            uploader.quit()
            uploading=False
    elif mode=="local":
        try:
            uploading=True
            address=_backup_path["address"]
            print("开始向"+address+"上传备份"+local_file)
            if Path(local_file).name not in os.listdir(_backup_path["address"]):
                shutil.copy(local_file , address)
                print("备份"+local_file+"向"+address+"上传成功！")
            else:
                print("已跳过向"+address+"备份，原因是：已存在同名文件"+Path(local_file).name)
        except Exception as e:
            print("向"+backup_name+"上传备份失败！原因是：")
            print(e)
        finally:
            uploading=False
    elif mode=="smb":
        pass
    elif mode=="ftps":
        pass
    elif mode=="sftp":
        pass
    elif mode=="ssh":
        pass
    else:
        print("无法向"+backup_name+"备份！原因是：不支持的协议("+mode+")！")


@mcdr.new_thread
def download(backup_path , backup_file):
    global downloading
    pass


def uploadall(server:mcdr.PluginServerInterface,source):
    if source=="schedule":
        print("定时备份触发，开始上传备份")
    else:
        print("手动备份触发，开始上传备份")
    for name in backup_path:
        backup_dest=backup_path[name]
        if backup_dest["enable"]=="true":
            for file in os.listdir(config["localfolder"]):
                upload(name , backup_path[name] , os.path.join(config["localfolder"], file))
        else:
            print("已跳过"+name+"备份")


def downloadall():
    pass


def abort():
    pass


def make_list():
    for file in os.listdir(config["localfolder"]):
        print(file)

    
@mcdr.new_thread
def backup_timer(schedule_config,server:mcdr.PluginServerInterface):
    if schedule_config["enable"]=="true":
        server.logger.info("定时备份已启动")
        seconds = time_str(schedule_config["interval"])
        schedule.every(seconds).seconds.do(uploadall,server,source="schedule")
    else:
        server.logger.info("定时备份未启动")


def start_scheduler_thread(server):
    def loop():
        while True:
            try:
                schedule.run_pending()
            except Exception as e:
                server.logger.error(f"[ExtraBackup] 定时任务执行失败: {e}")
            time.sleep(1)
    threading.Thread(target=loop, daemon=True).start()


def on_load(server , pre_state):
    global config,backup_path
    server.logger.info("ExtraBackup启动中...")
    server.logger.info("正在读取配置文件...")
    try:
        js=config_loader()
        for key in js:
            config[key]=js[key]
        server.logger.info("配置文件读取成功")
    except Exception as e:
        server.logger.warn("配置文件读取失败,原因是：")
        print(e)
        config=default_config
        try:
            with open(config_file , "w") as f:
                json.dump(default_config , f , indent=4 , ensure_ascii=False)
        except:
            pass
        server.logger.warn("extra_backup正在使用默认配置运行")
    if config["enable"]=="true":
        server.logger.info("正在读取备份路径...")
        try:
            backup_path=backup_path_loader()
            server.logger.info("备份路径加载完成")
        except Exception as e:
            server.logger.warn("备份路径加载失败！原因是：")
            print(e)
            server.logger.warn("Extra Backup插件将暂停运行直至有可用备份路径")
            try:
                with open(backup_config_path , "w") as f:
                    json.dump(backup_path , f , indent=4 , ensure_ascii=False)
            except:
                pass
            server.logger.warn("请使用!!exb help获取更多帮助")
        exb_command=mcdr.SimpleCommandBuilder()
        exb_command.command("!!exb uploadall",uploadall)
        exb_command.command("!!exb downloadall",downloadall)
        exb_command.command("!!exb upload <file_name>",upload)
        exb_command.command("!!exb download <file_name>",download)
        exb_command.command("!!exb list",make_list)
        exb_command.command("!!exb abort",abort)
        exb_command.arg("file_name",mcdr.Text)
        exb_command.register(server)
        if config["mode"]=="pb":
            config["localfolder"]=os.path.join(os.getcwd(),"pb_files")
            if os.path.exists(config["localfolder"]) and not os.path.exists(os.path.join(config["localfolder"],"export")):
                os.makedirs(os.path.exists(os.path.join(config["localfolder"],"export")))
            if os.path.exists(config["localfolder"]):
                config["localfolder"]=os.path.join(config["localfolder"],"export")
                server.logger.info("已检测到PrimeBackup导出文件夹")
                server.logger.info("ExtraBackup以pb模式启动")
        elif config["mode"]=="qb":
            pass
        elif config["mode"]=="normal":
            pass
        else:
            server.logger.warn("未知的启动模式！"+config["mode"])
            server.logger.warn("ExtraBackup将卸载！")
            on_unload(server)
        schedule_backup_config=config["schedule_backup"]
        backup_timer(schedule_backup_config,server)
        start_scheduler_thread(server)
        server.logger.info("Extra Backup启动成功")
    elif config["enable"]=="false":
        server.logger.warn("ExtraBackup没有运行，原因是你没有开启该插件！")

    else:
        server.logger.warn("错误的配置项：enable")

    
def on_unload(server):
    if uploading:
        server.logger.info("Extra Backup正在上传存档备份，请等待上传完成")
        server.logger.info("如需立即终止上传请使用!!exb abort指令")
    elif downloading:
        server.logger.info("Extra Backup正在下载存档备份，请等待下载完成")
        server.logger.info("如需立即终止下载请使用!!exb abort指令")
    else:
        server.logger.info("Extra Backup已卸载")