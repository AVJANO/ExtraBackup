#Extra Backup
#Open Source License: GNU General Public License v3.0

import mcdreforged.api.all as mcdr
from pathlib import Path
import importlib.resources
import schedule
import ftplib
import shutil
import time
import json
import os
import re


PLUGIN_METADATA = {
    'id': 'extra_backup',
    'version': '0.1.7',
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
                    "language":"zh_cn",
                    "mode":"pb",
                    "localfolder":"",
                    "multithreading":"true",
                    "schedule_backup":{"enable":"false",
                                "interval":"30m"},
                    "schedule_prnue":{"enable":"false",
                                "interval":"1d",
                                "max_lifetime":"3d"}
                  }
config=default_config.copy()

language_list = ["zh_cn" , "en_us"]

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
schedule_run = True
lang = {}
count = 0

config_path=os.path.join(os.getcwd(),"config")
config_folder=os.path.join(config_path,"extra_backup")
config_file=os.path.join(config_folder,"config.json")
backup_config_path=os.path.join(config_folder,"backup_path.json")
download_path=os.path.join(os.getcwd(),"exb_downloads")


def main():
    pass

def config_loader(config = default_config , re_write = False):
    if re_write:
        with open(config_file , "w") as f:
            json.dump(config , f , indent=4 , ensure_ascii=False)
            return config
    else:
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


def lang_loader(lang_code = config["language"]):
    # 读取语言文件
    if lang_code in language_list:
        with importlib.resources.open_text("lang", f"{lang_code}.json", encoding="utf-8") as f:
            return json.load(f)
    else:
        return lang_loader(lang_code = "en_us")


def cmd_change_lang(s:mcdr.CommandSource , command):
    global lang
    if command["language"] in language_list:
        lang = lang_loader(lang_code = command["language"])
        config["language"] = command["language"]
        config_loader(config=config , re_write=True)
        s.reply(t("lang_chanage_succeed" , language = command["language"]))
    else:
        s.reply(t("lang_chanage_failed" , language = command["language"]))


def t(key: str, **kwargs) -> str:
    # 获取翻译文本
    # key: 语言文件中的键
    text = lang.get(key, key)
    try:
        return text.format(**kwargs)
    except KeyError:
        return text  # 避免缺参时报错


@mcdr.new_thread
def download(s:mcdr.CommandSource , command):
    global downloading
    try:
        os.makedirs("exb_downloads")
    except:
        pass
    if command["from"] in backup_path:
        backup = backup_path[command["from"]]
        if backup["enable"] == "true":
            if backup["mode"] == "local":
                try:
                    downloading=True
                    s.reply(t("download_start" , file_name = command["file_name"]))
                    if command["file_name"] not in os.listdir(download_path):
                        shutil.copy(os.path.join(backup["address"], command["file_name"] ) , download_path)
                        downloading = False
                        s.reply(t("download_success" , file_name = {command["file_name"]}))
                    else:
                        s.reply(t("download_skip_exists" , file_name = command["file_name"]))
                except Exception as error:
                    s.reply(t("download_fail" , file_name = command["file_name"] , e = error))
                    downloading = False
            elif backup["mode"] == "ftp":
                s.reply(t("download_mode_unsupported" , mode = backup["mode"]))
            else:
                s.reply(t("download_mode_unsupported" , mode = backup["mode"]))
        else:
            s.reply(t("download_path_disabled" , from_where = command["from"]))
    else:
        s.reply(t("download_unknown_location" , from_where = command["from"]))


