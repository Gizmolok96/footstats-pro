[app]
# (str) Title of your application
title = sstats_android

# (str) Package name
package.name = sstats

# (str) Package domain (needed for android/ios packaging)
package.domain = org.gizmolok

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,ttf,woff,woff2,json,csv,txt,xml

# (list) List of inclusions using pattern matching
source.include_patterns = assets/*,data/*,images/*,fonts/*

# (list) Source files to exclude (let empty to not exclude anything)
source.exclude_exts = spec,log,gitignore

# (list) List of directory to exclude (let empty to not exclude anything)
source.exclude_dirs = tests, bin, venv, .git, .github, __pycache__, .buildozer

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements
# Добавлены kivy и зависимости явно
requirements = python3,kivy==2.2.1,android,pyjnius,requests,urllib3,chardet,certifi,idna

# (str) Presplash of the application
presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (list) List of service to declare
#services = NAME:ENTRYPOINT_TO_PY,NAME2:ENTRYPOINT2_TO_PY

#
# Android specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# (list) features (adds uses-feature -tags to manifest)
#android.features = android.hardware.usb.host

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK / AAB will support.
android.minapi = 21

# (int) Android SDK version to use
android.sdk = 33

# (str) Android NDK version to use
android.ndk = 25b

# (int) Android NDK API to use. This is the minimum API your app will support.
android.ndk_api = 21

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (str) Android entry point, default is ok for Kivy-based app
#android.entrypoint = org.kivy.android.PythonActivity

# (list) Pattern to whitelist for the whole project directory
#android.whitelist =

# (bool) If True, then skip trying to run android.py internally
android.skip_update = False

# (str) The format used to package the app for release mode (aab or apk or aar).
# android.release_artifact = aab

# (str) The format used to package the app for debug mode (apk or aar).
android.debug_artifact = apk

# (int) overrides automatic versionCode computation (used in build.gradle)
# this is not the same as app version and should only be edited if you know what you're doing
# android.numeric_version = 1

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (str) XML file for custom backup rules (see official auto backup documentation)
# android.backup_rules =

# (str) If you need to insert variables into your AndroidManifest.xml file,
# you can do so with the manifest_placeholders property.
# This property takes a map of key-value pairs. (via a string)
# Usage example : android.manifest_placeholders = [my_custom_url=https://github.com/kivy]
# android.manifest_placeholders = [:]

# (bool) disables the compilation of py to pyc/pyo files when packaging
# android.no-compile-pyo = True

# (str) The directory where python-for-android is cloned and built
# p4a.local_recipes =

# (str) The filename or url for the main python-for-android checkout to use
# p4a.fork = kivy
# p4a.branch = master

# (str) The filename or url for any python-for-android fork to use
# p4a.fork =

# (str) The filename or url for any python-for-android branch to use
# p4a.branch = develop

# (str) python-for-android specific commit to use
# p4a.commit =

# (str) python-for-android git clone directory (if empty, it will be automatically cloned from github)
#p4a.source_dir =

# (str) The bootstrap to use. Defaults tosdl2
# p4a.bootstrap = sdl2

# (int) port number to specify an explicit --port= p4a argument (eg for bootstrap flask/webview etc)
# p4a.port =

# Control passing the --use-setup-py vs --ignore-setup-py to p4a
# In the past, p4a hardcoded to ignore setup.py when building a hostpython recipe
# "in the future" p4a will use setup.py by default for all recipes
# p4a.setup_py = false

# (str) extra command line arguments to pass when invoking p4a
# p4a.extra_args =

#
# iOS specific
#

# (str) Path to a custom kivy-ios folder
#ios.kivy_ios_dir = ../kivy-ios

# Alternately, specify the URL and branch of a git checkout:
ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master

# Another platform dependency: ios-deploy
# Uncomment to use a custom checkout
#ios.ios_deploy_dir = ../ios_deploy
ios.ios_deploy_url = https://github.com/phonegap/ios-deploy
ios.ios_deploy_branch = 1.10.0

# (bool) Whether or not to sign the code
ios.codesign.allowed = false

# (str) Name of the certificate to use for signing the debug version
# Get a list of available identities: buildozer ios list_identities
#ios.codesign.debug = "iPhone Developer: <lastname> <firstname> (<hexstring>)"

# (str) The development team to use for signing the release version
#ios.codesign.development_team.debug = <hexstring>

#
# Buildozer specific
#

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage, absolute or relative to spec file
build_dir = ./.buildozer

# (str) Path to build output (i.e. .apk, .aab, .ipa) storage
bin_dir = ./bin

# (str) Path to the buildozer spec file, absolute or relative to spec file
# buildozer.spec = ./buildozer.spec

# (str) Default command to run when invoking buildozer without arguments
# default_command = android debug

# (str) Path to a custom buildozer binary
# buildozer.binary =

# (bool) Use a prebuild python-for-android clone
# p4a.local_recipes =

# (str) Bootstrap to use for android builds (sdl2, webview, service_only)
# android.bootstrap = sdl2

# (list) Add java classes to the project
# android.add_libs =

# (str) Gradle version to use
# android.gradle_version = 7.4.2

# (str) Gradle plugin version to use
# android.gradle_plugin_version = 7.3.1

# (bool) Use a private fork of python-for-android
# p4a.fork =
