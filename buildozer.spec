[app]
title = SStats Football Analytics
package.name = sstats
package.domain = org.gizmolok
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,woff,woff2,json,csv,txt,xml,so,dll
source.include_patterns = assets/*,data/*,images/*,fonts/*,src/*
source.exclude_dirs = tests, bin, venv, .git, .github, __pycache__, .buildozer, build, dist

version = 10.2.0

requirements = python3,kivy==2.2.1,kivymd==1.1.1,pillow,numpy,pandas,requests,scikit-learn,scipy,urllib3,certifi,charset-normalizer,idna,joblib,threadpoolctl,python-dateutil,pytz,six,android,pyjnius

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# УБРАНО: android.sdk (deprecated)
# Используем только android.api
android.api = 33
android.minapi = 21
android.ndk_api = 21

android.private_storage = True
android.allow_backup = True
android.arch = armeabi-v7a,arm64-v8a

# Явно указываем пути (опционально, Buildozer должен найти автоматически)
# android.sdk_path = ~/.buildozer/android/platform/android-sdk
# android.ndk_path = ~/.buildozer/android/platform/android-ndk-r25b

p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
build_dir = ./.buildozer
bin_dir = ./bin
