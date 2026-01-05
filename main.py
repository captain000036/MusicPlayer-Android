import os
import threading
import ssl
import certifi
import time
from kivy.config import Config

# ==========================================
# 1. 系統環境設定 (最優先)
# ==========================================
# 解決 HTTPS 下載閃退
try:
    os.environ['SSL_CERT_FILE'] = certifi.where()
    ssl._create_default_https_context = ssl._create_unverified_context
except: pass

# 解決圖片不顯示 (偽裝成 Android Chrome)
Config.set('network', 'useragent', 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36')

# 解決輸入法無法切換 (關鍵設定)
Config.set('kivy', 'keyboard_mode', 'system')
os.environ['SDL_IME_SHOW_UI'] = '1'

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.button import Button
from kivy.uix.image import AsyncImage
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.properties import StringProperty, ListProperty, BooleanProperty, NumericProperty
from kivy.clock import Clock, mainthread
from kivy.utils import platform
from kivy.event import EventDispatcher
from kivy.core.text import LabelBase
from kivy.loader import Loader

# 設定圖片載入標頭
Loader.headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36'
}

# 2. 字體載入
try:
    LabelBase.register(name='MyFont', fn_regular='NotoSansTC-Regular.otf', fn_bold='NotoSansTC-Regular.otf')
    FONT_NAME = 'MyFont'
except: FONT_NAME = 'Roboto'

# 3. 路徑設定
def get_storage_path():
    if platform == 'android':
        try:
            from jnius import autoclass
            return autoclass('org.kivy.android.PythonActivity').mActivity.getExternalFilesDir(None).getAbsolutePath()
        except: return "/sdcard/Download"
    return os.path.join(os.getcwd(), 'Music')

# ==========================================
# 4. 音樂引擎 (原生播放器 + 輪詢監聽)
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
        if not self.player: 
            # 電腦版測試用
            self.dispatch('on_playback_ready', True)
            return

        try:
            self.stop_monitor()
            if self.player.isPlaying(): self.player.stop()
            self.player.reset()
            self.player.setDataSource(filepath)
            self.player.prepare() # 同步準備，確保檔案就緒
            self.player.start()
            self.user_paused = False
            self.dispatch('on_playback_ready', True)
            self.start_monitor()
        except Exception as e:
            self.dispatch('on_error', str(e))

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
        Clock.schedule_interval(self._check, 1) # 每秒檢查一次
        
    def stop_monitor(self):
        Clock.unschedule(self._check)
    
    # 【關鍵】確保檢查邏輯在主線程運行，防止崩潰
    @mainthread
    def _check(self, dt):
        if self.player and not self.player.isPlaying() and not self.user_paused:
            try:
                # 如果播放結束 (誤差 1 秒內)
                if self.player.getCurrentPosition() >= self.player.getDuration() - 1000:
                    self.stop_monitor()
                    self.dispatch('on_track_finished')
            except: pass

    def on_playback_ready(self, s): pass
    def on_track_finished(self): pass
    def on_error(self, e): pass

# ==========================================
# 5. KV 介面 (完全保留您的雙介面設計)
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
            rgba: app.theme_card_bg
        Rectangle:
            pos: self.pos
            size: self.size
    AsyncImage:
        source: root.thumb
        color: [1,1,1,1] if root.thumb else [1,1,1,0]
        fit_mode: 'cover'
        size_hint_x: None
        width: '80dp'
        nocache: True
    BoxLayout:
        orientation: 'vertical'
        Label:
            text: root.title
            font_name: '{FONT_NAME}'
            font_size: '16sp'
            color: app.theme_text_color
            text_size: self.size
            halign: 'left'
            valign: 'bottom'
            shorten: True
        Label:
            text: root.status_text
            font_name: '{FONT_NAME}'
            font_size: '12sp'
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
<ThemedInput@TextInput>:
    font_name: '{FONT_NAME}'
    font_size: '18sp'
    multiline: False
    padding_y: [self.height/2.0-(self.line_height/2.0), 0]
    padding_x: '10dp'
    on_text_validate: app.search_music(self.text)
<DashboardCard@Button>:
    font_name: '{FONT_NAME}'
    font_size: '15sp'
    bold: True
    background_normal: ''
    background_color: 0,0,0,0
    on_release: app.show_local_files(self.text)
    canvas.before:
        Color:
            rgba: root.btn_color if hasattr(root, 'btn_color') else [0.5,0.5,0.5,1]
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10,]
<SpotifyCard@Button>:
    font_name: '{FONT_NAME}'
    font_size: '18sp'
    bold: True
    background_normal: ''
    background_color: 0,0,0,0
    canvas.before:
        Color:
            rgba: root.img_color if hasattr(root, 'img_color') else [0.3,0.3,0.3,1]
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10,]
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
        ThemedInput:
            id: search_input
            hint_text: '輸入歌手...'
            size_hint_x: 0.65
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
# 6. App 主程式邏輯
# ==========================================
class AutoScrollLabel(ScrollView):
    text, color, font_size = StringProperty(''), ListProperty([1,1,1,1]), StringProperty('16sp')
    def on_kv_post(self, w):
        self.lbl=self.ids.lbl; self.bind(text=self.ut, color=self.uc); self.lbl.bind(texture_size=self.ulw)
        Clock.schedule_interval(self.an, 3)
    def ut(self,i,v): self.lbl.text=v; self.scroll_x=0; Animation.cancel_all(self)
    def uc(self,i,v): self.lbl.color=v
    def ulw(self,*a): self.lbl.width=self.lbl.texture_size[0]+50
    def an(self,dt): 
        if self.lbl.width>self.width: Animation(scroll_x=1, d=8, t='linear').start(self)
        else: self.scroll_x=0

