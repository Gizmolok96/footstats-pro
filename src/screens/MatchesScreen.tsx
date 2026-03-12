import React, { useState, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SectionList,
  Pressable,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
  TextInput,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/Ionicons';
import { Colors } from '../constants/colors';
import { apiFetch } from '../lib/api';

// Types
interface Team {
  id: number;
  name: string;
  shortName?: string;
}

interface League {
  id: number;
  name: string;
  country?: string;
}

interface Match {
  id: number;
  date: string;
  homeTeam: Team;
  awayTeam: Team;
  league: League;
  status: string | number;
  statusName?: string;
  homeResult: number | null;
  awayResult: number | null;
  startTime?: string;
  minute?: number | null;
}

// Helpers
function getTodayDateStr() {
  return new Date().toISOString().split('T')[0];
}

function formatDate(d: Date) {
  return d.toISOString().split('T')[0];
}

function addDays(d: Date, n: number) {
  const r = new Date(d);
  r.setDate(r.getDate() + n);
  return r;
}

function getDayLabel(dateStr: string, today: string) {
  if (dateStr === today) return 'Today';
  const yesterday = formatDate(addDays(new Date(today), -1));
  if (dateStr === yesterday) return 'Yesterday';
  const tomorrow = formatDate(addDays(new Date(today), 1));
  if (dateStr === tomorrow) return 'Tomorrow';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}

const NOT_STARTED_NAMES = new Set(['not started', 'scheduled', 'tbd', 'ns']);
const ENDED_NAMES = new Set([
  'finished', 'ended', 'ft', 'full time', 'fulltime',
  'finished after extra time', 'finished after penalty',
  'aet', 'after penalties', 'finished after penalties',
]);
const CANCELLED_NAMES = new Set([
  'postponed', 'cancelled', 'abandoned', 'suspended', 'walkover', 'awarded',
]);

function getStatusName(match: Match): string {
  return String(match.statusName || '').toLowerCase().trim();
}

function isFinished(match: Match) {
  const name = getStatusName(match);
  if (ENDED_NAMES.has(name)) return true;
  if (name) return false;
  const num = Number(match.status);
  return num === 8 || num === 9 || num === 10;
}

function isLive(match: Match) {
  const name = getStatusName(match);
  if (NOT_STARTED_NAMES.has(name)) return false;
  if (ENDED_NAMES.has(name)) return false;
  if (CANCELLED_NAMES.has(name)) return false;
  if (name) return true;
  const num = Number(match.status);
  if (num === 2 || (num >= 8 && num <= 14)) return false;
  return !isNaN(num) && num > 0;
}

function getLiveLabel(match: Match): string {
  const name = getStatusName(match);
  if (name.includes('half time') || name === 'ht') return 'HT';
  if (name.includes('1st') || name.includes('first half') || name === '1h') return '1H';
  if (name.includes('2nd') || name.includes('second half') || name === '2h') return '2H';
  if (name.includes('extra time') || name === 'et') return 'ET';
  if (name.includes('penalty') || name === 'pen') return 'PEN';
  if (name) return name.toUpperCase().slice(0, 4);
  return 'LIVE';
}

function getMatchTime(match: Match) {
  if (!match.date) return '';
  const d = new Date(match.date);
  if (isNaN(d.getTime())) return '';
  return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
}

// Components
function DatePicker({ selected, onSelect }: { selected: string; onSelect: (d: string) => void }) {
  const today = getTodayDateStr();
  const days: string[] = [];
  for (let i = -3; i <= 4; i++) {
    days.push(formatDate(addDays(new Date(today), i)));
  }

  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={styles.datePicker}>
      {days.map((d) => {
        const isSelected = d === selected;
        const isToday = d === today;
        const label = getDayLabel(d, today);
        const dayOfMonth = new Date(d).getDate();
        const dayName = label === 'Today' || label === 'Yesterday' || label === 'Tomorrow'
          ? label
          : new Date(d).toLocaleDateString('en-US', { weekday: 'short' });

        return (
          <Pressable
            key={d}
            onPress={() => onSelect(d)}
            style={[
              styles.dateItem,
              isSelected && styles.dateItemSelected,
              isToday && !isSelected && styles.dateItemToday,
            ]}>
            <Text
              style={[
                styles.dateItemDay,
                isSelected && styles.dateItemTextSelected,
                !isSelected && { color: Colors.textSecondary },
              ]}>
              {dayName.length > 3 ? dayName.slice(0, 3) : dayName}
            </Text>
            <Text
              style={[
                styles.dateItemNum,
                isSelected && styles.dateItemTextSelected,
                !isSelected && { color: Colors.text },
              ]}>
              {dayOfMonth}
            </Text>
          </Pressable>
        );
      })}
    </ScrollView>
  );
}

