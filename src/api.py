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

# Android-specific импорты
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
        self.min_delay = 0.2  # Минимальная задержка между запросами
        
        # Проверка разрешений на Android
        if ANDROID_AVAILABLE:
            self.check_permissions()
    
    def check_permissions(self):
        """Проверка разрешений на Android"""
        try:
            request_permissions([
                Permission.INTERNET,
                Permission.ACCESS_NETWORK_STATE
            ])
        except:
            pass
    
    def _rate_limit(self):
        """Rate limiting"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Выполнение запроса с обработкой ошибок"""
        self._rate_limit()
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        params['apikey'] = self.api_key
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            print(f"[API] Timeout: {endpoint}")
            return None
        except Exception as e:
            print(f"[API] Error {endpoint}: {e}")
            return None
    
    @cache_api_request(ttl_seconds=3600)
    def get_leagues(self) -> List[Dict]:
        """Получение списка лиг"""
        data = self._make_request("/leagues")
        return data.get('data', []) if data else []
    
    def get_all_matches_for_date(self, date: str, league_id: int = None) -> List[Dict]:
        """Получение матчей за дату"""
        all_matches = []
        offset = 0
        limit = 500  # Меньше для мобильных
        
        while True:
            params = {'limit': limit, 'offset': offset}
            if date:
                params['date'] = date
            if league_id:
                params['leagueid'] = league_id
            
            data = self._make_request("/games/list", params)
            
            if data is None:
                break
            if isinstance(data, list):
                matches = data
            else:
                matches = data.get('data', [])
            
            if not matches:
                break
            
            all_matches.extend(matches)
            
            if len(matches) < limit:
                break
            
            offset += limit
            if offset > 5000:  # Лимит для мобильных
                break
        
        return all_matches
    
    @cache_api_request(ttl_seconds=1800)
    def get_match_details(self, match_id) -> Optional[Dict]:
        """Детали матча"""
        data = self._make_request(f"/games/{match_id}")
        return data.get('data') if data else None
    
    @cache_api_request(ttl_seconds=900)
    def get_team_last_matches(self, team_id: int, limit: int = 10) -> List[Dict]:
        """Последние матчи команды"""
        params = {
            'team': team_id,
            'ended': 'true',
            'order': -1,
            'limit': limit
        }
        
        data = self._make_request('/games/list', params)
        if not data:
            return []
        
        matches = data.get('data', []) if isinstance(data, dict) else data
        return matches
    
    def extract_team_stats(self, match_data: Dict, team_id: int) -> Dict:
        """Извлечение статистики команды из матча"""
        stats = {
            'goals_for': 0, 'goals_against': 0,
            'xg_for': None, 'xg_against': None,
            'possession': 50, 'shots': 0, 'shots_on_target': 0,
            'corners': 0, 'date': match_data.get('date', ''),
            'opponent': '', 'is_home': False, 'result': ''
        }
        
        home_team = match_data.get('homeTeam', {}) or {}
        away_team = match_data.get('awayTeam', {}) or {}
        
        if not isinstance(home_team, dict) or not isinstance(away_team, dict):
            return stats
        
        home_id = home_team.get('id')
        away_id = away_team.get('id')
        
        if home_id == team_id:
            stats['is_home'] = True
            stats['opponent'] = away_team.get('name', 'Unknown')
            stats['goals_for'] = match_data.get('homeResult', 0) or 0
            stats['goals_against'] = match_data.get('awayResult', 0) or 0
        elif away_id == team_id:
            stats['is_home'] = False
            stats['opponent'] = home_team.get('name', 'Unknown')
            stats['goals_for'] = match_data.get('awayResult', 0) or 0
            stats['goals_against'] = match_data.get('homeResult', 0) or 0
        else:
            return stats
        
        # Результат
        if stats['goals_for'] > stats['goals_against']:
            stats['result'] = 'W'
        elif stats['goals_for'] < stats['goals_against']:
            stats['result'] = 'L'
        else:
            stats['result'] = 'D'
        
        # xG
        xg_data = match_data.get('xg', {})
        if isinstance(xg_data, dict):
            if stats['is_home']:
                stats['xg_for'] = xg_data.get('home')
                stats['xg_against'] = xg_data.get('away')
            else:
                stats['xg_for'] = xg_data.get('away')
                stats['xg_against'] = xg_data.get('home')
        
        # Статистика
        stats_data = match_data.get('statistics', {})
        if isinstance(stats_data, dict):
            prefix = 'Home' if stats['is_home'] else 'Away'
            
            for key in ['ballPossession', 'totalShots', 'shotsOnGoal', 'cornerKicks']:
                full_key = f'{key}{prefix}'
                if full_key in stats_data:
                    try:
                        if key == 'ballPossession':
                            stats['possession'] = float(stats_data[full_key])
                        elif key == 'totalShots':
                            stats['shots'] = int(stats_data[full_key])
                        elif key == 'shotsOnGoal':
                            stats['shots_on_target'] = int(stats_data[full_key])
                        elif key == 'cornerKicks':
                            stats['corners'] = int(stats_data[full_key])
                    except:
                        pass
        
        return stats
    
    def get_team_full_stats(self, team_id: int, team_name: str = "") -> Dict:
        """Полная статистика команды"""
        try:
            matches = self.get_team_last_matches(team_id, limit=10)
        except Exception as e:
            print(f"[API] Error getting matches: {e}")
            matches = []
        
        if not matches:
            return {
                'matches': [],
                'team_id': team_id,
                'team_name': team_name,
                'total_matches': 0,
                'has_data': False
            }
        
        stats_list = []
        for match in matches:
            try:
                # Получаем детали если нужно
                if 'statistics' not in match:
                    details = self.get_match_details(match.get('id'))
                    if details:
                        match.update(details)
                
                match_stats = self.extract_team_stats(match, team_id)
                if match_stats.get('result'):
                    stats_list.append(match_stats)
            except Exception as e:
                continue
        
        return {
            'matches': stats_list,
            'team_id': team_id,
            'team_name': team_name,
            'total_matches': len(stats_list),
            'has_data': len(stats_list) > 0
        }
    
    @cache_api_request(ttl_seconds=3600)
    def get_head_to_head(self, team1_id: int, team2_id: int, limit: int = 5) -> Optional[Dict]:
        """Личные встречи"""
        params = {
            'team1': team1_id,
            'team2': team2_id,
            'ended': 'true',
            'limit': limit
        }
        
        data = self._make_request('/games/headtohead', params)
        matches = data.get('data', []) if data else []
        
        if not matches:
            return None
        
        team1_wins = team2_wins = draws = 0
        total_goals = 0
        
        for match in matches:
            home_res = match.get('homeResult', 0) or 0
            away_res = match.get('awayResult', 0) or 0
            home_id = (match.get('homeTeam') or {}).get('id')
            
            if home_res == away_res:
                draws += 1
            elif (home_res > away_res and home_id == team1_id) or \
                 (away_res > home_res and home_id != team1_id):
                team1_wins += 1
            else:
                team2_wins += 1
            
            total_goals += home_res + away_res
        
        return {
            'matches': matches,
            'team1_wins': team1_wins,
            'team2_wins': team2_wins,
            'draws': draws,
            'total_matches': len(matches),
            'avg_goals': total_goals / len(matches) if matches else 0
        }
    
    def update_matches_results_for_date(self, date_str: str, league_id: Optional[int] = None):
        """Обновление результатов"""
        from src.database import MobileDatabase
        db = MobileDatabase()
        
        try:
            matches = self.get_all_matches_for_date(date_str, league_id)
            updated = db.auto_update_finished_matches(matches)
            return updated
        except Exception as e:
            print(f"[API] Update error: {e}")
            return 0