class SongListItem(ButtonBehavior, BoxLayout):
    title, url, thumb, status_text = StringProperty(""), StringProperty(""), StringProperty(""), StringProperty("")
    index = NumericProperty(0)

class MusicPlayerApp(App):
    is_spotify = BooleanProperty(True)
    theme_bg_color = ListProperty([0.07, 0.07, 0.07, 1])
    theme_text_color = ListProperty([1, 1, 1, 1])
    theme_input_bg = ListProperty([0.2, 0.2, 0.2, 1])
    theme_card_bg = ListProperty([0.07, 0.07, 0.07, 1])
    theme_accent_color = ListProperty([0.11, 0.72, 0.32, 1])
    list_title = StringProperty("搜尋結果")
    current_playing_title = StringProperty("請點擊搜尋")
    is_playing = BooleanProperty(False)
    current_song_index = -1

    def build(self):
        self.engine = MusicEngine()
        self.engine.bind(on_playback_ready=self.on_ready, on_track_finished=self.on_fin, on_error=self.on_err)
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.INTERNET, Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
        return Builder.load_string(KV_CODE)

    @mainthread
    def on_ready(self, i, s): self.is_playing = True
    @mainthread
    def on_fin(self, i): self.play_next()
    @mainthread
    def on_err(self, i, e): self.current_playing_title="播放錯誤"; print(e)

    def toggle_theme(self):
        self.is_spotify = not self.is_spotify
        if self.is_spotify: 
            self.theme_bg_color=[0.07,0.07,0.07,1]; self.theme_text_color=[1,1,1,1]
            self.theme_input_bg=[0.2,0.2,0.2,1]; self.theme_card_bg=[0.07,0.07,0.07,1]
        else: 
            self.theme_bg_color=[0.98,0.98,0.98,1]; self.theme_text_color=[0.1,0.1,0.1,1]
            self.theme_input_bg=[0.92,0.92,0.92,1]; self.theme_card_bg=[1,1,1,0]

    def show_local_files(self, name):
        self.current_song_index, self.list_title = -1, f"{name} (本地)"
        folder, local = get_storage_path(), []
        if os.path.exists(folder):
            for i, f in enumerate(os.listdir(folder)):
                if f.endswith(('.m4a', '.mp3')): local.append({'title':os.path.splitext(f)[0], 'url':'', 'thumb':'', 'status_text':'[本地]', 'index':len(local)})
        self.root.ids.rv.data = local

    def search_music(self, kw):
        if not kw: return
        self.root.ids.search_input.focus = False
        threading.Thread(target=self._search, args=(kw,)).start()

    # 【關鍵】將 yt_dlp 延遲到這裡才載入，防止啟動時閃退
    def _search(self, kw):
        try:
            import yt_dlp
            # 增加 User-Agent 防止被擋，增加 ignoreerrors 防止崩潰
            opts = {'quiet':True, 'extract_flat':True, 'ignoreerrors':True, 'nocheckcertificate':True}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(f"ytsearch50:{kw}", download=False)
                res = []
                if 'entries' in info:
                    for i,e in enumerate(info['entries']):
                        if e: res.append({'title':e.get('title',''), 'url':e.get('url',''), 'thumb':e.get('thumbnail',''), 'status_text':'YouTube', 'index':i})
                Clock.schedule_once(lambda dt: setattr(self.root.ids.rv, 'data', res))
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self, 'current_playing_title', f"搜尋錯誤:{str(e)[:20]}"))

    def play_manager(self, idx):
        if idx<0 or idx>=len(self.root.ids.rv.data): return
        self.current_song_index = idx
        data = self.root.ids.rv.data[idx]
        self.current_playing_title = data['title']
        
        folder, safe_title = get_storage_path(), "".join([c for c in data['title'] if c.isalpha() or c.isdigit() or c in ' -_']).rstrip()
        target = None
        if os.path.exists(folder):
            for f in os.listdir(folder):
                if safe_title in f and f.endswith(('.mp3','.m4a')): target=os.path.join(folder,f); break
        
        if target: self.engine.load_track(target)
        elif data['url']: threading.Thread(target=self._dl, args=(data['url'], safe_title)).start()

    # 【關鍵】將 yt_dlp 延遲到這裡才載入
    def _dl(self, url, title):
        try:
            import yt_dlp
            folder = get_storage_path()
            if not os.path.exists(folder): os.makedirs(folder, exist_ok=True)
            out = os.path.join(folder, f'{title}.%(ext)s')
            # 強制只下載音訊，不進行合併，防止 FFmpeg 缺失導致閃退
            with yt_dlp.YoutubeDL({'format':'bestaudio[ext=m4a]/best', 'outtmpl':out, 'quiet':True, 'nocheckcertificate':True}) as ydl:
                ydl.download([url])
            
            # 下載完畢後，回到主線程通知播放引擎
            found = False
            for f in os.listdir(folder):
                if title in f: 
                    Clock.schedule_once(lambda dt: self.engine.load_track(os.path.join(folder,f)))
                    found = True
                    break
            if not found:
                Clock.schedule_once(lambda dt: setattr(self, 'current_playing_title', "下載失敗: 找不到檔案"))
                
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self, 'current_playing_title', f"錯誤:{str(e)[:20]}"))

    def play_next(self): self.play_manager(self.current_song_index + 1)
    def play_previous(self): self.play_manager(self.current_song_index - 1)
    def toggle_play(self): self.is_playing = self.engine.pause_resume()

if __name__ == '__main__':
    MusicPlayerApp().run()
