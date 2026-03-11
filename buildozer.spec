[app]
title = SStats Football Analytics
package.name = sstats
package.domain = com.sstats
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,db,txt
version = 10.2.0
requirements = python3,kivy==2.2.1,kivymd==1.1.1,pillow,numpy,pandas,requests,scikit-learn,scipy,urllib3,certifi,charset-normalizer,idna,joblib,threadpoolctl,python-dateutil,pytz,six
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.gradle_dependencies = com.google.android.material:material:1.9.0

[buildozer]
log_level = 2
warn_on_root = 0
