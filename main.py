import os
# 強制設定，防止圖形介面崩潰
os.environ['KIVY_IMAGE'] = 'sdl2'
os.environ['SDL_IME_SHOW_UI'] = '1'

import threading
from kivy.config import Config
# 輸入法修正
Config.set('kivy', 'keyboard_mode', '')

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.properties import StringProperty, ListProperty, NumericProperty
from kivy.clock import Clock, mainthread
from kivy.utils import platform
from kivy.event import EventDispatcher
from kivy.loader import Loader

# 偽裝標頭
Loader.headers = {'User-Agent': 'Mozilla/5.0'}

# 【關鍵修正】完全放棄自訂字型，使用系統預設，防止因缺檔而閃退
FONT_NAME = 'Roboto'

# 路徑管理
def get_path(folder_name):
    if platform == 'android':
        try:
            from jnius import autoclass
            root = autoclass('org.kivy.android.PythonActivity').mActivity.getExternalFilesDir(None).getAbsolutePath()
        except: root = "/sdcard/Download"
    else:
        root = os.path.join(os.getcwd(), 'MusicPlayer')
    
    target = os.path.join(root, folder_name)
    if not os.path.exists(target): os.makedirs(target, exist_ok=True)
    return target

# ==========================================
# KV 介面 (簡化版雙介面)
# ==========================================
KV_CODE = f"""
<SongListItem>:
    orientation: 'horizontal'
    size_hint_y: None
    height: '80dp'
    padding: '5dp'
    spacing: '10dp'
    on_release: app.play_manager(self.index)
    canvas.before:
        Color:
            rgba: [0.15, 0.15, 0.15, 1]
        Rectangle:
            pos: self.pos
            size: self.size
    
    Image:
        source: root.thumb
        color: [1, 1, 1, 1] if root.thumb else [1, 1, 1, 0]
        size_hint_x: None
        width: '80dp'
        fit_mode: 'cover'
        nocache: True

    BoxLayout:
        orientation: 'vertical'
        Label:
            text: root.title
            font_name: '{FONT_NAME}'
            font_size: '16sp'
            text_size: self.size
            halign: 'left'
            valign: 'center'
            shorten: True
            color: [1, 1, 1, 1]
        Label:
            text: root.status_text
            font_name: '{FONT_NAME}'
            font_size: '12sp'
            color: [0.6, 0.6, 0.6, 1]
            text_size: self.size
            halign: 'left'
            valign: 'top'
    Label:
        text: '▶'
        font_name: '{FONT_NAME}'
        size_hint_x: None
        width: '40dp'
        color: [0.1, 0.8, 0.3, 1]
        font_size: '24sp'

BoxLayout:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: [0.05, 0.05, 0.05, 1]
        Rectangle:
            pos: self.pos
            size: self.size

    # 上方搜尋區
    BoxLayout:
        size_hint_y: None
        height: '60dp' 
        padding: '8dp'
        spacing: '8dp'
        canvas.before:
            Color:
                rgba: [0.1, 0.1, 0.1, 1]
            Rectangle:
                pos: self.pos
                size: self.size
        TextInput:
            id: search_input
            hint_text: '搜尋歌曲...'
            font_name: '{FONT_NAME}'
            multiline: False
            size_hint_x: 0.7
            background_normal: ''
            background_color: [0.2, 0.2, 0.2, 1]
            foreground_color: [1, 1, 1, 1]
            padding_y: [self.height / 2.0 - (self.line_height / 2.0), 0]
        Button:
            text: 'Go'
            font_name: '{FONT_NAME}'
            size_hint_x: 0.3
            background_normal: ''
            background_color: [0.1, 0.7, 0.3, 1]
            on_release: app.search_music(search_input.text)

    # 中間列表區
    RecycleView:
        id: rv
        viewclass: 'SongListItem'
        scroll_type: ['bars', 'content']
        bar_width: 10
        RecycleBoxLayout:
            default_size: None, dp(80)
            default_size_hint: 1, None
            size_hint_y: None
            height: self.minimum_height
            orientation: 'vertical'
            spacing: '2dp'

    # 下方播放控制區
    BoxLayout:
        size_hint_y: None
        height: '80dp'
        padding: '10dp'
        orientation: 'vertical'
        canvas.before:
            Color:
                rgba: [0.2, 0.2, 0.2, 1]
            Rectangle:
                pos: self.pos
                size: self.size
        Label:
            text: app.current_playing_title
            font_name: '{FONT_NAME}'
            font_size: '14sp'
            size_hint_y: 0.4
            color: [1, 1, 1, 1]
            shorten: True
        BoxLayout:
            orientation: 'horizontal'
            spacing: '20dp'
            size_hint_y: 0.6
            Button:
                text: '上一首'
                font_name: '{FONT_NAME}'
                background_color: [0,0,0,0]
                on_release: app.play_previous()
            Button:
                text: '播放/暫停'
                font_name: '{FONT_NAME}'
                background_color: [0.1, 0.7, 0.3, 1]
                background_normal: ''
                on_release: app.toggle_play()
            Button:
                text: '下一首'
                font_name: '{FONT_NAME}'
                background_color: [0,0,0,0]
                on_release: app.play_next()
"""

