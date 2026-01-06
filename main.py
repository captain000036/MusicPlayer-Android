import os
import threading
import ssl
import certifi
import time
import requests # 新增：用來穩定下載圖片
from kivy.config import Config

# ==========================================
# 1. 系統補丁
# ==========================================
try:
    os.environ['SSL_CERT_FILE'] = certifi.where()
    ssl._create_default_https_context = ssl._create_unverified_context
except: pass

# 偽裝成 Android 手機瀏覽器
USER_AGENT = 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36'
Config.set('network', 'useragent', USER_AGENT)

# 【輸入法修正嘗試】設為空值，讓 Android 系統自己接管鍵盤
Config.set('kivy', 'keyboard_mode', '') 
os.environ['SDL_IME_SHOW_UI'] = '1'

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.button import Button
from kivy.uix.image import AsyncImage, Image
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.properties import StringProperty, ListProperty, BooleanProperty, NumericProperty
from kivy.clock import Clock, mainthread
from kivy.utils import platform
from kivy.event import EventDispatcher
from kivy.core.text import LabelBase
from kivy.loader import Loader

Loader.headers = {'User-Agent': USER_AGENT}

# 2. 字體載入
try:
    LabelBase.register(name='MyFont', fn_regular='NotoSansTC-Regular.otf', fn_bold='NotoSansTC-Regular.otf')
    FONT_NAME = 'MyFont'
except: FONT_NAME = 'Roboto'

# 3. 路徑管理 (分開存音樂和圖片快取)
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
# 4. 音樂引擎 (原生播放器)
# ==========================================
class MusicEngine(EventDispatcher):
    __events__ = ('on_playback_ready', 'on_track_finished', 'on_error')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.player = None
        self.user_paused = False
        if platform == 'android':
            try:
                from jnius import autoclass
                self.MediaPlayer = autoclass('android.media.MediaPlayer')
                self.player = self.MediaPlayer()
            except: pass

    def load_track(self, filepath):
        if not self.player: return self.dispatch('on_playback_ready', True)
        try:
            self.stop_monitor()
            if self.player.isPlaying(): self.player.stop()
            self.player.reset()
            self.player.setDataSource(filepath)
            self.player.prepare()
            self.player.start()
            self.user_paused = False
            self.dispatch('on_playback_ready', True)
            self.start_monitor()
        except Exception as e: self.dispatch('on_error', str(e))

    def pause_resume(self):
        if not self.player: return False
        try:
            if self.player.isPlaying():
                self.player.pause()
                self.user_paused = True
                return False
            else:
                self.player.start()
                self.user_paused = False
                self.start_monitor()
                return True
        except: return False

    def stop(self):
        self.stop_monitor()
        if self.player and self.player.isPlaying(): self.player.stop()

    def start_monitor(self):
        Clock.unschedule(self._check)
        Clock.schedule_interval(self._check, 1)
    def stop_monitor(self):
        Clock.unschedule(self._check)
    
    @mainthread
    def _check(self, dt):
        if self.player and not self.player.isPlaying() and not self.user_paused:
            if self.player.getCurrentPosition() >= self.player.getDuration() - 1000:
                self.stop_monitor()
                self.dispatch('on_track_finished')

    def on_playback_ready(self, s): pass
    def on_track_finished(self): pass
    def on_error(self, e): pass

# ==========================================
# 5. KV 介面 (完全還原您的設計)
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

<PrevButton@ButtonBehavior+Widget>:
    size_hint: None, None
    size: '40dp', '40dp'
    canvas:
        Color:
            rgba: [1, 1, 1, 1] if self.state == 'normal' else [0.5, 0.5, 0.5, 1]
        Line:
            points: [self.x, self.y + 10, self.x, self.top - 10]
            width: 2
        Triangle:
            points: [self.x, self.center_y, self.right, self.top - 10, self.right, self.y + 10]

<NextButton@ButtonBehavior+Widget>:
    size_hint: None, None
    size: '40dp', '40dp'
    canvas:
        Color:
            rgba: [1, 1, 1, 1] if self.state == 'normal' else [0.5, 0.5, 0.5, 1]
        Line:
            points: [self.right, self.y + 10, self.right, self.top - 10]
            width: 2
        Triangle:
            points: [self.right, self.center_y, self.x, self.top - 10, self.x, self.y + 10]

