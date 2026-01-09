import os
import sys
import threading
import contextlib
import urllib.request
import ssl
import time

# ==========================================
# 0. Android 救命補丁 (SSL)
# ==========================================
try:
    import certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()
    ssl._create_default_https_context = ssl._create_unverified_context
except ImportError:
    pass

# ==========================================
# 1. 環境設定
# ==========================================
from kivy.config import Config

# 強制使用系統原生鍵盤
Config.set('kivy', 'keyboard_mode', 'system')
Config.set('kivy', 'keyboard_layout', 'system')
Config.set('kivy', 'log_level', 'info')
Config.set('network', 'useragent', 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36')

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
from kivy.clock import Clock, mainthread
from kivy.utils import platform
from kivy.animation import Animation
from kivy.event import EventDispatcher
from kivy.core.text import LabelBase

# 字體註冊
try:
    LabelBase.register(name='Roboto',
                       fn_regular='NotoSansTC-Regular.otf',
                       fn_bold='NotoSansTC-Bold.otf')
    FONT_NAME = 'Roboto'
except Exception as e:
    FONT_NAME = 'Roboto'

# 檔案路徑：改用 App 私有路徑，保證不會有權限問題導致閃退
def get_storage_path():
    if platform == 'android':
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            context = PythonActivity.mActivity
            return context.getExternalFilesDir(None).getAbsolutePath()
        except:
            return "/sdcard/Download"
    else:
        root = os.path.join(os.getcwd(), 'Music')
        if not os.path.exists(root): os.makedirs(root, exist_ok=True)
        return root

class QuietLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): print(f"[YTDLP] {msg}")

# ==========================================
# 核心架構：MusicEngine (改回 Android 原生 MediaPlayer)
# ==========================================
class MusicEngine(EventDispatcher):
    __events__ = ('on_playback_ready', 'on_track_finished', 'on_error')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.player = None
        self.is_prepared = False
        
        if platform == 'android':
            try:
                from jnius import autoclass
                self.MediaPlayer = autoclass('android.media.MediaPlayer')
                self.player = self.MediaPlayer()
            except Exception as e:
                print(f"Native Player Init Fail: {e}")

    def load_track(self, filepath):
        if not self.player:
            # 電腦版測試 (空轉，避免報錯)
            self.dispatch('on_playback_ready', True)
            return

        try:
            self.player.reset()
            self.player.setDataSource(filepath)
            self.player.prepare() 
            self.player.start()
            self.is_prepared = True
            self.dispatch('on_playback_ready', True)
            
            # 監聽播放結束 (簡易實作)
            self.player.setOnCompletionListener(None) 
        except Exception as e:
            self.dispatch('on_error', str(e))

    def pause_resume(self):
        if not self.player: return False
        try:
            if self.player.isPlaying():
                self.player.pause()
                return False
            else:
                self.player.start()
                return True
        except:
            return False

    def stop(self):
        if self.player and self.player.isPlaying():
            self.player.stop()

    def on_playback_ready(self, success): pass
    def on_track_finished(self): pass
    def on_error(self, error): pass