@mcdr.new_thread
def upload(s:mcdr.CommandSource , backup_name , _backup_path , local_file):
    global uploading
    if _backup_path["enable"] == "true":
        mode = _backup_path["mode"]
        if mode == "ftp":
            uploading = True
            s.reply(t("upload_file_start" , backup_name = backup_name , file_name = Path(local_file).name))
            try:
                uploader = ftplib.FTP()
                pass
            except Exception as error:
                s.reply(t("upload_fail" , backup_name = backup_name , file_name = Path(local_file).name , error = error))
            finally:
                uploader.quit()
                uploading = False
        elif mode == "local":
            try:
                uploading = True
                address=_backup_path["address"]
                if Path(local_file).name not in os.listdir(_backup_path["address"]):
                    s.reply(t("upload_file_start" , backup_name = backup_name , file_name = Path(local_file).name))
                    shutil.copy(local_file , address)
                    s.reply(t("upload_file_success" , backup_name = backup_name , file_name = Path(local_file).name))
                else:
                    s.reply(t("upload_skip_duplicate" , backup_name = backup_name , file_name = Path(local_file).name))
            except Exception as e:
                s.reply(t("upload_fail" , backup_name = backup_name , file_name = Path(local_file).name , error = e))
            finally:
                uploading = False
        elif mode=="smb":
            pass
        elif mode=="ftps":
            pass
        elif mode=="sftp":
            pass
        elif mode=="ssh":
            pass
        else:
            s.reply(t("upload_mode_unsupported" , backup_name = backup_name , mode = mode))


def uploadall(s:mcdr.CommandSource,server:mcdr.PluginServerInterface=this_server):
    s.reply(t("manual_uploadall_start"))
    for name in backup_path:
        backup_dest=backup_path[name]
        if backup_dest["enable"]=="true":
            for file in os.listdir(config["localfolder"]):
                upload(s , name , backup_path[name] , os.path.join(config["localfolder"], file))
                time.sleep(0.2)
        else:
            pass
    s.reply(t("uploadall_completed"))


def cmd_upload(s:mcdr.CommandSource , commands):
    if commands["file_name"] in os.listdir(config["localfolder"]):
        for backup_name in backup_path:
            backup=backup_path[backup_name]
            if backup["mode"]=="local":
                try:
                    upload(s,backup_name,backup_path[backup_name],os.path.join(config["localfolder"], commands["file_name"]))
                except Exception as e:
                    s.reply(t("upload_fail" , backup_name = backup_name , file_name = commands["file_name"]))
            elif backup["mode"]=="ftp":
                s.reply(t("upload_mode_unsupported" , mode = backup["mode"]))
            else:
                s.reply(t("upload_mode_unsupported" , mode = backup["mode"]))
    else:
        s.reply(t("upload_fail_not_exist" , file_name = commands["file_name"]))


def downloadall(source:mcdr.CommandSource , from_where):
    #下载全部备份，已弃用 (到底什么情况下会有人要把所有备份都下载一遍呢？)
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
    #终止上传任务
    pass


def make_file_list(s:mcdr.CommandSource , from_where):
    if "from" in from_where:
        if from_where["from"]!="":
            if from_where["from"] in backup_path:
                backup=backup_path[from_where["from"]]
                if backup["enable"]=="true":
                    if backup["mode"]=="local":
                        for file in os.listdir(backup["address"]):
                            s.reply(file)
                    elif backup["mode"]=="ftp":
                        s.reply(t("unsupported_mode" , mode = backup["mode"]))
                    else:
                        s.reply(t("unsupported_mode" , mode = backup["mode"]))
                else:
                    s.reply(t("path_not_enabled" , from_where = from_where["from"]))
            else:
                s.reply(t("path_not_exist" , from_where = from_where["from"]))
    else:
        for file in os.listdir(config["localfolder"]):
            s.reply(file)


@mcdr.new_thread
def schedule_upload(s:mcdr.PluginServerInterface , backup_name , _backup_path , local_file):
    global uploading
    mode=_backup_path["mode"]
    if mode=="ftp":
        uploading = True
        s.logger.info(t("upload_file_start" , backup_name = backup_name , file_name = Path(local_file).name))
        try:
            uploader = ftplib.FTP()
            pass
        except Exception as e:
            s.logger.info(t("upload_fail" , backup_name = backup_name , file_name = Path(local_file).name , error = e))
        finally:
            uploader.quit()
            uploading=False
    elif mode=="local":
        try:
            uploading=True
            address=_backup_path["address"]
            if Path(local_file).name not in os.listdir(_backup_path["address"]):
                s.logger.info(t("upload_file_start" , backup_name = backup_name , file_name = Path(local_file).name))
                shutil.copy(local_file , address)
                s.logger.info(t("upload_file_success" , backup_name = backup_name , file_name = Path(local_file).name))
                time.sleep(0.2)
            else:
                s.logger.info(t("upload_skip_duplicate" , backup_name = backup_name , file_name = Path(local_file).name))
        except Exception as e:
            s.logger.info(t("upload_fail" , backup_name = backup_name , file_name = Path(local_file).name , error = e))
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
        s.logger.info(t("upload_mode_unsupported" , backup_name = backup_name , mode = mode))


