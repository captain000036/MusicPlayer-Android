[app]

# (1) 應用程式名稱與版本
title = MusicPlayer
package.name = musicplayer
package.domain = org.test
version = 1.3

# (2) 原始碼位置
source.dir = .

# (3) 【關鍵】資源副檔名
# 務必包含 otf, ttf (字體)、json (函式庫設定)
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,json

# (4) 【關鍵】依賴庫清單 (Requirements)
# -----------------------------------------------------------
# python3, kivy: 基礎核心
# android: 系統呼叫介面
# yt-dlp: 下載核心
# mutagen: 音訊處理
# openssl, certifi: ⚠️ 缺這兩個，HTTPS 連線時會閃退
# pyjnius: ⚠️ 缺這個，呼叫 Android 原生播放器時會閃退
# requests, pillow: 處理網路圖片
# sdl2_image: ⚠️ 缺這個，WebP 或特殊圖片格式顯示會失敗
# -----------------------------------------------------------
# 注意：已移除 ffpyplayer，避免崩潰
requirements = python3,kivy,android,yt-dlp,mutagen,openssl,certifi,pyjnius,requests,pillow,sdl2_image

# (5) 顯示設定
orientation = portrait
fullscreen = 0
# 【關鍵修正】讓鍵盤彈出時視窗自動縮放，解決輸入法卡住
android.window_softinput_mode = resize

# (6) 權限設定 (Permissions)
# INTERNET: 下載用
# WAKE_LOCK: 確保螢幕關閉時音樂繼續放
# STORAGE: 存取檔案用
android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,WAKE_LOCK

# (7) Android API 版本
# Target API 33 (Android 13)，符合 Google Play 標準
android.api = 33
# Min API 21 (Android 5.0)
android.minapi = 21

# (8) 架構設定
# 目前主流手機都是 arm64-v8a
android.archs = arm64-v8a

# (9) 啟動點設定
android.entrypoint = org.kivy.android.PythonActivity
android.accept_sdk_license = True

# (10) 白名單 (保持預設)
android.whitelist =

# (11) 啟動圖設定 (若無圖片請保持註解)
# icon.filename = %(source.dir)s/icon.png
# presplash.filename = %(source.dir)s/presplash.png

[buildozer]

# Log 等級 (2 = Debug)
log_level = 2
warn_on_root = 1
