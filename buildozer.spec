[app]
# (1) 應用名稱
title = MusicPlayer
package.name = musicplayer
package.domain = org.test
source.dir = .
# 【關鍵】版本號大跳躍，強制覆蓋舊版
version = 20.0

# (2) 檔案包含
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,json

# (3) 【成功啟動版依賴】
# 這是您上次成功看到 JOLIN 畫面時的配置
# 移除了 pillow (它是閃退元兇)
# 保留 sdl2_image (用來顯示圖片)
# 保留 requests (用來下載圖片)
requirements = python3,kivy,android,pyjnius,yt-dlp,requests,openssl,certifi,sdl2_image,libffi

# (4) 顯示設定
orientation = portrait
fullscreen = 0
# 【輸入法修正】
android.window_softinput_mode = adjustPan

# (5) 權限
android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,WAKE_LOCK

# (6) API
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.entrypoint = org.kivy.android.PythonActivity
android.accept_sdk_license = True
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
