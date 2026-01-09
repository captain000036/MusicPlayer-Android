import os
# 1.7 版保命設定：防止圖片和輸入法崩潰
os.environ['KIVY_IMAGE'] = 'sdl2'
os.environ['SDL_IME_SHOW_UI'] = '1'

import threading
from kivy.config import Config
# 嘗試叫出系統鍵盤
Config.set('kivy', 'keyboard_mode', '')

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.properties import StringProperty, ListProperty, BooleanProperty, NumericProperty
from kivy.clock import Clock, mainthread
from kivy.utils import platform
from kivy.event import EventDispatcher
from kivy.loader import Loader

# 偽裝
Loader.headers = {'User-Agent': 'Mozilla/5.0'}

# 路徑
def get_path(folder_name):
    if platform == 'android':
        try:
            from jnius import autoclass
            return autoclass('org.kivy.android.PythonActivity').mActivity.getExternalFilesDir(None).getAbsolutePath()
        except: return "/sdcard/Download"
    else:
        return os.path.join(os.getcwd(), 'MusicPlayer')

# 1.7 版預設字型 (避免亂抓導致閃退)
FONT_NAME = 'Roboto'

# ==========================================
# 核心引擎
# ==========================================
class MusicEngine(EventDispatcher):
    __events__ = ('on_playback_ready', 'on_track_finished', 'on_error')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.player = None
        if platform == 'android':
            try:
                from jnius import autoclass
                self.MediaPlayer = autoclass('android.media.MediaPlayer')
                self.player = self.MediaPlayer()
            except: pass

    def load_track(self, filepath):
        if not self.player: return
        try:
            if self.player.isPlaying(): self.player.stop()
            self.player.reset()
            self.player.setDataSource(filepath)
            self.player.prepare()
            self.player.start()
        except Exception as e: self.dispatch('on_error', str(e))

    def pause_resume(self):
        if not self.player: return False
        try:
            if self.player.isPlaying():
                self.player.pause()
                return False
            else:
                self.player.start()
                return True
        except: return False

    def on_playback_ready(self, s): pass
    def on_track_finished(self): pass
    def on_error(self, e): pass

# ==========================================
# KV 介面 (這就是您要的 1.7 漂亮版)
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

<ThemedInput@TextInput>:
    font_name: '{FONT_NAME}'
    font_size: '18sp'
    background_normal: ''
    background_active: ''
    background_color: app.theme_input_bg
    foreground_color: app.theme_text_color
    padding_y: [self.height / 2.0 - (self.line_height / 2.0), 0]
    padding_x: '10dp'
    hint_text_color: [0.6, 0.6, 0.6, 1]
    multiline: False
    on_text_validate: app.search_music(self.text)

<DashboardCard@Button>:
    btn_color: [0.5, 0.5, 0.5, 1]
    font_name: '{FONT_NAME}'
    font_size: '15sp'
    bold: True
    color: [1, 1, 1, 1]
    background_normal: ''
    background_color: [0,0,0,0]
    text_size: self.size
    halign: 'center'
    valign: 'center'
    canvas.before:
        Color:
            rgba: root.btn_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10,]

<SpotifyCard@Button>:
    font_name: '{FONT_NAME}'
    font_size: '18sp'
    bold: True
    background_normal: ''
    background_color: 0, 0, 0, 0
    font_size: '18sp'
    bold: True
    color: [1, 1, 1, 1]
    text_size: self.size
    halign: 'center'
    valign: 'center'
    canvas.before:
        Color:
            rgba: root.img_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10,]

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

    # 圖片區
    Image:
        source: root.thumb
        color: [1, 1, 1, 1] if root.thumb else [1, 1, 1, 0]
        fit_mode: 'cover'
        size_hint_x: None
        width: '80dp'
        nocache: True

    BoxLayout:
        orientation: 'vertical'
        padding: 0
        spacing: 0
        Label:
            text: root.title
            font_name: '{FONT_NAME}'
            font_size: '16sp'
            color: app.theme_text_color
            size_hint_y: 0.6
            text_size: self.size
            halign: 'left'
            valign: 'bottom'
            shorten: True
        Label:
            text: root.status_text
            font_name: '{FONT_NAME}'
            font_size: '12sp'
            size_hint_y: 0.4
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
        font_size: '20sp'

