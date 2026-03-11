"""
Главное приложение KivyMD с Material Design 3
"""

import os
import json
import threading
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from kivy.core.window import Window
from kivy.clock import Clock, mainthread
from kivy.properties import StringProperty, BooleanProperty, ListProperty, ObjectProperty
from kivy.metrics import dp
from kivy.storage.jsonstore import JsonStore
from kivy.utils import platform

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.navigationdrawer import MDNavigationDrawer
from kivymd.uix.list import MDList, OneLineListItem, TwoLineListItem, ThreeLineListItem
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton, MDFloatingActionButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.chip import MDChip
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.snackbar import MDSnackbar
from kivymd.uix.pickers import MDDatePicker
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.tab import MDTabs, MDTabsBase
from kivymd.uix.expansionpanel import MDExpansionPanel, MDExpansionPanelThreeLine
from kivymd.uix.behaviors import RoundedRectangularElevationBehavior
from kivymd.uix.menu import MDDropdownMenu
from kivymd.theming import ThemableBehavior
from kivymd.uix.behaviors import CommonElevationBehavior

from kivymd.toast import toast

from src.database import MobileDatabase
from src.api import SStatsAPI
from src.ml_model import MobileMLModel
from src.analyzer import AIAnalyzer

# Material Design 3 цветовые схемы
THEMES = {
    'dark': {
        'primary': '#3b82f6',
        'on_primary': '#ffffff',
        'primary_container': '#1e40af',
        'on_primary_container': '#dbeafe',
        'secondary': '#64748b',
        'on_secondary': '#ffffff',
        'secondary_container': '#1e293b',
        'on_secondary_container': '#e2e8f0',
        'surface': '#0f172a',
        'on_surface': '#f8fafc',
        'surface_variant': '#1e293b',
        'on_surface_variant': '#94a3b8',
        'outline': '#334155',
        'outline_variant': '#475569',
        'error': '#ef4444',
        'on_error': '#ffffff',
        'success': '#22c55e',
        'warning': '#eab308',
        'info': '#3b82f6',
    },
    'light': {
        'primary': '#2563eb',
        'on_primary': '#ffffff',
        'primary_container': '#dbeafe',
        'on_primary_container': '#1e40af',
        'secondary': '#64748b',
        'on_secondary': '#ffffff',
        'secondary_container': '#f1f5f9',
        'on_secondary_container': '#334155',
        'surface': '#ffffff',
        'on_surface': '#0f172a',
        'surface_variant': '#f8fafc',
        'on_surface_variant': '#64748b',
        'outline': '#cbd5e1',
        'outline_variant': '#e2e8f0',
        'error': '#dc2626',
        'on_error': '#ffffff',
        'success': '#16a34a',
        'warning': '#ca8a04',
        'info': '#2563eb',
    }
}


