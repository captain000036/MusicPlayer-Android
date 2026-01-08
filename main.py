import os
# 強制設定
os.environ['KIVY_IMAGE'] = 'sdl2'
os.environ['SDL_IME_SHOW_UI'] = '1'

import threading
from kivy.config import Config
# 【輸入法嘗試】改用 systemanddock 模式
Config.set('kivy', 'keyboard_mode', 'systemanddock')

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock, mainthread
from kivy.utils import platform
from kivy.event import EventDispatcher
from kivy.core.text import LabelBase
from kivy.core.audio import SoundLoader
from kivy.loader import Loader

Loader.headers = {'User-Agent': 'Mozilla/5.0'}

# ==========================================
# 1. 暴力解決亂碼：掃描手機所有字型
# ==========================================
FONT_NAME = 'Roboto' # 預設
if platform == 'android':
    font_dirs = ['/system/fonts', '/system/font', '/data/fonts']
    # 常見的中文字型檔名
    target_fonts = ['DroidSansFallback.ttf', 'NotoSansTC-Regular.otf', 'NotoSansCJK-Regular.ttc', 'Miui-Regular.ttf', 'HwChinese-Regular.ttf']
    
    found = False
    # 策略 A: 先找已知的中文檔名
    for d in font_dirs:
        if not os.path.exists(d): continue
        for target in target_fonts:
            fpath = os.path.join(d, target)
            if os.path.exists(fpath):
                try:
                    LabelBase.register(name='MyFont', fn_regular=fpath, fn_bold=fpath)
                    FONT_NAME = 'MyFont'
                    found = True
                    break
                except: pass
        if found: break
    
    # 策略 B: 如果都沒找到，隨便抓一個體積大的 ttf (通常體積大的是中文字型)
    if not found:
        for d in font_dirs:
            if not os.path.exists(d): continue
            for f in os.listdir(d):
                if f.endswith('.ttf') and os.path.getsize(os.path.join(d, f)) > 5000000: # 大於5MB
                    LabelBase.register(name='MyFont', fn_regular=os.path.join(d, f), fn_bold=os.path.join(d, f))
                    FONT_NAME = 'MyFont'
                    found = True
                    break
            if found: break

# 路徑
def get_storage_path():
    if platform == 'android':
        try:
            from jnius import autoclass
            return autoclass('org.kivy.android.PythonActivity').mActivity.getExternalFilesDir(None).getAbsolutePath()
        except: return "/sdcard/Download"
    else:
        return os.path.join(os.getcwd(), 'MusicPlayer')

# ==========================================
# KV 介面 (純文字版 - 避開圖片問題)
# ==========================================
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
    
    # 【改動】移除 Image 元件，只顯示文字，確保穩定
    Label:
        text: root.title
        font_name: '{FONT_NAME}'
        font_size: '18sp'
        text_size: self.size
        halign: 'left'
        valign: 'center'
        shorten: True
        color: [1, 1, 1, 1]

    Button:
        text: '播放'
        font_name: '{FONT_NAME}'
        size_hint_x: None
        width: '80dp'
        background_color: [0, 0.7, 0.3, 1]
        on_release: app.play_manager(root.index)

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

    # 搜尋
    BoxLayout:
        size_hint_y: None
        height: '50dp'
        TextInput:
            id: search_input
            hint_text: '請輸入歌名...'
            font_name: '{FONT_NAME}'
            multiline: False
            size_hint_x: 0.7
        Button:
            text: 'GO'
            font_name: '{FONT_NAME}'
            size_hint_x: 0.3
            on_release: app.search_music(search_input.text)

    # 狀態
    Label:
        text: app.status_msg
        font_name: '{FONT_NAME}'
        size_hint_y: None
        height: '40dp'
        color: [1, 1, 0, 1]

    # 列表
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

class SongItem(BoxLayout):
    title = StringProperty("")
    index = NumericProperty(0)

class MusicPlayerApp(App):
    status_msg = StringProperty("系統就緒")
    
    def build(self):
        self.sound = None
        return Builder.load_string(KV_CODE)

    def search_music(self, keyword):
        if not keyword: return
        self.status_msg = f"正在搜尋: {keyword}..."
        self.root.ids.search_input.focus = False
        threading.Thread(target=self._search_thread, args=(keyword,)).start()

    def _search_thread(self, keyword):
        try:
            import yt_dlp
            # 簡化參數
            ydl_opts = {'quiet': True, 'extract_flat': True, 'ignoreerrors': True, 'nocheckcertificate': True}
            
            results_data = []
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch10:{keyword}", download=False)
                if 'entries' in info:
                    for i, entry in enumerate(info['entries']):
                        title = entry.get('title', 'Unknown')
                        # 這次我們不處理圖片，直接略過，避免白屏問題
                        results_data.append({
                            'title': title, 
                            'url': entry.get('url', ''), 
                            'index': i
                        })
            Clock.schedule_once(lambda dt: self._update_list(results_data))
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self, 'status_msg', f"搜尋失敗: {e}"))

    @mainthread
    def _update_list(self, data):
        self.root.ids.rv.data = data
        self.status_msg = f"找到 {len(data)} 首歌曲"

    def play_manager(self, index):
        data = self.root.ids.rv.data[index]
        self.status_msg = f"準備播放: {data['title'][:10]}..."
        threading.Thread(target=self._download_thread, args=(data['url'], data['title'])).start()

    def _download_thread(self, url, title):
        try:
            import yt_dlp
            folder = get_path('Music')
            if not os.path.exists(folder): os.makedirs(folder)
            
            safe_title = "".join([c for c in title if c.isalnum() or c in ' -_']).rstrip()
            out_tmpl = os.path.join(folder, f'{safe_title}.%(ext)s')
            
            # 【關鍵】強制 m4a，這是 Kivy SoundLoader 支援最好的格式
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
                if safe_title in f: # 模糊比對，只要檔名包含關鍵字即可
                    target_file = os.path.join(folder, f)
                    break
            
            if target_file and os.path.exists(target_file):
                Clock.schedule_once(lambda dt: self.play_sound(target_file))
                Clock.schedule_once(lambda dt: setattr(self, 'status_msg', f"正在播放: {safe_title}"))
            else:
                Clock.schedule_once(lambda dt: setattr(self, 'status_msg', "下載失敗: 找不到檔案"))
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self, 'status_msg', f"下載錯誤: {e}"))

    @mainthread
    def play_sound(self, filepath):
        try:
            # 【改動】使用 Kivy SoundLoader 取代 Native Player
            # 這能避免底層 Crash
            if self.sound:
                self.sound.stop()
            
            self.sound = SoundLoader.load(filepath)
            if self.sound:
                self.sound.play()
            else:
                self.status_msg = "播放器無法載入此檔案"
        except Exception as e:
            self.status_msg = f"播放錯誤: {e}"

if __name__ == '__main__':
    MusicPlayerApp().run()