BoxLayout:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: app.theme_bg_color
        Rectangle:
            pos: self.pos
            size: self.size

    # 1. 頂部搜尋列
    BoxLayout:
        size_hint_y: None
        height: '60dp' 
        padding: '10dp'
        spacing: '10dp'
        ThemedInput:
            id: search_input
            hint_text: 'Search...'
            size_hint_x: 0.65
        Button:
            text: 'GO'
            font_name: '{FONT_NAME}'
            size_hint_x: 0.2
            background_normal: ''
            background_color: [0.11, 0.72, 0.32, 1]
            on_release: app.search_music(search_input.text)
        Button:
            text: 'Theme'
            font_name: '{FONT_NAME}'
            size_hint_x: 0.15
            background_normal: ''
            background_color: [0.3, 0.3, 0.3, 1]
            on_release: app.toggle_theme()

    # 2. 快捷按鈕 (Spotify 風格)
    BoxLayout:
        size_hint_y: None
        height: '100dp' if not app.is_spotify else '0dp'
        opacity: 1 if not app.is_spotify else 0
        padding: '10dp'
        spacing: '10dp'
        DashboardCard:
            text: 'Favorites'
            btn_color: [0.4, 0.2, 0.9, 1]
        DashboardCard:
            text: 'Playlists'
            btn_color: [0.2, 0.6, 0.5, 1]
        DashboardCard:
            text: 'Recent'
            btn_color: [0.9, 0.6, 0.2, 1]

    # 3. 推薦卡片
    GridLayout:
        cols: 2
        size_hint_y: None
        height: '140dp' if app.is_spotify else '0dp'
        opacity: 1 if app.is_spotify else 0
        padding: '10dp'
        spacing: '8dp'
        SpotifyCard:
            text: 'Mandopop'
            img_color: [0.8, 0.2, 0.2, 1]
            on_release: app.search_music('Mandopop Hits 2024')
        SpotifyCard:
            text: 'Billboard'
            img_color: [0.2, 0.5, 0.2, 1]
            on_release: app.search_music('Billboard Hot 100')
        SpotifyCard:
            text: 'K-POP'
            img_color: [0.8, 0.5, 0.2, 1]
            on_release: app.search_music('KPOP Hits 2024')
        SpotifyCard:
            text: 'TikTok'
            img_color: [0.2, 0.2, 0.8, 1]
            on_release: app.search_music('TikTok Viral 2024')

    # 4. 標題
    Label:
        text: app.list_title
        font_name: '{FONT_NAME}'
        font_size: '16sp'
        bold: True
        size_hint_y: None
        height: '30dp'
        color: app.theme_text_color
        text_size: self.size
        halign: 'left'
        padding_x: '15dp'

    # 5. 列表
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

    # 6. 底部播放條
    BoxLayout:
        size_hint_y: None
        height: '80dp'
        padding: '10dp'
        orientation: 'vertical'
        canvas.before:
            Color:
                rgba: [0.15, 0.15, 0.15, 1]
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [15, 15, 0, 0]
        AutoScrollLabel:
            text: app.current_playing_title
            font_size: '16sp'
            size_hint_y: 0.4
            color: [1, 1, 1, 1]
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: 0.6
            spacing: '40dp'
            Button:
                text: 'Prev'
                on_release: app.play_previous()
            Button:
                text: 'Play/Pause'
                on_release: app.toggle_play()
            Button:
                text: 'Next'
                on_release: app.play_next()
