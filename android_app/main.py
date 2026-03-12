from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.properties import StringProperty, ListProperty, NumericProperty
from kivy.network.urlrequest import UrlRequest
from kivy.storage.jsonstore import JsonStore
from kivy.clock import Clock
from kivy.metrics import dp
import json
from datetime import datetime, timedelta

# Colors matching the React Native app
COLORS = {
    'bg': '#0A0E1A',
    'bg_secondary': '#111827',
    'bg_card': '#1A2235',
    'bg_card_dark': '#141C2E',
    'border': '#1E2D45',
    'accent': '#10B981',
    'accent_dim': '#065F46',
    'blue': '#3B82F6',
    'blue_dim': '#1E3A5F',
    'amber': '#F59E0B',
    'amber_dim': '#78350F',
    'red': '#EF4444',
    'red_dim': '#7F1D1D',
    'text': '#F9FAFB',
    'text_secondary': '#94A3B8',
    'text_muted': '#64748B',
    'home': '#3B82F6',
    'away': '#8B5CF6',
}

API_KEY = "gbi1ldi9446kastj"
API_BASE = "https://api.sstats.net"


class ModernLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_name = 'Roboto'
        self.color = self.get_color(COLORS['text'])
        self.bind(pos=self.update_rect, size=self.update_rect)
        
    def get_color(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4)) + (1,)
    
    def update_rect(self, *args):
        pass


class Card(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(16)
        self.spacing = dp(10)
        self.size_hint_y = None
        self.bind(minimum_height=self.setter('height'))
        
        with self.canvas.before:
            Color(*self.get_color(COLORS['bg_card']))
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])
            Color(*self.get_color(COLORS['border']))
            self.border = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])
        self.bind(pos=self.update_rect, size=self.update_rect)
    
    def get_color(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4)) + (1,)
    
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.border.pos = self.pos
        self.border.size = self.size


class MatchCard(BoxLayout):
    match_id = NumericProperty(0)
    
    def __init__(self, match_data, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(100)
        self.padding = dp(12)
        self.spacing = dp(8)
        
        self.match_data = match_data
        self.match_id = match_data.get('id', 0)
        
        with self.canvas.before:
            Color(*self.get_color(COLORS['bg_card_dark']))
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
            Color(*self.get_color(COLORS['border']))
            self.border = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
        self.bind(pos=self.update_rect, size=self.update_rect)
        
        # Teams row
        teams_row = BoxLayout(orientation='horizontal', size_hint_y=0.7)
        
        home_team = match_data.get('homeTeam', {}).get('name', 'Home')
        away_team = match_data.get('awayTeam', {}).get('name', 'Away')
        
        # Home team
        home_box = BoxLayout(orientation='horizontal')
        home_badge = self.create_badge(home_team[:2].upper(), COLORS['blue_dim'])
        home_label = ModernLabel(text=home_team, font_size=dp(13), halign='left', valign='center')
        home_box.add_widget(home_badge)
        home_box.add_widget(home_label)
        
        # Score/Time
        score_box = BoxLayout(orientation='horizontal', size_hint_x=0.3)
        status = match_data.get('status', 0)
        home_result = match_data.get('homeResult')
        away_result = match_data.get('awayResult')
        
        if home_result is not None and away_result is not None:
            score_label = ModernLabel(
                text=f"{home_result} - {away_result}",
                font_size=dp(20),
                bold=True,
                halign='center'
            )
        else:
            time_str = self.format_time(match_data.get('date', ''))
            score_label = ModernLabel(text=time_str, font_size=dp(15), halign='center')
        
        score_box.add_widget(score_label)
        
        # Away team
        away_box = BoxLayout(orientation='horizontal')
        away_badge = self.create_badge(away_team[:2].upper(), '#3B1F5F')
        away_label = ModernLabel(text=away_team, font_size=dp(13), halign='right', valign='center')
        away_box.add_widget(away_label)
        away_box.add_widget(away_badge)
        
        teams_row.add_widget(home_box)
        teams_row.add_widget(score_box)
        teams_row.add_widget(away_box)
        
        # Footer
        footer = BoxLayout(orientation='horizontal', size_hint_y=0.3)
        hint = ModernLabel(text="Tap to analyze", font_size=dp(11), color=self.get_color(COLORS['accent']))
        footer.add_widget(hint)
        
        self.add_widget(teams_row)
        self.add_widget(footer)
        
        self.bind(on_touch_down=self.on_card_touch)
    
    def create_badge(self, text, color):
        badge = BoxLayout(size_hint=(None, None), size=(dp(32), dp(32)))
        with badge.canvas.before:
            Color(*self.get_color(color))
            badge.rect = RoundedRectangle(pos=badge.pos, size=badge.size, radius=[dp(8)])
        badge.bind(pos=self.update_badge_rect, size=self.update_badge_rect)
        label = ModernLabel(text=text, font_size=dp(10), bold=True)
        badge.add_widget(label)
        return badge
    
    def update_badge_rect(self, instance, value):
        instance.rect.pos = instance.pos
        instance.rect.size = instance.size
    
    def get_color(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4)) + (1,)
    
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.border.pos = self.pos
        self.border.size = self.size
    
    def format_time(self, date_str):
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%H:%M')
        except:
            return '--:--'
    
    def on_card_touch(self, touch):
        if self.collide_point(*touch.pos):
            # Navigate to match detail
            app = App.get_running_app()
            app.show_match_detail(self.match_id)


class MatchesScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.store = JsonStore('footstats_cache.json')
        self.matches = []
        self.selected_date = datetime.now().strftime('%Y-%m-%d')
        
        layout = BoxLayout(orientation='vertical')
        
        # Header
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), padding=dp(16))
        title = ModernLabel(text='FootStats Pro', font_size=dp(20), bold=True, halign='left')
        header.add_widget(title)
        layout.add_widget(header)
        
        # Date picker
        self.date_scroll = ScrollView(size_hint_y=None, height=dp(80), do_scroll_y=False)
        self.date_layout = BoxLayout(orientation='horizontal', size_hint_x=None, width=dp(400), spacing=dp(8), padding=dp(12))
        self.update_date_picker()
        self.date_scroll.add_widget(self.date_layout)
        layout.add_widget(self.date_scroll)
        
        # Filter buttons
        filter_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), padding=dp(12), spacing=dp(8))
        for filter_name in ['All', 'Live', 'Upcoming', 'Finished']:
            btn = Button(
                text=filter_name,
                background_color=self.get_color(COLORS['bg_card']),
                color=self.get_color(COLORS['text']),
                background_normal=''
            )
            btn.bind(on_press=lambda x, f=filter_name: self.set_filter(f))
            filter_box.add_widget(btn)
        layout.add_widget(filter_box)
        
        # Search
        search_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), padding=dp(12))
        self.search_input = TextInput(
            hint_text='Search teams...',
            background_color=self.get_color(COLORS['bg_card']),
            foreground_color=self.get_color(COLORS['text']),
            padding=dp(10),
            multiline=False
        )
        self.search_input.bind(text=self.on_search)
        search_box.add_widget(self.search_input)
        layout.add_widget(search_box)
        
        # Matches list
        self.scroll = ScrollView()
        self.matches_layout = GridLayout(cols=1, spacing=dp(10), padding=dp(12), size_hint_y=None)
        self.matches_layout.bind(minimum_height=self.matches_layout.setter('height'))
        self.scroll.add_widget(self.matches_layout)
        layout.add_widget(self.scroll)
        
        self.add_widget(layout)
        
        # Load matches
        self.load_matches()
        Clock.schedule_interval(self.refresh_matches, 30)
    
    def get_color(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4)) + (1,)
    
    def update_date_picker(self):
        self.date_layout.clear_widgets()
        today = datetime.now()
        for i in range(-3, 5):
            date = today + timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            day_name = date.strftime('%a')
            day_num = date.strftime('%d')
            
            if i == 0:
                day_name = 'Today'
            
            btn = Button(
                text=f'{day_name}\n{day_num}',
                size_hint=(None, None),
                size=(dp(60), dp(70)),
                background_color=self.get_color(COLORS['accent'] if date_str == self.selected_date else COLORS['bg_card']),
                color=self.get_color('#fff' if date_str == self.selected_date else COLORS['text']),
                background_normal='',
                halign='center'
            )
            btn.bind(on_press=lambda x, d=date_str: self.select_date(d))
            self.date_layout.add_widget(btn)
    
    def select_date(self, date_str):
        self.selected_date = date_str
        self.update_date_picker()
        self.load_matches()
    
    def set_filter(self, filter_name):
        self.current_filter = filter_name.lower()
        self.display_matches()
    
    def on_search(self, instance, value):
        self.search_query = value.lower()
        self.display_matches()
    
    def load_matches(self):
        url = f"{API_BASE}/api/matches?date={self.selected_date}&limit=500&apikey={API_KEY}"
        UrlRequest(url, self.on_matches_loaded, on_error=self.on_error)
    
    def on_matches_loaded(self, request, result):
        data = json.loads(result) if isinstance(result, str) else result
        self.matches = data.get('matches', [])
        self.display_matches()
    
    def display_matches(self):
        self.matches_layout.clear_widgets()
        
        filter_type = getattr(self, 'current_filter', 'all')
        search = getattr(self, 'search_query', '')
        
        filtered = self.matches
        if filter_type == 'live':
            filtered = [m for m in filtered if self.is_live(m)]
        elif filter_type == 'finished':
            filtered = [m for m in filtered if self.is_finished(m)]
        elif filter_type == 'upcoming':
            filtered = [m for m in filtered if not self.is_live(m) and not self.is_finished(m)]
        
        if search:
            filtered = [m for m in filtered if search in m.get('homeTeam', {}).get('name', '').lower() 
                       or search in m.get('awayTeam', {}).get('name', '').lower()]
        
        # Group by league
        by_league = {}
        for m in filtered:
            league = m.get('league', {}).get('name', 'Unknown')
            if league not in by_league:
                by_league[league] = []
            by_league[league].append(m)
        
        for league, matches in by_league.items():
            league_label = ModernLabel(
                text=f'{league} ({len(matches)})',
                font_size=dp(14),
                bold=True,
                size_hint_y=None,
                height=dp(40)
            )
            self.matches_layout.add_widget(league_label)
            
            for match in matches:
                card = MatchCard(match)
                self.matches_layout.add_widget(card)
    
    def is_live(self, match):
        status = str(match.get('statusName', '')).lower()
        return status and status not in ['finished', 'not started', 'scheduled']
    
    def is_finished(self, match):
        status = str(match.get('statusName', '')).lower()
        return 'finished' in status or match.get('homeResult') is not None
    
    def refresh_matches(self, dt):
        self.load_matches()
        return True
    
    def on_error(self, request, error):
        print(f"Error loading matches: {error}")


class FootStatsApp(App):
    def build(self):
        self.sm = ScreenManager()
        self.sm.add_widget(MatchesScreen(name='matches'))
        return self.sm
    
    def show_match_detail(self, match_id):
        # Implement match detail screen
        pass


if __name__ == '__main__':
    FootStatsApp().run()
