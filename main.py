import os
# 強制設定
os.environ['KIVY_IMAGE'] = 'sdl2'
os.environ['SDL_IME_SHOW_UI'] = '1'

import threading
import time
from kivy.config import Config

# 輸入法設定
Config.set('kivy', 'keyboard_mode', '')

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.button import Button
from kivy.clock import Clock, mainthread
from kivy.utils import platform
from kivy.event import EventDispatcher
from kivy.core.text import LabelBase
from kivy.loader import Loader

# 偽裝
Loader.headers = {'User-Agent': 'Mozilla/5.0'}

# ==========================================
# 【關鍵修復1】解決亂碼：借用 Android 系統字型
# ==========================================
FONT_NAME = 'Roboto' # 預設值
if platform == 'android':
    # 常見的 Android 中文字型路徑
    system_fonts = [
        '/system/fonts/DroidSansFallback.ttf',
        '/system/fonts/NotoSansTC-Regular.otf',
        '/system/fonts/NotoSansCJK-Regular.ttc'
    ]
    for font in system_fonts:
        if os.path.exists(font):
            try:
                # 註冊為 MyFont
                LabelBase.register(name='MyFont', fn_regular=font, fn_bold=font)
                FONT_NAME = 'MyFont'
                print(f"Success load font: {font}")
                break
            except: pass

# 路徑管理
def get_path(folder_name):
    if platform == 'android':
        try:
            from jnius import autoclass
            return autoclass('org.kivy.android.PythonActivity').mActivity.getExternalFilesDir(None).getAbsolutePath()
        except: return "/sdcard/Download"
    else:
        return os.path.join(os.getcwd(), 'MusicPlayer')

# ==========================================
# 音樂引擎 (防爆版)
# ==========================================
class MusicEngine(EventDispatcher):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.player = None
        if platform == 'android':
            try:
                from jnius import autoclass
                self.MediaPlayer = autoclass('android.media.MediaPlayer')
                self.player = self.MediaPlayer()
            except: pass

    def play_file(self, filepath):
        if not self.player: return False
        try:
            if self.player.isPlaying(): self.player.stop()
            self.player.reset()
            # 【關鍵】播放前再次確認檔案真的存在且可讀
            if not os.path.exists(filepath):
                return False
            self.player.setDataSource(filepath)
            self.player.prepare()
            self.player.start()
            return True
        except Exception as e:
            print(f"Play Error: {e}")
            return False

    def stop(self):
        if self.player and self.player.isPlaying(): self.player.stop()

