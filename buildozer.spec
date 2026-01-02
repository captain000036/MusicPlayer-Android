[app]

# (1) 應用程式名稱
title = MusicPlayer

# (2) 套件名稱 (請勿包含特殊符號)
package.name = musicplayer

# (3) 套件網域
package.domain = org.test

# (4) 原始碼路徑
source.dir = .

# (5) 來源副檔名 (務必包含 otf, ttf 以顯示中文)
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,json

# (6) 版本號
version = 0.1

# (7) 【關鍵修正】依賴庫清單
# ---------------------------------------------------------------------------
# python3, kivy: 基礎核心
# android: Android 系統呼叫
# yt-dlp: 下載功能
# mutagen: 音訊標籤處理
# openssl, certifi: ⚠️ 缺這兩個，HTTPS 連線下載時會閃退
# pyjnius: ⚠️ 缺這個，呼叫 Android 原生播放器時會閃退
# requests, pillow: 網路圖片處理
# sdl2_image: ⚠️ 缺這個，App 無法顯示 WebP/JPG 網路圖片
# libffi: 許多 Python 模組的底層依賴
# ---------------------------------------------------------------------------
# 注意：已移除 ffpyplayer，避免編譯失敗與執行閃退
requirements = python3,kivy,android,yt-dlp,mutagen,openssl,certifi,pyjnius,requests,pillow,sdl2_image,libffi

# (8) 顯示設定
orientation = portrait
fullscreen = 0

# (9) 【輸入法修正】讓鍵盤彈出時視窗自動縮放，解決無法切換中文的問題
android.window_softinput_mode = resize

# (10) Android 權限設定 (網路、儲存、喚醒鎖)
android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,WAKE_LOCK

# (11) Android API 版本 (符合 Google Play 規範)
android.api = 33
android.minapi = 21

# (12) 架構設定 (目前主流手機皆為 arm64-v8a)
android.archs = arm64-v8a

# (13) 啟動點設定
android.entrypoint = org.kivy.android.PythonActivity
android.accept_sdk_license = True

# (14) 白名單 (保持預設)
android.whitelist =

# (15) 啟動圖與圖示 (若無檔案請保持註解，若有請取消註解並確認路徑)
# icon.filename = %(source.dir)s/icon.png
# presplash.filename = %(source.dir)s/presplash.png

# (16) 使用 python-for-android 的 master 分支 (解決部分套件編譯問題)
p4a.branch = master

# (17) 額外的 Gradle 依賴 (通常不需要，保持空白)
# android.gradle_dependencies =

[buildozer]

# Log 等級 (2 代表顯示詳細資訊，方便除錯)
log_level = 2

# 在非專案根目錄執行時發出警告
warn_on_root = 1

# 指定 build 目錄 (通常保持預設)
# build_dir = ./.buildozer

# 指定 bin 目錄 (通常保持預設)
# bin_dir = ./bin
