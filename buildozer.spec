[app]

# 1. 基本資訊
title = MusicPlayer
package.name = musicplayer
package.domain = org.test
source.dir = .
version = 1.0

# 2. 【絕對關鍵】資源副檔名
# 一定要包含 otf, ttf，否則你的介面會全是亂碼
# 包含 json 是為了以防你有設定檔
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,json

# 3. 【核心依賴庫】(Requirements)
# python3, kivy: 基礎
# android: 系統呼叫
# yt-dlp: 下載核心
# openssl, certifi: 解決 HTTPS 連線失敗 (沒這個無法下載)
# ffpyplayer, ffpyplayer_codecs: 解決 SoundLoader 播放閃退或無聲 (Kivy 官方推薦)
# libffi, pyjnius: 處理 Android 權限路徑
requirements = python3,kivy,android,yt-dlp,mutagen,openssl,certifi,ffpyplayer,ffpyplayer_codecs,libffi,pyjnius,requests

# 4. 顯示設定
orientation = portrait
fullscreen = 0
# 【輸入法修正】讓鍵盤彈出時視窗會縮放，不會遮住輸入框
android.window_softinput_mode = resize

# 5. 權限設定 (網路 + 儲存 + 喚醒鎖)
android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,WAKE_LOCK

# 6. Android 版本設定 (Google Play 標準)
android.api = 33
android.minapi = 21
android.archs = arm64-v8a

# 7. 啟動點
android.entrypoint = org.kivy.android.PythonActivity
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
