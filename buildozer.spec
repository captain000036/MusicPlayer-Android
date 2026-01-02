[app]
title = MusicPlayer
package.name = musicplayer
package.domain = org.test

source.dir = .
source.include_exts = py,kv,otf,jpg,png

version = 1.0

requirements = python3,kivy,yt-dlp,requests,urllib3

orientation = portrait
fullscreen = 0

# ===== Android 權限 =====
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# ===== Android 穩定組合 =====
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a,armeabi-v7a

# ===== 關鍵設定 =====
android.allow_cleartext = True
android.add_compile_options = -DSDL_ENABLE_IME
android.logcat_filters = *:S python:D

[buildozer]
log_level = 2
warn_on_root = 0
