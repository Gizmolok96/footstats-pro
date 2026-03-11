"""
Оптимизированная ML модель для мобильных устройств
"""

import os
import json
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Проверка доступности sklearn
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("[ML] scikit-learn not available, using statistical fallback")

from src.database import get_db_path


def get_model_path():
    """Путь к сохраненной модели"""
    if 'ANDROID_STORAGE' in os.environ:
        base_dir = os.path.join(os.environ['ANDROID_STORAGE'], 'Android', 'data', 'com.sstats.app', 'files')
        return os.path.join(base_dir, 'ml_model.pkl')
    else:
        home = Path.home()
        model_dir = home / ".sstats_mobile" / "models"
        model_dir.mkdir(parents=True, exist_ok=True)
        return str(model_dir / "mobile_rf_v1.pkl")


class MobileMLModel:
    """Легковесная ML модель для Android"""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.is_trained = False
        self.accuracy = 0.0
        self.training_date = None
        self.model_path = get_model_path()
        self.scaler_path = self.model_path.replace('.pkl', '_scaler.pkl')
        self.metrics_path = self.model_path.replace('.pkl', '_metrics.json')
        
        self.load_model()
    
    def load_model(self):
        """Загрузка модели"""
        if not SKLEARN_AVAILABLE:
            return
        
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                
                if os.path.exists(self.metrics_path):
                    with open(self.metrics_path, 'r') as f:
                        metrics = json.load(f)
                        self.accuracy = metrics.get('accuracy', 0)
                        self.training_date = metrics.get('date')
                
                self.is_trained = True
                print(f"[ML] Model loaded, accuracy: {self.accuracy:.1f}%")
        except Exception as e:
            print(f"[ML] Error loading model: {e}")
            self.model = None
            self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
    
    def save_model(self, accuracy: float):
        """Сохранение модели"""
        if not SKLEARN_AVAILABLE or not self.model:
            return
        
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            with open(self.scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            
            metrics = {
                'date': datetime.now().isoformat(),
                'accuracy': accuracy,
                'version': 'mobile_v1'
            }
            with open(self.metrics_path, 'w') as f:
                json.dump(metrics, f)
            
            self.accuracy = accuracy
            self.training_date = metrics['date']
            
        except Exception as e:
            print(f"[ML] Error saving model: {e}")
    
    def get_feature_names(self) -> List[str]:
        """Названия признаков"""
        home = [f'h_{i}' for i in range(20)]
        away = [f'a_{i}' for i in range(20)]
        h2h = ['h2h_h', 'h2h_d', 'h2h_a', 'h2h_goals', 'league_goals', 'league_adv']
        return home + away + h2h
    
    def prepare_training_data(self, historical_data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Подготовка данных"""
        X, y = [], []
        
        for item in historical_data:
            try:
                features = item['features']
                actual = item['actual_result']
                
                result_map = {'draw': 0, 'home': 1, 'away': 2}
                y.append(result_map[actual])
                X.append(features.to_list())
            except:
                continue
        
        return np.array(X), np.array(y)
    
    def train(self, historical_data: List[Dict], test_size: float = 0.2) -> Dict:
        """Обучение модели"""
        if not SKLEARN_AVAILABLE:
            return {'success': False, 'error': 'sklearn not available'}
        
        if len(historical_data) < 30:
            return {'success': False, 'error': f'Need 30+ matches, got {len(historical_data)}'}
        
        try:
            X, y = self.prepare_training_data(historical_data)
            
            if len(X) < 30:
                return {'success': False, 'error': 'Insufficient valid data'}
            
            # Разделение
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, stratify=y
            )
            
            # Масштабирование
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Обучение Random Forest (оптимизированные параметры для мобильных)
            self.model = RandomForestClassifier(
                n_estimators=100,  # Меньше деревьев для скорости
                max_depth=10,      # Ограничение глубины
                min_samples_split=5,
                min_samples_leaf=2,
                max_features='sqrt',
                class_weight='balanced',
                random_state=42,
                n_jobs=1           # Один поток для Android
            )
            
            self.model.fit(X_train_scaled, y_train)
            
            # Оценка
            y_pred = self.model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred) * 100
            
            self.save_model(accuracy)
            self.is_trained = True
            
            return {
                'success': True,
                'accuracy': accuracy,
                'train_size': len(X_train),
                'test_size': len(X_test)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def predict(self, features) -> Optional[Dict]:
        """Предсказание"""
        if not SKLEARN_AVAILABLE or not self.is_trained or not self.model:
            return None
        
        try:
            X = np.array([features.to_list()])
            X_scaled = self.scaler.transform(X)
            
            proba = self.model.predict_proba(X_scaled)[0]
            confidence = max(proba) * 100
            
            if confidence < 40:
                reliability = 'low'
            elif confidence < 60:
                reliability = 'medium'
            else:
                reliability = 'high'
            
            return {
                'draw': round(proba[0] * 100, 1),
                'home_win': round(proba[1] * 100, 1),
                'away_win': round(proba[2] * 100, 1),
                'predicted_class': int(np.argmax(proba)),
                'confidence': round(confidence, 1),
                'reliability': reliability,
                'model_accuracy': self.accuracy,
                'model_date': self.training_date
            }
            
        except Exception as e:
            print(f"[ML] Prediction error: {e}")
            return None
    
    def get_feature_importance(self) -> List[Tuple[str, float]]:
        """Важность признаков"""
        if not self.is_trained or not self.model:
            return []
        
        importance = list(zip(
            self.get_feature_names(),
            self.model.feature_importances_
        ))
        return sorted(importance, key=lambda x: x[1], reverse=True)


# Импорт для type hints
from datetime import datetime