<PlayButton@ButtonBehavior+Widget>:
    size_hint: None, None
    size: '50dp', '50dp'
    canvas:
        Color:
            rgba: [1, 1, 1, 1] if self.state == 'normal' else [0.5, 0.5, 0.5, 1]
        Triangle:
            points: [self.x + 10, self.y + 5, self.x + 10, self.top - 5, self.right - 5, self.center_y]

<PauseButton@ButtonBehavior+Widget>:
    size_hint: None, None
    size: '50dp', '50dp'
    canvas:
        Color:
            rgba: [1, 1, 1, 1] if self.state == 'normal' else [0.5, 0.5, 0.5, 1]
        Rectangle:
            pos: self.x + 10, self.y + 5
            size: 10, self.height - 10
        Rectangle:
            pos: self.right - 20, self.y + 5
            size: 10, self.height - 10

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
    on_release: app.show_local_files(self.text)
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

    RelativeLayout:
        size_hint_x: None
        width: '80dp'
        canvas.before:
            Color:
                rgba: [0.2, 0.2, 0.2, 1]
            RoundedRectangle:
                pos: 0, 0
                size: self.size
                radius: [8,]
        Label:
            text: 'Music'
            font_name: '{FONT_NAME}'
            font_size: '12sp'
            bold: True
            color: [1, 1, 1, 0.3]
            pos_hint: {{'center_x': 0.5, 'center_y': 0.5}}
        
        # 使用 Image 讀取本地快取，不再用 AsyncImage
        Image:
            source: root.thumb
            color: [1, 1, 1, 1] if root.thumb else [1, 1, 1, 0]
            fit_mode: 'cover'
            size_hint_x: None
            width: '80dp'
            pos_hint: {{'center_x': 0.5, 'center_y': 0.5}}
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
            shorten_from: 'right'
        Label:
            text: root.status_text
            font_name: '{FONT_NAME}'
            font_size: '12sp'
            size_hint_y: 0.4
            color: app.theme_accent_color if '緩衝' in root.status_text else [0.5, 0.5, 0.5, 1]
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

    BoxLayout:
        size_hint_y: None
        height: '60dp' 
        padding: '10dp'
        spacing: '10dp'
        canvas.before:
            Color:
                rgba: app.theme_bg_color
            Rectangle:
                pos: self.pos
                size: self.size
        ThemedInput:
            id: search_input
            hint_text: '輸入歌手或歌名...'
            size_hint_x: 0.65
            canvas.after:
                Color:
                    rgba: [1, 1, 1, 0.1] if app.is_spotify else [0, 0, 0, 0.1]
                Line:
                    width: 1
                    rounded_rectangle: self.x, self.y, self.width, self.height, 6
        Button:
            text: '搜尋'
            font_name: '{FONT_NAME}'
            size_hint_x: 0.2
            background_normal: ''
            background_color: [0.11, 0.72, 0.32, 1]
            on_release: app.search_music(search_input.text)
        Button:
            text: '切換'
            font_name: '{FONT_NAME}'
            size_hint_x: 0.15
            background_normal: ''
            background_color: [0.3, 0.3, 0.3, 1]
            on_release: app.toggle_theme()

    BoxLayout:
        size_hint_y: None
        height: '100dp' if not app.is_spotify else '0dp'
        opacity: 1 if not app.is_spotify else 0
        padding: '10dp'
        spacing: '10dp'
        DashboardCard:
            text: '收藏的歌曲'
            btn_color: [0.4, 0.2, 0.9, 1]
        DashboardCard:
            text: '我的播放清單'
            btn_color: [0.2, 0.6, 0.5, 1]
        DashboardCard:
            text: '最近播放'
            btn_color: [0.9, 0.6, 0.2, 1]

    GridLayout:
        cols: 2
        size_hint_y: None
        height: '140dp' if app.is_spotify else '0dp'
        opacity: 1 if app.is_spotify else 0
        padding: '10dp'
        spacing: '8dp'
        SpotifyCard:
            text: '熱門華語'
            img_color: [0.8, 0.2, 0.2, 1]
            on_release: app.search_music('2024 熱門華語歌曲')
        SpotifyCard:
            text: '西洋排行榜'
            img_color: [0.2, 0.5, 0.2, 1]
            on_release: app.search_music('Billboard Hot 100 2024')
        SpotifyCard:
            text: 'K-POP 精選'
            img_color: [0.8, 0.5, 0.2, 1]
            on_release: app.search_music('KPOP 2024 Hits')
        SpotifyCard:
            text: '抖音熱歌'
            img_color: [0.2, 0.2, 0.8, 1]
            on_release: app.search_music('TikTok 抖音熱歌 2024')

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
        height: '100dp'
        padding: '10dp'
        orientation: 'vertical'
        canvas.before:
            Color:
                rgba: [0.4, 0.1, 0.1, 1] if app.is_spotify else [0.9, 0.9, 0.9, 1]
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [15, 15, 0, 0]
        AutoScrollLabel:
            text: app.current_playing_title
            font_size: '16sp'
            size_hint_y: 0.4
            color: [1, 1, 1, 1] if app.is_spotify else [0, 0, 0, 1]
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: 0.6
            spacing: '40dp'
            padding: [0, 5, 0, 5]
            Widget: 
            PrevButton:
                on_release: app.play_previous()
            RelativeLayout:
                size_hint: None, None
                size: '50dp', '50dp'
                PlayButton:
                    opacity: 1 if not app.is_playing else 0
                    disabled: True if app.is_playing else False
                    on_release: app.toggle_play()
                    pos_hint: {{'center_x': 0.5, 'center_y': 0.5}}
                PauseButton:
                    opacity: 1 if app.is_playing else 0
                    disabled: True if not app.is_playing else False
                    on_release: app.toggle_play()
                    pos_hint: {{'center_x': 0.5, 'center_y': 0.5}}
            NextButton:
                on_release: app.play_next()
            Widget: 
