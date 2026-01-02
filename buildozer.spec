[app]

# 1. 應用程式資訊
title = MusicPlayer
package.name = musicplayer
package.domain = org.test
source.dir = .
version = 1.1

# 【防閃退重點 1】副檔名設定
# 必須包含 otf 和 ttf，否則字體載入失敗會導致閃退
# 必須包含 json，以免某些庫讀取設定檔失敗
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,json

# 【防閃退重點 2】依賴庫大全 (Requirements)
# python3, kivy: 核心
# android: 系統呼叫
# yt-dlp: 下載功能
# mutagen: 音訊處理
# openssl, certifi: ⚠️ 缺這兩個，HTTPS 連線時會秒退
# ffpyplayer, ffpyplayer_codecs: ⚠️ 缺這兩個，SoundLoader 載入時會秒退
# libffi, pyjnius: ⚠️ 缺這兩個，呼叫 Java API 時會秒退
# requests, pillow: 常用輔助庫，加著保險
requirements = python3,kivy,android,yt-dlp,mutagen,openssl,certifi,ffpyplayer,ffpyplayer_codecs,libffi,pyjnius,requests,pillow

# 3. 顯示與方向
orientation = portrait
fullscreen = 0
# 讓鍵盤彈出時自動縮放視窗，避免遮擋
android.window_softinput_mode = resize

# 4. 權限設定 (網路 + 儲存 + 喚醒鎖)
# ⚠️ 缺 INTERNET 會導致網路功能閃退
android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,WAKE_LOCK

# 5. Android API 版本 (Google Play 標準)
# 建議設為 33 (Android 13)，相容性較好
android.api = 33
android.minapi = 21

# 6. 架構設定
# 目前 99% 手機都是 arm64-v8a
android.archs = arm64-v8a

# 7. 啟動設定
android.entrypoint = org.kivy.android.PythonActivity
android.accept_sdk_license = True

# 8. 白名單 (避免不必要的檔案被自動刪除)
# 這裡是空的，但保留欄位
android.whitelist =

# 9. 啟動圖 (若你有圖片可設定，沒有則註解掉)
# presplash.filename = %(source.dir)s/data/presplash.png
# icon.filename = %(source.dir)s/data/icon.png

[buildozer]

# Log 等級 (2 代表顯示詳細資訊，萬一失敗比較好找原因)
log_level = 2
warn_on_root = 1
