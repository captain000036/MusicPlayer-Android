import os
# 強制設定：使用最穩定的 SDL2 圖片引擎
os.environ['KIVY_IMAGE'] = 'sdl2'
os.environ['SDL_IME_SHOW_UI'] = '1'

import threading
from kivy.config import Config
# 【功能修復1】輸入法交給系統
Config.set('kivy', 'keyboard_mode', '')

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.clock import Clock, mainthread
from kivy.utils import platform
from kivy.event import EventDispatcher
from kivy.loader import Loader

# 偽裝標頭
Loader.headers = {'User-Agent': 'Mozilla/5.0'}

# 路徑管理
def get_storage_path():
    if platform == 'android':
        try:
            from jnius import autoclass
            return autoclass('org.kivy.android.PythonActivity').mActivity.getExternalFilesDir(None).getAbsolutePath()
        except: return "/sdcard/Download"
    else:
        return os.path.join(os.getcwd(), 'MusicPlayer')

# ==========================================
# 極簡 KV 介面 (去除所有可能導致崩潰的美化代碼)
# ==========================================
KV_CODE = f"""
<SongItem@BoxLayout>:
    orientation: 'horizontal'
    size_hint_y: None
    height: '100dp'
    padding: '5dp'
    # 簡單的灰色背景
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
        allow_stretch: True
        keep_ratio: True
        nocache: True

    # 文字區
    Label:
        text: root.title
        # 使用系統預設字型，不指定 font_name
        text_size: self.size
        halign: 'left'
        valign: 'center'
        shorten: True
        color: [1, 1, 1, 1]

    # 播放按鈕
    Button:
        text: 'Play'
        size_hint_x: None
        width: '60dp'
        on_release: app.play_music(root.index)

BoxLayout:
    orientation: 'vertical'
    padding: '10dp'
    spacing: '10dp'
    
    # 搜尋區
    BoxLayout:
        size_hint_y: None
        height: '50dp'
        TextInput:
            id: search_input
            hint_text: 'Search...'
            multiline: False
        Button:
            text: 'GO'
            size_hint_x: None
            width: '60dp'
            on_release: app.start_search(search_input.text)

    # 狀態顯示
    Label:
        text: app.status_msg
        size_hint_y: None
        height: '30dp'
        color: [0, 1, 0, 1]

    # 列表區
    RecycleView:
        id: rv
        viewclass: 'SongItem'
        RecycleBoxLayout:
            default_size: None, dp(100)
            default_size_hint: 1, None
            size_hint_y: None
            height: self.minimum_height
            orientation: 'vertical'
            spacing: '5dp'
"""

class MusicPlayerApp(App):
    from kivy.properties import StringProperty
    status_msg = StringProperty("Ready")
    
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
        self.status_msg = "Searching..."
        self.root.ids.search_input.focus = False
        threading.Thread(target=self._search_thread, args=(keyword,)).start()

    def _search_thread(self, keyword):
        try:
            import requests
            import yt_dlp
            
            root = get_storage_path()
            cache_dir = os.path.join(root, 'Cache')
            if not os.path.exists(cache_dir): os.makedirs(cache_dir)
            
            ydl_opts = {'quiet': True, 'extract_flat': True, 'ignoreerrors': True, 'nocheckcertificate': True}
            
            data_list = []
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch10:{keyword}", download=False)
                if 'entries' in info:
                    for i, e in enumerate(info['entries']):
                        vid = e.get('id', str(i))
                        thumb_url = e.get('thumbnail', '')
                        local_thumb = os.path.join(cache_dir, f"{vid}.jpg")
                        
                        # 【功能修復2】手動下載圖片
                        if thumb_url and not os.path.exists(local_thumb):
                            try:
                                r = requests.get(thumb_url, timeout=5, verify=False)
                                with open(local_thumb, 'wb') as f: f.write(r.content)
                            except: pass
                        
                        thumb = local_thumb if os.path.exists(local_thumb) else ''
                        data_list.append({
                            'title': e.get('title', 'Unknown'),
                            'url': e.get('url', ''),
                            'thumb': thumb,
                            'index': i
                        })
            
            Clock.schedule_once(lambda dt: self.update_ui(data_list))
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self, 'status_msg', f"Error: {e}"))

    @mainthread
    def update_ui(self, data):
        self.root.ids.rv.data = data
        self.status_msg = "Search Done"

    def play_music(self, index):
        data = self.root.ids.rv.data[index]
        self.status_msg = f"Downloading: {data['title'][:10]}..."
        threading.Thread(target=self._download_thread, args=(data['url'], data['title'])).start()

    def _download_thread(self, url, title):
        try:
            import yt_dlp
            root = get_storage_path()
            music_dir = os.path.join(root, 'Music')
            if not os.path.exists(music_dir): os.makedirs(music_dir)
            
            safe_title = "".join([c for c in title if c.isalnum() or c in ' -_']).rstrip()
            out_file = os.path.join(music_dir, f'{safe_title}.%(ext)s')
            
            # 【功能修復3】強制 m4a，無後製
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
            
            target = None
            for f in os.listdir(music_dir):
                if safe_title in f: target = os.path.join(music_dir, f); break
            
            if target:
                Clock.schedule_once(lambda dt: self.play_audio(target))
                Clock.schedule_once(lambda dt: setattr(self, 'status_msg', "Playing..."))
            else:
                Clock.schedule_once(lambda dt: setattr(self, 'status_msg', "Download Failed"))
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self, 'status_msg', f"Err: {e}"))

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