"""

# ==========================================
# 6. App 主程式 (Logic)
# ==========================================
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
    status_text = StringProperty("YouTube 音樂")
    index = NumericProperty(0)

class MusicPlayerApp(App):
    is_spotify = BooleanProperty(True)
    theme_bg_color = ListProperty([0.07, 0.07, 0.07, 1])
    theme_text_color = ListProperty([1, 1, 1, 1])
    theme_input_bg = ListProperty([0.2, 0.2, 0.2, 1])
    theme_card_bg = ListProperty([0.07, 0.07, 0.07, 1])
    theme_accent_color = ListProperty([0.11, 0.72, 0.32, 1])
    
    list_title = StringProperty("搜尋結果")
    current_playing_title = StringProperty("尚未播放")
    is_playing = BooleanProperty(False)
    current_song_index = -1
    
    def build(self):
        self.engine = MusicEngine()
        self.engine.bind(on_playback_ready=self.on_engine_ready)
        self.engine.bind(on_track_finished=self.on_track_finished)
        self.engine.bind(on_error=self.on_engine_error)
        self.apply_spotify_theme()
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.INTERNET, Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
        return Builder.load_string(KV_CODE)

    @mainthread
    def on_engine_ready(self, instance, success):
        if success: self.is_playing = True
        else: self.is_playing = False

    @mainthread
    def on_track_finished(self, instance):
        self.play_next()

    @mainthread
    def on_engine_error(self, instance, error):
        self.current_playing_title = "播放錯誤"
        print(f"Engine Error: {error}")

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

    def show_local_files(self, category_name):
        self.current_song_index = -1
        self.list_title = f"{category_name} (本地檔案)"
        folder = get_path('Music')
        cache_dir = get_path('Cache')
        local_songs = []
        if os.path.exists(folder):
            for i, f in enumerate(os.listdir(folder)):
                if f.endswith(('.m4a', '.mp3')):
                    title = os.path.splitext(f)[0]
                    # 嘗試找同名的快取圖片
                    thumb_path = os.path.join(cache_dir, f"{title}.jpg")
                    thumb = thumb_path if os.path.exists(thumb_path) else ''
                    
                    local_songs.append({
                        'title': title, 'url': '', 'thumb': thumb, 
                        'status_text': '[本機] 已下載', 'index': len(local_songs)
                    })
        self.root.ids.rv.data = local_songs

    def search_music(self, keyword):
        if not keyword: return
        self.current_song_index = -1
        self.list_title = f"搜尋：{keyword}"
        self.root.ids.search_input.focus = False
        self.current_playing_title = "搜尋中..."
        threading.Thread(target=self._search_thread, args=(keyword,)).start()

    def _search_thread(self, keyword):
        try:
            import yt_dlp
            
            cache_dir = get_path('Cache')
            
            # 【關鍵】只獲取資料，不下載影片
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
                            
                            # 【圖片修復】主動下載圖片到本地 Cache
                            local_thumb = os.path.join(cache_dir, f"{video_id}.jpg")
                            if thumb_url:
                                try:
                                    headers = {'User-Agent': USER_AGENT}
                                    # 忽略 SSL 驗證下載圖片
                                    resp = requests.get(thumb_url, headers=headers, timeout=3, verify=False)
                                    with open(local_thumb, 'wb') as f:
                                        f.write(resp.content)
                                except: local_thumb = '' # 下載失敗就留空
                            
                            # 確保給介面的是本地路徑
                            final_thumb = local_thumb if os.path.exists(local_thumb) else ''

                            results_data.append({
                                'title': title, 
                                'url': entry.get('url', ''), 
                                'thumb': final_thumb, 
                                'status_text': 'YouTube 音樂', 
                                'index': i
                            })
            
            Clock.schedule_once(lambda dt: self._update_list(results_data))
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self, 'current_playing_title', "搜尋完成"))

    @mainthread
    def _update_list(self, data):
        self.root.ids.rv.data = data
        self.current_playing_title = "請點擊播放"

    def play_manager(self, index):
        if index < 0 or index >= len(self.root.ids.rv.data): return
        
        self.current_song_index = index
        data = self.root.ids.rv.data[index]
        self.current_playing_title = f"準備播放: {data['title']}"
        
        folder = get_path('Music')
        # 簡易檔名過濾
        safe_title = "".join([c for c in data['title'] if c.isalpha() or c.isdigit() or c in ' -_']).rstrip()
        target_file = None
        
        # 1. 先找本地有沒有
        for f in os.listdir(folder):
            if safe_title in f and f.endswith(('.mp3', '.m4a', '.mp4')):
                target_file = os.path.join(folder, f)
                break
        
        if target_file:
            self.engine.load_track(target_file)
        elif data['url']:
            self.cache_and_play(data['url'], data['title'], data['thumb'])

    def cache_and_play(self, url, title, thumb_path):
        self.current_playing_title = f"下載中..."
        threading.Thread(target=self._download_thread, args=(url, title, thumb_path)).start()

    def _download_thread(self, url, title, thumb_path):
        try:
            import yt_dlp
            folder = get_path('Music')
            safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c in ' -_']).rstrip()
            out_tmpl = os.path.join(folder, f'{safe_title}.%(ext)s')
            
            # 【防閃退下載參數】
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/best', 
                'outtmpl': out_tmpl, 
                'quiet': True,
                'nocheckcertificate': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # 找檔案
            target_file = None
            for f in os.listdir(folder):
                if safe_title in f:
                    target_file = os.path.join(folder, f)
                    break
            
            # 順便把縮圖也存一份到 Music 資料夾，方便以後離線顯示
            if thumb_path and os.path.exists(thumb_path):
                import shutil
                try:
                    shutil.copy(thumb_path, os.path.join(folder, f"{safe_title}.jpg"))
                except: pass

            if target_file:
                Clock.schedule_once(lambda dt: self.engine.load_track(target_file))
                Clock.schedule_once(lambda dt: self._update_title(f"播放: {safe_title}"))
            else:
                Clock.schedule_once(lambda dt: self._update_title("下載失敗"))
        except Exception as e:
            Clock.schedule_once(lambda dt: self._update_title("下載錯誤"))

    @mainthread
    def _update_title(self, text):
        self.current_playing_title = text

    def play_previous(self):
        new_index = self.current_song_index - 1
        self.play_manager(new_index)

    def play_next(self):
        new_index = self.current_song_index + 1
        self.play_manager(new_index)

    def toggle_play(self):
        is_playing = self.engine.pause_resume()
        self.is_playing = is_playing

if __name__ == '__main__':
    MusicPlayerApp().run()
