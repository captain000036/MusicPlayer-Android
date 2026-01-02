# ==============================
# main.py  (Android 穩定版)
# UI / 行為與原版一致
# ==============================

import os
import threading
import contextlib
import urllib.request
import yt_dlp
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import AsyncImage
from kivy.properties import (
    StringProperty, ListProperty,
    BooleanProperty, NumericProperty
)
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.utils import platform
from kivy.animation import Animation
from kivy.event import EventDispatcher
from kivy.config import Config
from kivy.core.text import LabelBase

# ==========================================
# Android / Kivy 環境設定
# ==========================================
os.environ['SDL_IME_SHOW_UI'] = '1'
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

Config.set('kivy', 'log_enable', '1')
Config.set('kivy', 'log_level', 'info')

# ==========================================
# 字體（原樣）
# ==========================================
try:
    LabelBase.register(
        name='Roboto',
        fn_regular='NotoSansTC-Regular.otf',
        fn_bold='NotoSansTC-Bold.otf'
    )
    FONT_NAME = 'Roboto'
except Exception:
    FONT_NAME = 'Roboto'

# ==========================================
# Android 儲存路徑（安全）
# ==========================================
def get_storage_path():
    if platform == 'android':
        from android.storage import app_storage_path
        path = os.path.join(app_storage_path(), 'Music')
    else:
        path = os.path.join(os.getcwd(), 'Music')

    os.makedirs(path, exist_ok=True)
    return path

# ==========================================
# yt-dlp logger
# ==========================================
class QuietLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): print('[YTDLP]', msg)

# ==========================================
# MusicEngine（ANDROID FIX 重點）
# ==========================================
class MusicEngine(EventDispatcher):
    __events__ = ('on_playback_ready', 'on_track_finished', 'on_error')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sound = None
        self.lock = False

    def load_track(self, filepath):
        if self.lock:
            return
        self.lock = True

        # ===== ANDROID FIX 1 =====
        # 完整釋放上一首 native decoder
        if self.sound:
            try:
                self.sound.unbind(on_stop=self._on_stop)
                self.sound.stop()
                self.sound = None
                Clock.tick()          # 強制釋放
            except Exception:
                pass

        # 延遲初始化，避免 JNI 競態
        Clock.schedule_once(lambda dt: self._real_load(filepath), 0.35)

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
        if not self.sound:
            return False
        if self.sound.state == 'play':
            self.sound.stop()
            return False
        else:
            self.sound.play()
            return True

    def _on_stop(self, *_):
        if not self.lock:
            self.dispatch('on_track_finished')

    def on_playback_ready(self, success): pass
    def on_track_finished(self): pass
    def on_error(self, error): pass

# ==========================================
# KV（完全沿用你原本的，不再貼第二次）
# ==========================================
# ⚠️ 這裡請「原封不動」貼你原本的 KV_CODE
# （我不改 UI，所以這段請直接用你原本的）

KV_CODE = """<=== 你原本完整 KV_CODE 原樣貼在這裡 ===>"""

# ==========================================
# UI 類別（原樣）
# ==========================================
class AutoScrollLabel(ScrollView):
    text = StringProperty('')
    color = ListProperty([1,1,1,1])
    font_size = StringProperty('16sp')
    # 原樣略…

class SpotifyCard(Button):
    img_color = ListProperty([0.3,0.3,0.3,1])

class SongListItem(ButtonBehavior, BoxLayout):
    title = StringProperty("")
    url = StringProperty("")
    thumb = StringProperty("")
    status_text = StringProperty("")
    index = NumericProperty(0)

# ==========================================
# App 主體（ANDROID FIX 在下載）
# ==========================================
class MusicPlayerApp(App):
    is_playing = BooleanProperty(False)
    current_playing_title = StringProperty("尚未播放")

    def build(self):
        self.engine = MusicEngine()
        self.engine.bind(on_track_finished=lambda *_: self.play_next())

        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.INTERNET,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE
            ])

        return Builder.load_string(KV_CODE)

    # ======================================
    # ANDROID FIX 2：背景下載（part → rename）
    # ======================================
    def cache_and_play(self, url, title, thumb):
        threading.Thread(
            target=self._download_thread,
            args=(url, title, thumb),
            daemon=True
        ).start()

    def _download_thread(self, url, title, thumb):
        save_path = get_storage_path()
        safe = ''.join(c for c in title if c.isalnum() or c in ' -_').rstrip()

        outtmpl = os.path.join(
            save_path, f'{safe}.part.%(ext)s'
        )

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': outtmpl,
            'quiet': True,
            'noprogress': True,
            'nocheckcertificate': True,
            'postprocessors': [],
            'logger': QuietLogger()
        }

        with contextlib.redirect_stdout(None):
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        final_file = None
        for f in os.listdir(save_path):
            if f.startswith(safe + '.part'):
                src = os.path.join(save_path, f)
                final_file = src.replace('.part', '')
                os.rename(src, final_file)
                break

        if final_file:
            Clock.schedule_once(
                lambda dt: self.engine.load_track(final_file),
                0.5   # ANDROID FIX 3：延遲播放
            )

    # 其餘播放控制、列表邏輯
    # 原樣保留（略）

if __name__ == '__main__':
    MusicPlayerApp().run()
