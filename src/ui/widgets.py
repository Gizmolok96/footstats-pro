"""
Кастомные виджеты Material Design 3
"""

from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import StringProperty, NumericProperty, ListProperty, ColorProperty
from kivy.animation import Animation
from kivy.graphics import Color, RoundedRectangle, Line

from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.behaviors import RoundedRectangularElevationBehavior


class MaterialCard(MDCard, RoundedRectangularElevationBehavior):
    """Карточка с эффектом Material Design 3"""
    
    elevation_level = NumericProperty(1)
    ripple_color = ColorProperty([0, 0, 0, 0.1])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.radius = [dp(16), dp(16), dp(16), dp(16)]
        self.bind(elevation_level=self.update_elevation)
    
    def update_elevation(self, *args):
        self.elevation = self.elevation_level * 2


class ProbabilityIndicator(MDBoxLayout):
    """Индикатор вероятности с анимацией"""
    
    value = NumericProperty(0)
    label = StringProperty("")
    color = ListProperty([0.23, 0.51, 0.96, 1])  # Primary blue
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(60)
        self.build_ui()
    
    def build_ui(self):
        # Заголовок
        self.header = MDBoxLayout(size_hint_y=None, height=dp(24))
        self.label_widget = MDLabel(
            text=self.label,
            font_style="Caption",
            theme_text_color="Secondary"
        )
        self.value_label = MDLabel(
            text=f"{self.value}%",
            halign="right",
            font_style="Body1",
            bold=True
        )
        self.header.add_widget(self.label_widget)
        self.header.add_widget(self.value_label)
        self.add_widget(self.header)
        
        # Прогресс-бар кастомный
        self.progress_box = MDBoxLayout(size_hint_y=None, height=dp(8))
        self.add_widget(self.progress_box)
        
        self.bind(value=self.update_value)
    
    def update_value(self, instance, value):
        self.value_label.text = f"{value}%"
        # Анимация заполнения
        anim = Animation(width=value/100 * self.width, duration=0.5, t='out_quad')
        # Здесь можно добавить кастомную графику прогресса
    
    def on_parent(self, *args):
        if self.parent:
            self.update_value(self, self.value)


class TrendIndicator(MDBoxLayout):
    """Индикатор тренда команды (рост/падение)"""
    
    trend_value = NumericProperty(0)  # -1 to 1
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_x = None
        self.width = dp(60)
        self.build_ui()
    
    def build_ui(self):
        self.icon = MDIconButton(
            icon="trending-flat",
            theme_text_color="Secondary"
        )
        self.add_widget(self.icon)
        self.bind(trend_value=self.update_icon)
    
    def update_icon(self, instance, value):
        if value > 0.3:
            self.icon.icon = "trending-up"
            self.icon.theme_text_color = "Custom"
            self.icon.text_color = self.theme_cls.success_color
        elif value < -0.3:
            self.icon.icon = "trending-down"
            self.icon.theme_text_color = "Custom"
            self.icon.text_color = self.theme_cls.error_color
        else:
            self.icon.icon = "trending-flat"
            self.icon.theme_text_color = "Secondary"


class LeagueBadge(MDBoxLayout):
    """Бейдж лиги с цветовой индикацией"""
    
    league_name = StringProperty("Unknown")
    
    LEAGUE_COLORS = {
        'premier league': '#3b82f6',
        'la liga': '#ef4444',
        'serie a': '#22c55e',
        'bundesliga': '#eab308',
        'ligue 1': '#8b5cf6',
        'rpl': '#f97316',
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_x = None
        self.padding = [dp(8), dp(4)]
        self.build_ui()
    
    def build_ui(self):
        from kivymd.uix.chip import MDChip
        color = self.get_league_color()
        
        self.chip = MDChip(
            text=self.league_name[:15],
            icon="trophy",
            md_bg_color=color,
            size_hint_x=None,
            width=dp(120)
        )
        self.add_widget(self.chip)
    
    def get_league_color(self):
        league_lower = self.league_name.lower()
        for key, color in self.LEAGUE_COLORS.items():
            if key in league_lower:
                return color
        return '#64748b'  # Default gray


class ConfidenceBadge(MDLabel):
    """Бейдж уверенности прогноза"""
    
    confidence = NumericProperty(50)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_x = None
        self.width = dp(80)
        self.halign = "center"
        self.radius = [dp(12), dp(12), dp(12), dp(12)]
        self.bind(confidence=self.update_style)
    
    def update_style(self, instance, value):
        self.text = f"{value}%"
        
        if value >= 70:
            self.md_bg_color = self.theme_cls.success_color
            self.theme_text_color = "Custom"
            self.text_color = [1, 1, 1, 1]
        elif value >= 50:
            self.md_bg_color = self.theme_cls.warning_color
            self.theme_text_color = "Custom"
            self.text_color = [0, 0, 0, 1]
        else:
            self.md_bg_color = self.theme_cls.error_color
            self.theme_text_color = "Custom"
            self.text_color = [1, 1, 1, 1]
