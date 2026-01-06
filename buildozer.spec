[app]
title = MusicPlayer
package.name = musicplayer
package.domain = org.test
source.dir = .
version = 7.0

source.include_exts = py,png,jpg,kv,atlas,otf,ttf,json

# 【終極精簡清單】
# python3, kivy, android: 核心
# pyjnius: 播放器
# yt-dlp, requests: 下載功能
# sdl2_image: 圖片支援 (比 pillow 穩定)
# libffi: 系統依賴
# 注意：移除了 pillow 和 openssl 以防止啟動閃退
requirements = python3,kivy,android,pyjnius,yt-dlp,requests,sdl2_image,libffi

orientation = portrait
fullscreen = 0
# 【輸入法修正】
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
