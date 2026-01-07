[app]
title = MusicPlayer
package.name = musicplayer
package.domain = org.test
source.dir = .
version = 11.0

# 檔案過濾
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,json

# 【黃金組合依賴】
# 1. pillow: 必備！(Kivy 啟動核心，剛剛缺了這個才秒退)
# 2. requests, openssl: 下載功能
# 3. pyjnius: 播放功能
# 4. 移除了 sqlite3, sdl2_image (減少變數，只用最標準的 pillow)
requirements = python3,kivy==2.3.0,android,pyjnius,yt-dlp,requests,pillow,openssl,certifi,libffi

# 顯示設定
orientation = portrait
fullscreen = 0
android.window_softinput_mode = adjustPan

# 權限
android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,WAKE_LOCK

# API
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.entrypoint = org.kivy.android.PythonActivity
android.accept_sdk_license = True
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
