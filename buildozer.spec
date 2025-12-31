[app]
# 應用程式名稱
title = MusicPlayer
package.name = musicplayer
package.domain = org.test

# 程式碼位置
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,otf

# 版本號
version = 0.3

# 【關鍵修正 1】移除 brotli, pycryptodomex, websockets 這些會報錯的庫
# 只保留最核心、最純淨的依賴，解決 PyObject_GetBuffer 錯誤
requirements = python3,kivy,cython==0.29.36,yt_dlp,requests,mutagen,openssl,libffi,six,sqlite3,pyjnius,pillow,certifi

# 顯示設定
orientation = portrait
fullscreen = 0

# 【關鍵修正 2】解決輸入法無法切換、鍵盤遮擋問題
android.window_softinput_mode = resize

# Android 權限
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,WAKE_LOCK,ACCESS_NETWORK_STATE

# Android API 設定
android.api = 31
android.minapi = 21
android.accept_sdk_license = True
android.entrypoint = org.kivy.android.PythonActivity
android.archs = arm64-v8a

# 使用最新分支
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
