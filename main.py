import os
import sys
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
from kivy.uix.button import Button  # 確保匯入 Button
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import AsyncImage
from kivy.properties import StringProperty, ListProperty, BooleanProperty, NumericProperty
from kivy.clock import Clock, mainthread
from kivy.core.audio import SoundLoader
from kivy.utils import platform
from kivy.animation import Animation
from kivy.event import EventDispatcher
from kivy.config import Config
from kivy.core.text import LabelBase

# ==========================================
# 1. 環境與 Log 設定
# ==========================================
os.environ['SDL_IME_SHOW_UI'] = '1'
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

Config.set('kivy', 'log_enable', '1')
Config.set('kivy', 'log_maxfiles', '5')
Config.set('kivy', 'log_level', 'info')

Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '640')
Config.set('graphics', 'resizable', '1')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

# 字體註冊 (維持你已經成功的設定)
try:
    LabelBase.register(name='Roboto',
                       fn_regular='NotoSansTC-Regular.otf',
                       fn_bold='NotoSansTC-Bold.otf')
    FONT_NAME = 'Roboto'
except Exception as e:
    print(f"字體載入警告: {e}")
    FONT_NAME = 'Roboto'

def get_storage_path():
    if platform == 'android':
        from android.storage import primary_external_storage_path
        root_path = os.path.join(primary_external_storage_path(), 'Android', 'data', 'org.test.myapp', 'files', 'Music')
    else:
        root_path = os.path.join(os.getcwd(), 'Music')
    if not os.path.exists(root_path):
        try: os.makedirs(root_path, exist_ok=True)
        except: pass
    return root_path

class QuietLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): print(f"[YTDLP_ERROR] {msg}")

# ==========================================
# 核心架構：MusicEngine
# ==========================================
class MusicEngine(EventDispatcher):
    __events__ = ('on_playback_ready', 'on_track_finished', 'on_error')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sound = None
        self.lock = False

    def load_track(self, filepath):
        if self.lock: return
        self.lock = True
        
        if self.sound:
            try:
                self.sound.unbind(on_stop=self._on_stop_callback)
                if self.sound.state == 'play':
                    self.sound.stop()
                self.sound = None
            except Exception: pass

        Clock.schedule_once(lambda dt: self._real_load(filepath), 0.2)

    def _real_load(self, filepath):
        try:
            self.sound = SoundLoader.load(filepath)
            if self.sound:
                self.sound.bind(on_stop=self._on_stop_callback)
                self.sound.play()
                self.dispatch('on_playback_ready', True)
            else:
                self.dispatch('on_playback_ready', False)
        except Exception as e:
            self.dispatch('on_error', str(e))
        finally:
            self.lock = False

    def pause_resume(self):
        if not self.sound: return False
        if self.sound.state == 'play':
            self.sound.unbind(on_stop=self._on_stop_callback)
            self.sound.stop()
            return False
        else:
            self.sound.bind(on_stop=self._on_stop_callback)
            self.sound.play()
            return True

    def _on_stop_callback(self, instance):
        if not self.lock:
            self.dispatch('on_track_finished')

    def on_playback_ready(self, success): pass
    def on_track_finished(self): pass
    def on_error(self, error): pass