"""

class AutoScrollLabel(ScrollView):
    text = StringProperty('')
    color = ListProperty([1, 1, 1, 1])
    font_size = StringProperty('16sp')
    def on_kv_post(self, base_widget):
        self.lbl = self.ids.lbl
        self.bind(text=self.update_text, color=self.update_color)
        self.lbl.bind(texture_size=self.update_label_width)
        Clock.schedule_interval(self.animate, 3)
    def update_text(self, instance, value):
        if hasattr(self, 'lbl'):
            self.lbl.text = value
            self.scroll_x = 0
            from kivy.animation import Animation
            Animation.cancel_all(self)
    def update_color(self, instance, value):
        if hasattr(self, 'lbl'): self.lbl.color = value
    def update_label_width(self, *args):
        if hasattr(self, 'lbl'): self.lbl.width = self.lbl.texture_size[0] + 50
    def animate(self, dt):
        if hasattr(self, 'lbl') and self.lbl.width > self.width:
            from kivy.animation import Animation
            anim = Animation(scroll_x=1, duration=8, t='linear') + \
                   Animation(scroll_x=1, duration=2) + \
                   Animation(scroll_x=0, duration=0.5)
            anim.start(self)
        else: self.scroll_x = 0

class SongListItem(ButtonBehavior, BoxLayout):
    title = StringProperty("")
    url = StringProperty("")
    thumb = StringProperty("")
    status_text = StringProperty("YouTube")
    index = NumericProperty(0)

class MusicPlayerApp(App):
    is_spotify = BooleanProperty(True)
    theme_bg_color = ListProperty([0.07, 0.07, 0.07, 1])
    theme_text_color = ListProperty([1, 1, 1, 1])
    theme_input_bg = ListProperty([0.2, 0.2, 0.2, 1])
    theme_card_bg = ListProperty([0.07, 0.07, 0.07, 1])
    theme_accent_color = ListProperty([0.11, 0.72, 0.32, 1])
    
    list_title = StringProperty("Search Results")
    current_playing_title = StringProperty("Ready")
    is_playing = BooleanProperty(False)
    current_song_index = -1
    
    def build(self):
        self.engine = MusicEngine()
        self.apply_spotify_theme()
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.INTERNET, Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
        return Builder.load_string(KV_CODE)

    def toggle_theme(self):
        self.is_spotify = not self.is_spotify
        if self.is_spotify: self.apply_spotify_theme()
        else: self.apply_xiaomi_theme()

    def apply_spotify_theme(self):
        self.theme_bg_color = [0.07, 0.07, 0.07, 1]
        self.theme_text_color = [1, 1, 1, 1]
        self.theme_input_bg = [0.2, 0.2, 0.2, 1]
        self.theme_card_bg = [0.07, 0.07, 0.07, 1]
        self.theme_accent_color = [0.11, 0.72, 0.32, 1]

    def apply_xiaomi_theme(self):
        self.theme_bg_color = [0.98, 0.98, 0.98, 1]
        self.theme_text_color = [0.1, 0.1, 0.1, 1]
        self.theme_input_bg = [0.92, 0.92, 0.92, 1]
        self.theme_card_bg = [1, 1, 1, 0]
        self.theme_accent_color = [0.5, 0.2, 0.8, 1]

    def search_music(self, keyword):
        if not keyword: return
        self.current_song_index = -1
        self.list_title = f"Search: {keyword}"
        self.root.ids.search_input.focus = False
        self.current_playing_title = "Searching..."
        threading.Thread(target=self._search_thread, args=(keyword,)).start()

    def _search_thread(self, keyword):
        try:
            import requests
            import yt_dlp
            requests.packages.urllib3.disable_warnings()
            
            cache_dir = get_path('Cache')
            if not os.path.exists(cache_dir): os.makedirs(cache_dir)
            
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
                            
                            # 1.7版邏輯：手動下載圖片
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
            Clock.schedule_once(lambda dt: setattr(self, 'current_playing_title', "Error"))

    @mainthread
    def _update_list(self, data):
        self.root.ids.rv.data = data
        self.current_playing_title = "Click to Play"

    def play_manager(self, index):
        if index < 0 or index >= len(self.root.ids.rv.data): return
        self.current_song_index = index
        data = self.root.ids.rv.data[index]
        self.current_playing_title = f"Downloading..."
        threading.Thread(target=self._download_thread, args=(data['url'], data['title'])).start()

    def _download_thread(self, url, title):
        try:
            import yt_dlp
            folder = get_path('Music')
            if not os.path.exists(folder): os.makedirs(folder)
            
            safe_title = "".join([c for c in title if c.isalnum() or c in ' -_']).rstrip()
            out_tmpl = os.path.join(folder, f'{safe_title}.%(ext)s')
            
            # 1.7版邏輯：強制 m4a 避免閃退
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/best', 
                'outtmpl': out_tmpl, 
                'quiet': True,
                'nocheckcertificate': True,
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
                Clock.schedule_once(lambda dt: self.engine.load_track(target_file))
                Clock.schedule_once(lambda dt: self._update_title(f"Playing: {safe_title}"))
            else:
                Clock.schedule_once(lambda dt: self._update_title("Failed"))
        except:
            Clock.schedule_once(lambda dt: self._update_title("Error"))

    @mainthread
    def _update_title(self, text):
        self.current_playing_title = text

    def play_previous(self): pass
    def play_next(self): pass
    def toggle_play(self):
        self.engine.pause_resume()

if __name__ == '__main__':
    MusicPlayerApp().run()
