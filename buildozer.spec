[app]
# (1) App 名稱
title = MusicPlayer
package.name = musicplayer
package.domain = org.test
source.dir = .
version = 4.0

# (2) 檔案過濾
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,json

# (3) 【關鍵修正】依賴庫
# 必須包含 pillow, sdl2_image (否則 Kivy 無法啟動介面 -> 秒退)
# 必須包含 requests (下載圖片用)
# 移除 sqlite3 (避免系統衝突)
requirements = python3,kivy,android,pyjnius,yt-dlp,requests,pillow,openssl,certifi,sdl2_image,libffi

# (4) 顯示設定
orientation = portrait
fullscreen = 0
android.window_softinput_mode = adjustPan

# (5) 權限
android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,WAKE_LOCK

# (6) Android 設定
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.entrypoint = org.kivy.android.PythonActivity
android.accept_sdk_license = True
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
