from mcdreforged.api.all import *

def reply(s: CommandSource | PluginServerInterface, msg: str | RText, state: str="Info"):
    if isinstance(s, PluginServerInterface):
        if isinstance(msg, str):
            match state:
                case "Info":
                    s.logger.info(msg)
                case "Error":
                    s.logger.error(msg)
                case "Warning":
                    s.logger.warning(msg)
                case "Success":
                    s.logger.info(msg)
        elif isinstance(msg, RText):
            s.logger.info(msg)
    if isinstance(s, CommandSource):
        if isinstance(msg, str):
            match state:
                case "Info":
                    s.reply(msg)
                case "Success":
                    s.reply(RText(msg, RColor.green))
                case "Error":
                    s.reply(RText(msg, RColor.yellow))
                case "Warning":
                    s.reply(RText(msg, RColor.red))
            return
        elif isinstance(msg, RText):
            s.reply(msg)