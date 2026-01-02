[app]
title = MusicPlayer
package.name = musicplayer
package.domain = org.test
source.dir = .
version = 1.2

# 1. 強制打包字體與圖片格式
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,json

# 2. 依賴庫 (移除 ffmpeg，加入 sdl2_image 解決圖片問題)
# requests, pillow: 處理圖片
# pyjnius: 處理原生播放器
requirements = python3,kivy,android,yt-dlp,mutagen,openssl,certifi,pyjnius,requests,pillow,sdl2_image

# 3. 介面設定
orientation = portrait
fullscreen = 0
# 【關鍵】解決輸入法無法切換的問題
android.window_softinput_mode = resize

# 4. 權限
android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,WAKE_LOCK

# 5. Android 設定
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.entrypoint = org.kivy.android.PythonActivity
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