class SongListItem(ButtonBehavior, BoxLayout):
    title = StringProperty("")
    url = StringProperty("")
    thumb = StringProperty("")
    status_text = StringProperty("")
    index = NumericProperty(0)

class MusicPlayerApp(App):
    current_playing_title = StringProperty("歡迎使用")
    
    def build(self):
        self.player = None
        # 延遲載入播放器，避免啟動卡死
        Clock.schedule_once(self.init_player, 1)
        return Builder.load_string(KV_CODE)

    def init_player(self, dt):
        if platform == 'android':
            try:
                from jnius import autoclass
                self.MediaPlayer = autoclass('android.media.MediaPlayer')
                self.player = self.MediaPlayer()
            except: pass

    def search_music(self, keyword):
        if not keyword: return
        self.current_playing_title = "搜尋中，請稍候..."
        self.root.ids.search_input.focus = False
        threading.Thread(target=self._search_thread, args=(keyword,)).start()

    def _search_thread(self, keyword):
        try:
            # 延遲載入 heavy modules
            import requests
            import yt_dlp
            
            cache_dir = get_path('Cache')
            ydl_opts = {'quiet': True, 'extract_flat': True, 'ignoreerrors': True, 'nocheckcertificate': True}
            
            results_data = []
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch20:{keyword}", download=False)
                if info and 'entries' in info:
                    for i, entry in enumerate(info['entries']):
                        if entry:
                            title = entry.get('title', 'Unknown')
                            thumb_url = entry.get('thumbnail', '')
                            video_id = entry.get('id', str(i))
                            
                            # 手動下載圖片 (無 Pillow 方案)
                            local_thumb = os.path.join(cache_dir, f"{video_id}.jpg")
                            if thumb_url and not os.path.exists(local_thumb):
                                try:
                                    resp = requests.get(thumb_url, timeout=3, verify=False)
                                    with open(local_thumb, 'wb') as f: f.write(resp.content)
                                except: pass
                            
                            final_thumb = local_thumb if os.path.exists(local_thumb) else ''
                            results_data.append({
                                'title': title, 'url': entry.get('url', ''), 
                                'thumb': final_thumb, 'status_text': 'YouTube', 'index': i
                            })
            Clock.schedule_once(lambda dt: self._update_list(results_data))
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self, 'current_playing_title', f"錯誤: {e}"))

    @mainthread
    def _update_list(self, data):
        self.root.ids.rv.data = data
        self.current_playing_title = "搜尋完成，請點選播放"

    def play_manager(self, index):
        data = self.root.ids.rv.data[index]
        self.current_playing_title = f"下載中: {data['title']}"
        threading.Thread(target=self._download_thread, args=(data['url'], data['title'])).start()

    def _download_thread(self, url, title):
        try:
            import yt_dlp
            folder = get_path('Music')
            safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c in ' -_']).rstrip()
            out_tmpl = os.path.join(folder, f'{safe_title}.%(ext)s')
            
            # 強制 m4a + 禁止後製 (防閃退關鍵)
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/best', 
                'outtmpl': out_tmpl, 
                'quiet': True,
                'nocheckcertificate': True,
                'postprocessors': [],
                'keepvideo': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            target_file = None
            for f in os.listdir(folder):
                if safe_title in f:
                    target_file = os.path.join(folder, f)
                    break
            
            if target_file:
                Clock.schedule_once(lambda dt: self.engine_play(target_file))
                Clock.schedule_once(lambda dt: setattr(self, 'current_playing_title', f"播放: {safe_title}"))
            else:
                Clock.schedule_once(lambda dt: setattr(self, 'current_playing_title', "下載失敗，請重試"))
        except:
            Clock.schedule_once(lambda dt: setattr(self, 'current_playing_title', "下載錯誤"))

    @mainthread
    def engine_play(self, filepath):
        if not self.player: return
        try:
            if self.player.isPlaying(): self.player.stop()
            self.player.reset()
            self.player.setDataSource(filepath)
            self.player.prepare()
            self.player.start()
        except: pass

    def play_previous(self): pass
    def play_next(self): pass
    def toggle_play(self):
        if self.player:
            try:
                if self.player.isPlaying(): self.player.pause()
                else: self.player.start()
            except: pass

if __name__ == '__main__':
    MusicPlayerApp().run()
