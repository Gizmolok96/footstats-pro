"""
Мобильная база данных SQLite с оптимизацией для Android
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict

# Android-specific пути
def get_db_path():
    """Получить путь к БД в зависимости от платформы"""
    if 'ANDROID_STORAGE' in os.environ:
        # Android: используем private app storage
        base_dir = os.path.join(os.environ['ANDROID_STORAGE'], 'Android', 'data', 'com.sstats.app', 'files')
        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, 'sstats_mobile.db')
    else:
        # Desktop: стандартный путь
        home = Path.home()
        db_dir = home / ".sstats_mobile"
        db_dir.mkdir(parents=True, exist_ok=True)
        return str(db_dir / "football_mobile.db")


@dataclass
class TeamFeatures:
    """Оптимизированная структура признаков для мобильной версии"""
    points_per_game: float = 1.0
    win_rate: float = 0.33
    draw_rate: float = 0.33
    loss_rate: float = 0.34
    avg_goals_for: float = 1.3
    avg_shots: float = 12.0
    avg_shots_on_target: float = 4.0
    finishing_efficiency: float = 1.0
    xg_for_avg: float = 1.3
    avg_goals_against: float = 1.3
    xg_against_avg: float = 1.3
    defensive_efficiency: float = 1.0
    avg_possession: float = 50.0
    avg_corners: float = 5.0
    recent_points: float = 7.0
    recent_goals_for: float = 6.5
    recent_goals_against: float = 6.5
    trend: float = 0.0
    home_advantage: float = 1.0
    away_disadvantage: float = 1.0
    
    def to_list(self) -> List[float]:
        return [
            self.points_per_game, self.win_rate, self.draw_rate, self.loss_rate,
            self.avg_goals_for, self.avg_shots, self.avg_shots_on_target,
            self.finishing_efficiency, self.xg_for_avg, self.avg_goals_against,
            self.xg_against_avg, self.defensive_efficiency, self.avg_possession,
            self.avg_corners, self.recent_points, self.recent_goals_for,
            self.recent_goals_against, self.trend, self.home_advantage,
            self.away_disadvantage
        ]


@dataclass
class MatchFeatures:
    """Оптимизированные признаки матча"""
    home: TeamFeatures
    away: TeamFeatures
    h2h_home_wins: int = 0
    h2h_draws: int = 0
    h2h_away_wins: int = 0
    h2h_avg_goals: float = 2.5
    league_avg_goals: float = 2.5
    league_home_advantage: float = 1.4
    
    def to_list(self) -> List[float]:
        features = []
        features.extend(self.home.to_list())
        features.extend(self.away.to_list())
        total_h2h = max(self.h2h_home_wins + self.h2h_draws + self.h2h_away_wins, 1)
        features.extend([
            self.h2h_home_wins / total_h2h,
            self.h2h_draws / total_h2h,
            self.h2h_away_wins / total_h2h,
            self.h2h_avg_goals,
            self.league_avg_goals,
            self.league_home_advantage
        ])
        return features
    
    def to_dict(self) -> Dict:
        return {
            'home_features': asdict(self.home),
            'away_features': asdict(self.away),
            'h2h_home_wins': self.h2h_home_wins,
            'h2h_draws': self.h2h_draws,
            'h2h_away_wins': self.h2h_away_wins,
            'h2h_avg_goals': self.h2h_avg_goals,
            'league_avg_goals': self.league_avg_goals,
            'league_home_advantage': self.league_home_advantage,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MatchFeatures':
        home = TeamFeatures(**data['home_features'])
        away = TeamFeatures(**data['away_features'])
        return cls(
            home=home, away=away,
            h2h_home_wins=data.get('h2h_home_wins', 0),
            h2h_draws=data.get('h2h_draws', 0),
            h2h_away_wins=data.get('h2h_away_wins', 0),
            h2h_avg_goals=data.get('h2h_avg_goals', 2.5),
            league_avg_goals=data.get('league_avg_goals', 2.5),
            league_home_advantage=data.get('league_home_advantage', 1.4),
        )


class MobileDatabase:
    """Оптимизированная мобильная БД"""
    
    def __init__(self):
        self.db_path = get_db_path()
        self.init_db()
    
    def init_db(self):
        """Инициализация таблиц"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица матчей (кэш)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY,
                sstats_id INTEGER UNIQUE,
                date TEXT,
                home_team TEXT,
                away_team TEXT,
                home_team_id INTEGER,
                away_team_id INTEGER,
                league TEXT,
                league_id INTEGER,
                status TEXT,
                home_goals INTEGER,
                away_goals INTEGER,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица истории прогнозов (компактная)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prediction_history (
                id INTEGER PRIMARY KEY,
                match_id INTEGER,
                home_team TEXT,
                away_team TEXT,
                match_date TEXT,
                features_json TEXT,
                predicted_home_win REAL,
                predicted_draw REAL,
                predicted_away_win REAL,
                predicted_score TEXT,
                ml_predicted_class INTEGER,
                ml_confidence REAL,
                actual_home_goals INTEGER,
                actual_away_goals INTEGER,
                actual_result TEXT,
                prediction_correct BOOLEAN,
                model_version TEXT DEFAULT 'mobile_v1',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP
            )
        """)
        
        # Индексы для производительности
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_predictions_date 
            ON prediction_history(created_at DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_predictions_result 
            ON prediction_history(actual_result) WHERE actual_result IS NOT NULL
        """)
        
        conn.commit()
        conn.close()
    
    def execute(self, query: str, params: tuple = ()) -> List:
        """Выполнить запрос"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchall()
        conn.commit()
        conn.close()
        return [dict(row) for row in result]
    
    def save_prediction_with_features(self, match_data: Dict, analysis: Dict,
                                      features: MatchFeatures, ml_prediction: Optional[Dict]):
        """Сохранить прогноз с признаками"""
        home_team = match_data.get('homeTeam', {}) or {}
        away_team = match_data.get('awayTeam', {}) or {}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        probs = analysis['probabilities']
        
        ml_class = None
        ml_conf = None
        if ml_prediction:
            probs_list = [ml_prediction['draw'], ml_prediction['home_win'], ml_prediction['away_win']]
            ml_class = probs_list.index(max(probs_list))
            ml_conf = ml_prediction['confidence']
        
        cursor.execute("""
            INSERT INTO prediction_history 
            (match_id, home_team, away_team, match_date, features_json,
             predicted_home_win, predicted_draw, predicted_away_win, predicted_score,
             ml_predicted_class, ml_confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            match_data.get('id'),
            home_team.get('name', 'Unknown'),
            away_team.get('name', 'Unknown'),
            match_data.get('date'),
            json.dumps(features.to_dict(), ensure_ascii=False),
            probs['home_win'],
            probs['draw'],
            probs['away_win'],
            probs['most_likely_score'],
            ml_class,
            ml_conf
        ))
        
        conn.commit()
        conn.close()
    
    def get_training_data(self, min_confidence: float = 0.0) -> List[Dict]:
        """Получить данные для обучения"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM prediction_history 
            WHERE actual_result IS NOT NULL
            AND features_json IS NOT NULL
            AND (ml_confidence IS NULL OR ml_confidence >= ?)
            ORDER BY created_at DESC
            LIMIT 1000
        """, (min_confidence,))
        
        rows = cursor.fetchall()
        conn.close()
        
        result = []
        for row in rows:
            data = dict(row)
            try:
                data['features'] = MatchFeatures.from_dict(json.loads(data['features_json']))
                result.append(data)
            except:
                continue
        
        return result
    
    def update_match_result(self, match_id: int, home_goals: int, away_goals: int):
        """Обновить результат матча"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if home_goals > away_goals:
            actual_result = 'home'
        elif home_goals < away_goals:
            actual_result = 'away'
        else:
            actual_result = 'draw'
        
        # Получаем предсказание
        cursor.execute("""
            SELECT predicted_home_win, predicted_draw, predicted_away_win
            FROM prediction_history WHERE match_id = ?
        """, (match_id,))
        
        row = cursor.fetchone()
        if row:
            pred_home, pred_draw, pred_away = row
            
            max_prob = max(pred_home, pred_draw, pred_away)
            if max_prob == pred_home:
                predicted_class = 1
            elif max_prob == pred_draw:
                predicted_class = 0
            else:
                predicted_class = 2
            
            actual_class = {'draw': 0, 'home': 1, 'away': 2}[actual_result]
            correct = (predicted_class == actual_class)
            
            cursor.execute("""
                UPDATE prediction_history 
                SET actual_home_goals = ?, actual_away_goals = ?, 
                    actual_result = ?, prediction_correct = ?, resolved_at = CURRENT_TIMESTAMP
                WHERE match_id = ?
            """, (home_goals, away_goals, actual_result, correct, match_id))
            
            conn.commit()
        
        conn.close()
    
    def get_model_stats(self) -> Dict:
        """Получить статистику модели"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Общая точность
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN prediction_correct = 1 THEN 1 ELSE 0 END) as correct,
                AVG(ml_confidence) as avg_confidence
            FROM prediction_history
            WHERE actual_result IS NOT NULL
        """)
        
        row = cursor.fetchone()
        stats = {
            'total_predicted': row['total'] or 0,
            'total_correct': row['correct'] or 0,
            'accuracy': (row['correct'] / row['total'] * 100) if row['total'] else 0,
            'avg_ml_confidence': row['avg_confidence'] or 0,
        }
        
        # По исходам
        cursor.execute("""
            SELECT actual_result, COUNT(*) as count,
                   SUM(CASE WHEN prediction_correct = 1 THEN 1 ELSE 0 END) as correct
            FROM prediction_history
            WHERE actual_result IS NOT NULL
            GROUP BY actual_result
        """)
        
        stats['by_result'] = {}
        for row in cursor.fetchall():
            stats['by_result'][row['actual_result']] = {
                'total': row['count'],
                'correct': row['correct'],
                'accuracy': row['correct'] / row['count'] * 100 if row['count'] else 0
            }
        
        conn.close()
        return stats
    
    def get_prediction_history(self, limit: int = 50) -> List[Dict]:
        """История прогнозов"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT *,
                   CASE 
                       WHEN actual_home_goals IS NOT NULL AND actual_away_goals IS NOT NULL
                       THEN actual_home_goals || ':' || actual_away_goals
                       ELSE NULL
                   END AS actual_score
            FROM prediction_history
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def auto_update_finished_matches(self, matches: List[Dict]):
        """Автообновление результатов"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updated = 0
        
        for m in matches:
            try:
                match_id = m.get('id')
                if match_id is None:
                    continue
                
                status = str(m.get('status', '')).lower()
                home_goals = m.get('homeResult')
                away_goals = m.get('awayResult')
                
                if status in ('finished', 'ended', 'ft', 'after_penalties') or (
                    home_goals is not None and away_goals is not None
                ):
                    # Обновляем матч
                    cursor.execute("""
                        INSERT INTO matches (sstats_id, date, home_team, away_team,
                                           status, home_goals, away_goals, cached_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        ON CONFLICT(sstats_id) DO UPDATE SET
                            status = excluded.status,
                            home_goals = excluded.home_goals,
                            away_goals = excluded.away_goals,
                            cached_at = CURRENT_TIMESTAMP
                    """, (
                        match_id,
                        m.get('date'),
                        (m.get('homeTeam') or {}).get('name', ''),
                        (m.get('awayTeam') or {}).get('name', ''),
                        status,
                        home_goals,
                        away_goals
                    ))
                    
                    if home_goals is not None and away_goals is not None:
                        self.update_match_result(match_id, int(home_goals), int(away_goals))
                        updated += 1
                        
            except Exception as e:
                print(f"[DB] Error updating match: {e}")
                continue
        
        conn.commit()
        conn.close()
        return updated
