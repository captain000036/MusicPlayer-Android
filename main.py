import os
# 強制指定 Kivy 使用 sdl2 (因為我們沒裝 Pillow)
os.environ['KIVY_IMAGE'] = 'sdl2'
os.environ['SDL_IME_SHOW_UI'] = '1'

import threading
from kivy.config import Config
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
from kivy.core.text import LabelBase
from kivy.loader import Loader

# 偽裝標頭
Loader.headers = {'User-Agent': 'Mozilla/5.0'}

# 字體載入 (失敗不崩潰)
try:
    LabelBase.register(name='MyFont', fn_regular='NotoSansTC-Regular.otf', fn_bold='NotoSansTC-Regular.otf')
    FONT_NAME = 'MyFont'
except: 
    FONT_NAME = 'Roboto'

# 路徑函數 (改成呼叫時才執行，防止啟動崩潰)
def get_storage_path():
    if platform == 'android':
        try:
            from jnius import autoclass
            return autoclass('org.kivy.android.PythonActivity').mActivity.getExternalFilesDir(None).getAbsolutePath()
        except: return "/sdcard/Download"
    else:
        return os.path.join(os.getcwd(), 'MusicPlayer')

# ==========================================
# KV 介面 (保持您的設計)
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
            rgba: [0.1, 0.1, 0.1, 1]
        Rectangle:
            pos: self.pos
            size: self.size
    
    # 圖片顯示
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
        Label:
            text: root.status_text
            font_name: '{FONT_NAME}'
            font_size: '12sp'
            color: [0.5, 0.5, 0.5, 1]
            text_size: self.size
            halign: 'left'
            valign: 'top'
    Label:
        text: '▶'
        font_name: '{FONT_NAME}'
        size_hint_x: None
        width: '40dp'
        color: [0.1, 0.8, 0.3, 1]
        font_size: '20sp'

BoxLayout:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: [0.05, 0.05, 0.05, 1]
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        size_hint_y: None
        height: '60dp' 
        padding: '10dp'
        spacing: '10dp'
        TextInput:
            id: search_input
            hint_text: '輸入歌手...'
            font_name: '{FONT_NAME}'
            multiline: False
            size_hint_x: 0.7
        Button:
            text: '搜尋'
            font_name: '{FONT_NAME}'
            size_hint_x: 0.3
            background_color: [0.1, 0.8, 0.3, 1]
            on_release: app.search_music(search_input.text)

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

    BoxLayout:
        size_hint_y: None
        height: '80dp'
        padding: '10dp'
        orientation: 'vertical'
        canvas.before:
            Color:
                rgba: [0.2, 0.2, 0.2, 1]
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [15, 15, 0, 0]
        AutoScrollLabel:
            text: app.current_playing_title
            font_size: '16sp'
            color: [1, 1, 1, 1]
        BoxLayout:
            Button:
                text: '播放/暫停'
                font_name: '{FONT_NAME}'
                on_release: app.toggle_play()
"""

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
        if hasattr(self, 'lbl'): self.lbl.text = value
    def update_label_width(self, *args):
        if hasattr(self, 'lbl'): self.lbl.width = self.lbl.texture_size[0] + 50
    def animate(self, dt):
        if hasattr(self, 'lbl') and self.lbl.width > self.width:
            from kivy.animation import Animation
            anim = Animation(scroll_x=1, duration=8, t='linear') + Animation(scroll_x=0, duration=0.5)
            anim.start(self)

class SongListItem(ButtonBehavior, BoxLayout):
    title = StringProperty("")
    url = StringProperty("")
    thumb = StringProperty("")
    status_text = StringProperty("")
    index = NumericProperty(0)

class MusicPlayerApp(App):
    current_playing_title = StringProperty("準備就緒")
    
    def build(self):
        # 延遲初始化播放器，防止啟動崩潰
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

    def search_music(self, keyword):
        if not keyword: return
        self.current_playing_title = "搜尋中..."
        # 啟動線程
        threading.Thread(target=self._search_thread, args=(keyword,)).start()

    def _search_thread(self, keyword):
        try:
            import requests
            import yt_dlp
            
            root_path = get_storage_path()
            cache_dir = os.path.join(root_path, 'Cache')
            if not os.path.exists(cache_dir): os.makedirs(cache_dir, exist_ok=True)
            
            ydl_opts = {'quiet': True, 'extract_flat': True, 'ignoreerrors': True, 'nocheckcertificate': True}
            
            results_data = []
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch10:{keyword}", download=False)
                if info and 'entries' in info:
                    for i, entry in enumerate(info['entries']):
                        if entry:
                            title = entry.get('title', 'Unknown')
                            thumb_url = entry.get('thumbnail', '')
                            video_id = entry.get('id', str(i))
                            
                            # 手動下載圖片 (因為沒有 Pillow)
                            local_thumb = os.path.join(cache_dir, f"{video_id}.jpg")
                            if thumb_url and not os.path.exists(local_thumb):
                                try:
                                    resp = requests.get(thumb_url, timeout=3, verify=False)
                                    with open(local_thumb, 'wb') as f: f.write(resp.content)
                                except: pass
                            
                            # 檢查圖片是否存在
                            final_thumb = local_thumb if os.path.exists(local_thumb) else ''

                            results_data.append({
                                'title': title, 
                                'url': entry.get('url', ''), 
                                'thumb': final_thumb, 
                                'status_text': 'YouTube', 
                                'index': i
                            })
            
            Clock.schedule_once(lambda dt: self._update_list(results_data))
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self, 'current_playing_title', f"搜尋錯誤: {e}"))

    @mainthread
    def _update_list(self, data):
        self.root.ids.rv.data = data
        self.current_playing_title = "請選擇歌曲"

    def play_manager(self, index):
        data = self.root.ids.rv.data[index]
        self.current_playing_title = f"下載中: {data['title']}"
        threading.Thread(target=self._download_thread, args=(data['url'], data['title'])).start()

    def _download_thread(self, url, title):
        try:
            import yt_dlp
            root_path = get_storage_path()
            music_dir = os.path.join(root_path, 'Music')
            if not os.path.exists(music_dir): os.makedirs(music_dir, exist_ok=True)
            
            safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c in ' -_']).rstrip()
            out_tmpl = os.path.join(music_dir, f'{safe_title}.%(ext)s')
            
            # 強制 m4a (最穩定的格式，不需轉檔)
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/best', 
                'outtmpl': out_tmpl, 
                'quiet': True,
                'nocheckcertificate': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            target_file = None
            for f in os.listdir(music_dir):
                if safe_title in f:
                    target_file = os.path.join(music_dir, f)
                    break
            
            if target_file:
                Clock.schedule_once(lambda dt: self.play_file(target_file))
                Clock.schedule_once(lambda dt: setattr(self, 'current_playing_title', f"播放: {safe_title}"))
            else:
                Clock.schedule_once(lambda dt: setattr(self, 'current_playing_title', "下載失敗"))
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self, 'current_playing_title', f"錯誤: {e}"))

    @mainthread
    def play_file(self, filepath):
        if not self.player: return
        try:
            if self.player.isPlaying(): self.player.stop()
            self.player.reset()
            self.player.setDataSource(filepath)
            self.player.prepare()
            self.player.start()
        except: pass

    def toggle_play(self):
        if self.player:
            try:
                if self.player.isPlaying(): self.player.pause()
                else: self.player.start()
            except: pass

if __name__ == '__main__':
    MusicPlayerApp().run()
