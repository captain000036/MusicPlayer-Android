# main.py - 絕對防爆版
import os
import threading
# 啟動時完全不 import 複雜套件
from kivy.config import Config

# 1. 系統補丁
Config.set('kivy', 'keyboard_mode', '') # 解決輸入法
os.environ['SDL_IME_SHOW_UI'] = '1'
Config.set('network', 'useragent', 'Mozilla/5.0') # 偽裝

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.properties import StringProperty, ListProperty, NumericProperty
from kivy.clock import Clock, mainthread
from kivy.utils import platform
from kivy.event import EventDispatcher
from kivy.core.text import LabelBase
from kivy.loader import Loader

# 設定圖片 User-Agent
Loader.headers = {'User-Agent': 'Mozilla/5.0'}

# 載入字體 (失敗也不會閃退)
try:
    LabelBase.register(name='MyFont', fn_regular='NotoSansTC-Regular.otf', fn_bold='NotoSansTC-Regular.otf')
    FONT_NAME = 'MyFont'
except: 
    FONT_NAME = 'Roboto'

# 路徑
def get_path(folder_name):
    if platform == 'android':
        try:
            from jnius import autoclass
            root = autoclass('org.kivy.android.PythonActivity').mActivity.getExternalFilesDir(None).getAbsolutePath()
        except: root = "/sdcard/Download"
    else:
        root = os.path.join(os.getcwd(), 'MusicPlayer')
    
    target = os.path.join(root, folder_name)
    if not os.path.exists(target): os.makedirs(target, exist_ok=True)
    return target

# ==========================================
# KV 介面 (您原本的漂亮介面)
# ==========================================
KV_CODE = f"""
#:import hex kivy.utils.get_color_from_hex

<AutoScrollLabel>:
    do_scroll_x: False
    do_scroll_y: False
    Label:
        id: lbl
        text: root.text
        font_name: '{FONT_NAME}'
        font_size: '16sp'
        size_hint: None, 1
        width: self.texture_size[0] + 50
        halign: 'center'
        valign: 'middle'

<SongListItem>:
    orientation: 'horizontal'
    size_hint_y: None
    height: '80dp'
    padding: '10dp'
    spacing: '15dp'
    on_release: app.play_manager(self.index)
    canvas.before:
        Color:
            rgba: [0.1, 0.1, 0.1, 1]
        Rectangle:
            pos: self.pos
            size: self.size
    Image:
        source: root.thumb
        color: [1,1,1,1] if root.thumb else [1,1,1,0]
        size_hint_x: None
        width: '80dp'
        fit_mode: 'cover'
        nocache: True
    BoxLayout:
        orientation: 'vertical'
        Label:
            text: root.title
            font_name: '{FONT_NAME}'
            font_size: '16sp'
            text_size: self.size
            halign: 'left'
            valign: 'center'
            shorten: True
    Label:
        text: '▶'
        font_name: '{FONT_NAME}'
        size_hint_x: None
        width: '40dp'
        color: [0, 1, 0, 1]

BoxLayout:
    orientation: 'vertical'
    padding: '10dp'
    spacing: '10dp'
    canvas.before:
        Color:
            rgba: [0.05, 0.05, 0.05, 1]
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        size_hint_y: None
        height: '50dp'
        TextInput:
            id: search_input
            hint_text: '輸入歌手...'
            font_name: '{FONT_NAME}'
            multiline: False
        Button:
            text: '搜尋'
            font_name: '{FONT_NAME}'
            size_hint_x: 0.25
            on_release: app.search_music(search_input.text)

    RecycleView:
        id: rv
        viewclass: 'SongListItem'
        RecycleBoxLayout:
            default_size: None, dp(80)
            default_size_hint: 1, None
            size_hint_y: None
            height: self.minimum_height
            orientation: 'vertical'

    AutoScrollLabel:
        text: app.current_playing_title
        size_hint_y: None
        height: '40dp'
        
    BoxLayout:
        size_hint_y: None
        height: '60dp'
        Button:
            text: 'Prev'
            on_release: app.play_previous()
        Button:
            text: 'Play/Pause'
            on_release: app.toggle_play()
        Button:
            text: 'Next'
            on_release: app.play_next()
"""

