[app]
# (1) 應用程式名稱
title = MusicPlayer
package.name = musicplayer
package.domain = org.test
source.dir = .
version = 5.0

# (2) 檔案包含設定
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,json

# (3) 【黃金依賴組合】
# python3, kivy, android: 核心
# pyjnius: 播放器
# yt-dlp, requests: 下載功能
# pillow, sdl2_image: 【關鍵】介面渲染 (缺了這個會秒退)
# openssl, certifi: 網路安全
requirements = python3,kivy,android,pyjnius,yt-dlp,requests,pillow,openssl,certifi,sdl2_image,libffi

# (4) 顯示設定
orientation = portrait
fullscreen = 0
# 【關鍵】解決輸入法遮擋與切換問題
android.window_softinput_mode = adjustPan

# (5) 權限
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
