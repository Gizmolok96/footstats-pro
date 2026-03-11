#!/usr/bin/env python3
"""
SStats Football Analytics Pro - Android Edition
Powered by KivyMD + Material Design 3
"""

__version__ = "10.2.0"

import os
import sys

# Настройка путей для Android
if hasattr(sys, '_MEIPASS'):
    os.chdir(sys._MEIPASS)
elif 'ANDROID_STORAGE' in os.environ:
    # Android-specific paths
    os.environ['KIVY_HOME'] = os.path.join(os.environ['ANDROID_STORAGE'], 'sstats')

# Добавляем текущую директорию в путь для импортов src
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import SStatsApp

if __name__ == '__main__':
    SStatsApp().run()
