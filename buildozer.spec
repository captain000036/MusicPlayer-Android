[app]
# (1) 應用名稱
title = MusicPlayer
package.name = musicplayer
package.domain = org.test
source.dir = .
version = 70.0

# (2) 檔案包含
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,json

# (3) 【能開機的依賴清單】
# 絕對不加 pillow (會閃退)
# 絕對不加 sqlite3 (會閃退)
requirements = python3,kivy,android,pyjnius,yt-dlp,requests,openssl,certifi,sdl2_image,libffi

# (4) 顯示設定
orientation = portrait
fullscreen = 0
android.window_softinput_mode = adjustPan

# (5) 權限
android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,WAKE_LOCK

# (6) API
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.entrypoint = org.kivy.android.PythonActivity
android.accept_sdk_license = True
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
