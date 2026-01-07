[app]
# 應用程式名稱
title = MusicPlayer
package.name = musicplayer
package.domain = org.test

# 程式碼位置
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,otf

# 版本號
version = 0.1

# 【關鍵修正】加入 ffpyplayer, libffi, six 防止閃退
# 並且保留 cython==0.29.36 鎖定版本
requirements = python3,kivy,cython==0.29.36,yt_dlp,requests,mutagen,openssl,ffpyplayer,libffi,six

# 顯示設定
orientation = portrait
fullscreen = 0

# Android 權限
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# Android API 設定
android.api = 31
android.minapi = 21
android.accept_sdk_license = True
android.entrypoint = org.kivy.android.PythonActivity

# 分支設定
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
