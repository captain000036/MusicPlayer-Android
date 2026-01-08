import os
# 強制使用 SDL2 圖片引擎
os.environ['KIVY_IMAGE'] = 'sdl2'
# 嘗試讓輸入法介面浮現
os.environ['SDL_IME_SHOW_UI'] = '1'

import threading
import traceback
from kivy.config import Config

# 【嘗試修復輸入法】使用 'system' 模式
Config.set('kivy', 'keyboard_mode', 'system')

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.recycleview import RecycleView
from kivy.properties import StringProperty, NumericProperty, ListProperty
from kivy.clock import Clock, mainthread
from kivy.utils import platform
from kivy.event import EventDispatcher
from kivy.loader import Loader

# 偽裝標頭
Loader.headers = {'User-Agent': 'Mozilla/5.0'}

# 簡單路徑管理
def get_path(folder):
    if platform == 'android':
        try:
            from jnius import autoclass
            root = autoclass('org.kivy.android.PythonActivity').mActivity.getExternalFilesDir(None).getAbsolutePath()
        except: root = "/sdcard/Download"
    else:
        root = os.path.join(os.getcwd(), 'MusicPlayer')
    
    path = os.path.join(root, folder)
    if not os.path.exists(path): os.makedirs(path, exist_ok=True)
    return path

# ==========================================
# KV 介面 (極簡診斷版)
# ==========================================
KV_CODE = f"""
<SongItem@BoxLayout>:
    orientation: 'horizontal'
    size_hint_y: None
    height: '90dp'
    padding: '5dp'
    spacing: '10dp'
    canvas.before:
        Color:
            rgba: [0.15, 0.15, 0.15, 1]
        Rectangle:
            pos: self.pos
            size: self.size
    
    # 圖片區
    Image:
        source: root.thumb
        size_hint_x: None
        width: '90dp'
        fit_mode: 'cover'
        nocache: True

    # 文字區
    Label:
        text: root.title
        font_size: '16sp'
        text_size: self.size
        halign: 'left'
        valign: 'center'
        shorten: True
        color: [1, 1, 1, 1]

    # 播放鈕
    Button:
        text: 'PLAY'
        size_hint_x: None
        width: '60dp'
        background_color: [0, 0.8, 0, 1]
        on_release: app.play_music(root.index)

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

    # 1. 搜尋框
    BoxLayout:
        size_hint_y: None
        height: '50dp'
        TextInput:
            id: search_input
            hint_text: '請輸入關鍵字...'
            multiline: False
            size_hint_x: 0.7
        Button:
            text: '搜尋'
            size_hint_x: 0.3
            on_release: app.start_search(search_input.text)

    # 2. 狀態顯示 (這裡是重點，會顯示錯誤訊息)
    Label:
        id: status_lbl
        text: app.status_msg
        size_hint_y: None
        height: '60dp'
        color: [1, 0.2, 0.2, 1] if 'Error' in self.text else [0.2, 1, 0.2, 1]
        text_size: self.width, None
        halign: 'center'

    # 3. 列表
    RecycleView:
        id: rv
        viewclass: 'SongItem'
        RecycleBoxLayout:
            default_size: None, dp(90)
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
    status_msg = StringProperty("系統正常，請搜尋")
    
    def build(self):
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
        self.status_msg = f"正在搜尋: {keyword}..."
        self.root.ids.search_input.focus = False
        # 啟動搜尋線程
        threading.Thread(target=self._safe_search, args=(keyword,)).start()

    def _safe_search(self, keyword):
        # 【關鍵防護】這裡包住了所有的網路動作
        try:
            import requests
            import yt_dlp
            
            # 設定不依賴系統 SSL
            requests.packages.urllib3.disable_warnings()
            
            cache_dir = get_path('Cache')
            
            # 極簡化參數，減少錯誤機率
            ydl_opts = {
                'quiet': True, 
                'extract_flat': True, 
                'ignoreerrors': True,
                'nocheckcertificate': True
            }
            
            results = []
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch10:{keyword}", download=False)
                
                if 'entries' in info:
                    for i, e in enumerate(info['entries']):
                        vid = e.get('id', str(i))
                        thumb_url = e.get('thumbnail', '')
                        local_thumb = os.path.join(cache_dir, f"{vid}.jpg")
                        
                        # 手動下載圖片
                        if thumb_url and not os.path.exists(local_thumb):
                            try:
                                r = requests.get(thumb_url, timeout=3, verify=False)
                                with open(local_thumb, 'wb') as f: f.write(r.content)
                            except: pass
                        
                        final_thumb = local_thumb if os.path.exists(local_thumb) else ''
                        
                        results.append({
                            'title': e.get('title', 'Unknown'),
                            'url': e.get('url', ''),
                            'thumb': final_thumb,
                            'index': i
                        })
            
            Clock.schedule_once(lambda dt: self.update_list(results))
            
        except ImportError as e:
            # 這是最可能的錯誤：缺檔
            Clock.schedule_once(lambda dt: setattr(self, 'status_msg', f"缺檔錯誤: {e}"))
        except Exception as e:
            # 其他錯誤 (網路、權限等)
            err_msg = f"Error: {str(e)}"
            # 把詳細錯誤印出來
            traceback.print_exc()
            Clock.schedule_once(lambda dt: setattr(self, 'status_msg', err_msg))

    @mainthread
    def update_list(self, data):
        self.root.ids.rv.data = data
        self.status_msg = "搜尋完成 (點擊 PLAY 下載播放)"

    def play_music(self, index):
        data = self.root.ids.rv.data[index]
        self.status_msg = f"下載中... {data['title'][:10]}"
        threading.Thread(target=self._safe_download, args=(data['url'], data['title'])).start()

    def _safe_download(self, url, title):
        try:
            import yt_dlp
            music_dir = get_path('Music')
            safe_title = "".join([c for c in title if c.isalnum() or c in ' -_']).rstrip()
            out_path = os.path.join(music_dir, f'{safe_title}.%(ext)s')
            
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/best',
                'outtmpl': out_path,
                'quiet': True,
                'nocheckcertificate': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            target = None
            for f in os.listdir(music_dir):
                if safe_title in f:
                    target = os.path.join(music_dir, f)
                    break
            
            if target:
                Clock.schedule_once(lambda dt: self.do_play(target))
                Clock.schedule_once(lambda dt: setattr(self, 'status_msg', f"播放中: {safe_title}"))
            else:
                Clock.schedule_once(lambda dt: setattr(self, 'status_msg', "下載失敗: 找不到檔案"))
                
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self, 'status_msg', f"下載錯誤: {e}"))

    @mainthread
    def do_play(self, filepath):
        if self.player:
            try:
                if self.player.isPlaying(): self.player.stop()
                self.player.reset()
                self.player.setDataSource(filepath)
                self.player.prepare()
                self.player.start()
            except Exception as e:
                self.status_msg = f"播放器錯誤: {e}"

if __name__ == '__main__':
    MusicPlayerApp().run()