class AutoScrollLabel(ScrollView):
    text = StringProperty('')
    def on_kv_post(self, w):
        self.lbl = self.ids.lbl
        self.bind(text=self.update_text)
    def update_text(self, i, v):
        self.lbl.text = v

class SongListItem(ButtonBehavior, BoxLayout):
    title = StringProperty("")
    url = StringProperty("")
    thumb = StringProperty("")
    index = NumericProperty(0)

class MusicPlayerApp(App):
    current_playing_title = StringProperty("Ready")
    
    def build(self):
        # 1. 建立播放器 (使用最原始的 Android MediaPlayer)
        self.player = None
        if platform == 'android':
            try:
                from jnius import autoclass
                self.MediaPlayer = autoclass('android.media.MediaPlayer')
                self.player = self.MediaPlayer()
            except: pass
        return Builder.load_string(KV_CODE)

    def search_music(self, kw):
        if not kw: return
        self.current_playing_title = f"搜尋: {kw}..."
        # 2. 啟動線程 (防止卡死)
        threading.Thread(target=self._search_thread, args=(kw,)).start()

    def _search_thread(self, kw):
        try:
            # 3. 【關鍵】在這裡才載入 heavy libraries
            # 如果這裡崩潰，會被 try-except 抓到，並顯示在畫面上
            import yt_dlp
            import requests
            
            # 使用 requests 下載圖片
            cache_dir = get_path('Cache')
            
            ydl_opts = {'quiet': True, 'extract_flat': True, 'ignoreerrors': True, 'nocheckcertificate': True}
            
            results = []
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch10:{kw}", download=False)
                if 'entries' in info:
                    for i, e in enumerate(info['entries']):
                        title = e.get('title', 'Unknown')
                        thumb_url = e.get('thumbnail', '')
                        vid = e.get('id', str(i))
                        
                        # 下載圖片
                        local_thumb = os.path.join(cache_dir, f"{vid}.jpg")
                        if thumb_url:
                            try:
                                r = requests.get(thumb_url, timeout=3, verify=False)
                                with open(local_thumb, 'wb') as f: f.write(r.content)
                            except: pass
                        
                        thumb = local_thumb if os.path.exists(local_thumb) else ''
                        results.append({'title': title, 'url': e.get('url'), 'thumb': thumb, 'index': i})
            
            Clock.schedule_once(lambda dt: self.update_list(results))
            
        except Exception as e:
            # 顯示錯誤訊息在介面上，而不是閃退
            Clock.schedule_once(lambda dt: setattr(self, 'current_playing_title', f"錯誤: {str(e)[:30]}"))

    @mainthread
    def update_list(self, data):
        self.root.ids.rv.data = data
        self.current_playing_title = "請選擇歌曲"

    def play_manager(self, index):
        data = self.root.ids.rv.data[index]
        self.current_playing_title = f"準備下載: {data['title']}"
        threading.Thread(target=self._download_thread, args=(data['url'], data['title'])).start()

    def _download_thread(self, url, title):
        try:
            import yt_dlp
            folder = get_path('Music')
            safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c in ' -_']).rstrip()
            out = os.path.join(folder, f'{safe_title}.%(ext)s')
            
            # 4. 強制下載 m4a (最穩定)
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/best',
                'outtmpl': out,
                'quiet': True,
                'nocheckcertificate': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            # 找檔案並播放
            target = None
            for f in os.listdir(folder):
                if safe_title in f: target = os.path.join(folder, f); break
            
            if target:
                Clock.schedule_once(lambda dt: self.start_play(target))
            else:
                Clock.schedule_once(lambda dt: setattr(self, 'current_playing_title', "下載失敗"))
                
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self, 'current_playing_title', f"下載錯誤: {e}"))

    @mainthread
    def start_play(self, path):
        if self.player:
            try:
                self.player.reset()
                self.player.setDataSource(path)
                self.player.prepare()
                self.player.start()
                self.current_playing_title = f"播放中: {os.path.basename(path)}"
            except Exception as e:
                self.current_playing_title = f"播放失敗: {e}"

    def play_previous(self): pass
    def play_next(self): pass
    def toggle_play(self):
        if self.player:
            if self.player.isPlaying(): self.player.pause()
            else: self.player.start()

if __name__ == '__main__':
    MusicPlayerApp().run()