# ==========================================
# KV 介面 (維持不變)
# ==========================================
KV_CODE = f"""
#:import hex kivy.utils.get_color_from_hex

<AutoScrollLabel>:
    do_scroll_x: False
    do_scroll_y: False
    bar_width: 0
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

<SongListItem>:
    orientation: 'horizontal'
    size_hint_y: None
    height: '80dp'
    padding: '10dp'
    spacing: '15dp'
    on_release: app.play_manager(self.index)
    canvas.before:
        Color:
            rgba: app.theme_card_bg
        Rectangle:
            pos: self.pos
            size: self.size
    AsyncImage:
        source: root.thumb
        color: [1, 1, 1, 1] if root.thumb else [1, 1, 1, 0]
        fit_mode: 'cover'
        size_hint_x: None
        width: '80dp'
    BoxLayout:
        orientation: 'vertical'
        Label:
            text: root.title
            font_name: '{FONT_NAME}'
            font_size: '16sp'
            color: app.theme_text_color
            text_size: self.size
            halign: 'left'
            valign: 'bottom'
            shorten: True
        Label:
            text: root.status_text
            font_name: '{FONT_NAME}'
            font_size: '12sp'
            color: app.theme_accent_color
            text_size: self.size
            halign: 'left'
            valign: 'top'
    Label:
        text: '▶'
        font_name: '{FONT_NAME}'
        size_hint_x: None
        width: '40dp'
        color: app.theme_accent_color

<ThemedInput@TextInput>:
    font_name: '{FONT_NAME}'
    font_size: '18sp'
    multiline: False
    padding_y: [self.height / 2.0 - (self.line_height / 2.0), 0]
    on_text_validate: app.search_music(self.text)

<SpotifyCard@Button>:
    font_name: '{FONT_NAME}'
    font_size: '18sp'
    bold: True
    background_normal: ''
    background_color: 0,0,0,0
    canvas.before:
        Color:
            rgba: root.btn_color if hasattr(root, 'btn_color') else [0.3, 0.3, 0.3, 1]
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10,]

BoxLayout:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: app.theme_bg_color
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        size_hint_y: None
        height: '60dp' 
        padding: '10dp'
        spacing: '10dp'
        ThemedInput:
            id: search_input
            hint_text: '輸入歌手...'
            size_hint_x: 0.7
        Button:
            text: '搜尋'
            font_name: '{FONT_NAME}'
            size_hint_x: 0.3
            background_normal: ''
            background_color: [0.11, 0.72, 0.32, 1]
            on_release: app.search_music(search_input.text)

    GridLayout:
        cols: 2
        size_hint_y: None
        height: '140dp' if app.is_spotify else '0dp'
        opacity: 1 if app.is_spotify else 0
        padding: '10dp'
        spacing: '8dp'
        SpotifyCard:
            text: '熱門華語'
            btn_color: [0.8, 0.2, 0.2, 1]
            on_release: app.search_music('2024 熱門華語歌曲')
        SpotifyCard:
            text: '西洋排行榜'
            btn_color: [0.2, 0.5, 0.2, 1]
            on_release: app.search_music('Billboard Hot 100 2024')
        SpotifyCard:
            text: 'K-POP'
            btn_color: [0.8, 0.5, 0.2, 1]
            on_release: app.search_music('KPOP 2024 Hits')
        SpotifyCard:
            text: '抖音熱歌'
            btn_color: [0.2, 0.2, 0.8, 1]
            on_release: app.search_music('TikTok 抖音熱歌 2024')

    RecycleView:
        id: rv
        viewclass: 'SongListItem'
        RecycleBoxLayout:
            default_size: None, dp(80)
            default_size_hint: 1, None
            size_hint_y: None
            height: self.minimum_height
            orientation: 'vertical'

    BoxLayout:
        size_hint_y: None
        height: '80dp'
        padding: '10dp'
        canvas.before:
            Color:
                rgba: [0.1, 0.1, 0.1, 1]
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [15, 15, 0, 0]
        AutoScrollLabel:
            text: app.current_playing_title
            color: [1, 1, 1, 1]
        Button:
            text: '播放/暫停'
            font_name: '{FONT_NAME}'
            size_hint_x: None
            width: '100dp'
            on_release: app.toggle_play()
"""

