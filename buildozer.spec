[app]
title = MusicPlayer
package.name = musicplayer
package.domain = org.test
source.dir = .
version = 2.2

# 檔案過濾
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,json

# 【關鍵修正】依賴庫清單
# 移除了 sqlite3 (避免系統衝突導致秒退)
# 移除了 pycryptodome (避免編譯錯誤)
# 加入了 cffi, brotli (yt-dlp 網路依賴)
requirements = python3,kivy,android,yt-dlp,mutagen,openssl,certifi,pyjnius,requests,pillow,sdl2_image,libffi,cffi,brotli

# 顯示設定
orientation = portrait
fullscreen = 0
android.window_softinput_mode = resize

# 權限
android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,WAKE_LOCK

# Android 設定
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.entrypoint = org.kivy.android.PythonActivity
android.accept_sdk_license = True
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