class MatchCard(MDCard, RoundedRectangularElevationBehavior):
    """Карточка матча с современным дизайном"""
    
    match_id = StringProperty()
    home_team = StringProperty("Home")
    away_team = StringProperty("Away")
    league = StringProperty("Unknown")
    match_time = StringProperty("--:--")
    status = StringProperty("Not played")
    score = StringProperty("-")
    home_prob = StringProperty("33")
    draw_prob = StringProperty("34")
    away_prob = StringProperty("33")
    
    def __init__(self, match_data: Dict, **kwargs):
        super().__init__(**kwargs)
        self.match_data = match_data
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(180)
        self.radius = [dp(16), dp(16), dp(16), dp(16)]
        self.elevation = 2
        self.padding = dp(16)
        self.spacing = dp(12)
        
        # Привязка данных
        self.bind_match_data()
        self.build_ui()
    
    def bind_match_data(self):
        """Привязка данных матча к свойствам"""
        home = self.match_data.get('homeTeam', {}) or {}
        away = self.match_data.get('awayTeam', {}) or {}
        league = self.match_data.get('league', {}) or {}
        
        self.match_id = str(self.match_data.get('id', ''))
        self.home_team = home.get('name', 'Home')
        self.away_team = away.get('name', 'Away')
        self.league = league.get('name', 'Unknown')
        
        # Время
        date_str = self.match_data.get('date', '')
        if date_str:
            try:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                self.match_time = dt.strftime("%H:%M")
            except:
                self.match_time = "--:--"
        
        # Статус и счёт
        status_raw = str(self.match_data.get('status', '')).lower()
        if status_raw in ('finished', 'ended', 'ft'):
            self.status = "Finished"
            home_g = self.match_data.get('homeResult')
            away_g = self.match_data.get('awayResult')
            if home_g is not None and away_g is not None:
                self.score = f"{home_g}:{away_g}"
        else:
            self.status = "Not played"
        
        # Вероятности (если есть предпросчитанные)
        probs = self.match_data.get('cached_probs', {})
        if probs:
            self.home_prob = str(int(probs.get('home_win', 33)))
            self.draw_prob = str(int(probs.get('draw', 34)))
            self.away_prob = str(int(probs.get('away_win', 33)))
    
    def build_ui(self):
        """Построение UI карточки"""
        # Верхняя строка: лига и время
        header = MDBoxLayout(
            size_hint_y=None,
            height=dp(24),
            spacing=dp(8)
        )
        
        league_chip = MDChip(
            text=self.league[:20],
            icon="trophy",
            size_hint_x=None,
            width=dp(120)
        )
        league_chip.md_bg_color = self.theme_cls.primary_color
        
        time_label = MDLabel(
            text=self.match_time,
            halign="right",
            font_style="Caption",
            theme_text_color="Secondary"
        )
        
        header.add_widget(league_chip)
        header.add_widget(time_label)
        self.add_widget(header)
        
        # Команды
        teams_box = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=dp(12)
        )
        
        home_label = MDLabel(
            text=self.home_team,
            halign="left",
            font_style="H6",
            bold=True,
            theme_text_color="Primary"
        )
        
        vs_label = MDLabel(
            text="VS",
            halign="center",
            font_style="Caption",
            theme_text_color="Secondary",
            size_hint_x=None,
            width=dp(40)
        )
        
        away_label = MDLabel(
            text=self.away_team,
            halign="right",
            font_style="H6",
            bold=True,
            theme_text_color="Primary"
        )
        
        teams_box.add_widget(home_label)
        teams_box.add_widget(vs_label)
        teams_box.add_widget(away_label)
        self.add_widget(teams_box)
        
        # Индикатор вероятностей
        probs_box = MDBoxLayout(
            size_hint_y=None,
            height=dp(32),
            spacing=dp(4),
            padding=[0, dp(8), 0, 0]
        )
        
        # Прогресс-бары вероятностей
        home_bar = MDProgressBar(
            value=int(self.home_prob),
            color=self.theme_cls.primary_color,
            size_hint_x=float(self.home_prob) / 100
        )
        
        draw_bar = MDProgressBar(
            value=int(self.draw_prob),
            color=self.theme_cls.warning_color,
            size_hint_x=float(self.draw_prob) / 100
        )
        
        away_bar = MDProgressBar(
            value=int(self.away_prob),
            color=self.theme_cls.error_color,
            size_hint_x=float(self.away_prob) / 100
        )
        
        probs_box.add_widget(home_bar)
        probs_box.add_widget(draw_bar)
        probs_box.add_widget(away_bar)
        self.add_widget(probs_box)
        
        # Подписи вероятностей
        labels_box = MDBoxLayout(
            size_hint_y=None,
            height=dp(20)
        )
        
        labels_box.add_widget(MDLabel(
            text=f"1 ({self.home_prob}%)",
            halign="left",
            font_style="Caption"
        ))
        labels_box.add_widget(MDLabel(
            text=f"X ({self.draw_prob}%)",
            halign="center",
            font_style="Caption"
        ))
        labels_box.add_widget(MDLabel(
            text=f"2 ({self.away_prob}%)",
            halign="right",
            font_style="Caption"
        ))
        self.add_widget(labels_box)
        
        # Кнопка анализа (если матч не сыгран)
        if self.status == "Not played":
            analyze_btn = MDRaisedButton(
                text="ANALYZE",
                size_hint_x=1,
                height=dp(40),
                md_bg_color=self.theme_cls.primary_color,
                on_release=self.on_analyze
            )
            self.add_widget(analyze_btn)
        else:
            result_label = MDLabel(
                text=f"Result: {self.score}",
                halign="center",
                font_style="H6",
                theme_text_color="Secondary"
            )
            self.add_widget(result_label)
    
    def on_analyze(self, *args):
        """Открыть экран анализа"""
        app = MDApp.get_running_app()
        app.show_match_analysis(self.match_data)


