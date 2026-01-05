[app]
# (1) 應用程式名稱
title = MusicPlayer
package.name = musicplayer
package.domain = org.test
source.dir = .
version = 2.3

# (2) 資源副檔名
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,json

# (3) 【關鍵修正】依賴庫清單 (瘦身版)
# 移除了 cffi, brotli, sqlite3, pycryptodome (這些是導致秒退的元兇)
# 只保留最核心的庫，確保 App 能活著啟動
requirements = python3,kivy,android,pyjnius,yt-dlp,requests,pillow,openssl,certifi,sdl2_image

# (4) 顯示設定
orientation = portrait
fullscreen = 0
android.window_softinput_mode = resize

# (5) 權限設定
android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,WAKE_LOCK

# (6) Android API
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.entrypoint = org.kivy.android.PythonActivity
android.accept_sdk_license = True
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
