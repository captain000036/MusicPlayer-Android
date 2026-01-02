import os
import threading
import contextlib
import urllib.request

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import (
    StringProperty, ListProperty,
    BooleanProperty, NumericProperty
)
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.utils import platform
from kivy.event import EventDispatcher
from kivy.config import Config
from kivy.core.text import LabelBase

# =====================================================
# 基本設定（Android 穩定）
# =====================================================
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

try:
    LabelBase.register(
        name='Roboto',
        fn_regular='NotoSansTC-Regular.otf',
        fn_bold='NotoSansTC-Bold.otf'
    )
    FONT_NAME = 'Roboto'
except Exception:
    FONT_NAME = 'Roboto'

# =====================================================
# 儲存路徑
# =====================================================
def get_storage_path():
    if platform == 'android':
        from android.storage import primary_external_storage_path
        path = os.path.join(
            primary_external_storage_path(),
            'Android', 'data',
            'org.test.musicplayer',
            'files', 'Music'
        )
    else:
        path = os.path.join(os.getcwd(), 'Music')

    os.makedirs(path, exist_ok=True)
    return path


# =====================================================
# 音樂引擎（已處理 Android 音訊釋放）
# =====================================================
class MusicEngine(EventDispatcher):
    __events__ = ('on_ready', 'on_finished', 'on_error')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sound = None
        self.lock = False

    def load(self, filepath):
        if self.lock:
            return
        self.lock = True

        def _do(dt):
            try:
                if self.sound:
                    try:
                        self.sound.unbind(on_stop=self._on_stop)
                        self.sound.stop()
                    except Exception:
                        pass
                    self.sound = None

                self.sound = SoundLoader.load(filepath)
                if not self.sound:
                    self.dispatch('on_error', '不支援的音訊格式')
                    return

                self.sound.bind(on_stop=self._on_stop)
                self.sound.play()
                self.dispatch('on_ready')
            except Exception as e:
                self.dispatch('on_error', str(e))
            finally:
                self.lock = False

        Clock.schedule_once(_do, 0.1)

    def toggle(self):
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
            self.dispatch('on_finished')

    def on_ready(self): pass
    def on_finished(self): pass
    def on_error(self, err): pass


# =====================================================
# UI Item
# =====================================================
class SongItem(ButtonBehavior, BoxLayout):
    title = StringProperty('')
    url = StringProperty('')
    thumb = StringProperty('')
    index = NumericProperty(0)


# =====================================================
# App
# =====================================================
class MusicPlayerApp(App):
    is_playing = BooleanProperty(False)
    current_title = StringProperty('尚未播放')
    list_title = StringProperty('搜尋結果')

    current_index = -1
    manual_stop = False

    def build(self):
        self.engine = MusicEngine()
        self.engine.bind(on_ready=self._on_ready)
        self.engine.bind(on_finished=self._on_finish)
        self.engine.bind(on_error=self._on_error)

        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.INTERNET,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE
            ])

        return Builder.load_string(KV_CODE)

    # -------------------------
    # Engine callbacks
    # -------------------------
    def _on_ready(self, *_):
        self.is_playing = True

    def _on_finish(self, *_):
        if not self.manual_stop:
            self.play_next()

    def _on_error(self, *_):
        self.current_title = '播放失敗'
        self.is_playing = False

    # -------------------------
    # 搜尋（延遲 import yt_dlp）
    # -------------------------
    def search(self, keyword):
        if not keyword:
            return
        self.list_title = f'搜尋：{keyword}'
        threading.Thread(
            target=self._search_thread,
            args=(keyword,),
            daemon=True
        ).start()

    def _search_thread(self, keyword):
        try:
            import yt_dlp
        except Exception:
            return

        results = []
        opts = {
            'quiet': True,
            'extract_flat': True,
            'noplaylist': True
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(
                f'ytsearch20:{keyword}',
                download=False
            )
            for i, e in enumerate(info.get('entries', [])):
                vid = e.get('id', '')
                results.append({
                    'title': e.get('title', ''),
                    'url': e.get('url', ''),
                    'thumb': f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg',
                    'index': i
                })

        Clock.schedule_once(
            lambda dt: self.root.ids.rv.data.__setitem__(slice(None), results)
        )

    # -------------------------
    # 播放管理
    # -------------------------
    def play(self, index):
        data = self.root.ids.rv.data
        if index < 0 or index >= len(data):
            return

        self.current_index = index
        song = data[index]
        self.current_title = song['title']

        folder = get_storage_path()
        safe = ''.join(c for c in song['title'] if c.isalnum() or c in ' -_')

        for ext in ('.m4a', '.mp3'):
            p = os.path.join(folder, safe + ext)
            if os.path.exists(p):
                self.engine.load(p)
                return

        self._download_and_play(song['url'], safe, song['thumb'])

    def play_next(self):
        if not self.root.ids.rv.data:
            return
        self.play((self.current_index + 1) % len(self.root.ids.rv.data))

    def toggle(self):
        self.manual_stop = not self.engine.toggle()
        self.is_playing = not self.manual_stop

    # -------------------------
    # 下載（yt_dlp 延遲載入）
    # -------------------------
    def _download_and_play(self, url, safe, thumb):
        self.current_title = f'下載中：{safe}'

        def task():
            try:
                import yt_dlp
            except Exception:
                return

            path = get_storage_path()
            out = os.path.join(path, safe + '.%(ext)s')

            opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'outtmpl': out,
                'quiet': True
            }

            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])

            for f in os.listdir(path):
                if f.startswith(safe) and f.endswith(('.m4a', '.mp3')):
                    Clock.schedule_once(
                        lambda dt: self.engine.load(os.path.join(path, f))
                    )
                    break

        threading.Thread(target=task, daemon=True).start()


# =====================================================
# KV（精簡版示意，你可替換成你原本那份完整 UI）
# =====================================================
KV_CODE = f"""
BoxLayout:
    orientation: 'vertical'
    TextInput:
        id: q
        hint_text: '搜尋'
        on_text_validate: app.search(self.text)
    Label:
        text: app.list_title
    RecycleView:
        id: rv
        viewclass: 'SongItem'
        RecycleBoxLayout:
            default_size: None, dp(60)
            default_size_hint: 1, None
            size_hint_y: None
            height: self.minimum_height
    Label:
        text: app.current_title
"""

if __name__ == '__main__':
    MusicPlayerApp().run()
