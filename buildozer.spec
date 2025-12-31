[app]
title = MusicPlayer
package.name = musicplayer
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,otf

version = 0.1

# 【終極修正】加入 sqlite3, pyjnius, pillow 防止底層崩潰
requirements = python3,kivy,cython==0.29.36,yt_dlp,requests,mutagen,openssl,ffpyplayer,libffi,six,sqlite3,pyjnius,pillow

orientation = portrait
fullscreen = 0
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,WAKE_LOCK
android.api = 31
android.minapi = 21
android.accept_sdk_license = True
android.entrypoint = org.kivy.android.PythonActivity
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