class AnalysisScreen(MDScreen):
    """Экран детального анализа матча"""
    
    match_data = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "analysis"
        self.build_ui()
    
    def build_ui(self):
        layout = MDBoxLayout(orientation="vertical")
        
        # AppBar
        appbar = MDBoxLayout(
            size_hint_y=None,
            height=dp(56),
            padding=[dp(16), dp(8)],
            md_bg_color=self.theme_cls.primary_color
        )
        
        back_btn = MDIconButton(
            icon="arrow-left",
            theme_text_color="Custom",
            text_color=self.theme_cls.on_primary_color,
            on_release=self.go_back
        )
        
        title = MDLabel(
            text="Match Analysis",
            font_style="H6",
            theme_text_color="Custom",
            text_color=self.theme_cls.on_primary_color,
            halign="left"
        )
        
        appbar.add_widget(back_btn)
        appbar.add_widget(title)
        layout.add_widget(appbar)
        
        # ScrollView с контентом
        scroll = MDScrollView()
        self.content_box = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(1000),
            padding=dp(16),
            spacing=dp(16)
        )
        self.content_box.bind(minimum_height=self.content_box.setter('height'))
        
        scroll.add_widget(self.content_box)
        layout.add_widget(scroll)
        
        self.add_widget(layout)
    
    def on_enter(self):
        """Загрузка анализа при входе"""
        if self.match_data:
            self.load_analysis()
    
    def load_analysis(self):
        """Загрузка и отображение анализа"""
        self.content_box.clear_widgets()
        
        # Индикатор загрузки
        loading = MDLabel(
            text="🤖 AI is analyzing the match...",
            halign="center",
            font_style="H5"
        )
        self.content_box.add_widget(loading)
        
        # Запуск анализа в фоне
        threading.Thread(target=self._analyze_thread, daemon=True).start()
    
    def _analyze_thread(self):
        """Фоновый анализ"""
        try:
            app = MDApp.get_running_app()
            analyzer = app.analyzer
            api = app.api
            
            home_team = self.match_data.get('homeTeam', {})
            away_team = self.match_data.get('awayTeam', {})
            
            # Получение статистики
            home_stats = api.get_team_full_stats(home_team.get('id'), home_team.get('name'))
            away_stats = api.get_team_full_stats(away_team.get('id'), away_team.get('name'))
            h2h = api.get_head_to_head(home_team.get('id'), away_team.get('id'))
            
            # AI анализ
            analysis, features = analyzer.analyze_match(
                self.match_data, home_stats, away_stats, h2h
            )
            
            # ML предсказание
            ml_pred = analyzer.ml_model.predict(features)
            
            # Сохранение в БД
            app.db.save_prediction_with_features(
                self.match_data, analysis, features, ml_pred
            )
            
            # Обновление UI
            Clock.schedule_once(lambda dt: self.display_analysis(analysis, ml_pred), 0)
            
        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_error(str(e)), 0)
    
    @mainthread
    def display_analysis(self, analysis: Dict, ml_pred: Optional[Dict]):
        """Отображение результатов анализа"""
        self.content_box.clear_widgets()
        
        probs = analysis['probabilities']
        
        # Карточка заголовка
        header_card = MDCard(
            orientation="vertical",
            size_hint_y=None,
            height=dp(120),
            padding=dp(16),
            radius=[dp(16), dp(16), dp(16), dp(16)],
            elevation=2
        )
        
        teams_title = MDLabel(
            text=f"{analysis['home_name']} vs {analysis['away_name']}",
            font_style="H5",
            halign="center",
            bold=True
        )
        
        subtitle = MDLabel(
            text=f"Expected: {probs['most_likely_score']} ({probs['most_likely_prob']}%)",
            font_style="Subtitle1",
            halign="center",
            theme_text_color="Secondary"
        )
        
        header_card.add_widget(teams_title)
        header_card.add_widget(subtitle)
        self.content_box.add_widget(header_card)
        
        # Карточка вероятностей
        probs_card = MDCard(
            orientation="vertical",
            size_hint_y=None,
            height=dp(200),
            padding=dp(16),
            radius=[dp(16), dp(16), dp(16), dp(16)],
            elevation=2
        )
        
        probs_title = MDLabel(
            text="Outcome Probabilities",
            font_style="H6",
            size_hint_y=None,
            height=dp(32)
        )
        probs_card.add_widget(probs_title)
        
        # Прогресс-бары для вероятностей
        outcomes = [
            (f"Home Win ({analysis['home_name']})", probs['home_win'], "primary"),
            ("Draw", probs['draw'], "warning"),
            (f"Away Win ({analysis['away_name']})", probs['away_win'], "error")
        ]
        
        for label, value, color in outcomes:
            row = MDBoxLayout(
                size_hint_y=None,
                height=dp(48),
                spacing=dp(8)
            )
            
            name_label = MDLabel(
                text=label,
                size_hint_x=0.6,
                font_style="Body2"
            )
            
            value_label = MDLabel(
                text=f"{value}%",
                size_hint_x=0.2,
                halign="right",
                font_style="Body1",
                bold=True
            )
            
            progress = MDProgressBar(
                value=value,
                size_hint_x=0.2,
                color=getattr(self.theme_cls, f"{color}_color")
            )
            
            row.add_widget(name_label)
            row.add_widget(progress)
            row.add_widget(value_label)
            probs_card.add_widget(row)
        
        self.content_box.add_widget(probs_card)
        
        # ML секция (если есть)
        if ml_pred:
            ml_card = MDCard(
                orientation="vertical",
                size_hint_y=None,
                height=dp(160),
                padding=dp(16),
                radius=[dp(16), dp(16), dp(16), dp(16)],
                elevation=2,
                md_bg_color=self.theme_cls.primary_container_color
            )
            
            ml_title = MDLabel(
                text=f"🤖 ML Model (Accuracy: {ml_pred.get('model_accuracy', 0):.1f}%)",
                font_style="H6",
                theme_text_color="Custom",
                text_color=self.theme_cls.on_primary_container_color
            )
            
            ml_details = MDLabel(
                text=f"ML Prediction: 1-{ml_pred['home_win']}% | X-{ml_pred['draw']}% | 2-{ml_pred['away_win']}%\n"
                     f"Confidence: {ml_pred['confidence']:.1f}% | Reliability: {ml_pred['reliability']}",
                font_style="Body2",
                theme_text_color="Custom",
                text_color=self.theme_cls.on_primary_container_color
            )
            
            ml_card.add_widget(ml_title)
            ml_card.add_widget(ml_details)
            self.content_box.add_widget(ml_card)
        
        # Дополнительные прогнозы
        extras_card = MDCard(
            orientation="vertical",
            size_hint_y=None,
            height=dp(140),
            padding=dp(16),
            radius=[dp(16), dp(16), dp(16), dp(16)],
            elevation=2
        )
        
        extras_title = MDLabel(
            text="Additional Predictions",
            font_style="H6",
            size_hint_y=None,
            height=dp(32)
        )
        extras_card.add_widget(extras_title)
        
        extras_data = [
            ("Over 2.5 Goals", f"{probs['over_2_5']}%"),
            ("Both Teams to Score", f"{probs['btts']}%"),
            ("Expected Total", str(probs['expected_total']))
        ]
        
        for label, value in extras_data:
            row = MDBoxLayout(
                size_hint_y=None,
                height=dp(32),
                spacing=dp(8)
            )
            row.add_widget(MDLabel(text=label, size_hint_x=0.7))
            row.add_widget(MDLabel(
                text=value,
                size_hint_x=0.3,
                halign="right",
                font_style="Body1",
                bold=True
            ))
            extras_card.add_widget(row)
        
        self.content_box.add_widget(extras_card)
        
        # Рекомендации
        if analysis.get('betting_tips'):
            tips_card = MDCard(
                orientation="vertical",
                size_hint_y=None,
                height=dp(120 + len(analysis['betting_tips']) * 40),
                padding=dp(16),
                radius=[dp(16), dp(16), dp(16), dp(16)],
                elevation=2,
                md_bg_color=self.theme_cls.success_color if any(t['confidence'] == 'high' for t in analysis['betting_tips']) else self.theme_cls.warning_color
            )
            
            tips_title = MDLabel(
                text="💡 Betting Tips",
                font_style="H6",
                theme_text_color="Custom",
                text_color=self.theme_cls.on_primary_color
            )
            tips_card.add_widget(tips_title)
            
            for tip in analysis['betting_tips']:
                tip_text = f"• {tip['market']} - {tip['reason']}"
                tips_card.add_widget(MDLabel(
                    text=tip_text,
                    theme_text_color="Custom",
                    text_color=self.theme_cls.on_primary_color,
                    font_style="Body2"
                ))
            
            self.content_box.add_widget(tips_card)
        
        # Текстовый анализ (сворачиваемый)
        narrative_panel = MDExpansionPanel(
            icon="text-box",
            content=MDLabel(
                text=analysis['narrative'],
                font_style="Body2",
                size_hint_y=None,
                text_size=(None, None)
            ),
            panel_cls=MDExpansionPanelThreeLine(
                text="Detailed Analysis",
                secondary_text="Tap to expand",
                tertiary_text=f"Confidence: {analysis.get('confidence_score', 50)}%"
            )
        )
        self.content_box.add_widget(narrative_panel)
        
        # Кнопки действий
        actions_box = MDBoxLayout(
            size_hint_y=None,
            height=dp(56),
            spacing=dp(8)
        )
        
        save_btn = MDRaisedButton(
            text="SAVE",
            icon="content-save",
            on_release=lambda x: self.save_prediction(analysis)
        )
        
        share_btn = MDFlatButton(
            text="SHARE",
            icon="share-variant",
            on_release=lambda x: self.share_prediction(analysis)
        )
        
        actions_box.add_widget(save_btn)
        actions_box.add_widget(share_btn)
        self.content_box.add_widget(actions_box)
    
    def show_error(self, message: str):
        """Показать ошибку"""
        self.content_box.clear_widgets()
        error_label = MDLabel(
            text=f"Error: {message}",
            halign="center",
            theme_text_color="Error"
        )
        self.content_box.add_widget(error_label)
    
    def go_back(self, *args):
        """Вернуться назад"""
        self.manager.current = "matches"
    
    def save_prediction(self, analysis: Dict):
        """Сохранить прогноз"""
        app = MDApp.get_running_app()
        try:
            # Сохранение в JSON на устройстве
            store = JsonStore(os.path.join(app.user_data_dir, 'predictions.json'))
            key = f"{analysis['home_name']}_vs_{analysis['away_name']}_{datetime.now().strftime('%Y%m%d')}"
            store.put(key, **analysis)
            toast("Prediction saved!")
        except Exception as e:
            toast(f"Save error: {str(e)}")
    
    def share_prediction(self, analysis: Dict):
        """Поделиться прогнозом (Android intent)"""
        try:
            from android import activity
            from jnius import autoclass
            
            Intent = autoclass('android.content.Intent')
            String = autoclass('java.lang.String')
            
            share_text = f"🏆 {analysis['home_name']} vs {analysis['away_name']}\n"
            share_text += f"Prediction: {analysis['probabilities']['most_likely_score']}\n"
            share_text += f"Confidence: {analysis.get('confidence_score', 50)}%"
            
            intent = Intent()
            intent.setAction(Intent.ACTION_SEND)
            intent.setType("text/plain")
            intent.putExtra(Intent.EXTRA_TEXT, String(share_text))
            
            activity.startActivity(intent)
        except:
            toast("Sharing not available")


