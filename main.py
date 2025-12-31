import os
import threading
import contextlib
import urllib.request
# 注意：這裡先不 import yt_dlp，避免開機直接閃退

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import AsyncImage
from kivy.properties import StringProperty, ListProperty, BooleanProperty, NumericProperty
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.utils import platform
from kivy.animation import Animation
from kivy.event import EventDispatcher
from kivy.config import Config
from kivy.core.text import LabelBase

# 1. 環境設定
os.environ['SDL_IME_SHOW_UI'] = '1'
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'
Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '640')
Config.set('graphics', 'resizable', '1')

# 2. 字體載入 (含防呆)
FONT_NAME = 'Roboto'
try:
    LabelBase.register(name='MyFont',
                       fn_regular='NotoSansTC-Regular.otf',
                       fn_bold='NotoSansTC-Bold.otf')
    FONT_NAME = 'MyFont'
except Exception as e:
    print(f"Font Error: {e}")

def get_storage_path():
    if platform == 'android':
        try:
            from android.storage import primary_external_storage_path
            root = os.path.join(primary_external_storage_path(), 'Android', 'data', 'org.test.musicplayer', 'files', 'Music')
        except:
            root = "/sdcard/Music"
    else:
        root = os.path.join(os.getcwd(), 'Music')
    if not os.path.exists(root):
        try: os.makedirs(root, exist_ok=True)
        except: pass
    return root

class QuietLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): print(f"[YTDLP_ERROR] {msg}")

# ==========================================
# 核心引擎
# ==========================================
class MusicEngine(EventDispatcher):
    __events__ = ('on_playback_ready', 'on_track_finished', 'on_error')
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sound = None
        self.lock = False

    def load_track(self, filepath):
        if self.lock: return
        self.lock = True
        if self.sound:
            try:
                self.sound.stop()
                self.sound.unload()
                self.sound = None
            except: pass
        Clock.schedule_once(lambda dt: self._real_load(filepath), 0.2)

    def _real_load(self, filepath):
        try:
            self.sound = SoundLoader.load(filepath)
            if self.sound:
                self.sound.bind(on_stop=self._on_stop)
                self.sound.play()
                self.dispatch('on_playback_ready', True)
            else:
                self.dispatch('on_playback_ready', False)
        except Exception as e:
            self.dispatch('on_error', str(e))
        finally:
            self.lock = False

    def pause_resume(self):
        if not self.sound: return False
        if self.sound.state == 'play':
            self.sound.stop()
            return False
        else:
            self.sound.play()
            return True

    def _on_stop(self, instance):
        if not self.lock: self.dispatch('on_track_finished')
    def on_playback_ready(self, success): pass
    def on_track_finished(self): pass
    def on_error(self, error): pass

# ==========================================
# KV 介面
# ==========================================
KV_CODE = f"""
#:import hex kivy.utils.get_color_from_hex

<AutoScrollLabel>:
    Label:
        id: lbl
        text: root.text
        font_name: '{FONT_NAME}'
        font_size: root.font_size
        color: root.color
        size_hint: None, 1
        width: self.texture_size[0] + 50
        halign: 'center'
        valign: 'middle'

<SpotifyCard@Button>:
    background_normal: ''
    background_color: 0,0,0,0
    font_name: '{FONT_NAME}'
    font_size: '16sp'
    bold: True
    text_size: self.size
    halign: 'center'
    valign: 'center'
    canvas.before:
        Color:
            rgba: root.img_color if hasattr(root, 'img_color') else [0.3,0.3,0.3,1]
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10,]

<SongListItem@ButtonBehavior+BoxLayout>:
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
    AsyncImage:
        source: root.thumb
        size_hint_x: None
        width: '80dp'
    BoxLayout:
        orientation: 'vertical'
        Label:
            text: root.title
            font_name: '{FONT_NAME}'
            font_size: '16sp'
            text_size: self.size
            halign: 'left'
            valign: 'bottom'
            shorten: True
        Label:
            text: root.status_text
            font_name: '{FONT_NAME}'
            font_size: '12sp'
            color: [0.5, 0.5, 0.5, 1]
            text_size: self.size
            halign: 'left'
            valign: 'top'

BoxLayout:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: [0.07, 0.07, 0.07, 1]
        Rectangle:
            pos: self.pos
            size: self.size

    # --- 頂部狀態列 (顯示錯誤訊息用) ---
    Label:
        id: status_label
        text: app.init_status
        size_hint_y: None
        height: '40dp'
        color: [1, 0.2, 0.2, 1] if '錯誤' in self.text else [0.2, 1, 0.2, 1]
        font_name: '{FONT_NAME}'
        font_size: '14sp'

    # --- 搜尋欄 ---
    BoxLayout:
        size_hint_y: None
        height: '60dp'
        padding: '10dp'
        spacing: '10dp'
        TextInput:
            id: search_input
            hint_text: '輸入關鍵字...'
            font_name: '{FONT_NAME}'
            multiline: False
            size_hint_x: 0.7
            on_text_validate: app.search_music(self.text)
        Button:
            text: '搜尋'
            font_name: '{FONT_NAME}'
            size_hint_x: 0.3
            background_color: [0.11, 0.72, 0.32, 1]
            on_release: app.search_music(search_input.text)

    # --- 快捷卡片 ---
    GridLayout:
        cols: 2
        size_hint_y: None
        height: '120dp'
        padding: '10dp'
        spacing: '10dp'
        SpotifyCard:
            text: '華語熱門'
            img_color: [0.8, 0.2, 0.2, 1]
            on_release: app.search_music('華語熱門 2024')
        SpotifyCard:
            text: '西洋排行榜'
            img_color: [0.2, 0.2, 0.8, 1]
            on_release: app.search_music('Billboard Hot 100')

    # --- 列表 ---
    RecycleView:
        id: rv
        viewclass: 'SongListItem'
        RecycleBoxLayout:
            default_size: None, dp(80)
            default_size_hint: 1, None
            size_hint_y: None
            height: self.minimum_height
            orientation: 'vertical'

    # --- 底部播放列 ---
    Label:
        text: app.current_playing_title
        font_name: '{FONT_NAME}'
        size_hint_y: None
        height: '50dp'
    BoxLayout:
        size_hint_y: None
        height: '60dp'
        Button:
            text: '停止'
            font_name: '{FONT_NAME}'
            on_release: app.stop_play()
        Button:
            text: '播放/暫停'
            font_name: '{FONT_NAME}'
            on_release: app.toggle_play()
"""

