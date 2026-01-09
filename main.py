import os
# 設定輸入法模式
os.environ['SDL_IME_SHOW_UI'] = '1'

import threading
from kivy.config import Config
# 最後嘗試： dock 模式有時候對小米手機比較友善
Config.set('kivy', 'keyboard_mode', 'systemanddock')

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.recycleview import RecycleView
from kivy.clock import Clock, mainthread
from kivy.utils import platform
from kivy.core.text import LabelBase
from kivy.loader import Loader

Loader.headers = {'User-Agent': 'Mozilla/5.0'}

# 1. 取得絕對路徑
def get_path(folder_name):
    if platform == 'android':
        try:
            from jnius import autoclass
            context = autoclass('org.kivy.android.PythonActivity').mActivity
            return context.getExternalFilesDir(None).getAbsolutePath()
        except: return "/sdcard/Download"
    else:
        return os.path.join(os.getcwd(), 'MusicPlayer')

# 2. 啟動時下載字型 (這是唯一不依賴系統字型的解法)
font_path = os.path.join(get_path('Cache'), 'myfont.ttf')
FONT_NAME = 'Roboto'

if not os.path.exists(os.path.dirname(font_path)):
    os.makedirs(os.path.dirname(font_path), exist_ok=True)

# ==========================================
# KV 介面
# ==========================================
KV_CODE = f"""
<SongItem@BoxLayout>:
    orientation: 'horizontal'
    size_hint_y: None
    height: '80dp'
    padding: '10dp'
    canvas.before:
        Color:
            rgba: [0.2, 0.2, 0.2, 1]
        Rectangle:
            pos: self.pos
            size: self.size
    
    Label:
        text: root.title
        font_name: '{FONT_NAME}'
        font_size: '18sp'
        text_size: self.size
        halign: 'left'
        valign: 'center'
        shorten: True
        color: [1, 1, 1, 1]

    Button:
        text: 'PLAY'
        size_hint_x: None
        width: '80dp'
        on_release: app.play_music(root.index)

BoxLayout:
    orientation: 'vertical'
    padding: '10dp'
    spacing: '10dp'
    canvas.before:
        Color:
            rgba: [0.1, 0.1, 0.1, 1]
        Rectangle:
            pos: self.pos
            size: self.size

    Label:
        id: status
        text: app.status_msg
        font_name: '{FONT_NAME}'
        size_hint_y: None
        height: '40dp'
        color: [1, 1, 0, 1]

    BoxLayout:
        size_hint_y: None
        height: '50dp'
        TextInput:
            id: inp
            hint_text: 'Search...'
            multiline: False
        Button:
            text: 'GO'
            size_hint_x: None
            width: '60dp'
            on_release: app.search(inp.text)

    RecycleView:
        id: rv
        viewclass: 'SongItem'
        RecycleBoxLayout:
            default_size: None, dp(80)
            default_size_hint: 1, None
            size_hint_y: None
            height: self.minimum_height
            orientation: 'vertical'
"""

class MusicPlayerApp(App):
    from kivy.properties import StringProperty
    status_msg = StringProperty("Initializing...")
    
    def build(self):
        self.player = None
        # 啟動後下載字型
        threading.Thread(target=self.download_font).start()
        return Builder.load_string(KV_CODE)

    def download_font(self):
        import requests
        if not os.path.exists(font_path):
            try:
                self.update_status("Downloading Font...")
                # 下載一個開源中文字型
                url = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/TraditionalChinese/NotoSansCJKtc-Regular.otf"
                r = requests.get(url, timeout=30)
                with open(font_path, 'wb') as f: f.write(r.content)
            except: pass
        
        if os.path.exists(font_path):
            LabelBase.register(name='MyFont', fn_regular=font_path, fn_bold=font_path)
            global FONT_NAME
            FONT_NAME = 'MyFont'
            self.update_status("Ready (Font Loaded)")
        else:
            self.update_status("Ready (No Font)")

    @mainthread
    def update_status(self, msg):
        self.status_msg = msg

    def search(self, txt):
        if not txt: return
        self.update_status("Searching...")
        self.root.ids.inp.focus = False
        threading.Thread(target=self.do_search, args=(txt,)).start()

    def do_search(self, txt):
        try:
            import yt_dlp
            import requests
            requests.packages.urllib3.disable_warnings()
            opts = {'quiet':True, 'extract_flat':True, 'nocheckcertificate':True}
            res = []
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(f"ytsearch5:{txt}", download=False)
                for i, e in enumerate(info['entries']):
                    res.append({'title': e.get('title'), 'url': e.get('url'), 'index': i})
            Clock.schedule_once(lambda dt: self.set_list(res))
        except Exception as e:
            self.update_status(f"Err: {e}")

    @mainthread
    def set_list(self, data):
        self.root.ids.rv.data = data
        self.update_status("Done")

    def play_music(self, idx):
        data = self.root.ids.rv.data[idx]
        self.update_status("Downloading...")
        threading.Thread(target=self.do_dl, args=(data['url'], data['title'])).start()

    def do_dl(self, url, title):
        try:
            import yt_dlp
            folder = os.path.join(get_path('Music'))
            if not os.path.exists(folder): os.makedirs(folder)
            
            safe = "".join([c for c in title if c.isalnum()]).rstrip()
            out = os.path.join(folder, f"{safe}.%(ext)s")
            
            # 絕對保守的下載參數
            opts = {
                'format': 'bestaudio[ext=m4a]/best',
                'outtmpl': out,
                'quiet': True,
                'nocheckcertificate': True,
                'keepvideo': True # 避免混流導致的崩潰
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            
            # 找檔案
            target = None
            for f in os.listdir(folder):
                if safe in f: target = os.path.join(folder, f); break
            
            if target:
                Clock.schedule_once(lambda dt: self.play_native(target))
                self.update_status(f"Playing: {safe}")
            else:
                self.update_status("DL Fail")
        except Exception as e:
            self.update_status(f"Err: {e}")

    @mainthread
    def play_native(self, path):
        if platform == 'android':
            try:
                from jnius import autoclass
                MediaPlayer = autoclass('android.media.MediaPlayer')
                if self.player: 
                    try: self.player.stop(); self.player.release()
                    except: pass
                self.player = MediaPlayer()
                self.player.setDataSource(path)
                self.player.prepare()
                self.player.start()
            except Exception as e:
                self.status_msg = f"Native Play Err: {e}"

if __name__ == '__main__':
    MusicPlayerApp().run()
