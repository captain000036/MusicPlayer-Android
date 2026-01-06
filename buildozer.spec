[app]
title = MusicPlayer
package.name = musicplayer
package.domain = org.test
source.dir = .
version = 3.1

source.include_exts = py,png,jpg,kv,atlas,otf,ttf,json

# 【關鍵修正】
# 移除了 sqlite3 (解決秒閃退問題)
# 保留 requests (解決圖片下載)
requirements = python3,kivy,android,pyjnius,yt-dlp,requests,pillow,openssl,certifi,sdl2_image,libffi

orientation = portrait
fullscreen = 0
# 嘗試使用 adjustPan 解決輸入法遮擋
android.window_softinput_mode = adjustPan

android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,WAKE_LOCK

android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.entrypoint = org.kivy.android.PythonActivity
android.accept_sdk_license = True
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