class MatchesScreen(MDScreen):
    """Главный экран со списком матчей"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "matches"
        self.current_matches = []
        self.selected_date = datetime.now()
        self.build_ui()
    
    def build_ui(self):
        layout = MDBoxLayout(orientation="vertical")
        
        # AppBar с поиском
        appbar = MDBoxLayout(
            size_hint_y=None,
            height=dp(120),
            orientation="vertical",
            md_bg_color=self.theme_cls.primary_color,
            padding=[dp(16), dp(8)]
        )
        
        # Верхняя строка: заголовок и меню
        top_row = MDBoxLayout(size_hint_y=None, height=dp(48))
        
        menu_btn = MDIconButton(
            icon="menu",
            theme_text_color="Custom",
            text_color=self.theme_cls.on_primary_color,
            on_release=self.open_menu
        )
        
        title = MDLabel(
            text="SStats Pro",
            font_style="H5",
            theme_text_color="Custom",
            text_color=self.theme_cls.on_primary_color,
            halign="left"
        )
        
        ml_indicator = MDChip(
            text="ML Ready" if MDApp.get_running_app().ml_ready else "ML Off",
            icon="brain",
            size_hint_x=None,
            width=dp(100),
            md_bg_color=self.theme_cls.success_color if MDApp.get_running_app().ml_ready else self.theme_cls.error_color
        )
        
        top_row.add_widget(menu_btn)
        top_row.add_widget(title)
        top_row.add_widget(ml_indicator)
        appbar.add_widget(top_row)
        
        # Поиск и дата
        search_row = MDBoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        
        self.search_field = MDTextField(
            hint_text="Search teams...",
            size_hint_x=0.6,
            mode="round",
            line_color_normal=self.theme_cls.on_primary_color,
            text_color_normal=self.theme_cls.on_primary_color,
            hint_text_color_normal=self.theme_cls.on_primary_color
        )
        self.search_field.bind(on_text_validate=self.filter_matches)
        
        date_btn = MDRaisedButton(
            text=self.selected_date.strftime("%d.%m.%Y"),
            size_hint_x=0.3,
            on_release=self.show_date_picker
        )
        
        refresh_btn = MDIconButton(
            icon="refresh",
            on_release=self.load_matches
        )
        
        search_row.add_widget(self.search_field)
        search_row.add_widget(date_btn)
        search_row.add_widget(refresh_btn)
        appbar.add_widget(search_row)
        
        layout.add_widget(appbar)
        
        # Список матчей
        self.scroll = MDScrollView()
        self.matches_list = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(12),
            padding=dp(16)
        )
        self.matches_list.bind(minimum_height=self.matches_list.setter('height'))
        
        self.scroll.add_widget(self.matches_list)
        layout.add_widget(self.scroll)
        
        # FAB для быстрой даты
        fab = MDFloatingActionButton(
            icon="calendar-today",
            pos_hint={"right": 0.95, "y": 0.05},
            on_release=self.show_date_picker
        )
        layout.add_widget(fab)
        
        self.add_widget(layout)
    
    def on_enter(self):
        """При входе на экран загружаем матчи"""
        self.load_matches()
    
    def load_matches(self, *args):
        """Загрузка матчей"""
        self.matches_list.clear_widgets()
        loading = MDLabel(
            text="Loading matches...",
            halign="center",
            font_style="H6"
        )
        self.matches_list.add_widget(loading)
        
        threading.Thread(target=self._load_thread, daemon=True).start()
    
    def _load_thread(self):
        """Фоновая загрузка"""
        try:
            app = MDApp.get_running_app()
            date_str = self.selected_date.strftime("%Y-%m-%d")
            
            matches = app.api.get_all_matches_for_date(date_str)
            
            Clock.schedule_once(lambda dt: self.display_matches(matches), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_error(str(e)), 0)
    
    @mainthread
    def display_matches(self, matches: List[Dict]):
        """Отображение матчей"""
        self.current_matches = matches
        self.matches_list.clear_widgets()
        
        if not matches:
            empty = MDLabel(
                text="No matches found for this date",
                halign="center",
                theme_text_color="Secondary"
            )
            self.matches_list.add_widget(empty)
            return
        
        # Группировка по лигам
        by_league = {}
        for match in matches:
            league = match.get('league', {}).get('name', 'Unknown')
            if league not in by_league:
                by_league[league] = []
            by_league[league].append(match)
        
        for league, league_matches in by_league.items():
            # Заголовок лиги
            league_header = MDLabel(
                text=f"🏆 {league}",
                font_style="H6",
                size_hint_y=None,
                height=dp(40),
                theme_text_color="Primary",
                bold=True
            )
            self.matches_list.add_widget(league_header)
            
            # Карточки матчей
            for match in league_matches:
                card = MatchCard(match)
                self.matches_list.add_widget(card)
    
    def filter_matches(self, *args):
        """Фильтрация по поиску"""
        query = self.search_field.text.lower()
        if not query:
            self.display_matches(self.current_matches)
            return
        
        filtered = []
        for match in self.current_matches:
            home = match.get('homeTeam', {}).get('name', '').lower()
            away = match.get('awayTeam', {}).get('name', '').lower()
            league = match.get('league', {}).get('name', '').lower()
            
            if query in home or query in away or query in league:
                filtered.append(match)
        
        self.display_matches(filtered)
    
    def show_date_picker(self, *args):
        """Показать выбор даты"""
        date_dialog = MDDatePicker(
            min_date=datetime.now() - timedelta(days=7),
            max_date=datetime.now() + timedelta(days=14),
            date=self.selected_date
        )
        date_dialog.bind(on_save=self.on_date_selected)
        date_dialog.open()
    
    def on_date_selected(self, instance, value, date_range):
        """Обработка выбора даты"""
        self.selected_date = value
        self.load_matches()
    
    def show_error(self, message: str):
        """Показать ошибку"""
        self.matches_list.clear_widgets()
        error_label = MDLabel(
            text=f"Error: {message}",
            halign="center",
            theme_text_color="Error"
        )
        self.matches_list.add_widget(error_label)
    
    def open_menu(self, *args):
        """Открыть боковое меню"""
        app = MDApp.get_running_app()
        app.root.ids.nav_drawer.set_state("open")


class HistoryScreen(MDScreen):
    """Экран истории прогнозов"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "history"
        self.build_ui()
    
    def build_ui(self):
        layout = MDBoxLayout(orientation="vertical")
        
        # AppBar
        appbar = MDBoxLayout(
            size_hint_y=None,
            height=dp(56),
            md_bg_color=self.theme_cls.primary_color,
            padding=[dp(16), dp(8)]
        )
        
        back_btn = MDIconButton(
            icon="arrow-left",
            theme_text_color="Custom",
            text_color=self.theme_cls.on_primary_color,
            on_release=self.go_back
        )
        
        title = MDLabel(
            text="Prediction History",
            font_style="H6",
            theme_text_color="Custom",
            text_color=self.theme_cls.on_primary_color
        )
        
        appbar.add_widget(back_btn)
        appbar.add_widget(title)
        layout.add_widget(appbar)
        
        # Список истории
        self.scroll = MDScrollView()
        self.history_list = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(8),
            padding=dp(16)
        )
        self.history_list.bind(minimum_height=self.history_list.setter('height'))
        
        self.scroll.add_widget(self.history_list)
        layout.add_widget(self.scroll)
        
        self.add_widget(layout)
    
    def on_enter(self):
        """Загрузка истории"""
        self.load_history()
    
    def load_history(self):
        """Загрузка истории из БД"""
        self.history_list.clear_widgets()
        
        try:
            app = MDApp.get_running_app()
            history = app.db.get_prediction_history(50)
            
            if not history:
                empty = MDLabel(
                    text="No predictions yet",
                    halign="center",
                    theme_text_color="Secondary"
                )
                self.history_list.add_widget(empty)
                return
            
            for item in history:
                card = self.create_history_card(item)
                self.history_list.add_widget(card)
                
        except Exception as e:
            error = MDLabel(
                text=f"Error loading history: {str(e)}",
                halign="center",
                theme_text_color="Error"
            )
            self.history_list.add_widget(error)
    
    def create_history_card(self, item: Dict) -> MDCard:
        """Создание карточки истории"""
        card = MDCard(
            orientation="vertical",
            size_hint_y=None,
            height=dp(100),
            padding=dp(12),
            radius=[dp(12), dp(12), dp(12), dp(12)],
            elevation=1
        )
        
        # Команды
        teams = MDLabel(
            text=f"{item['home_team']} vs {item['away_team']}",
            font_style="H6",
            bold=True
        )
        card.add_widget(teams)
        
        # Дата и результат
        date_str = item['created_at'][:16] if item['created_at'] else ''
        actual = item.get('actual_score', '-')
        
        info = MDLabel(
            text=f"{date_str} | Result: {actual}",
            font_style="Caption",
            theme_text_color="Secondary"
        )
        card.add_widget(info)
        
        # Прогноз
        pred_text = f"Predicted: 1-{item['predicted_home_win']:.0f}% X-{item['predicted_draw']:.0f}% 2-{item['predicted_away_win']:.0f}%"
        pred_label = MDLabel(
            text=pred_text,
            font_style="Body2"
        )
        card.add_widget(pred_label)
        
        # Статус точности
        if item.get('prediction_correct') is not None:
            status = "✓ Correct" if item['prediction_correct'] else "✗ Wrong"
            color = self.theme_cls.success_color if item['prediction_correct'] else self.theme_cls.error_color
            
            status_label = MDLabel(
                text=status,
                font_style="Caption",
                theme_text_color="Custom",
                text_color=color,
                bold=True
            )
            card.add_widget(status_label)
        
        return card
    
    def go_back(self, *args):
        self.manager.current = "matches"


