[app]
# (1) 應用名稱
title = MusicPlayer
package.name = musicplayer
package.domain = org.test
source.dir = .
version = 40.0

# (2) 檔案包含
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,json

# (3) 【成功驗證過的清單】
# 這是您上次成功進入畫面的配置
# 移除了 pillow (防閃退)
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
