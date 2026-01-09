import os
# 強制設定
os.environ['KIVY_IMAGE'] = 'sdl2'
os.environ['SDL_IME_SHOW_UI'] = '1'

from kivy.config import Config
Config.set('kivy', 'keyboard_mode', '')

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.recycleview import RecycleView
from kivy.clock import Clock, mainthread
from kivy.utils import platform
from kivy.loader import Loader
import threading

# 偽裝
Loader.headers = {'User-Agent': 'Mozilla/5.0'}

# 【關鍵修正】使用 App 私有目錄 (Private Storage)
# 這裡絕對有讀寫權限，不會閃退
def get_safe_path():
    if platform == 'android':
        from jnius import autoclass
        context = autoclass('org.kivy.android.PythonActivity').mActivity
        return context.getFilesDir().getAbsolutePath()
    else:
        return os.getcwd()

# 介面 (極簡文字版，確保不因為圖片 crash)
KV_CODE = f"""
<SongItem@BoxLayout>:
    orientation: 'horizontal'
    size_hint_y: None
    height: '80dp'
    padding: '10dp'
    spacing: '10dp'
    canvas.before:
        Color:
            rgba: [0.2, 0.2, 0.2, 1]
        Rectangle:
            pos: self.pos
            size: self.size
    
    Label:
        text: root.title
        font_name: 'Roboto'
        font_size: '16sp'
        text_size: self.size
        halign: 'left'
        valign: 'center'
        shorten: True
        color: [1, 1, 1, 1]

    Button:
        text: 'PLAY'
        size_hint_x: None
        width: '80dp'
        background_color: [0, 0.7, 0, 1]
        on_release: app.play_music(root.index)

BoxLayout:
    orientation: 'vertical'
    padding: '10dp'
    spacing: '10dp'
    canvas.before:
        Color:
            rgba: [0.1, 0.1, 0.1, 1]
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        size_hint_y: None
        height: '50dp'
        TextInput:
            id: search_input
            hint_text: 'Search...'
            multiline: False
        Button:
            text: 'GO'
            size_hint_x: 0.3
            on_release: app.start_search(search_input.text)

    Label:
        text: app.status_msg
        size_hint_y: None
        height: '40dp'
        color: [1, 1, 0, 1]

    RecycleView:
        id: rv
        viewclass: 'SongItem'
        RecycleBoxLayout:
            default_size: None, dp(80)
            default_size_hint: 1, None
            size_hint_y: None
            height: self.minimum_height
            orientation: 'vertical'
            spacing: '2dp'
"""

class MusicPlayerApp(App):
    from kivy.properties import StringProperty
    status_msg = StringProperty("Ready")
    
    def build(self):
        self.player = None
        return Builder.load_string(KV_CODE)

    def start_search(self, keyword):
        if not keyword: return
        self.status_msg = "Searching..."
        threading.Thread(target=self._search_thread, args=(keyword,)).start()

    def _search_thread(self, keyword):
        try:
            import yt_dlp
            # 關閉快取，防止 sqlite 錯誤
            ydl_opts = {
                'quiet': True, 
                'extract_flat': True, 
                'ignoreerrors': True, 
                'nocheckcertificate': True,
                'cache_dir': False  # 【關鍵】禁用快取
            }
            
            data_list = []
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch10:{keyword}", download=False)
                if 'entries' in info:
                    for i, e in enumerate(info['entries']):
                        data_list.append({
                            'title': e.get('title', 'Unknown'),
                            'url': e.get('url', ''),
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
        self.status_msg = f"DL: {data['title'][:10]}..."
        threading.Thread(target=self._download_thread, args=(data['url'], data['title'])).start()

    def _download_thread(self, url, title):
        try:
            import yt_dlp
            # 使用 App 私有目錄
            safe_folder = get_safe_path()
            safe_title = "".join([c for c in title if c.isalnum() or c in ' -_']).rstrip()
            out_file = os.path.join(safe_folder, f'{safe_title}.%(ext)s')
            
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/best',
                'outtmpl': out_file,
                'quiet': True,
                'nocheckcertificate': True,
                'postprocessors': [],
                'keepvideo': True,
                'cache_dir': False # 禁用快取
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            target = None
            for f in os.listdir(safe_folder):
                if safe_title in f: target = os.path.join(safe_folder, f); break
            
            if target:
                Clock.schedule_once(lambda dt: self.play_audio(target))
                Clock.schedule_once(lambda dt: setattr(self, 'status_msg', "Playing..."))
            else:
                Clock.schedule_once(lambda dt: setattr(self, 'status_msg', "DL Failed"))
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self, 'status_msg', f"Err: {e}"))

    @mainthread
    def play_audio(self, filepath):
        if platform == 'android':
            try:
                from jnius import autoclass
                MediaPlayer = autoclass('android.media.MediaPlayer')
                if self.player: self.player.stop()
                self.player = MediaPlayer()
                self.player.setDataSource(filepath)
                self.player.prepare()
                self.player.start()
            except Exception as e:
                self.status_msg = f"Player Err: {e}"

if __name__ == '__main__':
    MusicPlayerApp().run()
