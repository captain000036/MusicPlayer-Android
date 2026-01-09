[app]
title = MusicPlayer
package.name = musicplayer
package.domain = org.test
source.dir = .
version = 999.0

# 檔案過濾
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,json

# 【極簡依賴】
# 移除所有可能導致衝突的庫，只留最核心的
requirements = python3,kivy,android,pyjnius,yt-dlp,requests,openssl,certifi,sdl2_image,libffi

orientation = portrait
fullscreen = 0
android.window_softinput_mode = adjustPan

# 權限 (雖然寫了，但我們改用私有目錄，不太依賴這些了)
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK

android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.entrypoint = org.kivy.android.PythonActivity
android.accept_sdk_license = True
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
