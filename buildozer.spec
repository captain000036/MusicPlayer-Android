[app]
# (1) 應用名稱
title = MusicPlayer
package.name = musicplayer
package.domain = org.test
source.dir = .
version = 9.0

# (2) 檔案包含
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,json

# (3) 【回歸完整依賴】
# 這是保證能「開啟 App」的最安全組合
# python3, kivy, android: 核心
# pyjnius: 播放器
# yt-dlp, requests: 下載
# pillow: 圖片處理 (必備！)
# openssl, certifi: 網路安全
# sqlite3: 資料庫 (yt-dlp 依賴)
requirements = python3,kivy,android,pyjnius,yt-dlp,requests,pillow,openssl,certifi,sqlite3,libffi

# (4) 顯示
orientation = portrait
fullscreen = 0
# 【輸入法解決方案】使用 adjustPan
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
