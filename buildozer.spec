[app]
title = SStats Football Analytics
package.name = sstats
package.domain = org.gizmolok
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,woff,woff2,json,csv,txt,xml
source.include_patterns = assets/*,data/*,images/*,fonts/*
source.exclude_exts = spec,log,gitignore
source.exclude_dirs = tests,bin,venv,.git,.github,__pycache__,.buildozer
version = 10.2.0

# ИСПРАВЛЕНО: Убран deprecated android.sdk, используем только android.api
requirements = python3,kivy==2.2.1,kivymd==1.1.1,pillow,numpy,pandas,requests,urllib3,certifi,charset-normalizer,idna,python-dateutil,pytz,six,scipy

orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_NETWORK_STATE

# API levels (android.sdk удален — он deprecated)
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21

# Дополнительные настройки Android
android.private_storage = True
android.skip_update = False
android.debug_artifact = apk
android.allow_backup = True

# Размеры памяти для сборки (важно для GitHub Actions)
android.gradle_options = org.gradle.jvmargs=-Xmx4096m
android.add_gradle_repositories = mavenCentral(),google()

# Иконки и пресплэш (если есть)
# android.presplash = 
# android.icon = 

[buildozer]
log_level = 2
warn_on_root = 1
build_dir = ./.buildozer
bin_dir = ./bin
