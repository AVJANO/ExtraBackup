from extra_backup.utils.Singleton import singleton
import importlib.resources
import json

@singleton
class Language:
    _initialized = False
    lang_list = ['en_us' , 'zh_cn']
    lang_code = "en_us"
    lang = {}

    def __init__(self):
        if self._initialized:
            return
        self.load(self.lang_code)
        self._initialized = True

    def load(self, lang_code):
        """加载语言"""
        if lang_code not in self.lang_list:
            raise ValueError
        self.lang_code = lang_code
        with importlib.resources.open_text("lang", f"{lang_code}.json", encoding="utf-8") as f:
            self.lang = json.load(f)

def tr(key , **kwargs):
    """翻译"""
    text = Language().lang.get(key , key)
    try:
        return text.format(**kwargs)
    except KeyError:
        return text