# ==========================================
# KV 介面 (極簡穩定版)
# ==========================================
KV_CODE = f"""
<SongItem@BoxLayout>:
    orientation: 'horizontal'
    size_hint_y: None
    height: '100dp'
    padding: '5dp'
    canvas.before:
        Color:
            rgba: [0.15, 0.15, 0.15, 1]
        Rectangle:
            pos: self.pos
            size: self.size
    
    # 圖片
    Image:
        source: root.thumb
        size_hint_x: None
        width: '100dp'
        fit_mode: 'cover'
        nocache: True
        color: [1, 1, 1, 1]

    # 文字
    Label:
        text: root.title
        font_name: '{FONT_NAME}'
        font_size: '16sp'
        text_size: self.size
        halign: 'left'
        valign: 'center'
        shorten: True
        color: [1, 1, 1, 1]
        padding_x: '10dp'

    # 播放按鈕
    Button:
        text: 'PLAY'
        font_name: '{FONT_NAME}'
        size_hint_x: None
        width: '70dp'
        background_normal: ''
        background_color: [0, 0.7, 0.3, 1]
        on_release: app.play_manager(root.index)

BoxLayout:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: [0.05, 0.05, 0.05, 1]
        Rectangle:
            pos: self.pos
            size: self.size

    # 搜尋區
    BoxLayout:
        size_hint_y: None
        height: '60dp' 
        padding: '10dp'
        spacing: '10dp'
        TextInput:
            id: search_input
            hint_text: '輸入歌手或歌名...'
            font_name: '{FONT_NAME}'
            multiline: False
            size_hint_x: 0.7
        Button:
            text: '搜尋'
            font_name: '{FONT_NAME}'
            size_hint_x: 0.3
            on_release: app.search_music(search_input.text)

    # 狀態列
    Label:
        text: app.status_text
        font_name: '{FONT_NAME}'
        size_hint_y: None
        height: '40dp'
        color: [1, 1, 0, 1]

    # 列表區
    RecycleView:
        id: rv
        viewclass: 'SongItem'
        scroll_type: ['bars', 'content']
        bar_width: 10
        RecycleBoxLayout:
            default_size: None, dp(100)
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
    status_text = StringProperty("請搜尋歌曲")
    
    def build(self):
        self.engine = MusicEngine()
        return Builder.load_string(KV_CODE)

    def search_music(self, keyword):
        if not keyword: return
        self.status_text = "搜尋中... (需要幾秒鐘)"
        self.root.ids.search_input.focus = False
        threading.Thread(target=self._search_thread, args=(keyword,)).start()

    def _search_thread(self, keyword):
        try:
            import requests
            import yt_dlp
            
            # 關閉 SSL 警告 (解決圖片下載問題)
            requests.packages.urllib3.disable_warnings()
            
            cache_dir = get_path('Cache')
            if not os.path.exists(cache_dir): os.makedirs(cache_dir)
            
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
                            
                            # 【修復2】下載圖片到本地
                            local_thumb = os.path.join(cache_dir, f"{video_id}.jpg")
                            # 檢查檔案是否有效 (大於 0 bytes)
                            if thumb_url and (not os.path.exists(local_thumb) or os.path.getsize(local_thumb) == 0):
                                try:
                                    resp = requests.get(thumb_url, timeout=5, verify=False)
                                    if resp.status_code == 200:
                                        with open(local_thumb, 'wb') as f: f.write(resp.content)
                                except: pass
                            
                            final_thumb = local_thumb if os.path.exists(local_thumb) else ''
                            results_data.append({
                                'title': title, 
                                'url': entry.get('url', ''), 
                                'thumb': final_thumb, 
                                'index': i
                            })
            Clock.schedule_once(lambda dt: self._update_list(results_data))
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self, 'status_text', f"搜尋錯誤: {e}"))

    @mainthread
    def _update_list(self, data):
        self.root.ids.rv.data = data
        self.status_text = "搜尋完成，請點選 PLAY"

    def play_manager(self, index):
        data = self.root.ids.rv.data[index]
        self.status_text = f"正在下載: {data['title'][:10]}..."
        threading.Thread(target=self._download_thread, args=(data['url'], data['title'])).start()

    def _download_thread(self, url, title):
        try:
            import yt_dlp
            folder = get_path('Music')
            if not os.path.exists(folder): os.makedirs(folder)
            
            safe_title = "".join([c for c in title if c.isalnum() or c in ' -_']).rstrip()
            out_tmpl = os.path.join(folder, f'{safe_title}.%(ext)s')
            
            # 【修復3】強制 m4a，確保播放器能讀
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/best', 
                'outtmpl': out_tmpl, 
                'quiet': True,
                'nocheckcertificate': True,
                'postprocessors': [], # 禁止轉檔，防閃退
                'keepvideo': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # 尋找下載好的檔案
            target_file = None
            for f in os.listdir(folder):
                if safe_title in f and f.endswith(('.m4a', '.mp3', '.mp4')):
                    target_file = os.path.join(folder, f)
                    break
            
            if target_file:
                # 播放
                Clock.schedule_once(lambda dt: self.safe_play(target_file))
                Clock.schedule_once(lambda dt: setattr(self, 'status_text', f"播放中: {safe_title}"))
            else:
                Clock.schedule_once(lambda dt: setattr(self, 'status_text', "下載失敗: 找不到檔案"))
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self, 'status_text', f"下載錯誤: {e}"))

    @mainthread
    def safe_play(self, filepath):
        success = self.engine.play_file(filepath)
        if not success:
            self.status_text = "播放失敗 (格式不支援)"

if __name__ == '__main__':
    MusicPlayerApp().run()
