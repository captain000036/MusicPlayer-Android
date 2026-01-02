[app]
# 1. 基本資訊
title = MusicPlayer
package.name = musicplayer
package.domain = org.test
source.dir = .
version = 0.1

# 2. 檔案副檔名 (必須包含 otf)
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,json

# 3. 依賴庫 (Requirements) - 這是防閃退的核心
# 必須加入: openssl, certifi (防網路閃退)
# 必須加入: ffpyplayer, ffpyplayer_codecs (防音訊閃退)
requirements = python3,kivy,android,yt-dlp,mutagen,openssl,certifi,ffpyplayer,ffpyplayer_codecs,libffi,pyjnius,requests

# 4. 顯示設定
orientation = portrait
fullscreen = 0
android.window_softinput_mode = resize

# 5. 權限設定
android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,WAKE_LOCK

# 6. Android 版本
android.api = 33
android.minapi = 21
android.archs = arm64-v8a

# 7. 啟動點
android.entrypoint = org.kivy.android.PythonActivity
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
