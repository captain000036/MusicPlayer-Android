import os
import threading
import traceback
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import AsyncImage
from kivy.uix.recycleview import RecycleView
from kivy.properties import StringProperty, NumericProperty, ListProperty
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.text import LabelBase

# 1. 基礎設定
os.environ['SDL_IME_SHOW_UI'] = '1'

# 2. 字體防呆
try:
    LabelBase.register(name='MyFont',
                       fn_regular='NotoSansTC-Regular.otf',
                       fn_bold='NotoSansTC-Bold.otf')
    FONT_NAME = 'MyFont'
except:
    FONT_NAME = 'Roboto'

# 3. Android 原生播放器封裝 (超級穩定，不會崩潰)
class NativePlayer:
    def __init__(self):
        self.player = None
        if platform == 'android':
            try:
                from jnius import autoclass
                MediaPlayer = autoclass('android.media.MediaPlayer')
                self.player = MediaPlayer()
            except Exception as e:
                print(f"Native Player Init Error: {e}")

    def load(self, path):
        if not self.player: return
        try:
            self.player.reset()
            self.player.setDataSource(path)
            self.player.prepare() 
        except Exception as e:
            print(f"Load Error: {e}")

    def play(self):
        if self.player: self.player.start()

    def stop(self):
        if self.player and self.player.isPlaying():
            self.player.stop()

    def is_playing(self):
        if self.player: return self.player.isPlaying()
        return False

# ==========================================
# KV 介面
# ==========================================
KV_CODE = f"""
<SongListItem@ButtonBehavior+BoxLayout>:
    orientation: 'horizontal'
    size_hint_y: None
    height: '80dp'
    padding: '10dp'
    spacing: '15dp'
    on_release: app.play_music(self.index)
    canvas.before:
        Color:
            rgba: [0.15, 0.15, 0.15, 1]
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10,]
    AsyncImage:
        source: root.thumb
        size_hint_x: None
        width: '80dp'
        radius: [10,]
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
            text: root.status
            font_name: '{FONT_NAME}'
            font_size: '12sp'
            color: [0.6, 0.6, 0.6, 1]
            text_size: self.size
            halign: 'left'
            valign: 'top'

BoxLayout:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: [0.05, 0.05, 0.05, 1]
        Rectangle:
            pos: self.pos
            size: self.size

    # 標題列
    Label:
        id: status_lbl
        text: app.status_text
        size_hint_y: None
        height: '50dp'
        font_name: '{FONT_NAME}'
        color: [0, 1, 0.8, 1]

    # 搜尋區
    BoxLayout:
        size_hint_y: None
        height: '60dp'
        padding: '10dp'
        spacing: '10dp'
        TextInput:
            id: search_input
            hint_text: '輸入歌曲名稱...'
            font_name: '{FONT_NAME}'
            size_hint_x: 0.7
            multiline: False
        Button:
            text: '搜尋'
            font_name: '{FONT_NAME}'
            size_hint_x: 0.3
            background_color: [0, 0.5, 1, 1]
            on_release: app.start_search(search_input.text)

    # 列表區
    RecycleView:
        id: rv
        viewclass: 'SongListItem'
        RecycleBoxLayout:
            default_size: None, dp(80)
            default_size_hint: 1, None
            size_hint_y: None
            height: self.minimum_height
            orientation: 'vertical'
            spacing: dp(10)
            padding: dp(10)

    # 底部控制
    Button:
        text: '停止播放'
        font_name: '{FONT_NAME}'
        size_hint_y: None
        height: '60dp'
        background_color: [0.8, 0.2, 0.2, 1]
        on_release: app.stop_music()
"""

# ==========================================
# APP 邏輯
# ==========================================
class SongListItem(ButtonBehavior, BoxLayout):
    index = NumericProperty(0)
    title = StringProperty('')
    thumb = StringProperty('')
    status = StringProperty('')

class MusicPlayerApp(App):
    status_text = StringProperty('準備就緒')
    
    def build(self):
        self.native_player = NativePlayer()
        # 延遲載入 yt_dlp，防止開機卡頓
        Clock.schedule_once(self.init_yt_dlp, 1)
        
        # 再次確保權限
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.INTERNET, Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
            
        return Builder.load_string(KV_CODE)

    def init_yt_dlp(self, dt):
        try:
            import yt_dlp
            self.yt_dlp = yt_dlp
            self.status_text = "搜尋引擎已載入"
        except Exception as e:
            self.status_text = f"引擎載入失敗: {e}"

    def get_save_dir(self):
        # 使用私有目錄，絕對有權限
        if platform == 'android':
            try:
                from jnius import autoclass
                context = autoclass('org.kivy.android.PythonActivity').mActivity
                return context.getExternalFilesDir(None).getAbsolutePath()
            except:
                return "/sdcard/Music" # Fallback
        return "Music"

    def start_search(self, query):
        if not hasattr(self, 'yt_dlp'):
            self.status_text = "系統忙碌中，請稍候..."
            return
        self.status_text = f"正在搜尋: {query}..."
        threading.Thread(target=self._search_thread, args=(query,)).start()

    def _search_thread(self, query):
        try:
            ydl_opts = {'quiet': True, 'extract_flat': True, 'noplaylist': True}
            results = []
            with self.yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch5:{query}", download=False)
                for i, entry in enumerate(info['entries']):
                    results.append({
                        'title': entry.get('title'),
                        'thumb': '', # 暫時不抓圖以加速
                        'status': 'YouTube 線上',
                        'index': i,
                        'url': entry.get('url')
                    })
            Clock.schedule_once(lambda dt: self._update_ui(results))
        except Exception as e:
            Clock.schedule_once(lambda dt: self._show_error(str(e)))

    def _update_ui(self, data):
        self.root.ids.rv.data = data
        self.status_text = "搜尋完成，請點擊播放"

    def _show_error(self, err):
        self.status_text = f"錯誤: {err}"

    def play_music(self, index):
        item = self.root.ids.rv.data[index]
        self.status_text = f"準備播放: {item['title']}"
        threading.Thread(target=self._download_and_play, args=(item['url'],)).start()

    def _download_and_play(self, url):
        try:
            save_dir = self.get_save_dir()
            if not os.path.exists(save_dir): os.makedirs(save_dir)
            
            # 下載
            out_path = os.path.join(save_dir, 'current.mp3') # 固定檔名避免垃圾堆積
            if os.path.exists(out_path): os.remove(out_path)
            
            ydl_opts = {'format': 'bestaudio/best', 'outtmpl': out_path, 'quiet': True}
            with self.yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # 播放
            Clock.schedule_once(lambda dt: self._start_native_play(out_path))
            
        except Exception as e:
            Clock.schedule_once(lambda dt: self._show_error(str(e)))

    def _start_native_play(self, path):
        self.native_player.load(path)
        self.native_player.play()
        self.status_text = "正在播放中..."

    def stop_music(self):
        self.native_player.stop()
        self.status_text = "已停止"

if __name__ == '__main__':
    try:
        MusicPlayerApp().run()
    except Exception as e:
        # 萬一連這樣都掛，至少印出來 (雖然只有 ADB 看得到)
        print(f"CRITICAL ERROR: {e}")
