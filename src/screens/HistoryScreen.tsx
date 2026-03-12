import React, { useCallback, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  Pressable,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/Ionicons';
import { Colors } from '../constants/colors';

const HISTORY_KEY = 'footstats_history';

interface HistoryItem {
  matchId: number;
  homeTeam: string;
  awayTeam: string;
  league: string;
  date: string;
  analyzedAt: string;
  homeWinPct: number;
  drawPct: number;
  awayWinPct: number;
  mostLikelyScore: string;
  over25Pct: number;
  bttsPct: number;
  homeResult: number | null;
  awayResult: number | null;
  status: string;
}

export async function saveToHistory(item: HistoryItem) {
  try {
    const raw = await AsyncStorage.getItem(HISTORY_KEY);
    const existing: HistoryItem[] = raw ? JSON.parse(raw) : [];
    const filtered = existing.filter((e) => e.matchId !== item.matchId);
    const updated = [item, ...filtered].slice(0, 100);
    await AsyncStorage.setItem(HISTORY_KEY, JSON.stringify(updated));
  } catch {
    /* ignore */
  }
}

export async function clearHistory() {
  await AsyncStorage.removeItem(HISTORY_KEY);
}

function ProbBar({ home, draw, away }: { home: number; draw: number; away: number }) {
  return (
    <View style={styles.probBarWrap}>
      <View style={[styles.probSegHome, { flex: home }]} />
      <View style={[styles.probSegDraw, { flex: draw }]} />
      <View style={[styles.probSegAway, { flex: away }]} />
    </View>
  );
}

function HistoryCard({ item, onDelete, onPress }: { item: HistoryItem; onDelete: () => void; onPress: () => void }) {
  const analyzedDate = new Date(item.analyzedAt);
  const timeStr =
    analyzedDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) +
    ' ' +
    analyzedDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

  const hasResult = item.homeResult !== null && item.awayResult !== null;

  const maxPct = Math.max(item.homeWinPct, item.drawPct, item.awayWinPct);
  let predictedWinner = 'Draw';
  if (item.homeWinPct === maxPct) predictedWinner = item.homeTeam;
  else if (item.awayWinPct === maxPct) predictedWinner = item.awayTeam;

  let outcomeCorrect: boolean | null = null;
  if (hasResult) {
    const actualWinner =
      (item.homeResult ?? 0) > (item.awayResult ?? 0)
        ? item.homeTeam
        : (item.homeResult ?? 0) < (item.awayResult ?? 0)
        ? item.awayTeam
        : 'Draw';
    outcomeCorrect = predictedWinner === actualWinner;
  }

  return (
    <Pressable style={({ pressed }) => [styles.card, pressed && { opacity: 0.85 }]} onPress={onPress}>
      <View style={styles.cardHeader}>
        <Text style={styles.leagueName} numberOfLines={1}>{item.league}</Text>
        <View style={styles.cardHeaderRight}>
          <Text style={styles.timeText}>{timeStr}</Text>
          <Pressable onPress={onDelete} hitSlop={12}>
            <Icon name="close-circle" size={18} color={Colors.textMuted} />
          </Pressable>
        </View>
      </View>

      <View style={styles.teamsRow}>
        <Text style={styles.teamText} numberOfLines={1}>{item.homeTeam}</Text>
        {hasResult ? (
          <View style={styles.resultBox}>
            <Text style={styles.resultText}>
              {item.homeResult} : {item.awayResult}
            </Text>
            {outcomeCorrect !== null && (
              <View style={[styles.outcomeTag, outcomeCorrect ? styles.outcomeCorrect : styles.outcomeWrong]}>
                <Icon name={outcomeCorrect ? 'checkmark' : 'close'} size={10} color="#fff" />
              </View>
            )}
          </View>
        ) : (
          <Text style={styles.vsText}>vs</Text>
        )}
        <Text style={[styles.teamText, { textAlign: 'right' }]} numberOfLines={1}>
          {item.awayTeam}
        </Text>
      </View>

      <ProbBar home={item.homeWinPct} draw={item.drawPct} away={item.awayWinPct} />

      <View style={styles.statsRow}>
        <View style={styles.statChip}>
          <Text style={styles.statChipLabel}>H</Text>
          <Text style={styles.statChipValue}>{item.homeWinPct.toFixed(0)}%</Text>
        </View>
        <View style={[styles.statChip, { backgroundColor: Colors.amberDim }]}>
          <Text style={[styles.statChipLabel, { color: Colors.amber }]}>X</Text>
          <Text style={styles.statChipValue}>{item.drawPct.toFixed(0)}%</Text>
        </View>
        <View style={[styles.statChip, { backgroundColor: '#3B1F5F' }]}>
          <Text style={[styles.statChipLabel, { color: Colors.away }]}>A</Text>
          <Text style={styles.statChipValue}>{item.awayWinPct.toFixed(0)}%</Text>
        </View>
        <View style={styles.statChipSm}>
          <Text style={styles.statSmLabel}>Score</Text>
          <Text style={styles.statSmValue}>{item.mostLikelyScore}</Text>
        </View>
        <View style={styles.statChipSm}>
          <Text style={styles.statSmLabel}>O2.5</Text>
          <Text style={styles.statSmValue}>{item.over25Pct.toFixed(0)}%</Text>
        </View>
      </View>
    </Pressable>
  );
}