def schedule_uploadall():
    this_server.logger.info(t("schedule_trigger"))
    for name in backup_path:
        backup_dest=backup_path[name]
        if backup_dest["enable"]=="true":
            for file in os.listdir(config["localfolder"]):
                schedule_upload(this_server , name , backup_path[name] , os.path.join(config["localfolder"], file))
                time.sleep(0.2)
        else:
            pass


def time_loader(s: str) -> int:
    #把类似 "1h30m", "2d3h15m20s" 转换成总秒数
    units = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400
    }
    matches = re.findall(r"(\d+)([smhd])", s.strip().lower())
    if not matches:
        raise ValueError(t("schedule_invalid_time" , time = s))
    total_seconds = sum(int(num) * units[unit] for num, unit in matches)
    return total_seconds

    
def backup_timer(schedule_config,server:mcdr.PluginServerInterface):
    if schedule_config["enable"]=="true":
        seconds = time_loader(schedule_config["interval"])
        schedule.every(seconds).seconds.do(schedule_uploadall)
        server.logger.info(t("schedule_enabled"))
    else:
        server.logger.info(t("schedule_disabled"))


def prnue_timer(prnue_config , server: mcdr.PluginServerInterface):
    if prnue_config["enable"] == "true":
        seconds = time_loader(prnue_config["interval"])
        schedule.every(seconds).seconds.do(schedule_prnue)
        server.logger.info(t("schedule_prnue_enable"))
    else:
        server.logger.info(t("schedule_prnue_disable"))


def schedule_prnue():
    prnue_config = config["schedule_prnue"]
    max_lifetime = time_loader(prnue_config["max_lifetime"])
    this_server.logger.info(t("schedule_prnue_started"))
    this_server.logger.info(t("local_prnue_started"))
    for file in os.listdir(config["localfolder"]):
        if (time.time() - os.path.getctime(os.path.join(config["localfolder"], file))) >= max_lifetime:
            try:
                os.remove(os.path.join(config["localfolder"], file))
                this_server.logger.info(t("del_file_succeed" , file_name = file))
            except FileNotFoundError:
                this_server.logger.info(t("del_file_not_exist" , file_name = file))
            except PermissionError:
                this_server.logger.info(t("del_file_no_perm" , file_name = file))
            except Exception as e:
                this_server.logger.info(t("del_file_fail" , file_name = file , error = e))
    for backup_name in backup_path:
        backup = backup_path[backup_name]
        if backup["enable"] == "true":
            if backup["mode"] == "local":
                this_server.logger.info(t("backup_prnue_started" , backup_name = backup_name))
                for file in os.listdir(backup["address"]):
                    if (time.time() - os.path.getctime(os.path.join(backup["address"], file))) >= max_lifetime:
                        try:
                            os.remove(os.path.join(backup["address"], file))
                            this_server.logger.info(t("del_file_succeed" , file_name = file))
                        except FileNotFoundError:
                            this_server.logger.warning(t("del_file_not_exist" , file_name = file))
                        except PermissionError:
                            this_server.logger.warning(t("del_file_no_perm" , file_name = file))
                        except Exception as e:
                            this_server.logger.warning(t("del_file_fail" , file_name = file , error = e))
            elif backup["mode"] == "ftp":
                this_server.logger.warning(t("unsupported_mode" , mode = backup["mdoe"]))
            else:
                this_server.logger.warning(t("unsupported_mode" , mode = backup["mdoe"]))

    this_server.logger.info(t("schedule_prnue_finished"))