type Filter = 'all' | 'live' | 'upcoming' | 'finished';

function FilterBar({ active, onPress, liveCount }: { active: Filter; onPress: (f: Filter) => void; liveCount: number }) {
  const filters: { key: Filter; label: string }[] = [
    { key: 'all', label: 'All' },
    { key: 'live', label: 'Live' },
    { key: 'upcoming', label: 'Upcoming' },
    { key: 'finished', label: 'Finished' },
  ];

  return (
    <View style={styles.filterBar}>
      {filters.map((f) => (
        <Pressable
          key={f.key}
          onPress={() => onPress(f.key)}
          style={[styles.filterBtn, active === f.key && styles.filterBtnActive]}>
          {f.key === 'live' && (
            <View style={[styles.liveDot, active === 'live' && { backgroundColor: '#fff' }]} />
          )}
          <Text style={[styles.filterText, active === f.key && styles.filterTextActive]}>
            {f.label}
          </Text>
          {f.key === 'live' && liveCount > 0 && (
            <View style={[styles.liveCountBadge, active === 'live' && { backgroundColor: 'rgba(255,255,255,0.25)' }]}>
              <Text style={styles.liveCountText}>{liveCount}</Text>
            </View>
          )}
        </Pressable>
      ))}
    </View>
  );
}

function SearchBar({ value, onChange }: { value: string; onChange: (text: string) => void }) {
  return (
    <View style={styles.searchContainer}>
      <Icon name="search-outline" size={16} color={Colors.textMuted} style={styles.searchIcon} />
      <TextInput
        style={styles.searchInput}
        value={value}
        onChangeText={onChange}
        placeholder="Search teams..."
        placeholderTextColor={Colors.textMuted}
        autoCorrect={false}
        autoCapitalize="none"
      />
      {value.length > 0 && (
        <Pressable onPress={() => onChange('')} style={styles.searchClear}>
          <Icon name="close-circle" size={16} color={Colors.textMuted} />
        </Pressable>
      )}
    </View>
  );
}

const MatchCard = React.memo(function MatchCard({ match, onPress }: { match: Match; onPress: () => void }) {
  const finished = isFinished(match);
  const live = isLive(match);
  const time = getMatchTime(match);
  const liveLabel = getLiveLabel(match);

  const homeName = match.homeTeam?.name || 'Home';
  const awayName = match.awayTeam?.name || 'Away';

  return (
    <Pressable style={({ pressed }) => [styles.matchCard, pressed && { opacity: 0.85 }]} onPress={onPress}>
      <View style={styles.matchCardInner}>
        <View style={styles.teamRow}>
          <View style={styles.teamSide}>
            <View style={styles.teamBadge}>
              <Text style={styles.teamBadgeText}>{homeName.slice(0, 2).toUpperCase()}</Text>
            </View>
            <Text style={styles.teamName} numberOfLines={1}>{homeName}</Text>
          </View>

          <View style={styles.scoreBox}>
            {finished ? (
              <View style={styles.scoreDisplay}>
                <Text style={styles.scoreText}>{match.homeResult ?? '–'}</Text>
                <Text style={styles.scoreSep}>:</Text>
                <Text style={styles.scoreText}>{match.awayResult ?? '–'}</Text>
              </View>
            ) : live ? (
              <View style={styles.liveBox}>
                <View style={styles.livePulse} />
                <Text style={styles.liveText}>{liveLabel}</Text>
              </View>
            ) : (
              <Text style={styles.matchTime}>{time}</Text>
            )}
          </View>

          <View style={[styles.teamSide, styles.teamSideAway]}>
            <View style={[styles.teamBadge, styles.teamBadgeAway]}>
              <Text style={styles.teamBadgeText}>{awayName.slice(0, 2).toUpperCase()}</Text>
            </View>
            <Text style={[styles.teamName, styles.teamNameAway]} numberOfLines={1}>{awayName}</Text>
          </View>
        </View>

        <View style={styles.matchCardFooter}>
          <Icon name="analytics-outline" size={11} color={Colors.accent} />
          <Text style={styles.analysisHint}>Tap to analyze</Text>
        </View>
      </View>
    </Pressable>
  );
});

