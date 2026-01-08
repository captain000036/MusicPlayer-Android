[app]
title = MusicPlayer
package.name = musicplayer
package.domain = org.test
source.dir = .
version = 99.0

source.include_exts = py,png,jpg,kv,atlas,otf,ttf,json

# 【維持能開機的配置】
requirements = python3,kivy,android,pyjnius,yt-dlp,requests,openssl,certifi,sdl2_image,libffi

orientation = portrait
fullscreen = 0
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
