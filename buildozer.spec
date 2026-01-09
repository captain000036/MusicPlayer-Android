[app]

# (1) 應用程式名稱與版本
title = MusicPlayer
package.name = musicplayer
package.domain = org.test
version = 1.0

# (2) 原始碼路徑
source.dir = .

# (3) 【關鍵】資源副檔名
# 務必包含 otf, ttf，否則字體載入失敗會導致閃退
# 務必包含 json，某些函式庫需要
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,json

# (4) 【關鍵】依賴庫清單 (Requirements)
# -----------------------------------------------------------
# python3, kivy: 基礎核心
# android: 系統呼叫介面
# yt-dlp: 下載音樂核心
# mutagen: 音訊處理 (yt-dlp 依賴)
# openssl, certifi: ⚠️ 缺這兩個，HTTPS 連線時會閃退
# pyjnius: ⚠️ 缺這個，呼叫 Android 原生播放器時會閃退
# requests, pillow: 網路請求與圖片處理
# libffi: 許多 Python 套件的基礎依賴
# -----------------------------------------------------------
# 注意：這裡已經移除了 ffpyplayer，因為我們改用原生播放器了
requirements = python3,kivy,android,yt-dlp,mutagen,openssl,certifi,pyjnius,requests,pillow,libffi

# (5) 顯示設定
orientation = portrait
fullscreen = 0
# 讓鍵盤彈出時視窗自動縮放，不會遮住輸入框
android.window_softinput_mode = resize

# (6) 權限設定 (Permissions)
# INTERNET: 下載用
# WAKE_LOCK: 確保螢幕關閉時音樂繼續放
# STORAGE: 存取檔案用
android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,WAKE_LOCK

# (7) Android API 版本
# Target API 33 (Android 13)，符合 Google Play 標準
android.api = 33
# Min API 21 (Android 5.0)，支援絕大多數舊手機
android.minapi = 21

# (8) 架構設定
# 目前主流手機都是 arm64-v8a
android.archs = arm64-v8a

# (9) 啟動點設定 (標準 Kivy 啟動)
android.entrypoint = org.kivy.android.PythonActivity
android.accept_sdk_license = True

# (10) 其他設定
# 開啟 Logcat 顯示，方便除錯
android.logcat_filters = *:S python:D

# 啟動圖設定 (如果你沒有圖片，請保持註解狀態)
# icon.filename = %(source.dir)s/icon.png
# presplash.filename = %(source.dir)s/presplash.png

[buildozer]

# Log 等級 (2 = Debug)
log_level = 2
warn_on_root = 1