const SectionHeader = React.memo(function SectionHeader({ title, count, expanded, onToggle }: { title: string; count: number; expanded: boolean; onToggle: () => void }) {
  return (
    <Pressable style={styles.leagueHeader} onPress={onToggle}>
      <View style={styles.leagueBadge}>
        <Icon name="football-outline" size={12} color={Colors.accent} />
      </View>
      <Text style={styles.leagueName} numberOfLines={1}>{title}</Text>
      <Text style={styles.leagueCount}>{count}</Text>
      <Icon name={expanded ? 'chevron-up' : 'chevron-down'} size={14} color={Colors.textMuted} />
    </Pressable>
  );
});

interface Section {
  title: string;
  totalCount: number;
  data: Match[];
}

export default function MatchesScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation();
  const today = getTodayDateStr();
  const [selectedDate, setSelectedDate] = useState(today);
  const [filter, setFilter] = useState<Filter>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());

  const toggleSection = useCallback((title: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(title)) next.delete(title);
      else next.add(title);
      return next;
    });
  }, []);

  const { data: dayData, refetch: refetchDay, isRefetching: isRefetchingDay } = useQuery<{ matches: Match[] }>({
    queryKey: ['/api/matches', selectedDate],
    queryFn: async () => {
      const url = `/api/matches?date=${selectedDate}&limit=500`;
      const res = await apiFetch(url);
      if (!res.ok) throw new Error('Failed to fetch matches');
      return res.json();
    },
    staleTime: 5 * 60 * 1000,
  });

  const { data: liveData, isLoading: liveLoading, isError: liveError, refetch: refetchLive, isRefetching: isRefetchingLive } = useQuery<{ matches: Match[] }>({
    queryKey: ['/api/matches/live'],
    queryFn: async () => {
      const res = await apiFetch('/api/matches/live');
      if (!res.ok) throw new Error('Failed to fetch live matches');
      return res.json();
    },
    enabled: filter === 'live',
    staleTime: 0,
    refetchInterval: 30000,
  });

  const allMatches = dayData?.matches || [];
  const totalMatchCount = (dayData as unknown as { total?: number })?.total ?? allMatches.length;
  const liveMatches = liveData?.matches || allMatches.filter(isLive);

  const isLoading = filter === 'live' ? liveLoading : !dayData;
  const isError = filter === 'live' ? liveError : false;
  const isRefetching = filter === 'live' ? isRefetchingLive : isRefetchingDay;
  const refetch = filter === 'live' ? refetchLive : refetchDay;

  const matchPool = filter === 'live' ? liveMatches : allMatches;

  const filteredMatches = matchPool
    .filter((m) => {
      if (filter === 'finished') return isFinished(m);
      if (filter === 'upcoming') return !isLive(m) && !isFinished(m);
      return true;
    })
    .filter((m) => {
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase();
      const home = (m.homeTeam?.name || '').toLowerCase();
      const away = (m.awayTeam?.name || '').toLowerCase();
      return home.includes(q) || away.includes(q);
    });

  const isSearching = searchQuery.trim().length > 0;
  const sections = useMemo<Section[]>(() => {
    const byLeague = filteredMatches.reduce<Record<string, Match[]>>((acc, m) => {
      const key = m.league?.name || 'Unknown League';
      if (!acc[key]) acc[key] = [];
      acc[key].push(m);
      return acc;
    }, {});
    return Object.keys(byLeague).map((title) => ({
      title,
      totalCount: byLeague[title].length,
      data: isSearching || expandedSections.has(title) ? byLeague[title] : [],
    }));
  }, [filteredMatches, expandedSections, isSearching]);

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Icon name="football" size={22} color={Colors.accent} />
          <Text style={styles.headerTitle}>FootStats Pro</Text>
        </View>
        <Text style={styles.matchCount}>{totalMatchCount > 0 ? `${totalMatchCount} matches` : ''}</Text>
      </View>

      <DatePicker selected={selectedDate} onSelect={(d) => { setSelectedDate(d); setSearchQuery(''); setExpandedSections(new Set()); }} />
      <FilterBar active={filter} onPress={(f) => { setFilter(f); setExpandedSections(new Set()); }} liveCount={liveMatches.length} />
      <SearchBar value={searchQuery} onChange={setSearchQuery} />

      {isLoading ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={Colors.accent} />
          <Text style={styles.loadingText}>Fetching matches...</Text>
        </View>
      ) : isError ? (
        <View style={styles.centered}>
          <Icon name="cloud-offline-outline" size={48} color={Colors.textMuted} />
          <Text style={styles.errorText}>Failed to load matches</Text>
          <Pressable style={styles.retryBtn} onPress={() => refetch()}>
            <Text style={styles.retryText}>Retry</Text>
          </Pressable>
        </View>
      ) : sections.length === 0 ? (
        <View style={styles.centered}>
          <Icon name="calendar-outline" size={48} color={Colors.textMuted} />
          <Text style={styles.emptyText}>{searchQuery ? 'No teams found' : 'No matches found'}</Text>
          <Text style={styles.emptySubtext}>
            {searchQuery ? `No results for "${searchQuery}"` : filter !== 'all' ? 'Try a different filter' : 'Try another date'}
          </Text>
        </View>
      ) : (
        <SectionList
          sections={sections}
          keyExtractor={(item) => String(item.id)}
          renderItem={({ item }) => (
            <MatchCard 
              match={item} 
              onPress={() => navigation.navigate('MatchAnalysis', { id: item.id })}
            />
          )}
          renderSectionHeader={({ section }) => (
            <SectionHeader
              title={section.title}
              count={section.totalCount}
              expanded={isSearching || expandedSections.has(section.title)}
              onToggle={() => toggleSection(section.title)}
            />
          )}
          renderSectionFooter={() => <View style={{ height: 8 }} />}
          contentContainerStyle={[styles.list, { paddingBottom: insets.bottom + 70 }]}
          showsVerticalScrollIndicator={false}
          stickySectionHeadersEnabled={false}
          removeClippedSubviews
          maxToRenderPerBatch={10}
          updateCellsBatchingPeriod={50}
          windowSize={5}
          initialNumToRender={20}
          refreshControl={
            <RefreshControl
              refreshing={!!isRefetching}
              onRefresh={() => { setExpandedSections(new Set()); refetch(); }}
              tintColor={Colors.accent}
            />
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingVertical: 10 },
  headerLeft: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  headerTitle: { fontSize: 20, fontWeight: '700', color: Colors.text },
  matchCount: { fontSize: 13, color: Colors.textMuted },
  datePicker: { paddingHorizontal: 12, paddingBottom: 8, gap: 8 },
  dateItem: { width: 52, height: 60, borderRadius: 12, backgroundColor: Colors.bgCard, alignItems: 'center', justifyContent: 'center', gap: 2, borderWidth: 1, borderColor: Colors.border },
  dateItemSelected: { backgroundColor: Colors.accent, borderColor: Colors.accent },
  dateItemToday: { borderColor: Colors.accentDim },
  dateItemDay: { fontSize: 10, fontWeight: '500' },
  dateItemNum: { fontSize: 18, fontWeight: '700' },
  dateItemTextSelected: { color: '#fff' },
  filterBar: { flexDirection: 'row', paddingHorizontal: 12, paddingBottom: 8, gap: 8 },
  filterBtn: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20, backgroundColor: Colors.bgCard, flexDirection: 'row', alignItems: 'center', gap: 5, borderWidth: 1, borderColor: Colors.border },
  filterBtnActive: { backgroundColor: Colors.accent, borderColor: Colors.accent },
  filterText: { fontSize: 13, fontWeight: '500', color: Colors.textSecondary },
  filterTextActive: { color: '#fff' },
  liveDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: Colors.red },
  liveCountBadge: { backgroundColor: Colors.redDim, borderRadius: 8, paddingHorizontal: 5, paddingVertical: 1, minWidth: 18, alignItems: 'center' },
  liveCountText: { fontSize: 10, fontWeight: '700', color: Colors.red },
  searchContainer: { flexDirection: 'row', alignItems: 'center', marginHorizontal: 12, marginBottom: 8, backgroundColor: Colors.bgCard, borderRadius: 12, borderWidth: 1, borderColor: Colors.border, paddingHorizontal: 12, height: 40 },
  searchIcon: { marginRight: 8 },
  searchInput: { flex: 1, fontSize: 14, color: Colors.text, height: '100%' },
  searchClear: { padding: 4, marginLeft: 4 },
  list: { paddingTop: 4, paddingHorizontal: 12 },
  leagueHeader: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 10, paddingVertical: 8, backgroundColor: Colors.bgCard, borderRadius: 10, marginBottom: 4, gap: 6 },
  leagueBadge: { width: 22, height: 22, borderRadius: 6, backgroundColor: Colors.accentDim, alignItems: 'center', justifyContent: 'center' },
  leagueName: { flex: 1, fontSize: 13, fontWeight: '600', color: Colors.text },
  leagueCount: { fontSize: 12, color: Colors.textMuted, marginRight: 4 },
  matchCard: { marginBottom: 4, borderRadius: 10, backgroundColor: Colors.bgCardDark, borderWidth: 1, borderColor: Colors.border, overflow: 'hidden' },
  matchCardInner: { padding: 12 },
  teamRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  teamSide: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: 8 },
  teamSideAway: { justifyContent: 'flex-end' },
  teamBadge: { width: 32, height: 32, borderRadius: 8, backgroundColor: Colors.blueDim, alignItems: 'center', justifyContent: 'center' },
  teamBadgeAway: { backgroundColor: '#3B1F5F' },
  teamBadgeText: { fontSize: 10, fontWeight: '700', color: Colors.text },
  teamName: { flex: 1, fontSize: 13, fontWeight: '500', color: Colors.text },
  teamNameAway: { textAlign: 'right' },
  scoreBox: { width: 72, alignItems: 'center', justifyContent: 'center' },
  scoreDisplay: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  scoreText: { fontSize: 20, fontWeight: '700', color: Colors.text },
  scoreSep: { fontSize: 16, fontWeight: '700', color: Colors.textMuted },
  liveBox: { flexDirection: 'row', alignItems: 'center', gap: 5, backgroundColor: '#1A0A0A', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8, borderWidth: 1, borderColor: Colors.red },
  livePulse: { width: 6, height: 6, borderRadius: 3, backgroundColor: Colors.red },
  liveText: { fontSize: 11, fontWeight: '700', color: Colors.red },
  matchTime: { fontSize: 15, fontWeight: '600', color: Colors.textSecondary },
  matchCardFooter: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 8, paddingTop: 6, borderTopWidth: 1, borderTopColor: Colors.border },
  analysisHint: { fontSize: 11, color: Colors.accent },
  centered: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12 },
  loadingText: { fontSize: 14, color: Colors.textMuted },
  errorText: { fontSize: 15, fontWeight: '500', color: Colors.textSecondary, marginTop: 8 },
  emptyText: { fontSize: 16, fontWeight: '600', color: Colors.textSecondary },
  emptySubtext: { fontSize: 14, color: Colors.textMuted },
  retryBtn: { backgroundColor: Colors.accent, paddingHorizontal: 24, paddingVertical: 10, borderRadius: 10, marginTop: 8 },
  retryText: { fontSize: 14, fontWeight: '600', color: '#fff' },
});
