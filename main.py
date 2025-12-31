# ==========================================
# 0. 系統環境與鍵盤修正 (必須在所有 import 之前)
# ==========================================
import os
os.environ['KIVY_NO_ARGS'] = '1' # 禁止 Kivy 解析參數，避免干擾

from kivy.config import Config
# 強制 Kivy 使用 Android 系統原生鍵盤，解決無法切換輸入法的問題
Config.set('kivy', 'keyboard_mode', 'system')
Config.set('kivy', 'keyboard_layout', 'system')
# 允許圖片載入忽略部分錯誤
Config.set('network', 'useragent', 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36')

import threading
import ssl
import certifi
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import AsyncImage
from kivy.properties import StringProperty, ListProperty, BooleanProperty, NumericProperty
from kivy.clock import Clock
from kivy.utils import platform
from kivy.animation import Animation
from kivy.core.text import LabelBase
from kivy.core.audio import SoundLoader # 改回 SoundLoader，配合 ffpyplayer 更穩定

# ==========================================
# 1. SSL 與 全域設定
# ==========================================
# 忽略 SSL 驗證，解決圖片載入黑屏與下載報錯
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    pass

os.environ['SSL_CERT_FILE'] = certifi.where()

# ==========================================
# 2. 字體載入
# ==========================================
FONT_NAME = 'Roboto'
try:
    # 注意：NotoSansTC 僅支援中文，韓文日文會顯示方塊是正常的，除非換成 20MB 的 CJK 大字體
    LabelBase.register(name='MyFont',
                       fn_regular='NotoSansTC-Regular.otf',
                       fn_bold='NotoSansTC-Regular.otf')
    FONT_NAME = 'MyFont'
except Exception as e:
    print(f"Font Error: {e}")

# ==========================================
# 3. 路徑設定
# ==========================================
def get_storage_path():
    if platform == 'android':
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            context = PythonActivity.mActivity
            # 使用 getExternalFilesDir 避免權限崩潰
            return context.getExternalFilesDir(None).getAbsolutePath()
        except:
            return "/sdcard/Download"
    else:
        return os.path.join(os.getcwd(), 'Music')

# ==========================================
# KV 介面 (加入圖片載入 loading 顯示)
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
    height: '90dp'
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
        size_hint_x: None
        width: '90dp'
        fit_mode: 'cover'
        radius: [8,]
        nocache: True
        # 圖片載入失敗時的佔位圖
        on_error: self.source = '' 

    BoxLayout:
        orientation: 'vertical'
        Label:
            text: root.title
            font_name: '{FONT_NAME}'
            font_size: '16sp'
            color: app.theme_text_color
            text_size: self.size
            halign: 'left'
            valign: 'center'
            shorten: True
            shorten_from: 'right'
            max_lines: 2
        Label:
            text: root.status_text
            font_name: '{FONT_NAME}'
            font_size: '12sp'
            color: [0.6, 0.6, 0.6, 1]
            size_hint_y: 0.4
            text_size: self.size
            halign: 'left'
            valign: 'top'

    Label:
        text: '▶'
        font_name: '{FONT_NAME}'
        size_hint_x: None
        width: '30dp'
        color: app.theme_accent_color
        font_size: '20sp'

# --- 主介面與之前的結構相同，保留 Input/Button 設定 ---
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
        padding: '8dp'
        spacing: '8dp'
        TextInput:
            id: search_input
            hint_text: '輸入歌手或歌名...'
            font_name: '{FONT_NAME}'
            size_hint_x: 0.65
            multiline: False
            on_text_validate: app.search_music(self.text)
        Button:
            text: '搜尋'
            font_name: '{FONT_NAME}'
            size_hint_x: 0.2
            background_color: [0.11, 0.72, 0.32, 1]
            on_release: app.search_music(search_input.text)
        Button:
            text: '切換'
            font_name: '{FONT_NAME}'
            size_hint_x: 0.15
            background_color: [0.3, 0.3, 0.3, 1]
            on_release: app.toggle_theme()

    # 快捷按鈕區
    GridLayout:
        cols: 2
        size_hint_y: None
        height: '120dp'
        padding: '5dp'
        spacing: '5dp'
        Button:
            text: '熱門華語'
            font_name: '{FONT_NAME}'
            background_color: [0.8, 0.2, 0.2, 1]
            on_release: app.search_music('2024 熱門華語歌曲')
        Button:
            text: '西洋排行榜'
            font_name: '{FONT_NAME}'
            background_color: [0.2, 0.5, 0.2, 1]
            on_release: app.search_music('Billboard Hot 100 2024')
        Button:
            text: 'K-POP 精選'
            font_name: '{FONT_NAME}'
            background_color: [0.8, 0.5, 0.2, 1]
            on_release: app.search_music('KPOP 2024 Hits')
        Button:
            text: '抖音熱歌'
            font_name: '{FONT_NAME}'
            background_color: [0.2, 0.2, 0.8, 1]
            on_release: app.search_music('TikTok 抖音熱歌 2024')

    Label:
        text: app.list_title
        font_name: '{FONT_NAME}'
        size_hint_y: None
        height: '30dp'
        color: app.theme_text_color

    RecycleView:
        id: rv
        viewclass: 'SongListItem'
        scroll_type: ['bars', 'content']
        bar_width: 10
        RecycleBoxLayout:
            default_size: None, dp(90)
            default_size_hint: 1, None
            size_hint_y: None
            height: self.minimum_height
            orientation: 'vertical'

    # 底部播放條
    BoxLayout:
        size_hint_y: None
        height: '80dp'
        padding: '5dp'
        orientation: 'vertical'
        canvas.before:
            Color:
                rgba: [0.1, 0.1, 0.1, 1]
            Rectangle:
                pos: self.pos
                size: self.size
        AutoScrollLabel:
            text: app.current_playing_title
            font_size: '14sp'
            size_hint_y: 0.4
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: 0.6
            Button:
                text: 'STOP'
                on_release: app.stop_music()
"""

# ==========================================
# 邏輯層 (修復閃退與功能)
# ==========================================
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
        if hasattr(self, 'lbl'):
            self.lbl.text = value
            self.scroll_x = 0
            Animation.cancel_all(self)
    def update_label_width(self, *args):
        if hasattr(self, 'lbl'): self.lbl.width = self.lbl.texture_size[0] + 50
    def animate(self, dt):
        if hasattr(self, 'lbl') and self.lbl.width > self.width:
            anim = Animation(scroll_x=1, duration=8) + Animation(scroll_x=0, duration=0.5)
            anim.start(self)

class SongListItem(ButtonBehavior, BoxLayout):
    title = StringProperty("")
    thumb = StringProperty("")
    status_text = StringProperty("")
    index = NumericProperty(0)

class MusicPlayerApp(App):
    theme_bg_color = ListProperty([0.07, 0.07, 0.07, 1])
    theme_text_color = ListProperty([1, 1, 1, 1])
    theme_card_bg = ListProperty([0.15, 0.15, 0.15, 1])
    theme_accent_color = ListProperty([0.11, 0.72, 0.32, 1])
    
    list_title = StringProperty("搜尋結果")
    current_playing_title = StringProperty("就緒")
    
    current_song_index = -1
    yt_dlp_module = None
    sound = None # 播放器物件
    
    def build(self):
        # 請求權限
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.INTERNET, Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
        
        Clock.schedule_once(self.load_libraries, 1)
        return Builder.load_string(KV_CODE)

    def load_libraries(self, dt):
        try:
            import yt_dlp
            self.yt_dlp_module = yt_dlp
        except Exception as e:
            self.current_playing_title = f"Lib Error: {e}"

    def toggle_theme(self):
        # 簡單的主題切換範例
        if self.theme_bg_color[0] < 0.5:
            self.theme_bg_color = [0.95, 0.95, 0.95, 1]
            self.theme_text_color = [0.1, 0.1, 0.1, 1]
        else:
            self.theme_bg_color = [0.07, 0.07, 0.07, 1]
            self.theme_text_color = [1, 1, 1, 1]

    def stop_music(self):
        if self.sound:
            self.sound.stop()
            self.current_playing_title = "已停止"

    def search_music(self, keyword):
        if not keyword: return
        self.list_title = f"搜尋中: {keyword}..."
        self.root.ids.search_input.focus = False # 收起鍵盤
        threading.Thread(target=self._search_thread, args=(keyword,)).start()

    def _search_thread(self, keyword):
        if not self.yt_dlp_module: return
        # 修正：搜尋數量改為 50
        ydl_opts = {'quiet': True, 'extract_flat': True, 'noplaylist': True, 'ignoreerrors': True}
        results_data = []
        try:
            with self.yt_dlp_module.YoutubeDL(ydl_opts) as ydl:
                # 這裡改為 ytsearch50
                info = ydl.extract_info(f"ytsearch50:{keyword}", download=False)
                if info and 'entries' in info:
                    for i, entry in enumerate(info['entries']):
                        if entry:
                            results_data.append({
                                'title': entry.get('title', 'Unknown'), 
                                'thumb': entry.get('thumbnail', ''), # 確保有縮圖網址
                                'status_text': 'YouTube', 
                                'index': i,
                                'url': entry.get('url', '')
                            })
        except Exception as e:
            print(e)
        Clock.schedule_once(lambda dt: self._update_list(results_data))

    def _update_list(self, data):
        self.root.ids.rv.data = data
        self.list_title = f"找到 {len(data)} 首歌曲"

    def play_manager(self, index):
        data = self.root.ids.rv.data[index]
        self.current_playing_title = f"準備下載: {data['title']}"
        threading.Thread(target=self._download_thread, args=(data['url'], data['title'])).start()

    def _download_thread(self, url, title):
        try:
            save_path = get_storage_path()
            if not os.path.exists(save_path): os.makedirs(save_path, exist_ok=True)
            
            safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c in ' -_']).rstrip()
            # 強制使用 m4a
            out_tmpl = os.path.join(save_path, f'{safe_title}.%(ext)s')
            
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/best',
                'outtmpl': out_tmpl,
                'quiet': True,
                'nocheckcertificate': True
            }
            
            with self.yt_dlp_module.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # 尋找檔案
            target_file = None
            for f in os.listdir(save_path):
                if safe_title in f:
                    target_file = os.path.join(save_path, f)
                    break

            if target_file:
                # 必須在主執行緒播放，否則會閃退
                Clock.schedule_once(lambda dt: self._play_file(target_file, title))
            else:
                Clock.schedule_once(lambda dt: self._update_title("下載失敗"))

        except Exception as e:
            Clock.schedule_once(lambda dt: self._update_title(f"錯誤: {str(e)[:20]}"))

    def _play_file(self, filepath, title):
        try:
            if self.sound: self.sound.stop()
            
            # 使用 Kivy SoundLoader (依賴 ffpyplayer)
            self.sound = SoundLoader.load(filepath)
            
            if self.sound:
                self.sound.play()
                self._update_title(f"播放中: {title}")
            else:
                self._update_title("無法解碼檔案")
        except Exception as e:
            self._update_title(f"播放錯誤: {e}")

    def _update_title(self, text):
        self.current_playing_title = text

if __name__ == '__main__':
    MusicPlayerApp().run()
