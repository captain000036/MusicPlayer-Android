[app]
# 應用名稱
title = MusicPlayer
package.name = musicplayer
package.domain = org.test
source.dir = .
version = 8.0

# 檔案過濾
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,json

# 【關鍵依賴 - 輕量穩定版】
# 1. 移除了 pillow (解決啟動秒退)
# 2. 移除了 sqlite3 (解決系統衝突)
# 3. 保留 sdl2_image (顯示圖片)
# 4. 保留 requests, openssl (下載功能)
requirements = python3,kivy,android,pyjnius,yt-dlp,requests,openssl,certifi,sdl2_image,libffi

# 顯示設定
orientation = portrait
fullscreen = 0
# 【輸入法修正】
android.window_softinput_mode = adjustPan

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
