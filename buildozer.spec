[app]
# 1. 基本設定
title = MusicPlayer
package.name = musicplayer
package.domain = org.test
source.dir = .
version = 1.4

# 2. 資源
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,json

# 3. 依賴庫 (無 ffmpeg, 有 pyjnius)
requirements = python3,kivy,android,yt-dlp,mutagen,openssl,certifi,pyjnius,requests,pillow,sdl2_image

# 4. 顯示與權限
orientation = portrait
fullscreen = 0
# 【輸入法修正】確保視窗會縮放，避免鍵盤遮擋或卡死
android.window_softinput_mode = resize
android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,WAKE_LOCK

# 5. Android 版本
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.entrypoint = org.kivy.android.PythonActivity
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
