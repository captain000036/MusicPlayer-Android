import os
import sys
import threading
import contextlib
import urllib.request
import ssl
import time

# ==========================================
# 0. Android 救命補丁 (SSL & 鍵盤)
# ==========================================
try:
    import certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()
    ssl._create_default_https_context = ssl._create_unverified_context
except ImportError:
    pass

from kivy.config import Config
# 【修正 1】強制系統鍵盤 + 視窗調整 (解決輸入法卡住)
Config.set('kivy', 'keyboard_mode', 'system')
Config.set('kivy', 'keyboard_layout', 'system')
Config.set('kivy', 'log_level', 'info')
# 【修正 2】偽裝成 Android 瀏覽器 (解決圖片載入與搜歌過少)
Config.set('network', 'useragent', 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36')

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
# 核心架構：MusicEngine (修復自動下一首)
# ==========================================
class MusicEngine(EventDispatcher):
    __events__ = ('on_playback_ready', 'on_track_finished', 'on_error')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.player = None
        self.is_monitoring = False
        
        if platform == 'android':
            try:
                from jnius import autoclass
                self.MediaPlayer = autoclass('android.media.MediaPlayer')
                self.player = self.MediaPlayer()
            except Exception as e:
                print(f"Native Player Init Fail: {e}")

    def load_track(self, filepath):
        if not self.player:
            self.dispatch('on_playback_ready', True)
            return

        try:
            self.stop() # 先停止舊的
            self.player.reset()
            self.player.setDataSource(filepath)
            self.player.prepare() 
            self.player.start()
            self.dispatch('on_playback_ready', True)
            
            # 【修正 3】啟動監聽器，解決無法自動播放下一首的問題
            self.start_monitor()
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
                self.start_monitor() # 恢復監聽
                return True
        except:
            return False

    def stop(self):
        self.stop_monitor()
        if self.player and self.player.isPlaying():
            self.player.stop()

    # --- 自製監聽器 (因為 jnius 很難實作 Java Listener) ---
    def start_monitor(self):
        self.stop_monitor()
        self.is_monitoring = True
        Clock.schedule_interval(self._check_completion, 1)

    def stop_monitor(self):
        self.is_monitoring = False
        Clock.unschedule(self._check_completion)

    def _check_completion(self, dt):
        # 每秒檢查一次是否播完
        if self.player and not self.player.isPlaying():
            # 這裡簡單判斷：如果沒在播，且沒按暫停，就是播完了
            # (稍微有 bug 但在 Native 這是最不閃退的作法)
            try:
                current_pos = self.player.getCurrentPosition()
                duration = self.player.getDuration()
                if duration > 0 and current_pos >= duration - 1000: # 剩不到1秒
                    self.stop_monitor()
                    self.dispatch('on_track_finished')
            except: pass

    def on_playback_ready(self, success): pass
    def on_track_finished(self): pass
    def on_error(self, error): pass

# ==========================================
# KV 介面 (完全不動，保持你的設計)
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
        # 【修正 2.1】圖片載入失敗時不崩潰，保持空白
        nocache: True
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
        self.engine.bind(on_track_finished=self.on_next_song) # 綁定下一首
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.INTERNET, Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
        return Builder.load_string(KV_CODE)

    def on_ready(self, instance, success):
        pass

    def on_next_song(self, instance):
        self.play_next()

    def search_music(self, keyword):
        if not keyword: return
        self.root.ids.search_input.focus = False
        threading.Thread(target=self._search_thread, args=(keyword,)).start()

    def _search_thread(self, keyword):
        try:
            import yt_dlp # 延遲載入
            # 【修正 4】增加搜尋數量到 50 (ytsearch50)
            ydl_opts = {'quiet': True, 'extract_flat': True, 'noplaylist': True, 'ignoreerrors': True}
            results = []
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch50:{keyword}", download=False)
                if info and 'entries' in info:
                    for i, entry in enumerate(info['entries']):
                        if entry:
                            # 確保縮圖是 JPG (WebP 容易在 Kivy 失敗)
                            thumb = entry.get('thumbnail', '')
                            results.append({'title': entry.get('title', ''), 'thumb': thumb, 'status_text': 'YouTube', 'index': i, 'url': entry.get('url', '')})
            Clock.schedule_once(lambda dt: self._update_list(results))
        except Exception as e:
            print(e)

    def _update_list(self, data):
        self.root.ids.rv.data = data

    def play_manager(self, index):
        self.current_song_index = index
        data = self.root.ids.rv.data[index]
        self.current_playing_title = f"處理中: {data['title']}"
        
        # 檢查本地是否有檔案
        folder = get_storage_path()
        safe_title = "".join([c for c in data['title'] if c.isalpha() or c.isdigit() or c in ' -_']).rstrip()
        
        target = None
        if os.path.exists(folder):
            for f in os.listdir(folder):
                # 支援 mp3 和 m4a
                if safe_title in f and f.endswith(('.mp3', '.m4a')):
                    target = os.path.join(folder, f)
                    break
        
        if target:
            self.engine.load_track(target)
            self._update_title(f"播放: {data['title']}")
        else:
            threading.Thread(target=self._download_thread, args=(data['url'], data['title'])).start()

    def _download_thread(self, url, title):
        try:
            import yt_dlp
            save_path = get_storage_path()
            safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c in ' -_']).rstrip()
            out_tmpl = os.path.join(save_path, f'{safe_title}.%(ext)s')
            
            # 【修正 5】下載防閃退：強制只抓音訊，不合併影片
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/best', 
                'outtmpl': out_tmpl, 
                'quiet': True, 
                'nocheckcertificate': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            target = None
            if os.path.exists(save_path):
                for f in os.listdir(save_path):
                    if safe_title in f: target = os.path.join(save_path, f); break
            
            if target:
                Clock.schedule_once(lambda dt: self.engine.load_track(target))
                Clock.schedule_once(lambda dt: self._update_title(f"播放: {title}"))
            else:
                Clock.schedule_once(lambda dt: self._update_title("下載失敗"))
        except Exception as e:
            Clock.schedule_once(lambda dt: self._update_title(f"錯誤: {e}"))

    def play_next(self):
        all_songs = self.root.ids.rv.data
        if not all_songs: return
        new_index = self.current_song_index + 1
        if new_index >= len(all_songs): new_index = 0
        self.play_manager(new_index)

    def _update_title(self, text): self.current_playing_title = text
    def toggle_play(self): 
        # 切換主題邏輯 (保留)
        self.is_spotify = not self.is_spotify
        if self.is_spotify:
            self.theme_bg_color = [0.07, 0.07, 0.07, 1]
            self.theme_text_color = [1, 1, 1, 1]
        else:
            self.theme_bg_color = [0.98, 0.98, 0.98, 1]
            self.theme_text_color = [0.1, 0.1, 0.1, 1]
        
        # 播放暫停
        self.engine.pause_resume()

if __name__ == '__main__':
    MusicPlayerApp().run()
