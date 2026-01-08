import os
# 1. 強制環境設定 (放在最前面)
os.environ['KIVY_IMAGE'] = 'sdl2'
os.environ['SDL_IME_SHOW_UI'] = '1'

from kivy.config import Config
# 【關鍵修復1】輸入法：這行必須在 App 載入前執行
Config.set('kivy', 'keyboard_mode', '')

import threading
import time
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import BooleanProperty, StringProperty, NumericProperty
from kivy.clock import Clock, mainthread
from kivy.utils import platform
from kivy.event import EventDispatcher
from kivy.loader import Loader

# 偽裝
Loader.headers = {'User-Agent': 'Mozilla/5.0'}

# 路徑
def get_storage_path():
    if platform == 'android':
        try:
            from jnius import autoclass
            return autoclass('org.kivy.android.PythonActivity').mActivity.getExternalFilesDir(None).getAbsolutePath()
        except: return "/sdcard/Download"
    else:
        return os.path.join(os.getcwd(), 'MusicPlayer')

# ==========================================
# 介面 (極簡黑底版 - 為了保證不閃退)
# ==========================================
KV_CODE = f"""
<SongItem@BoxLayout>:
    orientation: 'horizontal'
    size_hint_y: None
    height: '100dp'
    padding: '5dp'
    spacing: '5dp'
    canvas.before:
        Color:
            rgba: [0.2, 0.2, 0.2, 1]
        Rectangle:
            pos: self.pos
            size: self.size
    
    # 圖片區
    Image:
        source: root.thumb
        size_hint_x: None
        width: '100dp'
        fit_mode: 'cover'
        nocache: True
        color: [1, 1, 1, 1]

    # 文字區
    Label:
        text: root.title
        font_name: 'Roboto' 
        text_size: self.size
        halign: 'left'
        valign: 'center'
        shorten: True
        color: [1, 1, 1, 1]

    # 播放按鈕
    Button:
        text: 'PLAY'
        size_hint_x: None
        width: '70dp'
        background_color: [0, 0.8, 0, 1]
        on_release: app.play_manager(root.index)

BoxLayout:
    orientation: 'vertical'
    padding: '5dp'
    spacing: '5dp'
    canvas.before:
        Color:
            rgba: [0.1, 0.1, 0.1, 1]
        Rectangle:
            pos: self.pos
            size: self.size

    # 搜尋列
    BoxLayout:
        size_hint_y: None
        height: '60dp'
        TextInput:
            id: search_input
            hint_text: 'Search...'
            multiline: False
            size_hint_x: 0.7
        Button:
            text: 'GO'
            size_hint_x: 0.3
            on_release: app.start_search(search_input.text)

    # 狀態列
    Label:
        text: app.status_msg
        size_hint_y: None
        height: '40dp'
        color: [1, 1, 0, 1]

    # 列表
    RecycleView:
        id: rv
        viewclass: 'SongItem'
        RecycleBoxLayout:
            default_size: None, dp(100)
            default_size_hint: 1, None
            size_hint_y: None
            height: self.minimum_height
            orientation: 'vertical'
            spacing: '2dp'
"""

class SongItem(BoxLayout):
    title = StringProperty("")
    thumb = StringProperty("")
    index = NumericProperty(0)

class MusicPlayerApp(App):
    status_msg = StringProperty("Ready")
    
    def build(self):
        # 延遲載入播放器，防止啟動崩潰
        self.player = None
        Clock.schedule_once(self.init_player, 1)
        return Builder.load_string(KV_CODE)

    def init_player(self, dt):
        if platform == 'android':
            try:
                from jnius import autoclass
                self.MediaPlayer = autoclass('android.media.MediaPlayer')
                self.player = self.MediaPlayer()
            except: pass

    def start_search(self, keyword):
        if not keyword: return
        self.status_msg = "Searching..."
        self.root.ids.search_input.focus = False
        threading.Thread(target=self._search_thread, args=(keyword,)).start()

    def _search_thread(self, keyword):
        try:
            import requests
            import yt_dlp
            # 忽略 SSL 錯誤
            requests.packages.urllib3.disable_warnings()
            
            root = get_storage_path()
            cache_dir = os.path.join(root, 'Cache')
            if not os.path.exists(cache_dir): os.makedirs(cache_dir)
            
            ydl_opts = {'quiet': True, 'extract_flat': True, 'ignoreerrors': True, 'nocheckcertificate': True}
            
            results = []
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch10:{keyword}", download=False)
                if 'entries' in info:
                    for i, e in enumerate(info['entries']):
                        vid = e.get('id', str(i))
                        thumb_url = e.get('thumbnail', '')
                        local_thumb = os.path.join(cache_dir, f"{vid}.jpg")
                        
                        # 【關鍵修復2】手動下載圖片
                        # 如果檔案不存在或大小為0，就下載
                        if thumb_url and (not os.path.exists(local_thumb) or os.path.getsize(local_thumb) == 0):
                            try:
                                r = requests.get(thumb_url, timeout=5, verify=False)
                                with open(local_thumb, 'wb') as f: f.write(r.content)
                            except: pass
                        
                        final_thumb = local_thumb if os.path.exists(local_thumb) else ''
                        results.append({
                            'title': e.get('title', 'Unknown'),
                            'url': e.get('url', ''),
                            'thumb': final_thumb,
                            'index': i
                        })
            
            Clock.schedule_once(lambda dt: self.update_ui(results))
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self, 'status_msg', f"Err: {e}"))

    @mainthread
    def update_ui(self, data):
        self.root.ids.rv.data = data
        self.status_msg = "Search Done"

    def play_manager(self, index):
        data = self.root.ids.rv.data[index]
        self.status_msg = f"DL: {data['title'][:10]}..."
        threading.Thread(target=self._download_thread, args=(data['url'], data['title'])).start()

    def _download_thread(self, url, title):
        try:
            import yt_dlp
            root = get_storage_path()
            music_dir = os.path.join(root, 'Music')
            if not os.path.exists(music_dir): os.makedirs(music_dir)
            
            safe_title = "".join([c for c in title if c.isalnum() or c in ' -_']).rstrip()
            out_file = os.path.join(music_dir, f'{safe_title}.%(ext)s')
            
            # 【關鍵修復3】強制 m4a，禁止轉檔
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/best',
                'outtmpl': out_file,
                'quiet': True,
                'nocheckcertificate': True,
                'postprocessors': [],
                'keepvideo': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # 尋找檔案
            target = None
            for f in os.listdir(music_dir):
                if safe_title in f and f.endswith(('.m4a', '.mp3')):
                    target = os.path.join(music_dir, f)
                    break
            
            if target and os.path.exists(target) and os.path.getsize(target) > 0:
                Clock.schedule_once(lambda dt: self.play_audio(target))
                Clock.schedule_once(lambda dt: setattr(self, 'status_msg', f"Playing: {safe_title}"))
            else:
                Clock.schedule_once(lambda dt: setattr(self, 'status_msg', "DL Failed"))
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self, 'status_msg', f"DL Err: {e}"))

    @mainthread
    def play_audio(self, filepath):
        if self.player:
            try:
                if self.player.isPlaying(): self.player.stop()
                self.player.reset()
                self.player.setDataSource(filepath)
                self.player.prepare()
                self.player.start()
            except Exception as e:
                self.status_msg = f"Play Err: {e}"

if __name__ == '__main__':
    MusicPlayerApp().run()