def manual_prnue(s:mcdr.CommandSource , command={}):
    prnue_config = config["schedule_prnue"]
    max_lifetime = time_loader(prnue_config["max_lifetime"])
    if "location" in command:
        if command["location"] == "local":
            s.reply(t("local_prnue_started"))
            for file in os.listdir(config["localfolder"]):
                if (time.time() - os.path.getctime(os.path.join(config["localfolder"], file))) >= max_lifetime:
                    try:
                        os.remove(os.path.join(config["localfolder"], file))
                        s.reply(t("del_file_succeed" , file_name = file))
                    except FileNotFoundError:
                        s.reply(t("del_file_not_exist" , file_name = file))
                    except PermissionError:
                        s.reply(t("del_file_no_perm" , file_name = file))
                    except Exception as e:
                        s.reply(t("del_file_fail" , file_name = file , error = e))
            s.reply(t("manual_prnue_finished"))
        elif command["location"] in backup_path:
            backup = backup_path[command["location"]]
            s.reply(t("manual_prnue_started"))
            if backup["enable"] == "true":
                if backup["mode"] == "local":
                    s.reply(t("backup_prnue_started" , backup_name = command["location"]))
                    for file in os.listdir(backup["address"]):
                        if (time.time() - os.path.getctime(os.path.join(backup["address"], file))) >= max_lifetime:
                            try:
                                os.remove(os.path.join(backup["address"], file))
                                s.reply(t("del_file_succeed" , file_name = file))
                            except FileNotFoundError:
                                s.reply(t("del_file_not_exist" , file_name = file))
                            except PermissionError:
                                s.reply(t("del_file_no_perm" , file_name = file))
                            except Exception as e:
                                s.reply(t("del_file_fail" , file_name = file , error = e))
                elif backup["mode"] == "ftp":
                    s.reply(t("unsupported_mode" , mode = backup["mdoe"]))
                else:
                    s.reply(t("unsupported_mode" , mode = backup["mdoe"]))
            else:
                s.reply(t("path_not_enabled" , from_where = command["location"]))
        else:
            s.reply(t("path_not_exist" , from_where = command["location"]))
        s.reply(t("manual_prnue_finished"))
    else:
        s.reply(t("manual_prnueall_started"))
        s.reply(t("local_prnue_started"))
        for file in os.listdir(config["localfolder"]):
            if (time.time() - os.path.getctime(os.path.join(config["localfolder"], file))) >= max_lifetime:
                try:
                    os.remove(os.path.join(config["localfolder"], file))
                    s.reply(t("del_file_succeed" , file_name = file))
                except FileNotFoundError:
                    s.reply(t("del_file_not_exist" , file_name = file))
                except PermissionError:
                    s.reply(t("del_file_no_perm" , file_name = file))
                except Exception as e:
                    s.reply(t("del_file_fail" , file_name = file , error = e))
        for backup_name in backup_path:
            backup = backup_path[backup_name]
            if backup["enable"] == "true":
                if backup["mode"] == "local":
                    s.reply(t("backup_prnue_started" , backup_name = backup_name))
                    for file in os.listdir(backup["address"]):
                        if (time.time() - os.path.getctime(os.path.join(backup["address"], file))) >= max_lifetime:
                            try:
                                os.remove(os.path.join(backup["address"], file))
                                s.reply(t("del_file_succeed" , file_name = file))
                            except FileNotFoundError:
                                s.reply(t("del_file_not_exist" , file_name = file))
                            except PermissionError:
                                s.reply(t("del_file_no_perm" , file_name = file))
                            except Exception as e:
                                s.reply(t("del_file_fail" , file_name = file , error = e))
                elif backup["mode"] == "ftp":
                    s.reply(t("unsupported_mode" , mode = backup["mdoe"]))
                else:
                    s.reply(t("unsupported_mode" , mode = backup["mdoe"]))
        s.reply(t("manual_prnueall_finished"))
        


