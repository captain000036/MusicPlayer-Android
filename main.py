import os
import sys
import traceback

# 1. 全局防崩潰啟動器
# 如果下面的任何 import 失敗，這裡會攔截並顯示錯誤，而不是閃退
try:
    from kivy.app import App
    from kivy.lang import Builder
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.label import Label
    from kivy.clock import Clock, mainthread
    from kivy.utils import platform
    from kivy.config import Config
    
    # 強制設定
    Config.set('kivy', 'keyboard_mode', '')
    os.environ['SDL_IME_SHOW_UI'] = '1'
    
    # 偽裝標頭
    USER_AGENT = 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36'
    Config.set('network', 'useragent', USER_AGENT)

except Exception as e:
    # 萬一連 Kivy 都載入失敗 (極低機率)
    print(f"CRITICAL ERROR: {e}")

# KV 介面 (保持您的雙介面設計)
KV_CODE = f"""
#:import hex kivy.utils.get_color_from_hex

<AutoScrollLabel@ScrollView>:
    do_scroll_x: False
    do_scroll_y: False
    Label:
        text: root.text if hasattr(root, 'text') else ''
        font_name: 'Roboto'
        font_size: '16sp'
        size_hint: None, 1
        width: self.texture_size[0] + 50
        halign: 'center'
        valign: 'middle'

<SongListItem@BoxLayout>:
    orientation: 'horizontal'
    size_hint_y: None
    height: '80dp'
    padding: '10dp'
    spacing: '15dp'
    canvas.before:
        Color:
            rgba: [0.1, 0.1, 0.1, 1]
        Rectangle:
            pos: self.pos
            size: self.size
    Label:
        text: root.title if hasattr(root, 'title') else ''
        font_name: 'Roboto'
        font_size: '16sp'
        text_size: self.size
        halign: 'left'
        valign: 'center'
        shorten: True

BoxLayout:
    orientation: 'vertical'
    padding: '20dp'
    spacing: '20dp'
    canvas.before:
        Color:
            rgba: [0.05, 0.05, 0.05, 1]
        Rectangle:
            pos: self.pos
            size: self.size

    Label:
        id: status_lbl
        text: app.status_text
        color: [1, 0, 0, 1] if 'Error' in self.text else [0, 1, 0, 1]
        text_size: self.width, None
        size_hint_y: None
        height: self.texture_size[1] + 50
        font_size: '14sp'

    TextInput:
        id: search_input
        size_hint_y: None
        height: '50dp'
        hint_text: '輸入搜尋...'
        multiline: False
    
    Button:
        text: '搜尋'
        size_hint_y: None
        height: '50dp'
        on_release: app.safe_search(search_input.text)

    RecycleView:
        id: rv
        viewclass: 'SongListItem'
        RecycleBoxLayout:
            default_size: None, dp(80)
            default_size_hint: 1, None
            size_hint_y: None
            height: self.minimum_height
            orientation: 'vertical'
"""

class MusicPlayerApp(App):
    status_text = StringProperty("系統正常...等待指令")
    
    def build(self):
        return Builder.load_string(KV_CODE)

    def safe_search(self, kw):
        # 使用線程來執行搜尋，避免卡死
        threading.Thread(target=self._do_search, args=(kw,)).start()

    def _do_search(self, kw):
        try:
            self.update_status("正在載入 yt-dlp...")
            import yt_dlp
            import requests
            
            self.update_status(f"搜尋中: {kw}")
            ydl_opts = {'quiet': True, 'extract_flat': True, 'ignoreerrors': True, 'nocheckcertificate': True}
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch10:{kw}", download=False)
                
            res = []
            if 'entries' in info:
                for e in info['entries']:
                    res.append({'title': e.get('title', 'No Title')})
            
            Clock.schedule_once(lambda dt: self.update_list(res))
            self.update_status("搜尋完成")
            
        except Exception as e:
            # 【關鍵】捕捉錯誤並顯示在畫面上
            err_msg = f"Error: {str(e)}\n{traceback.format_exc()}"
            self.update_status(err_msg)

    @mainthread
    def update_status(self, msg):
        self.status_text = msg

    @mainthread
    def update_list(self, data):
        self.root.ids.rv.data = data

# ==========================================
# 2. 這是防止閃退的最後一道防線
# ==========================================
if __name__ == '__main__':
    try:
        from kivy.properties import StringProperty
        import threading
        MusicPlayerApp().run()
    except Exception as e:
        # 如果真的發生毀滅性錯誤，這裡會嘗試顯示一個純文字視窗
        # 這樣您就能截圖告訴我錯在哪，而不是直接消失
        print(f"CRITICAL: {e}")
        try:
            from kivy.base import runTouchApp
            from kivy.uix.label import Label
            runTouchApp(Label(text=f"CRITICAL ERROR:\n{e}", color=(1,0,0,1)))
        except: pass
