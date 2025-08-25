#Open Source License: GNU General Public License v3.0

import mcdreforged.api.all as mcdr
from pathlib import Path
import schedule
import ftplib
import shutil
import time
import json
import os
import re

PLUGIN_METADATA = {
    'id': 'extra_backup',
    'version': '0.1.6',
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
                    "schedule_backup":{"enable":"false",
                                "interval":"30m"},
                    "schedule_prnue":{"enable":"false",
                                "interval":"30m"}
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
this_server = None

config_path=os.path.join(os.getcwd(),"config")
config_folder=os.path.join(config_path,"extra_backup")
config_file=os.path.join(config_folder,"config.json")
backup_config_path=os.path.join(config_folder,"backup_path.json")
download_path=os.path.join(os.getcwd(),"exb_downloads")

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
def download(s:mcdr.CommandSource , command):
    global downloading
    try:
        os.makedirs("exb_downloads")
    except:
        pass
    if command["from"] in backup_path:
        backup=backup_path[command["from"]]
        if backup["enable"]=="true":
            try:
                downloading=True
                s.reply("开始下载备份"+command["file_name"])
                if command["file_name"] not in os.listdir(download_path):
                    shutil.copy(os.path.join(backup["address"], command["file_name"] ) , download_path)
                    downloading=False
                    s.reply(f"备份{command["file_name"]}下载成功！")
                else:
                    s.reply(f"跳过下载备份{command["file_name"]}原因是：文件已存在")
            except Exception as e:
                s.reply(f"下载{command["file_name"]}失败：{e}")
                downloading=False
        else:
            s.reply(f"无法从{command["from"]}下载存档，原因是：未开启的备份路径")



def uploadall(s:mcdr.CommandSource,server:mcdr.PluginServerInterface=this_server):
    s.reply("手动备份触发，开始上传备份")
    for name in backup_path:
        backup_dest=backup_path[name]
        if backup_dest["enable"]=="true":
            for file in os.listdir(config["localfolder"]):
                upload(s , name , backup_path[name] , os.path.join(config["localfolder"], file))
                time.sleep(0.2)
        else:
            pass


def schedule_uploadall():
    this_server.logger.info("定时备份触发，开始上传备份")
    for name in backup_path:
        backup_dest=backup_path[name]
        if backup_dest["enable"]=="true":
            for file in os.listdir(config["localfolder"]):
                schedule_upload(this_server , name , backup_path[name] , os.path.join(config["localfolder"], file))
                time.sleep(0.2)
        else:
            pass


@mcdr.new_thread
def schedule_upload(s:mcdr.PluginServerInterface , backup_name , _backup_path , local_file):
    global uploading
    mode=_backup_path["mode"]
    if mode=="ftp":
        uploading = True
        s.logger.info(f"开始向{backup_name}上传备份...")
        try:
            uploader = ftplib.FTP()
            pass
        except Exception as e:
            s.logger.info(f"向{backup_name}上传备份失败！原因是：{e}")
        finally:
            uploader.quit()
            uploading=False
    elif mode=="local":
        try:
            uploading=True
            address=_backup_path["address"]
            if Path(local_file).name not in os.listdir(_backup_path["address"]):
                s.logger.info(f"开始向{backup_name}上传新增备份{Path(local_file).name}")
                shutil.copy(local_file , address)
                s.logger.info(f"备份{Path(local_file).name}向{backup_name}上传成功！")
                time.sleep(0.2)
            else:
                s.reply(f"跳过向{backup_name}上传备份{Path(local_file).name},原因是：重复的文件")
        except Exception as e:
            s.logger.info(f"向{backup_name}上传备份失败！原因是：{e}")
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
        s.logger.info(f"无法向{backup_name}备份！原因是：不支持的协议({mode})！")


@mcdr.new_thread
def upload(s:mcdr.CommandSource , backup_name , _backup_path , local_file):
    global uploading
    if _backup_path["enable"]=="true":
        mode=_backup_path["mode"]
        if mode=="ftp":
            uploading = True
            s.reply(f"开始向{backup_name}上传备份...")
            try:
                uploader = ftplib.FTP()
                pass
            except Exception as e:
                s.reply(f"向{backup_name}上传备份失败！原因是：{e}")
            finally:
                uploader.quit()
                uploading=False
        elif mode=="local":
            try:
                uploading=True
                address=_backup_path["address"]
                if Path(local_file).name not in os.listdir(_backup_path["address"]):
                    s.reply(f"开始向{backup_name}上传备份{Path(local_file).name}")
                    shutil.copy(local_file , address)
                    s.reply(f"备份{Path(local_file).name}向{backup_name}上传成功！")
                else:
                    s.reply(f"跳过向{backup_name}上传备份{Path(local_file).name},原因是：重复的文件")
            except Exception as e:
                s.reply(f"向{backup_name}上传备份失败！原因是：{e}")
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
            s.reply(f"无法向{backup_name}备份！原因是：不支持的协议({mode})！")

def cmd_upload(s:mcdr.CommandSource , commands):
    for backup_name in backup_path:
        backup=backup_path[backup_name]
        if backup["mode"]=="local":
            try:
                upload(s,backup_name,backup_path[backup_name],os.path.join(config["localfolder"], commands["file_name"]))
            except Exception as e:
                s.reply(f"上传{commands["file_name"]}失败：{e}")
        elif backup["mode"]=="ftp":
            s.reply(f"跳过向{backup_name}备份，原因是：")
            s.reply("暂不支持ftp备份")
        else:
            s.reply(f"不支持的备份模式：{backup["mode"]}")


def downloadall(source:mcdr.CommandSource , from_where):
    source.reply(f"开始从{from_where["from"]}下载全部备份:")
    if from_where["from"] in backup_path:
        backup=backup_path[from_where["from"]]
        if backup["mode"]=="local":
            for file in os.listdir(backup["address"]):
                from_where["file_name"]=file
                download(source , from_where)
                time.sleep(0.2)
        elif backup["mode"]=="ftp":
            source.reply(f"无法从{from_where["from"]}下载备份，原因是：")
            source.reply("暂不支持ftp模式")
        else:
            source.reply(f"不支持的备份模式：{backup["mode"]}")
    else:
        source.reply(f"下载失败！原因：未知的备份位置{from_where["from"]}")

def abort():
    pass


def make_list(s:mcdr.CommandSource , from_where):
    if "from" in from_where:
        if from_where["from"]!="":
            if from_where["from"] in backup_path:
                backup=backup_path[from_where["from"]]
                if backup["enable"]=="true":
                    if backup["mode"]=="local":
                        for file in os.listdir(backup["address"]):
                            s.reply(file)
                    elif backup["mode"]=="ftp":
                        s.reply("暂不支持ftp模式")
                else:
                    s.reply(f"错误! 未启用的备份路径：{from_where["from"]}")
            else:
                s.reply(f"错误的备份位置：{from_where["from"]}")
    else:
        for file in os.listdir(config["localfolder"]):
            s.reply(file)

    
def backup_timer(schedule_config,server:mcdr.PluginServerInterface):
    if schedule_config["enable"]=="true":
        server.logger.info("定时备份已启动")
        seconds = time_str(schedule_config["interval"])
        schedule.every(seconds).seconds.do(schedule_uploadall)
        start_scheduler_thread(server)
    else:
        server.logger.info("定时备份未启动")


@mcdr.new_thread
def start_scheduler_thread(server:mcdr.PluginServerInterface):
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            server.logger.error(f"[ExtraBackup] 定时任务执行失败: {e}")
        time.sleep(1)


def on_load(server:mcdr.PluginServerInterface, pre_state):
    global config,backup_path,this_server
    server.logger.info("ExtraBackup启动中...")
    this_server=server
    server.logger.info("正在读取配置文件...")
    try:
        js=config_loader()
        for key in js:
            config[key]=js[key]
        server.logger.info("配置文件读取成功")
    except Exception as e:
        server.logger.warning("配置文件读取失败,原因是："+e)
        config=default_config
        try:
            with open(config_file , "w") as f:
                json.dump(default_config , f , indent=4 , ensure_ascii=False)
        except:
            pass
        server.logger.warning("extra_backup正在使用默认配置运行")
    if config["enable"]=="true":
        server.logger.info("正在读取备份路径...")
        try:
            backup_path=backup_path_loader()
            server.logger.info("备份路径加载完成")
        except Exception as e:
            server.logger.warning("备份路径加载失败！原因是："+e)
            server.logger.warning("Extra Backup插件将暂停运行直至有可用备份路径")
            try:
                with open(backup_config_path , "w") as f:
                    json.dump(backup_path , f , indent=4 , ensure_ascii=False)
            except:
                pass
            server.logger.warning("请使用!!exb help获取更多帮助")
        exb_command=mcdr.SimpleCommandBuilder()
        exb_command.command("!!exb uploadall",uploadall)
        exb_command.command("!!exb downloadall <from>",downloadall)
        exb_command.command("!!exb upload <file_name>",cmd_upload)
        exb_command.command("!!exb download <from> <file_name>",download)
        exb_command.command("!!exb list",make_list)
        exb_command.command("!!exb list <from>",make_list)
        exb_command.command("!!exb abort",abort)
        exb_command.arg("file_name",mcdr.Text)
        exb_command.arg("from",mcdr.Text)
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
            server.logger.warning("未知的启动模式！"+config["mode"])
            server.logger.warning("ExtraBackup将卸载！")
            on_unload(server)
        schedule_backup_config=config["schedule_backup"]
        backup_timer(schedule_backup_config,server)
        server.logger.info("Extra Backup启动成功")
    elif config["enable"]=="false":
        server.logger.warning("ExtraBackup没有运行，原因:你没有开启该插件！")

    else:
        server.logger.warning("错误的配置项：enable")

    
def on_unload(server):
    if uploading:
        server.logger.info("Extra Backup正在上传存档备份，请等待上传完成")
        server.logger.info("如需立即终止上传请使用!!exb abort指令")
    elif downloading:
        server.logger.info("Extra Backup正在下载存档备份，请等待下载完成")
        server.logger.info("如需立即终止下载请使用!!exb abort指令")
    else:
        server.logger.info("Extra Backup已卸载")