# ==========================================
# 邏輯層
# ==========================================
class AutoScrollLabel(ScrollView):
    text = StringProperty('')
    color = ListProperty([1, 1, 1, 1])
    font_size = StringProperty('16sp')

class SongListItem(ButtonBehavior, BoxLayout):
    title = StringProperty("")
    thumb = StringProperty("")
    status_text = StringProperty("")
    index = NumericProperty(0)

class MusicPlayerApp(App):
    init_status = StringProperty("系統初始化中...")
    current_playing_title = StringProperty("準備就緒")
    yt_dlp_module = None # 用來存放延遲載入的模組

    def build(self):
        self.engine = MusicEngine()
        self.engine.bind(on_playback_ready=self.on_ready)
        self.engine.bind(on_track_finished=self.on_finish)
        
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.INTERNET, Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
        
        # 延遲載入 yt_dlp，防止開機閃退
        Clock.schedule_once(self.load_libraries, 1)
        return Builder.load_string(KV_CODE)

    def load_libraries(self, dt):
        try:
            import yt_dlp
            self.yt_dlp_module = yt_dlp
            self.init_status = "系統正常：搜尋引擎已載入"
        except Exception as e:
            self.init_status = f"錯誤：無法載入 yt_dlp\n{str(e)}"
            print(f"Import Error: {e}")

    def on_ready(self, instance, success):
        self.current_playing_title = "正在播放..." if success else "播放失敗"

    def on_finish(self, instance):
        self.current_playing_title = "播放結束"

    def stop_play(self):
        if self.engine.sound: self.engine.sound.stop()

    def toggle_play(self):
        self.engine.pause_resume()

    def search_music(self, keyword):
        if not self.yt_dlp_module:
            self.init_status = "錯誤：搜尋引擎尚未就緒，請稍候"
            return
            
        self.init_status = f"搜尋中：{keyword}..."
        threading.Thread(target=self._search_thread, args=(keyword,)).start()

    def _search_thread(self, keyword):
        results = []
        try:
            ydl_opts = {'quiet': True, 'extract_flat': True, 'noplaylist': True}
            with self.yt_dlp_module.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch5:{keyword}", download=False)
                for i, entry in enumerate(info['entries']):
                    results.append({
                        'title': entry.get('title', ''),
                        'thumb': '', # 簡化測試
                        'status_text': 'YouTube',
                        'index': i,
                        'url': entry.get('url', '')
                    })
        except Exception as e:
            self.init_status = f"搜尋錯誤：{str(e)}"
        
        Clock.schedule_once(lambda dt: self._update_list(results))

    def _update_list(self, data):
        self.root.ids.rv.data = data
        if not data: self.init_status = "搜尋無結果"
        else: self.init_status = "搜尋完成"

    def play_manager(self, index):
        # 簡化版播放邏輯，先測試能否搜尋
        data = self.root.ids.rv.data[index]
        self.current_playing_title = f"準備下載：{data['title']}"
        threading.Thread(target=self._download_thread, args=(data['url'],)).start()

    def _download_thread(self, url):
        try:
            save_path = get_storage_path()
            out_tmpl = os.path.join(save_path, 'temp.%(ext)s')
            # 刪除舊檔
            for f in os.listdir(save_path):
                if f.startswith('temp'): os.remove(os.path.join(save_path, f))

            ydl_opts = {'format': 'bestaudio/best', 'outtmpl': out_tmpl, 'quiet': True}
            with self.yt_dlp_module.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # 找檔案播放
            target = None
            for f in os.listdir(save_path):
                if f.startswith('temp'): target = os.path.join(save_path, f)
            
            if target:
                Clock.schedule_once(lambda dt: self.engine.load_track(target))
        except Exception as e:
            self.init_status = f"下載錯誤：{str(e)}"

if __name__ == '__main__':
    MusicPlayerApp().run()
