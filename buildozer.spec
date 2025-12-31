[app]

# (1) 應用程式名稱與版本
title = MusicPlayer
package.name = musicplayer
package.domain = org.test
version = 0.4

# (2) 程式碼與資源位置
source.dir = .
# 【關鍵修正】這裡必須包含 otf, ttf (解決亂碼) 以及 json (若有設定檔)
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,json

# (3) 核心依賴庫 (Requirements)
# 【關鍵修正】
# 1. 加入 openssl, certifi -> 解決圖片顯示全黑、無法下載的問題 (HTTPS 支援)
# 2. 加入 pyjnius -> 讓你的 Python 可以呼叫 Android Java (MediaPlayer)
# 3. 加入 android -> 基礎依賴
# 4. 保留 cython 固定版本 -> 避免編譯失敗
requirements = python3,kivy,android,cython==0.29.36,yt-dlp,requests,mutagen,openssl,certifi,pyjnius,pillow

# (4) 顯示與方向
orientation = portrait
fullscreen = 0
# 【關鍵修正】解決鍵盤遮擋輸入框的問題
android.window_softinput_mode = resize

# (5) 權限設定 (Permissions)
# 包含網路、儲存讀寫、喚醒鎖(避免播歌時休眠)
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,WAKE_LOCK,ACCESS_NETWORK_STATE

# (6) Android API 設定
# 建議升級到 33 (Android 13)，相容性較好，minapi 21 支援到 Android 5.0
android.api = 33
android.minapi = 21
android.accept_sdk_license = True
android.entrypoint = org.kivy.android.PythonActivity

# (7) 架構設定
# 目前主流手機都是 arm64-v8a，若要支援舊手機可加上 armeabi-v7a
android.archs = arm64-v8a

# 使用最新分支
p4a.branch = master

# (8) 啟動圖與圖示 (若你有準備圖片，請取消註解並確認檔名)
# icon.filename = %(source.dir)s/icon.png
# presplash.filename = %(source.dir)s/presplash.png

[buildozer]

# Log 等級 (2 = Debug，打包失敗時可以看到詳細原因)
log_level = 2
warn_on_root = 1
