[app]
title = MusicPlayer
package.name = musicplayer
package.domain = org.test
source.dir = .
version = 2.4

# 來源檔案
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,json

# 【依賴庫 - 防閃退終極版】
# 只包含絕對必要的：
# 1. 核心: python3, kivy, android
# 2. 播放: pyjnius (原生播放器)
# 3. 功能: yt-dlp, requests
# 4. 圖片: pillow, sdl2_image
# 5. SSL: openssl, certifi
requirements = python3,kivy,android,pyjnius,yt-dlp,requests,pillow,openssl,certifi,sdl2_image

# 顯示設定
orientation = portrait
fullscreen = 0
android.window_softinput_mode = resize

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