class MLStatsScreen(MDScreen):
    """Экран статистики ML модели"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "ml_stats"
        self.build_ui()
    
    def build_ui(self):
        layout = MDBoxLayout(orientation="vertical")
        
        # AppBar
        appbar = MDBoxLayout(
            size_hint_y=None,
            height=dp(56),
            md_bg_color=self.theme_cls.primary_color,
            padding=[dp(16), dp(8)]
        )
        
        back_btn = MDIconButton(
            icon="arrow-left",
            theme_text_color="Custom",
            text_color=self.theme_cls.on_primary_color,
            on_release=self.go_back
        )
        
        title = MDLabel(
            text="ML Model Stats",
            font_style="H6",
            theme_text_color="Custom",
            text_color=self.theme_cls.on_primary_color
        )
        
        train_btn = MDIconButton(
            icon="brain",
            theme_text_color="Custom",
            text_color=self.theme_cls.on_primary_color,
            on_release=self.train_model
        )
        
        appbar.add_widget(back_btn)
        appbar.add_widget(title)
        appbar.add_widget(train_btn)
        layout.add_widget(appbar)
        
        # Контент
        self.scroll = MDScrollView()
        self.content = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(16),
            padding=dp(16)
        )
        self.content.bind(minimum_height=self.content.setter('height'))
        
        self.scroll.add_widget(self.content)
        layout.add_widget(self.scroll)
        
        self.add_widget(layout)
    
    def on_enter(self):
        self.load_stats()
    
    def load_stats(self):
        """Загрузка статистики"""
        self.content.clear_widgets()
        
        try:
            app = MDApp.get_running_app()
            stats = app.db.get_model_stats()
            
            # Общая карточка
            total_card = MDCard(
                orientation="vertical",
                size_hint_y=None,
                height=dp(140),
                padding=dp(16),
                radius=[dp(16), dp(16), dp(16), dp(16)],
                elevation=2
            )
            
            total_title = MDLabel(
                text="Overall Accuracy",
                font_style="H6"
            )
            
            accuracy = stats.get('accuracy', 0)
            total_value = MDLabel(
                text=f"{accuracy:.1f}%",
                font_style="H2",
                halign="center",
                theme_text_color="Primary",
                bold=True
            )
            
            total_subtitle = MDLabel(
                text=f"{stats.get('total_correct', 0)} / {stats.get('total_predicted', 0)} correct",
                halign="center",
                theme_text_color="Secondary"
            )
            
            total_card.add_widget(total_title)
            total_card.add_widget(total_value)
            total_card.add_widget(total_subtitle)
            self.content.add_widget(total_card)
            
            # По исходам
            by_result = stats.get('by_result', {})
            for result, data in by_result.items():
                card = MDCard(
                    orientation="horizontal",
                    size_hint_y=None,
                    height=dp(80),
                    padding=dp(16),
                    radius=[dp(12), dp(12), dp(12), dp(12)],
                    elevation=1
                )
                
                result_label = MDLabel(
                    text=result.upper(),
                    size_hint_x=0.3,
                    font_style="H6"
                )
                
                acc_label = MDLabel(
                    text=f"{data['accuracy']:.1f}%",
                    size_hint_x=0.4,
                    halign="center",
                    font_style="H5",
                    bold=True
                )
                
                count_label = MDLabel(
                    text=f"{data['correct']}/{data['total']}",
                    size_hint_x=0.3,
                    halign="right",
                    theme_text_color="Secondary"
                )
                
                card.add_widget(result_label)
                card.add_widget(acc_label)
                card.add_widget(count_label)
                self.content.add_widget(card)
            
            # Кнопка обучения
            train_card = MDCard(
                orientation="vertical",
                size_hint_y=None,
                height=dp(100),
                padding=dp(16),
                radius=[dp(16), dp(16), dp(16), dp(16)],
                elevation=2,
                md_bg_color=self.theme_cls.primary_container_color
            )
            
            train_info = MDLabel(
                text="Train model on new data to improve accuracy",
                font_style="Body2",
                theme_text_color="Secondary"
            )
            
            train_btn = MDRaisedButton(
                text="TRAIN MODEL",
                size_hint_x=1,
                on_release=self.train_model
            )
            
            train_card.add_widget(train_info)
            train_card.add_widget(train_btn)
            self.content.add_widget(train_card)
            
        except Exception as e:
            error = MDLabel(
                text=f"Error: {str(e)}",
                halign="center",
                theme_text_color="Error"
            )
            self.content.add_widget(error)
    
    def train_model(self, *args):
        """Обучение модели"""
        self.content.clear_widgets()
        loading = MDLabel(
            text="Training model... This may take a while",
            halign="center"
        )
        self.content.add_widget(loading)
        
        threading.Thread(target=self._train_thread, daemon=True).start()
    
    def _train_thread(self):
        """Фоновое обучение"""
        try:
            app = MDApp.get_running_app()
            training_data = app.db.get_training_data(min_confidence=0)
            
            if len(training_data) < 30:
                Clock.schedule_once(
                    lambda dt: toast(f"Need 30+ matches, got {len(training_data)}"), 0
                )
                Clock.schedule_once(lambda dt: self.load_stats(), 0)
                return
            
            result = app.analyzer.ml_model.train(training_data)
            
            if result.get('success'):
                Clock.schedule_once(
                    lambda dt: toast(f"Trained! Accuracy: {result['accuracy']:.1f}%"), 0
                )
            else:
                Clock.schedule_once(
                    lambda dt: toast(f"Training failed: {result.get('error')}"), 0
                )
            
            Clock.schedule_once(lambda dt: self.load_stats(), 0)
            
        except Exception as e:
            Clock.schedule_once(lambda dt: toast(f"Error: {str(e)}"), 0)
            Clock.schedule_once(lambda dt: self.load_stats(), 0)
    
    def go_back(self, *args):
        self.manager.current = "matches"


class SStatsApp(MDApp):
    """Главное приложение"""
    
    ml_ready = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "SStats Pro"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Amber"
        
        # Инициализация компонентов
        self.db = None
        self.api = None
        self.analyzer = None
        self.ml_model = None
    
    def build(self):
        # Инициализация БД и API
        self.init_services()
        
        # Создание UI
        return self.build_ui()
    
    def init_services(self):
        """Инициализация сервисов"""
        try:
            self.db = MobileDatabase()
            self.api = SStatsAPI("gbi1ldi9446kastj")
            self.analyzer = AIAnalyzer()
            self.ml_model = MobileMLModel()
            
            # Проверка ML
            self.ml_ready = self.ml_model.is_trained
            
        except Exception as e:
            print(f"Init error: {e}")
            toast(f"Initialization error: {str(e)}")
    
    def build_ui(self):
        """Построение интерфейса"""
        # ScreenManager
        sm = MDScreenManager()
        
        # Экраны
        sm.add_widget(MatchesScreen())
        sm.add_widget(AnalysisScreen())
        sm.add_widget(HistoryScreen())
        sm.add_widget(MLStatsScreen())
        
        # Навигационный дроер
        nav_drawer = MDNavigationDrawer(
            id="nav_drawer",
            radius=(0, dp(16), dp(16), 0)
        )
        
        nav_content = MDBoxLayout(orientation="vertical", padding=dp(16), spacing=dp(8))
        
        # Заголовок меню
        nav_header = MDLabel(
            text="⚽ SStats Pro",
            font_style="H5",
            size_hint_y=None,
            height=dp(56),
            theme_text_color="Primary"
        )
        nav_content.add_widget(nav_header)
        
        # Пункты меню
        menu_items = [
            ("soccer-field", "Matches", "matches"),
            ("history", "History", "history"),
            ("brain", "ML Stats", "ml_stats"),
            ("cog", "Settings", "settings"),
        ]
        
        for icon, text, screen in menu_items:
            item = OneLineListItem(
                text=text,
                on_release=lambda x, s=screen: self.switch_screen(s, nav_drawer)
            )
            nav_content.add_widget(item)
        
        nav_content.add_widget(MDBoxLayout())  # Spacer
        
        # Инфо
        version_label = MDLabel(
            text=f"v{__version__}",
            font_style="Caption",
            theme_text_color="Secondary",
            halign="center"
        )
        nav_content.add_widget(version_label)
        
        nav_drawer.add_widget(nav_content)
        
        # Root layout
        root = MDBoxLayout(orientation="horizontal")
        root.add_widget(sm)
        root.add_widget(nav_drawer)
        
        # Сохраняем ссылки
        root.ids = {'nav_drawer': nav_drawer}
        self.screen_manager = sm
        
        return root
    
    def switch_screen(self, screen_name: str, nav_drawer=None):
        """Переключение экранов"""
        if screen_name in [s.name for s in self.screen_manager.screens]:
            self.screen_manager.current = screen_name
        
        if nav_drawer:
            nav_drawer.set_state("closed")
    
    def show_match_analysis(self, match_data: Dict):
        """Показать анализ матча"""
        analysis_screen = self.screen_manager.get_screen("analysis")
        analysis_screen.match_data = match_data
        self.screen_manager.current = "analysis"


if __name__ == '__main__':
    SStatsApp().run()
