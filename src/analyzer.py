"""
AI Анализатор для мобильной версии
"""

import numpy as np
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass

from src.database import TeamFeatures, MatchFeatures
from src.ml_model import MobileMLModel

try:
    from scipy.stats import poisson
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


@dataclass
class LeagueContext:
    """Контекст лиги"""
    avg_goals: float = 2.5
    home_advantage: float = 1.4
    style: str = 'balanced'


class AIAnalyzer:
    """AI анализатор матчей"""
    
    LEAGUE_CONTEXTS = {
        'premier_league': LeagueContext(2.7, 1.4, 'physical'),
        'la_liga': LeagueContext(2.5, 1.35, 'technical'),
        'serie_a': LeagueContext(2.4, 1.45, 'tactical'),
        'bundesliga': LeagueContext(3.0, 1.3, 'attacking'),
        'ligue_1': LeagueContext(2.3, 1.4, 'balanced'),
        'rpl': LeagueContext(2.2, 1.5, 'defensive'),
    }
    
    def __init__(self):
        self.ml_model = MobileMLModel()
    
    def detect_league_context(self, league_name: str) -> LeagueContext:
        """Определение контекста лиги"""
        league_lower = league_name.lower()
        for key, ctx in self.LEAGUE_CONTEXTS.items():
            if key.replace('_', ' ') in league_lower or key in league_lower:
                return ctx
        return LeagueContext()
    
    def extract_team_features(self, stats: Dict, is_home: bool,
                              league_context: LeagueContext) -> TeamFeatures:
        """Извлечение признаков команды"""
        if not stats or 'matches' not in stats or not stats['matches']:
            defaults = TeamFeatures()
            if is_home:
                defaults.home_advantage = league_context.home_advantage
                defaults.points_per_game *= league_context.home_advantage
                defaults.avg_goals_for *= league_context.home_advantage
            else:
                defaults.away_disadvantage = 0.85
                defaults.points_per_game *= 0.85
            defaults.is_home = is_home
            return defaults
        
        matches = stats['matches']
        total = len(matches)
        
        # Базовая статистика
        wins = sum(1 for m in matches if m.get('result') == 'W')
        draws = sum(1 for m in matches if m.get('result') == 'D')
        losses = total - wins - draws
        
        goals_for = sum(m.get('goals_for', 0) for m in matches)
        goals_against = sum(m.get('goals_against', 0) for m in matches)
        
        # xG
        xg_for_list = [m.get('xg_for') for m in matches if m.get('xg_for') is not None]
        xg_against_list = [m.get('xg_against') for m in matches if m.get('xg_against') is not None]
        
        xg_for_avg = sum(xg_for_list) / len(xg_for_list) if xg_for_list else goals_for / total
        xg_against_avg = sum(xg_against_list) / len(xg_against_list) if xg_against_list else goals_against / total
        
        # Эффективность
        finishing_eff = (goals_for / total) / xg_for_avg if xg_for_avg > 0 else 1.0
        defensive_eff = (goals_against / total) / xg_against_avg if xg_against_avg > 0 else 1.0
        
        # Средние показатели
        avg_possession = sum(m.get('possession', 50) for m in matches) / total
        avg_shots = sum(m.get('shots', 0) for m in matches) / total
        avg_sot = sum(m.get('shots_on_target', 0) for m in matches) / total
        avg_corners = sum(m.get('corners', 0) for m in matches) / total
        
        # Форма (последние 5)
        recent = matches[:5]
        recent_points = sum({'W': 3, 'D': 1, 'L': 0}.get(m.get('result'), 0) for m in recent)
        recent_gf = sum(m.get('goals_for', 0) for m in recent)
        recent_ga = sum(m.get('goals_against', 0) for m in recent)
        
        # Тренд
        trend = self.calculate_trend(recent)
        
        # Домашнее преимущество
        home_advantage = 1.0
        if is_home:
            home_matches = [m for m in matches if m.get('is_home')]
            if home_matches:
                home_ppg = sum({'W': 3, 'D': 1, 'L': 0}.get(m.get('result'), 0)
                               for m in home_matches) / len(home_matches)
                away_matches = [m for m in matches if not m.get('is_home')]
                away_ppg = sum({'W': 3, 'D': 1, 'L': 0}.get(m.get('result'), 0)
                               for m in away_matches) / len(away_matches) if away_matches else home_ppg
                home_advantage = home_ppg / max(away_ppg, 0.1)
        
        features = TeamFeatures(
            points_per_game=(wins * 3 + draws) / total,
            win_rate=wins / total,
            draw_rate=draws / total,
            loss_rate=losses / total,
            avg_goals_for=goals_for / total,
            avg_shots=avg_shots,
            avg_shots_on_target=avg_sot,
            finishing_efficiency=finishing_eff,
            xg_for_avg=xg_for_avg,
            avg_goals_against=goals_against / total,
            xg_against_avg=xg_against_avg,
            defensive_efficiency=defensive_eff,
            avg_possession=avg_possession,
            avg_corners=avg_corners,
            recent_points=recent_points,
            recent_goals_for=recent_gf,
            recent_goals_against=recent_ga,
            trend=trend,
            home_advantage=home_advantage if is_home else 1.0,
            away_disadvantage=0.85 if not is_home else 1.0
        )
        features.is_home = is_home
        
        return features
    
    def calculate_trend(self, recent_matches: List[Dict]) -> float:
        """Расчет тренда"""
        if len(recent_matches) < 3:
            return 0.0
        
        mid = len(recent_matches) // 2
        first = recent_matches[:mid]
        second = recent_matches[mid:]
        
        def calc_ppg(matches):
            return sum({'W': 3, 'D': 1, 'L': 0}.get(m.get('result'), 0) for m in matches) / len(matches)
        
        ppg_first = calc_ppg(first)
        ppg_second = calc_ppg(second)
        
        diff = ppg_second - ppg_first
        return max(-1.0, min(1.0, diff / 1.5))
    
    def analyze_match(self, match_data: Dict, home_stats: Dict, away_stats: Dict,
                      h2h: Optional[Dict] = None) -> Tuple[Dict, MatchFeatures]:
        """Полный анализ матча"""
        home_team = match_data.get('homeTeam', {}) or {}
        away_team = match_data.get('awayTeam', {}) or {}
        
        home_name = home_team.get('name', 'Home')
        away_name = away_team.get('name', 'Away')
        league_name = match_data.get('league', {}).get('name', '').lower()
        
        league_context = self.detect_league_context(league_name)
        
        # Признаки команд
        home_features = self.extract_team_features(home_stats, True, league_context)
        away_features = self.extract_team_features(away_stats, False, league_context)
        
        # Признаки матча
        match_features = MatchFeatures(
            home=home_features,
            away=away_features,
            h2h_home_wins=h2h.get('team1_wins', 0) if h2h else 0,
            h2h_draws=h2h.get('draws', 0) if h2h else 0,
            h2h_away_wins=h2h.get('team2_wins', 0) if h2h else 0,
            h2h_avg_goals=h2h.get('avg_goals', 2.5) if h2h else 2.5,
            league_avg_goals=league_context.avg_goals,
            league_home_advantage=league_context.home_advantage
        )
        
        # xG
        home_xg = self.calculate_xg(home_features, True, league_context)
        away_xg = self.calculate_xg(away_features, False, league_context)
        
        # Вероятности
        base_probs = self.calculate_probabilities(home_xg, away_xg)
        
        # ML прогноз
        ml_prediction = self.ml_model.predict(match_features)
        
        # Комбинирование
        final_probs = self.combine_predictions(base_probs, ml_prediction)
        
        # Генерация отчета
        analysis = {
            'home_name': home_name,
            'away_name': away_name,
            'home_xg': round(home_xg, 2),
            'away_xg': round(away_xg, 2),
            'probabilities': final_probs,
            'base_probabilities': base_probs,
            'ml_prediction': ml_prediction,
            'match_features': match_features,
            'narrative': self.generate_narrative(
                home_name, away_name, home_features, away_features,
                home_xg, away_xg, final_probs, ml_prediction, league_context, h2h
            ),
            'betting_tips': self.generate_tips(final_probs, home_features, away_features),
            'key_factors': self.identify_factors(home_features, away_features, h2h),
            'confidence_score': self.calculate_confidence(home_features, away_features, ml_prediction),
            'league_context': {'avg_goals': league_context.avg_goals, 
                             'home_advantage': league_context.home_advantage,
                             'style': league_context.style}
        }
        
        return analysis, match_features
    
    def calculate_xg(self, features: TeamFeatures, is_home: bool,
                     league_context: LeagueContext) -> float:
        """Расчет ожидаемых голов"""
        base = features.xg_for_avg if features.xg_for_avg > 0 else features.avg_goals_for
        
        if is_home:
            base *= league_context.home_advantage * features.home_advantage
        else:
            base *= 0.85 * features.away_disadvantage
        
        # Корректировки
        form_mult = 1 + (features.trend * 0.15)
        eff_mult = 0.5 + (features.finishing_efficiency * 0.5)
        poss_mult = 0.8 + (features.avg_possession / 100) * 0.4
        
        final = base * form_mult * eff_mult * poss_mult
        return max(0.3, min(final, 3.5))
    
    def calculate_probabilities(self, home_xg: float, away_xg: float) -> Dict:
        """Расчет вероятностей исходов"""
        max_goals = 6
        score_probs = {}
        
        if SCIPY_AVAILABLE:
            # Используем распределение Пуассона
            for h in range(max_goals + 1):
                for a in range(max_goals + 1):
                    prob = poisson.pmf(h, home_xg) * poisson.pmf(a, away_xg)
                    score_probs[f"{h}-{a}"] = prob
        else:
            # Упрощенный расчет без scipy
            for h in range(max_goals + 1):
                for a in range(max_goals + 1):
                    # Упрощенная аппроксимация
                    prob = np.exp(-home_xg) * (home_xg ** h) / np.math.factorial(h) * \
                           np.exp(-away_xg) * (away_xg ** a) / np.math.factorial(a)
                    score_probs[f"{h}-{a}"] = prob
        
        # Суммирование вероятностей
        home_win = sum(p for s, p in score_probs.items() 
                      if int(s.split('-')[0]) > int(s.split('-')[1]))
        draw = sum(p for s, p in score_probs.items() 
                  if int(s.split('-')[0]) == int(s.split('-')[1]))
        away_win = sum(p for s, p in score_probs.items() 
                      if int(s.split('-')[0]) < int(s.split('-')[1]))
        
        total = home_win + draw + away_win
        
        most_likely = max(score_probs, key=score_probs.get)
        
        return {
            'home_win': round(home_win / total * 100, 1),
            'draw': round(draw / total * 100, 1),
            'away_win': round(away_win / total * 100, 1),
            'most_likely_score': most_likely,
            'most_likely_prob': round(score_probs[most_likely] * 100, 1),
            'over_2_5': round(sum(p for s, p in score_probs.items()
                                  if int(s.split('-')[0]) + int(s.split('-')[1]) > 2.5) * 100, 1),
            'btts': round(sum(p for s, p in score_probs.items()
                             if int(s.split('-')[0]) > 0 and int(s.split('-')[1]) > 0) * 100, 1),
            'expected_total': round(home_xg + away_xg, 2)
        }
    
    def combine_predictions(self, base_probs: Dict, ml_probs: Optional[Dict]) -> Dict:
        """Комбинирование статистики и ML"""
        if not ml_probs or ml_probs['reliability'] == 'low':
            weight_ml = 0.1
        elif ml_probs['reliability'] == 'medium':
            weight_ml = 0.25
        else:
            weight_ml = 0.4
        
        weight_base = 1 - weight_ml
        
        combined = {}
        for key in ['home_win', 'draw', 'away_win']:
            base = base_probs.get(key, 33)
            ml = ml_probs.get(key, 33) if ml_probs else 33
            combined[key] = base * weight_base + ml * weight_ml
        
        # Нормализация
        total = sum(combined.values())
        for key in combined:
            combined[key] = round(combined[key] / total * 100, 1)
        
        # Копируем остальные поля
        for key in ['most_likely_score', 'most_likely_prob', 'over_2_5', 'btts', 'expected_total']:
            combined[key] = base_probs[key]
        
        combined['ml_weight_used'] = weight_ml
        return combined
    
    def generate_narrative(self, home_name: str, away_name: str,
                          home_f: TeamFeatures, away_f: TeamFeatures,
                          home_xg: float, away_xg: float,
                          probs: Dict, ml_pred: Optional[Dict],
                          league_ctx: LeagueContext, h2h: Optional[Dict]) -> str:
        """Генерация текстового анализа"""
        lines = []
        
        lines.append(f"📊 Analysis: {home_name} vs {away_name}\n")
        lines.append(f"League: {league_ctx.style.title()} style, "
                    f"avg {league_ctx.avg_goals} goals\n")
        
        if ml_pred:
            lines.append(f"🤖 ML Model (accuracy {ml_pred['model_accuracy']:.1f}%): "
                        f"confidence {ml_pred['confidence']:.1f}%, "
                        f"reliability {ml_pred['reliability']}\n")
        
        # Хозяева
        lines.append(f"\n🏠 {home_name} (Home)")
        lines.append(f"  Form: {home_f.points_per_game:.2f} ppg, trend {home_f.trend:+.2f}")
        lines.append(f"  Attack: {home_f.avg_goals_for:.2f} goals, xG {home_f.xg_for_avg:.2f}")
        lines.append(f"  Defense: {home_f.avg_goals_against:.2f} conceded")
        
        # Гости
        lines.append(f"\n✈️ {away_name} (Away)")
        lines.append(f"  Form: {away_f.points_per_game:.2f} ppg, trend {away_f.trend:+.2f}")
        lines.append(f"  Attack: {away_f.avg_goals_for:.2f} goals, xG {away_f.xg_for_avg:.2f}")
        lines.append(f"  Defense: {away_f.avg_goals_against:.2f} conceded")
        
        # H2H
        if h2h and h2h.get('total_matches', 0) > 0:
            lines.append(f"\n📊 H2H: {h2h['team1_wins']}-{h2h['draws']}-{h2h['team2_wins']}, "
                        f"avg goals {h2h['avg_goals']:.1f}")
        
        # Прогноз
        lines.append(f"\n🎯 Prediction:")
        lines.append(f"  1: {probs['home_win']}% | X: {probs['draw']}% | 2: {probs['away_win']}%")
        lines.append(f"  Score: {probs['most_likely_score']} (prob {probs['most_likely_prob']}%)")
        lines.append(f"  Over 2.5: {probs['over_2.5']}%, BTTS: {probs['btts']}%")
        
        # Вывод
        lines.append(f"\n💡 Conclusion:")
        if probs['home_win'] > 55:
            lines.append(f"  {home_name} favorite with home advantage")
        elif probs['away_win'] > 55:
            lines.append(f"  {away_name} favorite despite away status")
        elif abs(probs['home_win'] - probs['away_win']) < 10:
            lines.append(f"  Even match, likely draw or narrow win")
        else:
            fav = home_name if probs['home_win'] > probs['away_win'] else away_name
            lines.append(f"  Slight advantage for {fav}")
        
        return "\n".join(lines)
    
    def generate_tips(self, probs: Dict, home_f: TeamFeatures,
                     away_f: TeamFeatures) -> List[Dict]:
        """Генерация рекомендаций"""
        tips = []
        
        if probs['home_win'] > 60:
            tips.append({
                'market': f"1 ({probs['home_win']}%)",
                'confidence': 'high',
                'reason': 'Strong home form' if home_f.win_rate > 0.5 else 'Home advantage'
            })
        elif probs['away_win'] > 55:
            tips.append({
                'market': f"2 ({probs['away_win']}%)",
                'confidence': 'medium',
                'reason': 'Away team in form' if away_f.trend > 0 else 'Weak home team'
            })
        
        if probs['expected_total'] > 2.8:
            tips.append({
                'market': f"Over 2.5 ({probs['over_2_5']}%)",
                'confidence': 'high' if probs['over_2_5'] > 65 else 'medium',
                'reason': "High scoring expected"
            })
        elif probs['expected_total'] < 2.2:
            tips.append({
                'market': f"Under 2.5 ({100 - probs['over_2_5']:.1f}%)",
                'confidence': 'medium',
                'reason': "Low scoring match expected"
            })
        
        if probs['btts'] > 60:
            tips.append({
                'market': f"BTTS Yes ({probs['btts']}%)",
                'confidence': 'medium',
                'reason': "Both teams attacking"
            })
        
        return tips
    
    def identify_factors(self, home_f: TeamFeatures, away_f: TeamFeatures,
                        h2h: Optional[Dict]) -> List[str]:
        """Ключевые факторы"""
        factors = []
        
        if home_f.trend > 0.3:
            factors.append(f"📈 {home_f.home_advantage:.2f}x home advantage")
        if away_f.trend > 0.3:
            factors.append(f"📈 Away team rising")
        if home_f.finishing_efficiency > 1.2:
            factors.append("🎯 Clinical home finishing")
        if away_f.defensive_efficiency < 0.9:
            factors.append("🛡️ Solid away defense")
        if h2h and h2h.get('team1_wins', 0) > h2h.get('team2_wins', 0) * 2:
            factors.append("📊 Historical home dominance")
        
        return factors if factors else ["Standard match without clear factors"]
    
    def calculate_confidence(self, home_f: TeamFeatures, away_f: TeamFeatures,
                            ml_pred: Optional[Dict]) -> int:
        """Расчет уверенности"""
        conf = 50
        
        if home_f.win_rate != 0.33:
            conf += 15
        if away_f.win_rate != 0.33:
            conf += 15
        
        if ml_pred:
            conf += min(ml_pred['confidence'] / 5, 15)
        
        if abs(home_f.trend) < 0.3:
            conf += 5
        if abs(away_f.trend) < 0.3:
            conf += 5
        
        return min(conf, 95)