@mcdr.new_thread
def start_schedule_thread(server:mcdr.PluginServerInterface):
    while schedule_run:
        try:
            schedule.run_pending()
        except Exception as e:
            server.logger.error(t("schedule_fail" , error = e))
        time.sleep(1)
    schedule.clear()
    server.logger.info(t("schedule_stopped"))

def exporter(mode:str = config["mode"] , backup_id:int = 0):
    if backup_id >= 0:
        if backup_id == 0:
            latest_id = 0
            return latest_id
        if backup_id > 0:
            return backup_id
    else:
        return ValueError


def pb_watcher():
    pass


def on_load(server:mcdr.PluginServerInterface, pre_state):
    global config,backup_path,this_server
    global lang
    lang = lang_loader(lang_code="en_us")
    server.logger.info(t("plugin_starting"))
    this_server=server
    server.logger.info(t("plugin_loading_config"))
    try:
        js=config_loader()
        for key in js:
            config[key]=js[key]
        server.logger.info(t("plugin_config_success"))
    except Exception as e:
        server.logger.warning(t("plugin_config_fail" , error = e))
        config=default_config
        try:
            with open(config_file , "w") as f:
                json.dump(default_config , f , indent=4 , ensure_ascii=False)
        except:
            pass
        server.logger.warning(t("plugin_default_config"))
    lang = lang_loader(lang_code=config["language"])
    if config["enable"]=="true":
        server.logger.info(t("plugin_loading_path"))
        try:
            backup_path=backup_path_loader()
            server.logger.info(t("plugin_path_success"))
        except Exception as e:
            server.logger.warning(t("plugin_path_fail" , error = e))
            server.logger.warning(t("plugin_no_path"))
            try:
                with open(backup_config_path , "w") as f:
                    json.dump(backup_path , f , indent=4 , ensure_ascii=False)
            except:
                pass
            server.logger.warning(t("plugin_help"))
        exb_command=mcdr.SimpleCommandBuilder()
        exb_command.command("!!exb uploadall",uploadall)
        exb_command.command("!!exb downloadall <from>",downloadall)
        exb_command.command("!!exb upload <file_name>",cmd_upload)
        exb_command.command("!!exb download <from> <file_name>",download)
        exb_command.command("!!exb list",make_file_list)
        exb_command.command("!!exb list <from>",make_file_list)
        exb_command.command("!!exb abort",abort)
        exb_command.command("!!exb lang <language>",cmd_change_lang)
        exb_command.command("!!exb prnue",manual_prnue)
        exb_command.command("!!exb prnue <location>",manual_prnue)
        exb_command.arg("file_name",mcdr.Text)
        exb_command.arg("from",mcdr.Text)
        exb_command.arg("language",mcdr.Text)
        exb_command.arg("location",mcdr.Text)
        exb_command.register(server)
        if config["mode"]=="pb":
            config["localfolder"]=os.path.join(os.getcwd(),"pb_files")
            if os.path.exists(config["localfolder"]) and not os.path.exists(os.path.join(config["localfolder"],"export")):
                os.makedirs(os.path.exists(os.path.join(config["localfolder"],"export")))
            if os.path.exists(config["localfolder"]):
                config["localfolder"]=os.path.join(config["localfolder"],"export")
                server.logger.info(t("plugin_detect_pb"))
                server.logger.info(t("plugin_mode_pb"))
        elif config["mode"]=="qb":
            pass
        elif config["mode"]=="normal":
            pass
        else:
            server.logger.warning(t("plugin_unknown_mode" , mode = config["mode"]))
        schedule_backup_config = config["schedule_backup"]
        schedule_prnue_config = config["schedule_prnue"]
        prnue_timer(schedule_prnue_config , server)
        backup_timer(schedule_backup_config,server)
        start_schedule_thread(server)
        server.logger.info(t("plugin_started"))
    elif config["enable"]=="false":
        server.logger.warning(t("plugin_not_running"))

    else:
        server.logger.warning(t("plugin_invalid_enable"))

    
def on_unload(server):
    global schedule_run
    schedule_run = False
    time.sleep(2)
    server.logger.info(t("plugin_unloaded"))