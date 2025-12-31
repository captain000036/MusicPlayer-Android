[app]
# 應用程式名稱
title = MusicPlayer
package.name = musicplayer
package.domain = org.test
# 強制支援 64 位元架構 (現代手機必備)
android.archs = arm64-v8a

# 程式碼位置
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,otf

# 版本號
version = 0.2

# 【無敵全配版】
# 加入了所有可能的隱藏依賴：
# - pycryptodomex, brotli, certifi, websockets: yt_dlp 的隱藏需求
# - sqlite3, pyjnius: Android 系統互動需求
# - libffi, openssl, six: 底層通訊需求
# - pillow: 圖片處理需求
requirements = python3,kivy,cython==0.29.36,yt_dlp,requests,mutagen,openssl,libffi,six,sqlite3,pyjnius,pillow,certifi,pycryptodomex,brotli,websockets

# 顯示設定
orientation = portrait
fullscreen = 0

# Android 權限 (加入 WAKE_LOCK 防止下載時休眠斷線)
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,WAKE_LOCK,ACCESS_NETWORK_STATE

# Android API 設定 (維持 31 較穩定)
android.api = 31
android.minapi = 21
android.accept_sdk_license = True
android.entrypoint = org.kivy.android.PythonActivity

# 使用最新分支
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1

