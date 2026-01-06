[app]
title = MusicPlayer
package.name = musicplayer
package.domain = org.test
source.dir = .
version = 2.5

# 來源檔案 (確保包含 json 和字型)
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,json

# 依賴庫 (最穩定組合)
# 1. 核心: python3, kivy, android
# 2. 功能: yt-dlp, requests, pyjnius
# 3. 圖片: pillow, sdl2_image
# 4. 安全: openssl, certifi
# 5. 系統: sqlite3 (yt-dlp 依賴), libffi
requirements = python3,kivy,android,pyjnius,yt-dlp,requests,pillow,openssl,certifi,sdl2_image,libffi,sqlite3

# 顯示
orientation = portrait
fullscreen = 0
android.window_softinput_mode = resize

# 權限
android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,WAKE_LOCK

# API
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.entrypoint = org.kivy.android.PythonActivity
android.accept_sdk_license = True
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