export default function HistoryScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation();
  const [items, setItems] = useState<HistoryItem[]>([]);

  useFocusEffect(
    useCallback(() => {
      AsyncStorage.getItem(HISTORY_KEY).then((raw) => {
        setItems(raw ? JSON.parse(raw) : []);
      });
    }, [])
  );

  const handleDelete = useCallback(
    async (matchId: number) => {
      const updated = items.filter((i) => i.matchId !== matchId);
      setItems(updated);
      await AsyncStorage.setItem(HISTORY_KEY, JSON.stringify(updated));
    },
    [items]
  );

  const handleClearAll = useCallback(async () => {
    setItems([]);
    await clearHistory();
  }, []);

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Icon name="time" size={22} color={Colors.accent} />
          <Text style={styles.headerTitle}>Analysis History</Text>
        </View>
        {items.length > 0 && (
          <Pressable onPress={handleClearAll} style={styles.clearBtn}>
            <Text style={styles.clearText}>Clear all</Text>
          </Pressable>
        )}
      </View>

      {items.length === 0 ? (
        <View style={styles.emptyState}>
          <Icon name="football" size={56} color={Colors.border} />
          <Text style={styles.emptyTitle}>No analyses yet</Text>
          <Text style={styles.emptySubtitle}>Open a match from the Matches tab to get predictions</Text>
        </View>
      ) : (
        <FlatList
          data={items}
          keyExtractor={(item) => String(item.matchId)}
          renderItem={({ item }) => (
            <HistoryCard 
              item={item} 
              onDelete={() => handleDelete(item.matchId)}
              onPress={() => navigation.navigate('MatchAnalysis', { id: item.matchId })}
            />
          )}
          contentContainerStyle={[styles.list, { paddingBottom: insets.bottom + 70 }]}
          showsVerticalScrollIndicator={false}
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
  clearBtn: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8, borderWidth: 1, borderColor: Colors.border },
  clearText: { fontSize: 13, color: Colors.textMuted },
  list: { paddingHorizontal: 12, paddingTop: 4, gap: 10 },
  card: { backgroundColor: Colors.bgCard, borderRadius: 12, padding: 14, borderWidth: 1, borderColor: Colors.border, gap: 10, marginBottom: 10 },
  cardHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  cardHeaderRight: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  leagueName: { flex: 1, fontSize: 12, fontWeight: '500', color: Colors.textMuted },
  timeText: { fontSize: 11, color: Colors.textMuted },
  teamsRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8 },
  teamText: { flex: 1, fontSize: 14, fontWeight: '600', color: Colors.text },
  vsText: { fontSize: 13, color: Colors.textMuted },
  resultBox: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  resultText: { fontSize: 18, fontWeight: '700', color: Colors.text },
  outcomeTag: { width: 18, height: 18, borderRadius: 9, alignItems: 'center', justifyContent: 'center' },
  outcomeCorrect: { backgroundColor: Colors.accent },
  outcomeWrong: { backgroundColor: Colors.red },
  probBarWrap: { height: 4, borderRadius: 2, flexDirection: 'row', overflow: 'hidden', gap: 1 },
  probSegHome: { backgroundColor: Colors.home, borderRadius: 2 },
  probSegDraw: { backgroundColor: Colors.amber, borderRadius: 2 },
  probSegAway: { backgroundColor: Colors.away, borderRadius: 2 },
  statsRow: { flexDirection: 'row', gap: 6, flexWrap: 'wrap' },
  statChip: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8, backgroundColor: Colors.blueDim },
  statChipLabel: { fontSize: 10, fontWeight: '700', color: Colors.home },
  statChipValue: { fontSize: 12, fontWeight: '600', color: Colors.text },
  statChipSm: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8, backgroundColor: Colors.bgCardDark, borderWidth: 1, borderColor: Colors.border, alignItems: 'center' },
  statSmLabel: { fontSize: 9, color: Colors.textMuted },
  statSmValue: { fontSize: 12, fontWeight: '600', color: Colors.text },
  emptyState: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12, paddingHorizontal: 40 },
  emptyTitle: { fontSize: 18, fontWeight: '600', color: Colors.textSecondary },
  emptySubtitle: { fontSize: 14, color: Colors.textMuted, textAlign: 'center', lineHeight: 20 },
});