# ==========================================
# 邏輯層
# ==========================================
class AutoScrollLabel(ScrollView):
    text = StringProperty('')
    color = ListProperty([1, 1, 1, 1])
    font_size = StringProperty('16sp')
    def on_kv_post(self, base_widget):
        self.lbl = self.ids.lbl
        self.bind(text=self.update_text)
        self.lbl.bind(texture_size=self.update_label_width)
        Clock.schedule_interval(self.animate, 3)
    def update_text(self, instance, value):
        if hasattr(self, 'lbl'):
            self.lbl.text = value
            self.scroll_x = 0
            Animation.cancel_all(self)
            self.start_anim()
    def update_label_width(self, *args):
        if hasattr(self, 'lbl'): self.lbl.width = self.lbl.texture_size[0] + 50
    def start_anim(self, *args):
        Clock.unschedule(self.animate)
        Clock.schedule_interval(self.animate, 3)
    def animate(self, dt):
        if hasattr(self, 'lbl') and self.lbl.width > self.width:
            anim = Animation(scroll_x=1, duration=8) + Animation(scroll_x=0, duration=0.5)
            anim.start(self)
        else: self.scroll_x = 0

class SongListItem(ButtonBehavior, BoxLayout):
    title = StringProperty("")
    thumb = StringProperty("")
    status_text = StringProperty("")
    index = NumericProperty(0)

class MusicPlayerApp(App):
    is_spotify = BooleanProperty(True)
    theme_bg_color = ListProperty([0.07, 0.07, 0.07, 1])
    theme_text_color = ListProperty([1, 1, 1, 1])
    theme_card_bg = ListProperty([0.07, 0.07, 0.07, 1])
    theme_accent_color = ListProperty([0.11, 0.72, 0.32, 1])
    current_playing_title = StringProperty("尚未播放")
    
    def build(self):
        self.engine = MusicEngine()
        self.engine.bind(on_playback_ready=self.on_ready)
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.INTERNET, Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
        return Builder.load_string(KV_CODE)

    def on_ready(self, instance, success):
        pass # 播放準備完成

    def search_music(self, keyword):
        if not keyword: return
        self.root.ids.search_input.focus = False
        threading.Thread(target=self._search_thread, args=(keyword,)).start()

    def _search_thread(self, keyword):
        try:
            import yt_dlp # 延遲載入，防閃退
            ydl_opts = {'quiet': True, 'extract_flat': True, 'noplaylist': True, 'ignoreerrors': True}
            results = []
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch20:{keyword}", download=False)
                if info and 'entries' in info:
                    for i, entry in enumerate(info['entries']):
                        if entry:
                            thumb = entry.get('thumbnail', '')
                            results.append({'title': entry.get('title', ''), 'thumb': thumb, 'status_text': 'YouTube', 'index': i, 'url': entry.get('url', '')})
            Clock.schedule_once(lambda dt: self._update_list(results))
        except Exception as e:
            print(e)

    def _update_list(self, data):
        self.root.ids.rv.data = data

    def play_manager(self, index):
        data = self.root.ids.rv.data[index]
        self.current_playing_title = f"下載中: {data['title']}"
        threading.Thread(target=self._download_thread, args=(data['url'], data['title'], data['thumb'])).start()

    def _download_thread(self, url, title, thumb):
        try:
            import yt_dlp
            save_path = get_storage_path()
            safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c in ' -_']).rstrip()
            out_tmpl = os.path.join(save_path, f'{safe_title}.%(ext)s')
            
            # 強制 m4a (Android 原生支援)
            ydl_opts = {'format': 'bestaudio[ext=m4a]/best', 'outtmpl': out_tmpl, 'quiet': True, 'nocheckcertificate': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            target = None
            if os.path.exists(save_path):
                for f in os.listdir(save_path):
                    if safe_title in f: target = os.path.join(save_path, f); break
            
            if target:
                Clock.schedule_once(lambda dt: self.engine.load_track(target))
                Clock.schedule_once(lambda dt: self._update_title(f"播放: {safe_title}"))
        except Exception as e:
            Clock.schedule_once(lambda dt: self._update_title(f"錯誤: {e}"))

    def _update_title(self, text): self.current_playing_title = text
    def toggle_play(self): self.engine.pause_resume()

if __name__ == '__main__':
    MusicPlayerApp().run()
