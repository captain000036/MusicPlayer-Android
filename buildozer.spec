[app]
# (1) 應用程式名稱
title = MusicPlayer
package.name = musicplayer
package.domain = org.test
source.dir = .
version = 14.0

# (2) 檔案過濾
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,json

# (3) 【回歸原廠依賴】
# 只列出我們 Python 程式碼裡有 "import" 到的東西
# python3, kivy, android: 基礎
# pyjnius: 播放器用
# yt-dlp: 搜歌用
# requests: 下載圖片用
# pillow: 顯示介面用 (Buildozer 會自動處理它需要的底層依賴)
requirements = python3,kivy,android,pyjnius,yt-dlp,requests,pillow

# (4) 顯示設定
orientation = portrait
fullscreen = 0
# 【輸入法修正】
android.window_softinput_mode = adjustPan

# (5) 權限 (針對 Android 13 優化)
android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,WAKE_LOCK

# (6) API 設定
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.entrypoint = org.kivy.android.PythonActivity
android.accept_sdk_license = True

# (7) 系統優化
# 啟用 AndroidX (現代 Android 必備)
android.enable_androidx = True
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
