[app]
title = FootStats Pro
package.name = footstatspro
package.domain = org.footstats
source.dir = ./android_app
source.include_exts = py,png,jpg,kv,atlas,ttf,json
version = 1.0.0
orientation = portrait
fullscreen = 0
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.arch = arm64-v8a
requirements = python3,kivy==2.2.1,requests,pillow,numpy
orientation = portrait
osx.python_version = 3
osx.kivy_version = 1.9.1
android.presplash_color = #0A0E1A
android.icon = ./assets/icon.png
android.presplash = ./assets/presplash.png
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.gradle_dependencies = com.android.support:support-compat:28.0.0
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
p4a.local_recipes = 
ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master
ios.ios_deploy_url = https://github.com/phonegap/ios-deploy
ios.ios_deploy_branch = 1.10.0
[buildozer]
log_level = 2
warn_on_root = 1
