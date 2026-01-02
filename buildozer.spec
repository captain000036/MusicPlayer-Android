[app]

# (1) 應用程式名稱
title = MusicPlayer

# (2) 套件名稱 (建議全小寫，不要有特殊符號)
package.name = musicplayer

# (3) 網域
package.domain = org.test

# (4) 原始碼路徑
source.dir = .

# (5) 【關鍵】來源副檔名
# 務必包含 otf, ttf (解決亂碼)
# 務必包含 json (部分套件需要)
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,json

# (6) 版本號
version = 1.6

# (7) 【關鍵】依賴庫清單 (Requirements)
# ---------------------------------------------------------------------------
# python3, kivy: 核心
# android: 系統呼叫
# yt-dlp: 下載核心
# mutagen: 音訊標籤處理
# openssl, certifi: ⚠️ 缺這兩個，HTTPS 下載會閃退
# pyjnius: ⚠️ 缺這個，呼叫 Android 原生播放器會閃退
# requests, pillow: 處理網路圖片
# sdl2_image: ⚠️ 缺這個，WebP/JPG 圖片顯示會失敗
# libffi: 底層依賴
# ---------------------------------------------------------------------------
# 絕對不要加 ffpyplayer 或 ffmpeg，會跟系統打架導致閃退
requirements = python3,kivy,android,yt-dlp,mutagen,openssl,certifi,pyjnius,requests,pillow,sdl2_image,libffi

# (8) 顯示設定
orientation = portrait
fullscreen = 0

# (9) 【輸入法修正】
# 設定為 resize，讓鍵盤彈出時視窗自動縮放，解決輸入法卡住無法切換的問題
android.window_softinput_mode = resize

# (10) Android 權限 (Permissions)
# INTERNET: 聯網搜歌
# WAKE_LOCK: 確保播歌時螢幕關閉不中斷
# STORAGE: 存取下載的檔案
android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,WAKE_LOCK

# (11) Android API 版本 (符合 Google Play 標準)
android.api = 33
android.minapi = 21

# (12) 架構設定 (目前主流手機皆為 arm64-v8a)
android.archs = arm64-v8a

# (13) 啟動點設定
android.entrypoint = org.kivy.android.PythonActivity
android.accept_sdk_license = True

# (14) 白名單 (保持預設)
android.whitelist =

# (15) 啟動圖與圖示 (若您沒有準備圖片，請保持註解，避免打包錯誤)
# icon.filename = %(source.dir)s/icon.png
# presplash.filename = %(source.dir)s/presplash.png

# (16) 使用 master 分支 (解決部分編譯相容性問題)
p4a.branch = master

[buildozer]

# Log 等級 (2 = Debug，顯示詳細錯誤資訊)
log_level = 2

# 在非專案根目錄執行時警告
warn_on_root = 1
