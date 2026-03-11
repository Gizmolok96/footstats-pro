"""
Оптимизированный API клиент для мобильных устройств
"""

import time
import json
import hashlib
import functools
import threading
from datetime import datetime
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

# Android-specific импорты - откладываем до runtime
ANDROID_AVAILABLE = False
Permission = None
request_permissions = None
autoclass = None

def init_android():
    global ANDROID_AVAILABLE, Permission, request_permissions, autoclass
    try:
        from android.permissions import request_permissions, Permission
        from jnius import autoclass
        ANDROID_AVAILABLE = True
    except ImportError:
        ANDROID_AVAILABLE = False


SSTATS_API_KEY = "gbi1ldi9446kastj"
SSTATS_BASE_URL = "https://api.sstats.net"

HEADERS = {
    "User-Agent": "SStats-Mobile-App/10.2",
    "Accept": "application/json"
}


def cache_api_request(ttl_seconds=1800):
    """Декоратор для кэширования"""
    cache = {}
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = hashlib.md5(
                f"{func.__name__}:{str(args)}:{str(kwargs)}".encode()
            ).hexdigest()
            
            now = time.time()
            
            if key in cache:
                result, timestamp = cache[key]
                if now - timestamp < ttl_seconds:
                    return result
            
            result = func(*args, **kwargs)
            cache[key] = (result, now)
            return result
        
        wrapper.clear_cache = lambda: cache.clear()
        return wrapper
    return decorator


class SStatsAPI:
    """API клиент с оптимизациями для мобильных"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = SSTATS_BASE_URL
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.last_request_time = 0
        self.min_delay = 0.2
        
        # Инициализация Android при необходимости
        init_android()
        if ANDROID_AVAILABLE:
            self.check_permissions()
    
    def check_permissions(self):
        """Проверка разрешений на Android"""
        if not ANDROID_AVAILABLE:
            return
        try:
            request_permissions([
                Permission.INTERNET,
                Permission.ACCESS_NETWORK_STATE
            ])
        except:
            pass
    
    # ... остальной код api.py без изменений ...