# ==========================================
# KV 介面設計
# ==========================================
KV_CODE = f"""
#:import hex kivy.utils.get_color_from_hex

<AutoScrollLabel>:
    do_scroll_x: False
    do_scroll_y: False
    bar_width: 0
    effect_cls: 'ScrollEffect'
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
    canvas.after:
        Color:
            rgba: [1, 1, 1, 0.2]
        Ellipse:
            pos: self.x + self.width - 40, self.y - 10
            size: 60, 60

# --- 【修正重點】將 SpotifyCard 改為單一按鈕 ---
# 這樣文字就會強制在正中間，而不是被擠在下面
<SpotifyCard>:
    background_normal: ''
    background_color: 0, 0, 0, 0
    font_name: '{FONT_NAME}'
    font_size: '18sp'  # 字體加大
    bold: True
    color: [1, 1, 1, 1]
    
    # 強制文字置中
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
        AsyncImage:
            source: root.thumb
            color: [1, 1, 1, 1] if root.thumb else [1, 1, 1, 0]
            fit_mode: 'cover'
            radius: [8,]
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
# 邏輯層
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
        if hasattr(self, 'lbl'):
            self.lbl.color = value
    def update_label_width(self, *args):
        if hasattr(self, 'lbl'):
            self.lbl.width = self.lbl.texture_size[0] + 50
    def animate(self, dt):
        if hasattr(self, 'lbl') and self.lbl.width > self.width:
            anim = Animation(scroll_x=1, duration=8, t='linear') + \
                   Animation(scroll_x=1, duration=2) + \
                   Animation(scroll_x=0, duration=0.5)
            anim.start(self)
        else:
            self.scroll_x = 0

# --- 【修正重點】類別改為繼承 Button ---
class SpotifyCard(Button): 
    img_color = ListProperty([0.3, 0.3, 0.3, 1])
    # 因為是 Button，本身就有 text 屬性，不需要額外定義

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
    
    list_title = StringProperty("搜尋結果 (點擊即播)")
    current_playing_title = StringProperty("尚未播放")
    is_playing = BooleanProperty(False)
    
    current_song_index = -1
    manual_stop = False
    
    def build(self):
        self.engine = MusicEngine()
        self.engine.bind(on_playback_ready=self.on_engine_ready)
        self.engine.bind(on_track_finished=self.on_engine_finished)
        self.engine.bind(on_error=self.on_engine_error)
        
        self.apply_spotify_theme()
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.INTERNET, Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
        return Builder.load_string(KV_CODE)

    def on_engine_ready(self, instance, success):
        if success:
            self.is_playing = True
        else:
            self.current_playing_title = "播放失敗"
            self.is_playing = False

    def on_engine_finished(self, instance):
        if not self.manual_stop:
            self.play_next()

    def on_engine_error(self, instance, error):
        self.current_playing_title = "發生錯誤，請重試"

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
        folder = get_storage_path()
        local_songs = []
        if os.path.exists(folder):
            for i, f in enumerate(os.listdir(folder)):
                if f.endswith(('.m4a', '.mp3', '.webm', '.mp4', '.wav')):
                    title = os.path.splitext(f)[0]
                    thumb_path = os.path.join(folder, f"{title}.jpg")
                    thumb_to_show = thumb_path if os.path.exists(thumb_path) else ''
                    local_songs.append({
                        'title': title, 'url': '', 'thumb': thumb_to_show, 
                        'status_text': '[本機] 已下載', 'index': len(local_songs)
                    })
        if not local_songs:
            local_songs.append({'title': '尚無下載歌曲', 'url': '', 'thumb': '', 'status_text': '', 'index': 0})
        self.root.ids.rv.data = local_songs

    def search_music(self, keyword):
        if not keyword: return
        self.current_song_index = -1
        self.list_title = f"搜尋：{keyword}"
        self.root.ids.search_input.focus = False
        threading.Thread(target=self._search_thread, args=(keyword,)).start()

    def _search_thread(self, keyword):
        ydl_opts = {'quiet': True, 'extract_flat': True, 'noplaylist': True, 'ignoreerrors': True, 'logger': QuietLogger()}
        results_data = []
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch100:{keyword}", download=False)
                if info and 'entries' in info:
                    for i, entry in enumerate(info['entries']):
                        if entry:
                            vid = entry.get('id', '')
                            thumb_url = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg" if vid else ''
                            results_data.append({'title': entry.get('title', 'Unknown'), 'url': entry.get('url', ''), 'thumb': thumb_url, 'status_text': 'YouTube 音樂', 'index': i})
        except Exception: pass
        Clock.schedule_once(lambda dt: self._update_list(results_data))

    def _update_list(self, data):
        self.root.ids.rv.data = data

    def play_manager(self, index):
        all_songs = self.root.ids.rv.data
        if not all_songs or index < 0 or index >= len(all_songs): return
        
        self.manual_stop = False
        self.current_song_index = index
        song_data = all_songs[index]
        self.current_playing_title = song_data['title']
        
        folder = get_storage_path()
        safe_title = "".join([c for c in song_data['title'] if c.isalpha() or c.isdigit() or c in ' -_']).rstrip()
        target_file = None
        if os.path.exists(folder):
            for f in os.listdir(folder):
                if f.startswith(safe_title) and f.endswith(('.m4a', '.mp3')):
                    target_file = os.path.join(folder, f)
                    break
        
        if target_file:
            self.engine.load_track(target_file)
        elif song_data['url']:
            self.cache_and_play(song_data['url'], song_data['title'], song_data['thumb'], None)

    def play_previous(self):
        all_songs = self.root.ids.rv.data
        if not all_songs: return
        new_index = self.current_song_index - 1
        if new_index < 0: new_index = len(all_songs) - 1
        self.play_manager(new_index)

    def play_next(self, *args):
        all_songs = self.root.ids.rv.data
        if not all_songs: return
        new_index = self.current_song_index + 1
        if new_index >= len(all_songs): new_index = 0
        self.play_manager(new_index)

    def toggle_play(self):
        is_playing = self.engine.pause_resume()
        self.is_playing = is_playing
        if not is_playing:
            self.manual_stop = True
        else:
            self.manual_stop = False

    def cache_and_play(self, url, title, thumb_url, item_widget):
        self.current_playing_title = f"下載中：{title}..."
        threading.Thread(target=self._download_thread, args=(url, title, thumb_url, item_widget)).start()

    def _download_thread(self, url, title, thumb_url, item_widget):
        try:
            save_path = get_storage_path()
            safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c in ' -_']).rstrip()
            out_tmpl = os.path.join(save_path, f'{safe_title}.%(ext)s')
            
            with open(os.devnull, 'w') as devnull:
                with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
                    ydl_opts = {
                        'format': 'bestaudio[ext=m4a]/bestaudio/best', 
                        'outtmpl': out_tmpl, 
                        'quiet': True, 
                        'noprogress': True, 
                        'logger': QuietLogger()
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
            
            if thumb_url:
                try:
                    local_thumb_path = os.path.join(save_path, f'{safe_title}.jpg')
                    urllib.request.urlretrieve(thumb_url, local_thumb_path)
                except: pass

            target_file = None
            if os.path.exists(save_path):
                for f in os.listdir(save_path):
                    if f.startswith(safe_title) and f.endswith(('.m4a', '.mp3')):
                        target_file = os.path.join(save_path, f)
                        break

            if target_file:
                Clock.schedule_once(lambda dt: self.engine.load_track(target_file), 0.1)
                if item_widget:
                    Clock.schedule_once(lambda dt: self._update_item_status(item_widget, "已下載"))
            else:
                Clock.schedule_once(lambda dt: self._update_title("格式錯誤"))
        except Exception: pass

    def _update_item_status(self, widget, text):
        widget.status_text = text
    def _update_title(self, text):
        self.current_playing_title = text

if __name__ == '__main__':
    MusicPlayerApp().run()